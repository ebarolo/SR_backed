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
    # Calcolo degli embeddings
    #embeddings = model.encode(data)['dense_vecs']
    embeddings = model(data, return_tensors='pt')[0].numpy().mean(axis=0)

    # Salvataggio degli embeddings come file .npy
    np.save('embeddings.npy', embeddings)
    return embeddings

def load_embedding_matrix(dembeddings_path):
    # Caricamento degli embeddings per verifica
    loaded_embeddings = np.load(dembeddings_path)
    return loaded_embeddings

def search(query, embedding_matrix):
    query_embedding = model(query, return_tensors='pt')[0].numpy().mean(axis=0)
    similarities = cosine_similarity([query_embedding], embedding_matrix)[0]
    similarity_results = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
    return similarity_results


def visualize_space_query(data, query, embedding_matrix):
    query_embedding = model.encode([query])['dense_vecs'][0]

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


"""# Frasi da elaborare
frasi = [
    "iscriviti al canale di simone rizzo su youtube.",
    "video su yotube", 
    "creazione di contenuti sui social", 
    "ultimo modello open-source di Meta si chiama LLama 8.5",
    "nuovo modello di machine learning", 
    "il meccanico mi ha appena riparato l'automobile",
    "La ferrari california: Il V8 da 3.855 cm3 sviluppa 560 CV (145 CV/l, top di categoria) e una coppia massima che, in settima marcia, è di 755 Nm."
]

# Aggiunta della query
query = "voglio riparare la mia auto"

# index_database(frasi) # cread il database vettoriale
matrix = load_embedding_matrix("embeddings.npy")
out = search(query=query, embedding_matrix = matrix)
print(out)
visualize_space_query(frasi, query, matrix)"""