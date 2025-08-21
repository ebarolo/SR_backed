import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline

import json
from datetime import datetime, date
import os
from typing import Optional, List, Tuple

from config import RAG_EMBEDDING_MODEL, EMBEDDINGS_NPZ_PATH
from utility import clean_text

# -------------------------------------
# Cache embeddings/metadata su file NPZ
# -------------------------------------
_npz_cache = {
    'path': None,
    'mtime': None,
    'E': None,
    'meta': None,
    'info': None,
}

def _get_mtime(path: str):
    try:
        return os.path.getmtime(path)
    except Exception:
        return None

def invalidate_embeddings_cache(path: Optional[str] = None):
    global _npz_cache
    if path is None or _npz_cache['path'] is None or os.path.abspath(path) == os.path.abspath(_npz_cache['path']):
        _npz_cache = {'path': None, 'mtime': None, 'E': None, 'meta': None, 'info': None}

def load_embeddings_with_metadata_cached(path):
    """Carica embeddings+metadata con cache basata su mtime del file."""
    global _npz_cache
    path_abs = os.path.abspath(path)
    mtime = _get_mtime(path_abs)
    if (
        _npz_cache['path'] == path_abs
        and _npz_cache['mtime'] is not None
        and mtime is not None
        and _npz_cache['mtime'] == mtime
        and _npz_cache['E'] is not None
    ):
        return _npz_cache['E'], _npz_cache['meta'], _npz_cache['info']

    E, meta, info = load_embeddings_with_metadata(path_abs)
    _npz_cache = {'path': path_abs, 'mtime': _get_mtime(path_abs), 'E': E, 'meta': meta, 'info': info}
    return E, meta, info

# -------------------------------------
# Gestione dinamica del modello HF usato per gli embeddings
# -------------------------------------
_current_rag_model_name: str = RAG_EMBEDDING_MODEL
_feature_extractor = pipeline('feature-extraction', model=_current_rag_model_name, framework='pt')

def get_current_rag_model_name() -> str:
    return _current_rag_model_name

def set_rag_model(model_name: str) -> str:
    global _current_rag_model_name, _feature_extractor
    if not model_name or not isinstance(model_name, str):
        raise ValueError("model_name non valido")
    _current_rag_model_name = model_name
    _feature_extractor = pipeline('feature-extraction', model=model_name, framework='pt')
    return _current_rag_model_name

def index_database(data, metadata=None, out_path: Optional[str] = None, append: bool = True):
    if out_path is None:
        out_path = EMBEDDINGS_NPZ_PATH
    texts = [data] if isinstance(data, str) else list(data)
    vectors = []
    for text in texts:
        vec = _feature_extractor(text, return_tensors='pt')[0].numpy().mean(axis=0)
        vectors.append(vec)
    new_E = np.vstack(vectors) if len(vectors) > 0 else np.empty((0, 0))

    # Se append è richiesto, concatena agli embeddings esistenti (se presenti)
    if append and os.path.exists(out_path):
        try:
            E_old, meta_old, _ = load_embeddings_with_metadata(out_path)
        except Exception:
            E_old, meta_old = None, None
        if E_old is not None and E_old.size > 0 and new_E.size > 0:
            # Verifica dimensioni coerenti
            if E_old.shape[1] != new_E.shape[1]:
                raise ValueError(
                    f"Dimensione vettoriale diversa tra esistenti ({E_old.shape[1]}) e nuovi ({new_E.shape[1]}). "
                    f"Cambia modello o ricalcola gli embeddings."
                )
            E_merged = np.vstack([E_old, new_E])
        elif E_old is not None and E_old.size > 0 and new_E.size == 0:
            E_merged = E_old
        elif (E_old is None or E_old.size == 0) and new_E.size > 0:
            E_merged = new_E
        else:
            E_merged = np.empty((0, 0))

        # Gestione metadata
        merged_meta = None
        num_new = new_E.shape[0]
        if meta_old is not None:
            base_meta = list(meta_old)
        else:
            base_meta = None
        if isinstance(metadata, dict):
            metadata = [metadata] * num_new
        if base_meta is not None and metadata is not None:
            merged_meta = base_meta + list(metadata)
        elif base_meta is not None and metadata is None:
            merged_meta = base_meta + ([{}] * num_new)
        elif base_meta is None and metadata is not None:
            merged_meta = list(metadata)
        else:
            merged_meta = None

        save_embeddings_with_metadata(
            embeddings=E_merged,
            metadata=merged_meta,
            out_path=out_path,
            info={'source': 'index_database_append'}
        )
        return E_merged

    # No append: salva solo i nuovi
    save_embeddings_with_metadata(
        embeddings=new_E,
        metadata=metadata,
        out_path=out_path,
        info={'source': 'index_database'}
    )
    return new_E

