import os
import json
import uuid
from typing import Any, Dict, List, Tuple, Optional

import chromadb
from FlagEmbedding import BGEM3FlagModel
from dotenv import load_dotenv
load_dotenv()
# ---------------------------------------
# Helpers
# ---------------------------------------
def _coerce_items_from_json(j: Any) -> List[Dict[str, Any]]:
    """
    Accetta:
      - list[dict] con chiavi: id (fac.), text|document|content|page_content (obbl.), metadata/meta (fac.)
      - dict con chiave wrapper: {'data'| 'items'| 'documents'| 'records': list[dict]}
      - dict come mappa id -> { ... }
      - stringa JSON (verrà json.loads)
    Ritorna: list di record normalizzati {id, text, metadata}
    """
    if isinstance(j, str):
        j = json.loads(j)

    if isinstance(j, list):
        items = j
    elif isinstance(j, dict):
        for key in ("data", "items", "documents", "records"):
            if key in j and isinstance(j[key], list):
                items = j[key]
                break
        else:
            items = [
                {"id": k, **(v if isinstance(v, dict) else {"text": str(v)})}
                for k, v in j.items()
            ]
    else:
        raise ValueError("Formato JSON non supportato.")

    norm: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            it = {"text": str(it)}
        text = (
            it.get("text")
            or it.get("document")
            or it.get("content")
            or it.get("page_content")
        )
        if not text:
            continue
        rec = {
            "id": str(it.get("id") or uuid.uuid4()),
            "text": str(text),
            "metadata": it.get("metadata") or it.get("meta") or {},
        }
        norm.append(rec)

    if not norm:
        raise ValueError("Nessun record valido trovato nel JSON (manca 'text'/'document'/'content').")
    return norm


def _chunks(seq: List[Any], n: int):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def build_client() -> "chromadb.api.client.Client":
    """
    Usa Chroma Cloud se è presente CHROMA_API_KEY, altrimenti fallback locale (in-memory).
    """
    api_key = os.getenv("CHROMA_API_KEY")
    tenant = os.getenv("CHROMA_TENANT")
    database = os.getenv("CHROMA_DATABASE")
    print(f"api_key: {api_key}")
    print(f"tenant: {tenant}")
    print(f"database: {database}")
    if api_key and (tenant or database):
        return chromadb.CloudClient(api_key=api_key, tenant=tenant, database=database)
    elif api_key:
        return chromadb.CloudClient(api_key=api_key)
    else:
        # Per test locali
        return chromadb.Client()


def build_bge_m3() -> BGEM3FlagModel:
    """
    Istanzia BGEM3FlagModel (BAAI/bge-m3). Se c'è GPU abilita fp16.
    """
    try:
        import torch
        use_fp16 = bool(torch.cuda.is_available())
    except Exception:
        use_fp16 = False

    return BGEM3FlagModel("BAAI/bge-m3", use_fp16=use_fp16)


def embed_texts(
    model: BGEM3FlagModel,
    texts: List[str],
    batch_size: int = 32,
    max_length: int = 8192,
) -> List[List[float]]:
    """
    Restituisce solo i dense embedding (1024-D per bge-m3).
    """
    dense_vectors: List[List[float]] = []
    for batch in _chunks(texts, batch_size):
        out = model.encode(
            batch,
            batch_size=batch_size,
            max_length=max_length,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
        vecs = out["dense_vecs"]
        if hasattr(vecs, "tolist"):
            vecs = vecs.tolist()
        dense_vectors.extend(vecs)
    return dense_vectors


# ---------------------------------------
# API principale da usare
# ---------------------------------------
def ingest_json_to_chroma(
    json_data: Any,
    collection_name: str = "",
    *,
    client: Optional["chromadb.api.client.Client"] = None,
    model: Optional[BGEM3FlagModel] = None,
    batch_size_embed: int = 32,
    batch_size_add: int = 128,
    max_length_tokens: int = 8192,
    use_upsert: bool = True,  # esegue upsert se disponibile
) -> Tuple[int, str]:
    """
    Ingest di un JSON in memoria su Chroma (Cloud o locale).

    Args:
        json_data: variabile Python (list/dict) o stringa JSON.
        collection_name: nome della collection target.
        client: opzionale, istanza Chroma già creata (CloudClient o Client).
        model: opzionale, istanza BGEM3FlagModel riusabile.
        batch_size_embed: batch per inferenza embedding.
        batch_size_add: batch per add/upsert in Chroma.
        max_length_tokens: trimming/token cap per bge-m3.
        use_upsert: se True prova collection.upsert(), altrimenti add().

    Returns:
        (num_inseriti, collection_name)
    """
    #items = _coerce_items_from_json(json_data)
    items = json_data
    ids = [it["shortcode"] for it in items]
    titles = [it["title"] for it in items]
    docs = [it["title"] + '. ' + it["description"] for it in items]
    metas = [it for it in items]

    client = client or build_client()
    collection = client.get_or_create_collection(collection_name)

    model = model or build_bge_m3()
    embeddings = embed_texts(model, docs, batch_size=batch_size_embed, max_length=max_length_tokens)
    if len(embeddings) != len(ids):
        raise RuntimeError("Numero di embedding non corrisponde al numero di documenti.")

    # Add/Upsert in batch
    for i in range(0, len(ids), batch_size_add):
        sl = slice(i, i + batch_size_add)
        payload = dict(
            ids=ids[sl],
            documents=titles[sl],
            metadatas=metas[sl],
            embeddings=embeddings[sl],
        )
        if use_upsert and hasattr(collection, "upsert"):
            collection.upsert(**payload)  # idempotent
        else:
            collection.add(**payload)     # più veloce, ma fallisce su id duplicati

    try:
        total = collection.count()
    except Exception:
        total = len(ids)

    return len(ids), collection_name


# ---------------------------------------
# Esempio d’uso (variabile in memoria)
# ---------------------------------------
if __name__ == "__main__":
    example_json = {
        "documents": [
            {"id": "doc-1", "text": "Questo è un esempio di documento.", "metadata": {"lang": "it"}},
            {"text": "Secondo documento senza id esplicito.", "metadata": {"tag": "demo"}},
        ]
    }
    n, coll = ingest_json_to_chroma(example_json, collection_name="smartRecipe")
    print(f"Inseriti {n} record nella collection '{coll}'.")
    
    