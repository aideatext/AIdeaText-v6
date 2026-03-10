#/modules/database/semantic_mongo_db.py

# Importaciones estándar
import io
import base64
from datetime import datetime, timezone
import logging

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
logger = logging.getLogger(__name__)  # Cambiado de name a __name__
COLLECTION_NAME = 'student_semantic_analysis'

####################################################################
# modules/database/semantic_mongo_db.py
def store_student_semantic_result(username, text, analysis_result, lang_code='en'):
    """
    Guarda el resultado del análisis semántico en MongoDB.
    Args:
        username: Nombre del usuario
        text: Texto completo analizado
        analysis_result: Diccionario con los resultados del análisis
        lang_code: Código de idioma (opcional, default 'en')
    """
    try:
        # Verificar datos mínimos requeridos
        if not username or not text or not analysis_result:
            logger.error("Datos insuficientes para guardar el análisis")
            return False

        # Preparar el gráfico conceptual
        concept_graph_data = None
        if 'concept_graph' in analysis_result and analysis_result['concept_graph'] is not None:
            try:
                if isinstance(analysis_result['concept_graph'], bytes):
                    concept_graph_data = base64.b64encode(analysis_result['concept_graph']).decode('utf-8')
                else:
                    logger.warning("El gráfico conceptual no está en formato bytes")
            except Exception as e:
                logger.error(f"Error al codificar gráfico conceptual: {str(e)}")

        # Crear documento para MongoDB
        analysis_document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'text': text,
            'analysis_type': 'semantic',
            'key_concepts': analysis_result.get('key_concepts', []),
            'concept_centrality': analysis_result.get('concept_centrality', {}),
            'concept_graph': concept_graph_data,
            'language': lang_code  # Usamos el parámetro directamente
        }

        # Insertar en MongoDB
        result = insert_document(COLLECTION_NAME, analysis_document)
        if result:
            logger.info(f"Análisis semántico guardado para {username}")
            return True
        
        logger.error("No se pudo insertar el documento en MongoDB")
        return False

    except Exception as e:
        logger.error(f"Error al guardar el análisis semántico: {str(e)}", exc_info=True)
        return False

####################################################################################
def get_student_semantic_analysis(username, limit=10):
    """
    Recupera los análisis semánticos de un estudiante.
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección semantic")
            return []

        query = {
            "username": username,
            "analysis_type": "semantic"
        }
        
        # Actualizar la proyección para incluir todos los campos necesarios
        projection = {
            "timestamp": 1,
            "text": 1,  # Añadir este campo
            "key_concepts": 1,  # Añadir este campo
            "entities": 1,  # Añadir este campo
            "concept_graph": 1,
            "_id": 1
        }
        
        try:
            cursor = collection.find(query, projection).sort("timestamp", -1)
            if limit:
                cursor = cursor.limit(limit)
            
            results = list(cursor)
            logger.info(f"Recuperados {len(results)} análisis semánticos para {username}")
            return results
            
        except Exception as db_error:
            logger.error(f"Error en la consulta a MongoDB: {str(db_error)}")
            return []
        
    except Exception as e:
        logger.error(f"Error recuperando análisis semántico: {str(e)}")
        return []
####################################################################################################


def update_student_semantic_analysis(analysis_id, update_data):
    """
    Actualiza un análisis semántico existente.
    Args:
        analysis_id: ID del análisis a actualizar
        update_data: Datos a actualizar
    """
    query = {"_id": analysis_id}
    update = {"$set": update_data}
    return update_document(COLLECTION_NAME, query, update)

def delete_student_semantic_analysis(analysis_id):
    """
    Elimina un análisis semántico.
    Args:
        analysis_id: ID del análisis a eliminar
    """
    query = {"_id": analysis_id}
    return delete_document(COLLECTION_NAME, query)


############################################################################
def get_student_semantic_data(username):
    """
    Obtiene todos los análisis semánticos de un estudiante.
    Args:
        username: Nombre del usuario
    Returns:
        dict: Diccionario con todos los análisis del estudiante
    """
    try:
        analyses = get_student_semantic_analysis(username, limit=None)
        
        formatted_analyses = []
        for analysis in analyses:
            # Asegurarse de que los campos existan antes de acceder a ellos
            formatted_analysis = {
                'timestamp': analysis.get('timestamp'),
                'text': analysis.get('text', ''),  # Usar get() con valor por defecto
                'key_concepts': analysis.get('key_concepts', []),
                'entities': analysis.get('entities', []),
                'concept_graph': analysis.get('concept_graph')  # Mantener el gráfico
            }
            formatted_analyses.append(formatted_analysis)
        
        return {
            'username': username,
            'entries': formatted_analyses,
            'count': len(formatted_analyses),
            'status': 'success'
        }
    
    except Exception as e:
        logger.error(f"Error al obtener datos semánticos para {username}: {str(e)}")
        return {
            'username': username,
            'entries': [],
            'count': 0,
            'status': 'error',
            'error': str(e)
        }


##########################################################################
# Exportar las funciones necesarias
__all__ = [
    'store_student_semantic_result',
    'get_student_semantic_analysis',
    'update_student_semantic_analysis',
    'delete_student_semantic_analysis',
    'get_student_semantic_data'
]