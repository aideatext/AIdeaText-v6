# modules/database/current_situation_mongo_db.py
from datetime import datetime, timezone, timedelta
import logging
from .mongo_db import get_collection

logger = logging.getLogger(__name__)
COLLECTION_NAME = 'student_current_situation'

# En modules/database/current_situation_mongo_db.py

def store_current_situation_result(username, text, metrics, feedback):
    """
    Guarda los resultados del análisis de situación actual.
    """
    try:
        # Verificar parámetros
        if not all([username, text, metrics]):
            logger.error("Faltan parámetros requeridos")
            return False

        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección")
            return False

        # Crear documento
        document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc) # Mejor práctica
            'text': text,
            'metrics': metrics,
            'feedback': feedback or {},
            'analysis_type': 'current_situation'
        }

        # Insertar documento y verificar
        result = collection.insert_one(document)
        if result.inserted_id:
            logger.info(f"""
                Análisis de situación actual guardado:
                - Usuario: {username}
                - ID: {result.inserted_id}
                - Longitud texto: {len(text)}
            """)
            
            # Verificar almacenamiento
            storage_verified = verify_storage(username)
            if not storage_verified:
                logger.warning("Verificación de almacenamiento falló")
            
            return True

        logger.error("No se pudo insertar el documento")
        return False

    except Exception as e:
        logger.error(f"Error guardando análisis de situación actual: {str(e)}")
        return False

def verify_storage(username):
    """
    Verifica que los datos se están guardando correctamente.
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección para verificación")
            return False
            
        # Buscar documentos recientes del usuario
        timestamp_threshold = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        
        recent_docs = collection.find({
            'username': username,
            'timestamp': {'$gte': timestamp_threshold}
        }).sort('timestamp', -1).limit(1)

        docs = list(recent_docs)
        if docs:
            logger.info(f"""
                Último documento guardado:
                - ID: {docs[0]['_id']}
                - Timestamp: {docs[0]['timestamp']}
                - Métricas guardadas: {bool(docs[0].get('metrics'))}
            """)
            return True
        
        logger.warning(f"No se encontraron documentos recientes para {username}")
        return False

    except Exception as e:
        logger.error(f"Error verificando almacenamiento: {str(e)}")
        return False

def get_current_situation_analysis(username, limit=5):
    """
    Obtiene los análisis de situación actual de un usuario.
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección")
            return []
            
        # Buscar documentos
        query = {'username': username, 'analysis_type': 'current_situation'}
        cursor = collection.find(query).sort('timestamp', -1)
        
        # Aplicar límite si se especifica
        if limit:
            cursor = cursor.limit(limit)
            
        # Convertir cursor a lista
        return list(cursor)
        
    except Exception as e:
        logger.error(f"Error obteniendo análisis de situación actual: {str(e)}")
        return []

def get_recent_situation_analysis(username, limit=5):
    """
    Obtiene los análisis más recientes de un usuario.
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            return []
            
        results = collection.find(
            {'username': username}
        ).sort('timestamp', -1).limit(limit)
        
        return list(results)
        
    except Exception as e:
        logger.error(f"Error obteniendo análisis recientes: {str(e)}")
        return []