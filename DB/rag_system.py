import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
#from FlagEmbedding import BGEM3FlagModel 
from transformers import pipeline

import json
from datetime import datetime
import os

# Caricamento del modello
#model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
model = pipeline(
        'feature-extraction', model='alexdseo/RecipeBERT', framework='pt'
    )

def index_database(data, metadata=None, out_path='static/recipeEmbeddings.npz'):
    texts = [data] if isinstance(data, str) else list(data)
    vectors = []
    for text in texts:
        vec = model(text, return_tensors='pt')[0].numpy().mean(axis=0)
        vectors.append(vec)
    embeddings = np.vstack(vectors) if len(vectors) > 0 else np.empty((0, 0))

    save_embeddings_with_metadata(
        embeddings=embeddings,
        metadata=metadata,
        out_path=out_path,
        info={'source': 'index_database'}
    )
    return embeddings

def save_embeddings_with_metadata(embeddings, metadata=None, out_path='static/recipeEmbeddings.npz', info=None, compress=True):
    E = np.atleast_2d(embeddings)
    arrays = {'embeddings': E}

    if metadata is not None:
        # metadata: lista di dict (uno per riga) o dict singolo
        if isinstance(metadata, dict):
            metadata = [metadata] * E.shape[0]
        if len(metadata) == E.shape[0]:
            meta_arr = np.array([json.dumps(m, ensure_ascii=False) for m in metadata], dtype=object)
            arrays['meta_json'] = meta_arr

    info = info or {}
    info.setdefault('schema_version', 1)
    info.setdefault('model', 'alexdseo/RecipeBERT')
    info.setdefault('created_at', datetime.utcnow().isoformat() + 'Z')
    info.setdefault('dim', int(E.shape[1] if E.size else 0))
    arrays['info_json'] = np.array([json.dumps(info, ensure_ascii=False)], dtype=object)

    if compress:
        np.savez_compressed(out_path, **arrays)
    else:
        np.savez(out_path, **arrays)
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
        default_npz = 'static/recipeEmbeddings.npz'
        if os.path.exists(default_npz):
            return load_embeddings_with_metadata(default_npz)[0]
        return np.load(embeddings_path)

def search(query, embedding_matrix):
    query_embedding = model(query, return_tensors='pt')[0].numpy().mean(axis=0)
    # Assicura che le forme siano 2D
    embedding_matrix = np.atleast_2d(embedding_matrix)
    query_embedding = query_embedding.reshape(1, -1)

    similarities = cosine_similarity(query_embedding, embedding_matrix)[0]
    similarity_results = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
    return similarity_results

def visualize_space_query(data, query, embedding_matrix):
    #query_embedding = model.encode([query])['dense_vecs'][0]
    query_embedding = model(query, return_tensors='pt')[0].numpy().mean(axis=0)

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
        plt.text(embeddings_2d[i, 0] + 0.1, embeddings_2d[i, 1] + 0.1, data, fontsize=9)

    # Annotazione per la query
    plt.text(embeddings_2d[-1, 0] + 0.1, embeddings_2d[-1, 1] + 0.1, query, fontsize=9, color='red')

    plt.title('Visualizzazione degli Embeddings con t-SNE')
    plt.xlabel('Dimensione 1')
    plt.ylabel('Dimensione 2')
    plt.grid(True)
    plt.legend()
    plt.show()

# Aggiunta della query
#query = "risotto ai gamberi"
# index_database(frasi) # cread il database vettoriale
#matrix = load_embedding_matrix("embeddings.npy")
#embedding, meta, info = load_embeddings_with_metadata('static/recipeEmbeddings.npz')

#out = search(query=query, embedding_matrix = embedding)
#print(out)
#visualize_space_query(meta, query, embedding)