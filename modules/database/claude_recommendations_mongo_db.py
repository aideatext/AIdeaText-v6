# modules/database/claude_recommendations_mongo_db.py
from datetime import datetime, timezone, timedelta
import logging
from .mongo_db import get_collection

logger = logging.getLogger(__name__)
COLLECTION_NAME = 'student_claude_recommendations'

def store_claude_recommendation(username, text, metrics, text_type, recommendations):
    """
    Guarda las recomendaciones generadas por Claude AI.
    
    Args:
        username: Nombre del usuario
        text: Texto analizado
        metrics: Métricas del análisis
        text_type: Tipo de texto (academic_article, university_work, general_communication)
        recommendations: Recomendaciones generadas por Claude
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        # Verificar parámetros
        if not all([username, text, recommendations]):
            logger.error("Faltan parámetros requeridos para guardar recomendaciones de Claude")
            return False
            
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección de recomendaciones de Claude")
            return False
            
        # Crear documento
        document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc) # Mejor práctica
            'text': text,
            'metrics': metrics or {},
            'text_type': text_type,
            'recommendations': recommendations,
            'analysis_type': 'claude_recommendation'
        }
        
        # Insertar documento
        result = collection.insert_one(document)
        if result.inserted_id:
            logger.info(f"""
                Recomendaciones de Claude guardadas:
                - Usuario: {username}
                - ID: {result.inserted_id}
                - Tipo de texto: {text_type}
                - Longitud del texto: {len(text)}
            """)
            
            # Verificar almacenamiento
            storage_verified = verify_recommendation_storage(username)
            if not storage_verified:
                logger.warning("Verificación de almacenamiento de recomendaciones falló")
            
            return True
            
        logger.error("No se pudo insertar el documento de recomendaciones")
        return False
        
    except Exception as e:
        logger.error(f"Error guardando recomendaciones de Claude: {str(e)}")
        return False

def verify_recommendation_storage(username):
    """
    Verifica que las recomendaciones se están guardando correctamente.
    
    Args:
        username: Nombre del usuario
        
    Returns:
        bool: True si la verificación es exitosa, False en caso contrario
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección para verificación de recomendaciones")
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
                Último documento de recomendaciones guardado:
                - ID: {docs[0]['_id']}
                - Timestamp: {docs[0]['timestamp']}
                - Tipo de texto: {docs[0].get('text_type', 'N/A')}
            """)
            return True
            
        logger.warning(f"No se encontraron documentos recientes de recomendaciones para {username}")
        return False
        
    except Exception as e:
        logger.error(f"Error verificando almacenamiento de recomendaciones: {str(e)}")
        return False

def get_claude_recommendations(username, limit=10):
    """
    Obtiene las recomendaciones más recientes de Claude para un usuario.
    
    Args:
        username: Nombre del usuario
        limit: Número máximo de recomendaciones a recuperar
        
    Returns:
        list: Lista de recomendaciones
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección de recomendaciones")
            return []
            
        results = collection.find(
            {'username': username}
        ).sort('timestamp', -1).limit(limit)
        
        recommendations = list(results)
        logger.info(f"Recuperadas {len(recommendations)} recomendaciones de Claude para {username}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error obteniendo recomendaciones de Claude: {str(e)}")
        return []