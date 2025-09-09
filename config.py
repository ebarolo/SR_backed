import os
from openai import OpenAI
from dotenv import load_dotenv
# -------------------------------
# Configurazione tramite variabili d'ambiente
# -------------------------------
load_dotenv()

BASE_FOLDER_RICETTE = os.path.join(os.getcwd(), "static","mediaRicette")
BASE_FOLDER_PREPROCESS_VIDEO = os.path.join(os.getcwd(), "static/preprocess_video")

ISTA_USERNAME = os.getenv("ISTA_USERNAME")
ISTA_PASSWORD = os.getenv("ISTA_PASSWORD")

# -------------------------------
# Modelli OpenAI
# -------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Modello Responses (estrazione ricetta testuale)
OPENAI_RESPONSES_MODEL = os.getenv("OPENAI_RESPONSES_MODEL", "gpt-5")
# Modello Chat Vision (analisi frames immagine)
OPENAI_VISION_CHAT_MODEL = os.getenv("OPENAI_VISION_CHAT_MODEL", "gpt-4o-mini")
# Modello trascrizione audio
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
# Modello generazione immagini
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
# Client OpenAI condiviso
openAIclient = OpenAI(api_key=OPENAI_API_KEY)

# modell EMBEDDING_MODEL da usare
EMBEDDING_MODEL = "BAAI/bge-m3"
FLAGEMBEDDING_AVAILABLE = True
NO_IMAGE = True

# Percorso file NPZ che contiene embeddings e metadati
EMBEDDINGS_NPZ_PATH = os.getenv(
    "EMBEDDINGS_NPZ_PATH",
    os.path.join(os.getcwd(), "static/recipeEmbeddings.npz")
)

# -------------------------------
# Configurazione ChromaDB
# -------------------------------
# Forza l'uso della versione locale di ChromaDB invece di Chroma Cloud
USE_LOCAL_CHROMA = os.getenv("USE_LOCAL_CHROMA", "false").lower() in ("true", "1", "yes")
CHROMADB_AVAILABLE = False

# Percorso per il database ChromaDB locale (se None, usa in-memory)
CHROMA_LOCAL_PATH = os.getenv("CHROMA_LOCAL_PATH", os.path.join(os.getcwd(), "chroma_db"))
COLLECTION_NAME = "SmartRecipe"

# -------------------------------
# Configurazione Weaviate/Elysia 
# -------------------------------
# URL del cluster Weaviate (es. https://your-cluster.weaviate.network)
WCD_URL = os.getenv("WCD_URL")
WCD_API_KEY = os.getenv("WCD_API_KEY")

# Configurazione Elysia
ELYSIA_AVAILABLE = True
ELYSIA_COLLECTION_NAME = os.getenv("ELYSIA_COLLECTION_NAME", "Recipe_Vector")