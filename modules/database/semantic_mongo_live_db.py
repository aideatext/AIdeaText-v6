
# modules/database/semantic_mongo_live_db.py
# Importaciones estándar
import logging
import io
import base64
from datetime import datetime, timezone
from pymongo.errors import PyMongoError
from PIL import Image

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

def store_student_semantic_live_result(username, group_id, text, analysis_result, lang_code='es'):
    """
    Guarda o ACTUALIZA el análisis actual del grupo. 
    Al usar upsert=True, el Tutor Virtual siempre leerá la última versión.
    """
    try:
        if not all([username, group_id, text]):
            logger.error("Faltan datos esenciales (username, group_id o texto)")
            return False

        collection = get_collection(COLLECTION_NAME)
        if collection is None: return False

        # Extraemos el grafo (el corazón de la retroalimentación del tutor)
        graph_b64 = analysis_result.get('concept_graph')

       # 4. Preparar el documento normalizado para semantic_mongo_live_db.py
        document = {
            'group_id': group_id,
            'username': username,
            'timestamp': datetime.now(timezone.utc),
            'analysis_type': 'live_semantic',
            'is_latest': True,                  # Para que el tutor sepa que es lo que el alumno escribe "ahora"
            'language': lang_code,
            'text': text,                       # Contenido del text_area en vivo
            'key_concepts': analysis_result.get('key_concepts', []),
            'concept_graph': graph_b64,         # Grafo generado del texto en vivo
            'status': 'active'                  # Metadato adicional de sesión
        }

        # LA MAGIA: update_one con upsert=True
        # Si el group_id ya existe, lo actualiza. Si no, lo crea.
        result = collection.update_one(
            {'group_id': group_id}, 
            {'$set': document}, 
            upsert=True
        )
        
        logger.info(f"Pizarrón actualizado para grupo {group_id}. Listo para el Tutor.")
        return True

    except Exception as e:
        logger.error(f"Error al actualizar el pizarrón en vivo: {str(e)}")
        return False

##########################################
def get_live_analysis_for_tutor(group_id):
    """
    Función que usará el Tutor Virtual para obtener el contexto actual.
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        return collection.find_one({'group_id': group_id})
    except Exception as e:
        logger.error(f"Error al recuperar contexto para el tutor: {e}")
        return None
##########################################
def get_student_semantic_live_analysis(username=None, group_id=None, limit=10):
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None: return []

        # CAMBIO: Priorizamos group_id para unificar la visualización
        query = {"concept_graph": {"$exists": True, "$ne": None}}
        if group_id:
            query["group_id"] = group_id
        elif username:
            query["username"] = username

        pipeline = [
            {"$match": query},
            {"$addFields": {
                "sort_date": {"$convert": {"input": "$timestamp", "to": "date", "onError": "$timestamp"}}
            }},
            {"$sort": {"sort_date": -1}},
            {"$limit": limit},
            {"$project": {
                "username": 1,
                "group_id": 1,
                "timestamp": 1,
                "text": 1,
                "key_concepts": 1,
                "concept_graph": 1,
                "_id": 1
            }}
        ]
        return list(collection.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error en live analysis: {e}")
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