def save_embeddings_with_metadata(embeddings, metadata=None, out_path: Optional[str] = None, info=None, compress=True):
    if out_path is None:
        out_path = EMBEDDINGS_NPZ_PATH
    E = np.atleast_2d(embeddings)
    arrays = {'embeddings': E}

    # Funzione di default per serializzazione JSON robusta
    def _json_default(o):
        # Pydantic v2
        if hasattr(o, 'model_dump') and callable(getattr(o, 'model_dump')):
            try:
                return o.model_dump()
            except Exception:
                pass
        # Pydantic v1
        if hasattr(o, 'dict') and callable(getattr(o, 'dict')):
            try:
                return o.dict()
            except Exception:
                pass
        # numpy scalari e array
        try:
            import numpy as _np
            if isinstance(o, (_np.integer, _np.floating)):
                return o.item()
            if isinstance(o, _np.ndarray):
                return o.tolist()
        except Exception:
            pass
        # datetime/date
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        # set/tuple/bytes
        if isinstance(o, (set, tuple)):
            return list(o)
        if isinstance(o, (bytes, bytearray)):
            return o.decode('utf-8', errors='ignore')
        # oggetti generici
        if hasattr(o, '__dict__'):
            try:
                return vars(o)
            except Exception:
                pass
        # fallback a stringa
        return str(o)

    if metadata is not None:
        # metadata: lista di dict (uno per riga) o dict singolo
        if isinstance(metadata, dict):
            metadata = [metadata] * E.shape[0]
        if len(metadata) == E.shape[0]:
            meta_arr = np.array([json.dumps(m, ensure_ascii=False, default=_json_default) for m in metadata], dtype=object)
            arrays['meta_json'] = meta_arr

    info = info or {}
    info.setdefault('schema_version', 1)
    info.setdefault('model', get_current_rag_model_name())
    info.setdefault('created_at', datetime.utcnow().isoformat() + 'Z')
    info.setdefault('dim', int(E.shape[1] if E.size else 0))
    arrays['info_json'] = np.array([json.dumps(info, ensure_ascii=False, default=_json_default)], dtype=object)

    # Scrittura atomica: salva su file temporaneo e poi replace
    out_dir = os.path.dirname(out_path) or '.'
    os.makedirs(out_dir, exist_ok=True)
    tmp_path = out_path + ".tmp"
    if compress:
        np.savez_compressed(tmp_path, **arrays)
    else:
        np.savez(tmp_path, **arrays)
    os.replace(tmp_path, out_path)
    # invalida cache
    invalidate_embeddings_cache(out_path)
    return out_path

def load_embeddings_with_metadata(path):
    if path.endswith('.npz') and os.path.exists(path):
        with np.load(path, allow_pickle=True) as f:
            E = f['embeddings']
            meta_json = f.get('meta_json', None)
            info_json = f.get('info_json', None)
        meta = [json.loads(x) for x in meta_json] if meta_json is not None else None
        info = json.loads(info_json[0]) if info_json is not None else {}
        return E, meta, info
    # Fallback .npy
    E = np.load(path)
    return np.atleast_2d(E), None, {}

def load_embedding_matrix(embeddings_path):
    try:
        E, _, _ = load_embeddings_with_metadata(embeddings_path)
        return E
    except Exception:
        default_npz = EMBEDDINGS_NPZ_PATH
        if os.path.exists(default_npz):
            return load_embeddings_with_metadata(default_npz)[0]
        return np.load(embeddings_path)

def search(query, embedding_matrix, top_k: Optional[int] = None):
    query_embedding = _feature_extractor(query, return_tensors='pt')[0].numpy().mean(axis=0)
    # Assicura che le forme siano 2D
    embedding_matrix = np.atleast_2d(embedding_matrix)
    query_embedding = query_embedding.reshape(1, -1)

    # Validazione dimensioni
    if embedding_matrix.size > 0 and query_embedding.shape[1] != embedding_matrix.shape[1]:
        raise ValueError(
            f"Dimensione vettoriale diversa tra query ({query_embedding.shape[1]}) e matrice ({embedding_matrix.shape[1]}). "
            f"Ricalcola gli embeddings con il nuovo modello o seleziona un modello coerente."
        )

    similarities = cosine_similarity(query_embedding, embedding_matrix)[0]
    n = similarities.shape[0]
    if top_k is None or top_k >= n:
        similarity_results = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
        return similarity_results
    # top-k efficiente
    top_k = max(1, int(top_k))
    idx = np.argpartition(similarities, -top_k)[-top_k:]
    selected = [(int(i), float(similarities[i])) for i in idx]
    selected.sort(key=lambda x: x[1], reverse=True)
    return selected

