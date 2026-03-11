#/modules/database/semantic_mongo_db.py

# Importaciones estándar corregidas y optimizadas
import io
import base64
from datetime import datetime, timezone
import logging
from PIL import Image  # Necesario para la optimización

# Importaciones de terceros
import matplotlib.pyplot as plt
from pymongo.errors import PyMongoError

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
COLLECTION_NAME = 'student_semantic_analysis'

def store_student_semantic_result(username, text, analysis_result, lang_code='en'):
    """
    NOMBRE PRESERVADO. Guarda el resultado del análisis semántico en MongoDB.
    Optimizado para evitar el error 413 (Request size too large) mediante compresión.
    """
    try:
        # 1. Validación de datos mínimos
        if not all([username, text, analysis_result]):
            logger.error("Datos insuficientes para guardar el análisis")
            return False

        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error(f"No se pudo obtener la colección {COLLECTION_NAME}")
            return False

        # 2. Procesamiento Único del Gráfico (Optimizado y sin redundancias)
        concept_graph_data = analysis_result.get('concept_graph')
        final_graph_bytes = None

        if concept_graph_data:
            try:
                # Convertir de base64 a bytes si es necesario
                if isinstance(concept_graph_data, str):
                    final_graph_bytes = base64.b64decode(concept_graph_data)
                else:
                    final_graph_bytes = concept_graph_data

                # --- COMPRESIÓN PARA EVITAR ERROR 413 ---
                img = Image.open(io.BytesIO(final_graph_bytes))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                output = io.BytesIO()
                # Calidad 75% reduce el peso drásticamente sin perder claridad en los nodos
                img.save(output, format="JPEG", quality=75, optimize=True)
                final_graph_bytes = output.getvalue()
                
                logger.info(f"Grafo optimizado: {len(final_graph_bytes)} bytes para usuario {username}")
            except Exception as e:
                logger.warning(f"Error procesando gráfico, se intentará guardar original: {str(e)}")
                # Si falla la compresión, mantenemos los bytes originales si existen
                if not final_graph_bytes and isinstance(concept_graph_data, bytes):
                    final_graph_bytes = concept_graph_data

        # 3. Preparar el documento (Estructura limpia)
        analysis_document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc),
            'text': text[:50000],  # Límite de seguridad para textos extremadamente largos
            'language': lang_code,
            'analysis_type': 'standard_semantic',
            'key_concepts': analysis_result.get('key_concepts', []),
            'entities': analysis_result.get('entities', []),
            'concept_graph': final_graph_bytes  # Los bytes ya procesados/comprimidos
        }

        # 4. Inserción en MongoDB
        try:
            result = collection.insert_one(analysis_document)
            if result.inserted_id:
                logger.info(f"Análisis guardado exitosamente. ID: {result.inserted_id}")
                return True
            return False
        except PyMongoError as e:
            logger.error(f"Error de inserción en MongoDB: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"Error inesperado en store_student_semantic_result: {str(e)}", exc_info=True)
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

        # Estandarizado: Buscamos todo lo del usuario que tenga un grafo
        query = {
            "username": username,
            "concept_graph": {"$exists": True, "$ne": None}
        }
        
        # Recuperamos y ordenamos por fecha (2026 aparecerá primero, luego 2025)
        analyses = list(collection.find(query).sort("timestamp", -1).limit(limit))
        
        # Versión alternativa sin projection
        cursor = collection.find(query, {
            "timestamp": 1,
            "text": 1,
            "key_concepts": 1,
            "concept_graph": 1,
            "analysis_type": 1,
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