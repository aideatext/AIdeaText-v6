# modules/database/writing_progress_mongo_db.py

from .mongo_db import get_collection, insert_document
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
COLLECTION_NAME = 'writing_progress'

def store_writing_baseline(username, metrics, text):
    """
    Guarda la línea base de escritura de un usuario.
    Args:
        username: ID del usuario
        metrics: Diccionario con métricas iniciales
        text: Texto analizado
    """
    try:
        document = {
            'username': username,
            'type': 'baseline',
            'metrics': metrics,
            'text': text,
            'timestamp': datetime.now(timezone.utc) # Mejor práctica
            'iteration': 0  # Línea base siempre es iteración 0
        }
        
        # Verificar si ya existe una línea base
        collection = get_collection(COLLECTION_NAME)
        existing = collection.find_one({
            'username': username,
            'type': 'baseline'
        })
        
        if existing:
            # Actualizar línea base existente
            result = collection.update_one(
                {'_id': existing['_id']},
                {'$set': document}
            )
            success = result.modified_count > 0
        else:
            # Insertar nueva línea base
            result = collection.insert_one(document)
            success = result.inserted_id is not None
            
        logger.info(f"Línea base {'actualizada' if existing else 'creada'} para usuario: {username}")
        return success
        
    except Exception as e:
        logger.error(f"Error al guardar línea base: {str(e)}")
        return False

def store_writing_progress(username, metrics, text):
    """
    Guarda una nueva iteración de progreso.
    """
    try:
        # Obtener último número de iteración
        collection = get_collection(COLLECTION_NAME)
        last_progress = collection.find_one(
            {'username': username},
            sort=[('iteration', -1)]
        )
        
        next_iteration = (last_progress['iteration'] + 1) if last_progress else 1
        
        document = {
            'username': username,
            'type': 'progress',
            'metrics': metrics,
            'text': text,
            'timestamp': datetime.now(timezone.utc) # Mejor práctica
            'iteration': next_iteration
        }
        
        result = collection.insert_one(document)
        success = result.inserted_id is not None
        
        if success:
            logger.info(f"Progreso guardado para {username}, iteración {next_iteration}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error al guardar progreso: {str(e)}")
        return False

def get_writing_baseline(username):
    """
    Obtiene la línea base de un usuario.
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        return collection.find_one({
            'username': username,
            'type': 'baseline'
        })
    except Exception as e:
        logger.error(f"Error al obtener línea base: {str(e)}")
        return None

def get_writing_progress(username, limit=None):
    """
    Obtiene el historial de progreso de un usuario.
    Args:
        username: ID del usuario
        limit: Número máximo de registros a retornar
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        cursor = collection.find(
            {
                'username': username,
                'type': 'progress'
            },
            sort=[('iteration', -1)]
        )
        
        if limit:
            cursor = cursor.limit(limit)
            
        return list(cursor)
        
    except Exception as e:
        logger.error(f"Error al obtener progreso: {str(e)}")
        return []

def get_latest_writing_metrics(username):
    """
    Obtiene las métricas más recientes (línea base o progreso).
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        return collection.find_one(
            {'username': username},
            sort=[('timestamp', -1)]
        )
    except Exception as e:
        logger.error(f"Error al obtener métricas recientes: {str(e)}")
        return None