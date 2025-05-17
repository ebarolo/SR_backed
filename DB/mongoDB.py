from functools import lru_cache
from pymongo import MongoClient
from pymongo.server_api import ServerApi

from config import MONGODB_URL, MONGODB_DB, MONGODB_COLLECTION, EMBEDDING_MODEL, MONGODB_VECTOR_SEARCH_INDEX_NAME

#-------------------------------    
# Inizializzazione MongoDB per semantic search
# -------------------------------
@lru_cache(maxsize=1)
def get_mongo_client():
    return MongoClient(
        MONGODB_URL,
        server_api=ServerApi('1'),
        retryWrites=True,
        connectTimeoutMS=300000,
        socketTimeoutMS=300000,
        tlsAllowInvalidCertificates=True  # Fix for SSL certificate verification issue
    )

@lru_cache(maxsize=1)
def get_mongo_collection():
    client = get_mongo_client()
    db = client[MONGODB_DB]
    return db[MONGODB_COLLECTION]

def get_db():
    """Alias for get_mongo_collection to satisfy dependency injection"""
    return get_mongo_collection()
