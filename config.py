import os
from openai import OpenAI
from dotenv import load_dotenv
# -------------------------------
# Configurazione tramite variabili d'ambiente
# -------------------------------
load_dotenv()

STATIC_DIR = os.path.join(os.getcwd(), "static")
BASE_FOLDER_RICETTE = os.path.join(STATIC_DIR, "mediaRicette")
BASE_FOLDER_PREPROCESS_VIDEO = os.path.join(STATIC_DIR, "preprocess_video")
MEDIA_RICETTE_WEB_PREFIX = "/static/mediaRicette"

ISTA_USERNAME = os.getenv("ISTA_USERNAME")
ISTA_PASSWORD = os.getenv("ISTA_PASSWORD")

# -------------------------------
# Modelli OpenAI
# -------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Modello Responses (estrazione ricetta testuale)
OPENAI_RESPONSES_MODEL = os.getenv("OPENAI_RESPONSES_MODEL", "gpt-5")
# Modello Chat Vision (analisi frames immagine)
OPENAI_VISION_CHAT_MODEL = os.getenv("OPENAI_VISION_CHAT_MODEL", "gpt-4.1")
# Modello trascrizione audio (usare "gpt-4o-transcribe" o "whisper-1")
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
# Modello generazione immagini
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
# Client OpenAI condiviso
openAIclient = OpenAI(api_key=OPENAI_API_KEY)

NO_IMAGE = False

# -------------------------------
# Configurazione Weaviate/Elysia 
# -------------------------------
WCD_URL = os.getenv("WCD_URL")
WCD_API_KEY = os.getenv("WCD_API_KEY")

# Configurazione Elysia
ELYSIA_AVAILABLE = False
WCD_AVAILABLE = True
WCD_COLLECTION_NAME = os.getenv("WCD_COLLECTION_NAME", "Recipe_Vector")
