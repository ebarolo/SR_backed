import os
from dotenv import load_dotenv  # load .env file
from openai import OpenAI
import logging

load_dotenv()
# Central configuration for OpenAI API key and client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://ebarolo:cAMV8Yfe9PnKLQ7z@smart-recider-1.n74uydt.mongodb.net/?retryWrites=true&w=majority&appName=smart-recider-1")
MONGODB_DB = os.getenv("MONGODB_DB", "smart-recider-1")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "recipes_vector")
MONGO_SEARCH_INDEX = os.getenv("MONGO_SEARCH_INDEX", "smart-recipe-index")
EMBEDDING_MODEL = "text-embedding-3-small"

# Add centralized logging configuration and logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d:%(funcName)s - %(message)s",
    handlers=[logging.FileHandler("backend.log"), logging.StreamHandler()],
)

logger = logging.getLogger()

if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY environment variable")

OpenAIclient = OpenAI(api_key=OPENAI_API_KEY) 