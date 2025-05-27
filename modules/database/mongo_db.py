from .database_init import get_mongodb
import logging

logger = logging.getLogger(__name__)

def get_collection(collection_name):
    try:
        db = get_mongodb()
        if db is None:
            logger.error(f"No se pudo obtener la base de datos para {collection_name}")
            return None
            
        collection = db[collection_name]
        logger.info(f"Colección {collection_name} obtenida exitosamente")
        return collection
        
    except Exception as e:
        logger.error(f"Error al obtener colección {collection_name}: {str(e)}")
        return None

def insert_document(collection_name, document):
    collection = get_collection(collection_name)
    try:
        result = collection.insert_one(document)
        logger.info(f"Documento insertado en {collection_name} con ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error al insertar documento en {collection_name}: {str(e)}")
        return None

def find_documents(collection_name, query, sort=None, limit=None):
    collection = get_collection(collection_name)
    try:
        cursor = collection.find(query)
        if sort:
            cursor = cursor.sort(sort)
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)
    except Exception as e:
        logger.error(f"Error al buscar documentos en {collection_name}: {str(e)}")
        return []

def update_document(collection_name, query, update):
    collection = get_collection(collection_name)
    try:
        result = collection.update_one(query, update)
        logger.info(f"Documento actualizado en {collection_name}: {result.modified_count} modificado(s)")
        return result.modified_count
    except Exception as e:
        logger.error(f"Error al actualizar documento en {collection_name}: {str(e)}")
        return 0

def delete_document(collection_name, query):
    collection = get_collection(collection_name)
    try:
        result = collection.delete_one(query)
        logger.info(f"Documento eliminado de {collection_name}: {result.deleted_count} eliminado(s)")
        return result.deleted_count
    except Exception as e:
        logger.error(f"Error al eliminar documento de {collection_name}: {str(e)}")
        return 0