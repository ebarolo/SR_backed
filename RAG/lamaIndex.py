
import os
import logging
from dotenv import load_dotenv
from llamaIndex import 
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

COLLECTION_NAME = "smart_Recipe"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"