def visualize_space_query(data, query, embedding_matrix):
    #query_embedding = model.encode([query])['dense_vecs'][0]
    query_embedding = _feature_extractor(query, return_tensors='pt')[0].numpy().mean(axis=0)

    # Normalizza forme per l'aggregazione
    embedding_matrix = np.atleast_2d(embedding_matrix)
    query_embedding = query_embedding.reshape(1, -1)

    jointed_matrix = np.vstack([embedding_matrix, query_embedding])

    # Gestione dataset piccoli per TSNE: serve perplexity < n_samples
    n_samples = jointed_matrix.shape[0]
    if n_samples < 2:
        print("TSNE: numero di campioni insufficiente per la visualizzazione.")
        return
    perplexity = min(30, max(1, n_samples - 1))
    if perplexity >= n_samples:
        perplexity = n_samples - 1

    # Riduzione dimensionale con TSNE
    tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42)
    embeddings_2d = tsne.fit_transform(jointed_matrix)

    # Plotting dei risultati
    plt.figure(figsize=(8, 6))

    # Plot delle frasi
    plt.scatter(embeddings_2d[:-1, 0], embeddings_2d[:-1, 1], c='blue', edgecolor='k', label='Ricette')

    # Plot della query
    plt.scatter(embeddings_2d[-1, 0], embeddings_2d[-1, 1], c='red', edgecolor='k', label='Query')

    # Annotazioni con le frasi originali
    for i, data in enumerate(data):
        plt.text(embeddings_2d[i, 0] + 0.1, embeddings_2d[i, 1] + 0.1, data['title'], fontsize=9)

    # Annotazione per la query
    plt.text(embeddings_2d[-1, 0] + 0.1, embeddings_2d[-1, 1] + 0.1, query, fontsize=9, color='red')

    plt.title('Visualizzazione degli Embeddings con t-SNE')
    plt.xlabel('Dimensione 1')
    plt.ylabel('Dimensione 2')
    plt.grid(True)
    plt.legend()
    plt.show()


# -------------------------------------
# Utilità: ricostruzione testo da metadata e ricalcolo embeddings
# -------------------------------------
def _text_from_metadata(meta: dict) -> str:
    try:
        title = meta.get('title', '')
        categories = meta.get('category', []) or []
        if isinstance(categories, str):
            categories = [categories]
        ingredients = meta.get('ingredients', []) or []
        if ingredients and isinstance(ingredients[0], dict):
            ingredient_names = [ing.get('name', '') for ing in ingredients]
        else:
            ingredient_names = [str(x) for x in ingredients]
        title_clean = clean_text(title)
        category_clean = ' '.join([clean_text(cat) for cat in categories])
        ingredients_clean = ' '.join([clean_text(n) for n in ingredient_names])
        return f"{title_clean}. Categoria: {category_clean}. Ingredienti: {ingredients_clean}"
    except Exception:
        # Fallback minimale
        return clean_text(str(meta))

def recalculate_embeddings_from_npz(npz_path: Optional[str] = None, model_name: Optional[str] = None, out_path: Optional[str] = None) -> Tuple[np.ndarray, Optional[List[dict]], dict]:
    """
    Ricarica meta e info dal file .npz, rigenera gli embeddings con il modello indicato
    e sovrascrive (o salva su nuovo percorso) il file .npz con i nuovi vettori.

    Ritorna: (embeddings, metadata, info)
    """
    npz_path = npz_path or EMBEDDINGS_NPZ_PATH
    out_path = out_path or npz_path

    # Cambia modello se richiesto
    if model_name:
        set_rag_model(model_name)

    E_old, meta, info = load_embeddings_with_metadata(npz_path)
    if meta is None:
        raise ValueError("Il file .npz non contiene 'meta_json'. Impossibile ricalcolare i testi per gli embeddings.")

    texts = [_text_from_metadata(m) for m in meta]
    new_embeddings = index_database(texts, metadata=meta, out_path=out_path, append=False)
    return new_embeddings, meta, {
        'model': get_current_rag_model_name(),
        'source': 'recalculate_embeddings_from_npz'
    }

def load_npz_info(npz_path: Optional[str] = None) -> dict:
    npz_path = npz_path or EMBEDDINGS_NPZ_PATH
    _, _, info = load_embeddings_with_metadata_cached(npz_path)
    return {'path': npz_path, 'info': info, 'model_runtime': get_current_rag_model_name()}

'''
# Aggiunta della query
query = "risotto ai gamberi"
# index_database(frasi) # cread il database vettoriale
#matrix = load_embedding_matrix("embeddings.npy")
embedding, meta, info = load_embeddings_with_metadata('static/recipeEmbeddings.npz')

out = search(query=query, embedding_matrix = embedding)[:3]
print(out)
visualize_space_query(meta, query, embedding)
'''