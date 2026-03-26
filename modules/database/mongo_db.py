import logging
from .database_init import get_mongodb

logger = logging.getLogger(__name__)

def get_collection(collection_name):
    db = get_mongodb()
    if db is not None:
        return db[collection_name]
    return None

def insert_document(collection_name, document):
    col = get_collection(collection_name)
    if col is not None:
        return col.insert_one(document)
    return None

def find_documents(collection_name, query=None):
    col = get_collection(collection_name)
    if col is not None:
        return list(col.find(query or {}))
    return []

def update_document(collection_name, query, update_values):
    col = get_collection(collection_name)
    if col is not None:
        return col.update_one(query, {"$set": update_values})
    return None

def delete_document(collection_name, query):
    """Nombre corregido a singular para cumplir con la importación"""
    col = get_collection(collection_name)
    if col is not None:
        return col.delete_one(query)
    return None

def delete_documents(collection_name, query):
    col = get_collection(collection_name)
    if col is not None:
        return col.delete_many(query)
    return None
