
import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline

from config import RAG_EMBEDDING_MODEL

embedding_matrix = np.load("static/recipeEmbeddings.npz", allow_pickle=True)     # restituisce un NpzFile (dict-like)
_current_rag_model_name: str = RAG_EMBEDDING_MODEL
_feature_extractor = pipeline('feature-extraction', model=_current_rag_model_name, framework='pt')

def visualize_space_query(data, query, embedding_matrix):
   #query_embedding = model.encode([query])['dense_vecs'][0]
    query_embedding = _feature_extractor(query, return_tensors='pt')[0].numpy().mean(axis=0)

    jointed_matrix = np.vstack([embedding_matrix, query_embedding])

    # Riduzione dimensionale con TSNE
    tsne = TSNE(n_components=2, perplexity=2, random_state=42)
    embeddings_2d = tsne.fit_transform(jointed_matrix)

    # Plotting dei risultati
    plt.figure(figsize=(8, 6))

    # Plot delle frasi
    plt.scatter(embeddings_2d[:-1, 0], embeddings_2d[:-1, 1], c='blue', edgecolor='k', label='Frasi')

    # Plot della query
    plt.scatter(embeddings_2d[-1, 0], embeddings_2d[-1, 1], c='red', edgecolor='k', label='Query')

    # Annotazioni con le frasi originali
    for i, frase in enumerate(data):
        plt.text(embeddings_2d[i, 0] + 0.1, embeddings_2d[i, 1] + 0.1, frase, fontsize=9)

    # Annotazione per la query
    plt.text(embeddings_2d[-1, 0] + 0.1, embeddings_2d[-1, 1] + 0.1, query, fontsize=9, color='red')

    plt.title('Visualizzazione degli Embeddings con t-SNE')
    plt.xlabel('Dimensione 1')
    plt.ylabel('Dimensione 2')
    plt.grid(True)
    plt.legend()
    plt.show()

