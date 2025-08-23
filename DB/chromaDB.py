import os
import json
import uuid
from typing import Any, Dict, List, Tuple, Optional

import chromadb
from FlagEmbedding import BGEM3FlagModel
from dotenv import load_dotenv
load_dotenv()

# Importa configurazioni
from config import USE_LOCAL_CHROMA, CHROMA_LOCAL_PATH
# ---------------------------------------
# Helpers
# ---------------------------------------
def _parse_recipe_string(recipe_str: str) -> Dict[str, Any]:
    """Parse formato stringa come nell'example_json."""
    import re
    
    # Estrae tutti i campi dal formato "field='value'" o "field=[...]"
    patterns = {
        'title': r"title='([^']*)'",
        'description': r"description='([^']*)'", 
        'shortcode': r"shortcode='([^']*)'",
        'category': r"category=\[([^\]]*)\]",
        'tags': r"tags=\[([^\]]*)\]",
        'preparation_time': r"preparation_time=(\d+)",
        'cooking_time': r"cooking_time=(\d+)",
        'diet': r"diet='([^']*)'",
        'technique': r"technique='([^']*)'",
        'language': r"language='([^']*)'",
        'chef_advise': r"chef_advise='([^']*)'",
        'cuisine_type': r"cuisine_type='([^']*)'",
        'ricetta_audio': r"ricetta_audio='([^']*)'",
        'ricetta_caption': r"ricetta_caption='([^']*)'",
    }
    
    result = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, recipe_str)
        if match:
            value = match.group(1)
            if field in ['category', 'tags']:
                # Parse array-like strings
                result[field] = [item.strip().strip("'\"") for item in value.split(',') if item.strip()]
            elif field in ['preparation_time', 'cooking_time']:
                result[field] = int(value)
            else:
                result[field] = value
        else:
            result[field] = [] if field in ['category', 'tags'] else (0 if field in ['preparation_time', 'cooking_time'] else '')
    
    return result


def _coerce_items_from_json(j: Any) -> List[Dict[str, Any]]:
    """
    Accetta:
      - list[dict] con chiavi per ricette (title, description, shortcode, etc.)
      - list[str] formato example_json 
      - dict con chiave wrapper: {'data'| 'items'| 'documents'| 'records': list[dict]}
      - stringa JSON (verrà json.loads)
    Ritorna: list di record normalizzati per ricette
    """
    if isinstance(j, str):
        j = json.loads(j)

    if isinstance(j, list):
        items = []
        for item in j:
            if isinstance(item, str):
                # Parse formato example_json
                items.append(_parse_recipe_string(item))
            elif isinstance(item, dict):
                items.append(item)
            else:
                items.append({"title": str(item)})
    elif isinstance(j, dict):
        for key in ("data", "items", "documents", "records"):
            if key in j and isinstance(j[key], list):
                return _coerce_items_from_json(j[key])
        items = [{"id": k, **(v if isinstance(v, dict) else {"title": str(v)})} for k, v in j.items()]
    else:
        raise ValueError("Formato JSON non supportato.")

    return items


