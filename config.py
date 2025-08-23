import os
from openai import OpenAI
from dotenv import load_dotenv
# -------------------------------
# Configurazione tramite variabili d'ambiente
# -------------------------------
load_dotenv()

BASE_FOLDER_RICETTE = os.path.join(os.getcwd(), "static/mediaRicette")
BASE_FOLDER_PREPROCESS_VIDEO = os.path.join(os.getcwd(), "static/preprocess_video")

ISTA_USERNAME = os.getenv("ISTA_USERNAME")
ISTA_PASSWORD = os.getenv("ISTA_PASSWORD")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Client OpenAI condiviso
openAIclient = OpenAI(api_key=OPENAI_API_KEY)

# -------------------------------
# Modelli OpenAI/HF centralizzati
# -------------------------------
# Modello Responses (estrazione ricetta testuale)
OPENAI_RESPONSES_MODEL = os.getenv("OPENAI_RESPONSES_MODEL", "gpt-5")
# Modello Chat Vision (analisi frames immagine)
OPENAI_VISION_CHAT_MODEL = os.getenv("OPENAI_VISION_CHAT_MODEL", "gpt-4o-mini")
# Modello trascrizione audio
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
# Modello generazione immagini
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

# -------------------------------
# Parametri RAG (mancanti) usati da DB/rag_system.py e main.py
# -------------------------------
# Modello HF per l'estrazione di feature; default: usa EMBEDDING_MODEL già definito
EMBEDDING_MODEL = "BAAI/bge-m3"

RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", EMBEDDING_MODEL)

# Percorso file NPZ che contiene embeddings e metadati delle ricette
EMBEDDINGS_NPZ_PATH = os.getenv(
    "EMBEDDINGS_NPZ_PATH",
    os.path.join(os.getcwd(), "static/recipeEmbeddings.npz")
)

# -------------------------------
# Configurazione ChromaDB
# -------------------------------
# Forza l'uso della versione locale di ChromaDB invece di Chroma Cloud
USE_LOCAL_CHROMA = os.getenv("USE_LOCAL_CHROMA", "true").lower() in ("true", "1", "yes")

# Percorso per il database ChromaDB locale (se None, usa in-memory)
CHROMA_LOCAL_PATH = os.getenv("CHROMA_LOCAL_PATH", os.path.join(os.getcwd(), "chroma_db"))
