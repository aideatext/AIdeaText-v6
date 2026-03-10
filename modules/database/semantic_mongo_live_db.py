
# Importaciones estándar
import logging
import io
import base64
from datetime import datetime, timezone
from pymongo.errors import PyMongoError

# Importaciones de terceros
import matplotlib.pyplot as plt

# Importaciones locales
from .mongo_db import (
    get_collection,
    insert_document, 
    find_documents, 
    update_document, 
    delete_document
)

# Configuración del logger
logger = logging.getLogger(__name__)
COLLECTION_NAME = 'student_semantic_live_analysis'

##########################################
##########################################

def store_student_semantic_live_result(username, text, analysis_result, lang_code='en'):
    """
    Versión corregida con:
    - Verificación correcta de colección
    - Manejo de proyección alternativo
    - Mejor manejo de errores
    """
    try:
        # 1. Obtener colección con verificación correcta
        collection = get_collection(COLLECTION_NAME)
        if collection is None:  # Cambiado de 'if not collection'
            logger.error(f"No se pudo obtener la colección {COLLECTION_NAME}")
            return False

        # 2. Validación de parámetros
        if not all([username, text, analysis_result]):
            logger.error("Parámetros incompletos para guardar análisis")
            return False

        # 3. Preparar documento (CORREGIDO)
        analysis_document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc) # Mejor práctica
            'text': text[:50000],
            'analysis_type': 'semantic_live',
            'language': lang_code,
            # Extraer datos correctamente del análisis
            'key_concepts': analysis_result.get('key_concepts', []),
            'concept_centrality': analysis_result.get('concept_centrality', {}),
            'concept_graph': None  # Inicializar como None
        }
        
        # 4. Manejo del gráfico (CORREGIDO)
        if 'concept_graph' in analysis_result and analysis_result['concept_graph']:
            try:
                # Si ya es bytes, usar directamente
                if isinstance(analysis_result['concept_graph'], bytes):
                    analysis_document['concept_graph'] = analysis_result['concept_graph']
                else:
                    # Convertir a bytes si es necesario
                    analysis_document['concept_graph'] = base64.b64decode(
                        analysis_result['concept_graph'])
            except Exception as e:
                logger.error(f"Error procesando gráfico: {str(e)}")

        # 5. Insertar documento
        try:
            result = collection.insert_one(analysis_document)
            if result.inserted_id:
                logger.info(f"Análisis guardado. ID: {result.inserted_id}")
                return True
            logger.error("Inserción fallida - Sin ID devuelto")
            return False
        except PyMongoError as e:
            logger.error(f"Error de MongoDB: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
        return False

##########################################
##########################################
def get_student_semantic_live_analysis(username, limit=10):
    """
    Versión corregida sin usar projection
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección")
            return []

        query = {"username": username, "analysis_type": "semantic_live"}
        
        # Versión alternativa sin projection
        cursor = collection.find(query, {
            "timestamp": 1,
            "text": 1,
            "key_concepts": 1,
            "concept_graph": 1,
            "_id": 1
        }).sort("timestamp", -1).limit(limit)
        
        results = list(cursor)
        logger.info(f"Recuperados {len(results)} análisis para {username}")
        return results
        
    except PyMongoError as e:
        logger.error(f"Error de MongoDB: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        return []

#######################################################
#######################################################
def update_student_semantic_live_analysis(analysis_id, update_data):
    """Actualiza un análisis existente con manejo de errores"""
    try:
        query = {"_id": analysis_id}
        update = {"$set": update_data}
        return update_document(COLLECTION_NAME, query, update) > 0
    except PyMongoError as e:
        logger.error(f"Error al actualizar: {str(e)}")
        return False

#######################################################
#######################################################
def delete_student_semantic_live_analysis(analysis_id):
    """Elimina un análisis con manejo de errores"""
    try:
        query = {"_id": analysis_id}
        return delete_document(COLLECTION_NAME, query) > 0
    except PyMongoError as e:
        logger.error(f"Error al eliminar: {str(e)}")
        return False

#######################################################
#######################################################
def get_student_semantic_live_data(username):
    """
    Obtiene todos los análisis semánticos en vivo de un estudiante.
    Versión corregida que usa la función _live.
    """
    try:
        analyses = get_student_semantic_live_analysis(username, limit=None)
        
        formatted_analyses = []
        for analysis in analyses:
            formatted_analysis = {
                'timestamp': analysis.get('timestamp'),
                'text': analysis.get('text', ''),
                'key_concepts': analysis.get('key_concepts', []),
                'concept_graph': analysis.get('concept_graph')
            }
            formatted_analyses.append(formatted_analysis)
        
        return {
            'username': username,
            'entries': formatted_analyses,
            'count': len(formatted_analyses),
            'status': 'success'
        }
    
    except Exception as e:
        logger.error(f"Error al obtener datos: {str(e)}")
        return {
            'username': username,
            'entries': [],
            'count': 0,
            'status': 'error',
            'error': str(e)
        }


#######################################################
#######################################################

__all__ = [
    'store_student_semantic_live_result',
    'get_student_semantic_live_analysis',
    'update_student_semantic_live_analysis',
    'delete_student_semantic_live_analysis',
    'get_student_semantic_live_data'
]