def _chunks(seq: List[Any], n: int):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Converte liste in stringhe per compatibilità ChromaDB."""
    sanitized = {}
    for key, value in metadata.items():
        if isinstance(value, list):
            sanitized[key] = ", ".join(str(item) for item in value)
        elif value is None:
            sanitized[key] = ""
        else:
            sanitized[key] = value
    return sanitized


def build_client() -> "chromadb.api.client.Client":
    """
    Crea un client ChromaDB basato sulla configurazione.
    
    Se USE_LOCAL_CHROMA=True (default), usa sempre la versione locale.
    Altrimenti, usa Chroma Cloud se è presente CHROMA_API_KEY.
    """
    if USE_LOCAL_CHROMA:
        print(f"Usando ChromaDB locale: {CHROMA_LOCAL_PATH}")
        if CHROMA_LOCAL_PATH and os.path.exists(os.path.dirname(CHROMA_LOCAL_PATH)):
            # Usa database persistente su disco
            return chromadb.PersistentClient(path=CHROMA_LOCAL_PATH)
        else:
            # Usa database in-memory per test
            print("Usando ChromaDB in-memory (per test)")
            return chromadb.Client()
    else:
        # Modalità cloud (legacy)
        api_key = os.getenv("CHROMA_API_KEY")
        tenant = os.getenv("CHROMA_TENANT")
        database = os.getenv("CHROMA_DATABASE")
        print(f"Usando Chroma Cloud - api_key: {bool(api_key)}, tenant: {tenant}, database: {database}")
        
        if api_key and (tenant or database):
            return chromadb.CloudClient(api_key=api_key, tenant=tenant, database=database)
        elif api_key:
            return chromadb.CloudClient(api_key=api_key)
        else:
            print("Nessuna configurazione cloud trovata, fallback a locale")
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
    use_upsert: bool = True,
) -> Tuple[int, str]:
    """
    Ingest di ricette da JSON (supporta formato example_json e dict standard).

    Args:
        json_data: list[str] formato example_json o list[dict] con chiavi ricetta.
        collection_name: nome della collection target.
        Altri parametri: configurazione Chroma e embedding.

    Returns:
        (num_inseriti, collection_name)
    """
    items = _coerce_items_from_json(json_data)
    
    # Estrai dati necessari con valori di default
    ids = [item.get("shortcode") or str(uuid.uuid4()) for item in items]
    titles = [item.get("title", "") for item in items]
    descriptions = [item.get("description", "") for item in items]
    docs = [f"{title}. {desc}".strip(". ") for title, desc in zip(titles, descriptions)]
    
    client = client or build_client()
    collection = client.get_or_create_collection(collection_name)
    
    model = model or build_bge_m3()
    embeddings = embed_texts(model, docs, batch_size=batch_size_embed, max_length=max_length_tokens)
    
    # Add/Upsert in batch
    for i in range(0, len(ids), batch_size_add):
        sl = slice(i, i + batch_size_add)
        sanitized_metas = [_sanitize_metadata(item) for item in items[sl]]
        payload = dict(
            ids=ids[sl],
            documents=titles[sl],
            metadatas=sanitized_metas,
            embeddings=embeddings[sl],
        )
        if use_upsert and hasattr(collection, "upsert"):
            collection.upsert(**payload)
        else:
            collection.add(**payload)

    return len(ids), collection_name


# ---------------------------------------
# Esempio d’uso (variabile in memoria)
# ---------------------------------------
'''
if __name__ == "__main__":
    example_json = [
     "title='Risotto ai gamberi con zafferano' category=['primo'] preparation_time=0 cooking_time=0 ingredients=[] recipe_step=[] description='Un risotto allo zafferano con gamberi, cremoso e confortante; un piatto semplice e appagante, perfetto da solo o con abbinamenti di mare o carni brasate.' diet='unknown' technique='unknown' language='it' chef_advise='' tags=['risotto', 'gamberi', 'zafferano', 'comfort food'] nutritional_info=[] cuisine_type='italiana' ricetta_audio='Thank you' ricetta_caption='Risotto ai gamberi con zafferano - a cozy and delicious saffron risotto and shrimp. On days like this, my favorite saffron risotto is all I need. I love this risotto because it is amazing on its own, with seafood or braised meat. It is creamy, warm and comforting to the soul. \\n\\nJust me, posting a comfort meal that I make when I take the night off from cooking complexity and the world in general. So if youre wondering what I make when Im not creating a new dish, this is the go to dish that does it for me  \\n\\nComforting, delicious, satisfying, and from the heart' shortcode='DDZicfkRfiO'"
   ]
    
    n, coll = ingest_json_to_chroma(example_json, collection_name="smartRecipe")
    print(f"Inseriti {n} record nella collection '{coll}'.")
'''
    