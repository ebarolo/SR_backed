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
OPENAI_RESPONSES_MODEL = os.getenv("OPENAI_RESPONSES_MODEL", "gpt-5")
OPENAI_VISION_CHAT_MODEL = os.getenv("OPENAI_VISION_CHAT_MODEL", "gpt-4.1")
OPENAI_TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-transcribe")
OPENAI_IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")
openAIclient = OpenAI(api_key=OPENAI_API_KEY)

NO_IMAGE = os.getenv("NO_IMAGE", "False").lower() == "true"

# -------------------------------
# Configurazione Weaviate/Elysia 
# -------------------------------
WCD_URL = os.getenv("WCD_URL")
WCD_API_KEY = os.getenv("WCD_API_KEY")
WCD_COLLECTION_NAME = os.getenv("WCD_COLLECTION_NAME", "Recipe_Vector")
WCD_AVAILABLE = bool(WCD_URL and WCD_API_KEY)
