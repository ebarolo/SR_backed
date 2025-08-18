import numpy as np
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
#from FlagEmbedding import BGEM3FlagModel 
from transformers import pipeline

# Caricamento del modello
#model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
model = pipeline(
        'feature-extraction', model='alexdseo/RecipeBERT', framework='pt'
    )

def index_database(data):
    # Calcolo degli embeddings: una riga per documento (N, D)
    vectors = []
    for text in data:
        vec = model(text, return_tensors='pt')[0].numpy().mean(axis=0)
        vectors.append(vec)
    embeddings = np.vstack(vectors) if len(vectors) > 0 else np.empty((0, 0))

    # Salvataggio degli embeddings come file .npy
    np.save('static/recipeEmbeddings.npy', embeddings)
    return embeddings

def load_embedding_matrix(embeddings_path):
    # Caricamento degli embeddings per verifica e normalizzazione forma 2D
    loaded_embeddings = np.load(embeddings_path)
    #loaded_embeddings = np.atleast_2d(loaded_embeddings)
    return loaded_embeddings

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
    # for i, frase in enumerate(data):
    #    plt.text(embeddings_2d[i, 0] + 0.1, embeddings_2d[i, 1] + 0.1, frase, fontsize=9)

    # Annotazione per la query
    plt.text(embeddings_2d[-1, 0] + 0.1, embeddings_2d[-1, 1] + 0.1, query, fontsize=9, color='red')

    plt.title('Visualizzazione degli Embeddings con t-SNE')
    plt.xlabel('Dimensione 1')
    plt.ylabel('Dimensione 2')
    plt.grid(True)
    plt.legend()
    plt.show()


# Aggiunta della query
query = "risotto ai gamberi"
# index_database(frasi) # cread il database vettoriale
matrix = load_embedding_matrix("embeddings.npy")
out = search(query=query, embedding_matrix = matrix)
print(out)
visualize_space_query(frasi, query, matrix)