import os
from openai import OpenAI

# -------------------------------
# Configurazione tramite variabili d'ambiente
# -------------------------------
#DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recipes.db")
#QDRANT_URL = os.getenv("QDRANT_URL", "https://cd762cc1-d29b-42aa-8fa4-660b5c79871f.europe-west3-0.gcp.cloud.qdrant.io:6333")
#QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
#QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "smart-recipe")
#QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.TI1jEYFRxKghin8baG_wtBiK-imMFOf98rOEejelcUI")  

BASE_FOLDER_RICETTE = os.path.join(os.getcwd(), "static/mediaRicette")
BASE_FOLDER_PREPROCESS_VIDEO = os.path.join(os.getcwd(), "static/preprocess_video")

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://ebarolo:cAMV8Yfe9PnKLQ7z@smart-recider-1.n74uydt.mongodb.net/?retryWrites=true&w=majority&appName=smart-recider-1")
MONGODB_DB = os.getenv("MONGODB_DB", "smart-recipe")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "recipe")
MONGODB_VECTOR_SEARCH_INDEX_NAME = os.getenv("MONGO_SEARCH_INDEX", "openAIVector")
EMBEDDING_FIELD_NAME = "embedding"

ISTA_USERNAME = os.getenv("ISTA_USERNAME")
ISTA_PASSWORD = os.getenv("ISTA_PASSWORD")

EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_API_KEY = "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"
openAIclient = OpenAI(api_key=OPENAI_API_KEY)
