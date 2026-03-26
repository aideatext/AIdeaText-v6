
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

def store_student_semantic_live_result(username, text, analysis_result, lang_code='en'):
    """
    Versión optimizada:
    - Elimina redundancias en el procesamiento de bytes.
    - Soluciona el error 413 (RequestEntityTooLarge) mediante compresión JPEG.
    - Manejo de fechas nativo para MongoDB.
    """
    try:
        # 1. Validación inicial y obtención de colección
        if not all([username, text, analysis_result]):
            logger.error("Parámetros incompletos para guardar análisis")
            return False

        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error(f"No se pudo obtener la colección {COLLECTION_NAME}")
            return False

        # 2. Procesamiento y Optimización del Gráfico (Sin redundancias)
        graph_data = analysis_result.get('concept_graph')
        final_graph_bytes = None

        if graph_data:
            try:
                # Convertir a bytes si viene en base64 (string)
                if isinstance(graph_data, str):
                    final_graph_bytes = base64.b64decode(graph_data)
                else:
                    final_graph_bytes = graph_data

                # Optimización de tamaño para evitar error 413 en Azure/Mongo
                # Solo comprimimos si detectamos que existe la imagen
                img = Image.open(io.BytesIO(final_graph_bytes))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                output = io.BytesIO()
                # JPEG al 75% mantiene legibilidad y reduce el peso drásticamente
                img.save(output, format="JPEG", quality=75, optimize=True)
                final_graph_bytes = output.getvalue()
                
                logger.info(f"Grafo optimizado para {username} ({len(final_graph_bytes)} bytes)")
            except Exception as e:
                logger.warning(f"Error optimizando imagen, se usará formato original: {e}")
                # Si falla la optimización, mantenemos lo que teníamos (si eran bytes)
                final_graph_bytes = final_graph_bytes if isinstance(final_graph_bytes, bytes) else None

        # 3. Preparación del documento (Directo y limpio)
        analysis_document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc),
            'text': text[:50000],  # Límite de seguridad
            'analysis_type': 'semantic_live',
            'language': lang_code,
            'key_concepts': analysis_result.get('key_concepts', []),
            'concept_centrality': analysis_result.get('concept_centrality', {}),
            'concept_graph': final_graph_bytes  # Insertamos los bytes ya procesados
        }

        # 4. Inserción en base de datos
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
        logger.error(f"Error inesperado en store_student_semantic_live_result: {str(e)}", exc_info=True)
        return False

##########################################
##########################################
def get_student_semantic_live_analysis(username, limit=10):
    """
    Versión optimizada: Elimina redundancia y garantiza orden cronológico 
    mediante normalización de fechas al vuelo.
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección")
            return []

        # Criterio de búsqueda: usuario específico y que tenga el grafo generado
        query = {
            "username": username,
            "concept_graph": {"$exists": True, "$ne": None}
        }

        # Pipeline de Agregación para resolver el desorden de fechas (2025 vs 2026)
        pipeline = [
            {"$match": query},
            # Convertimos el timestamp a objeto Date real para que el sort sea exacto
            {"$addFields": {
                "sort_date": {
                    "$convert": {
                        "input": "$timestamp",
                        "to": "date",
                        "onError": "$timestamp", # Si falla, mantiene el valor original
                        "onNull": "$timestamp"
                    }
                }
            }},
            # Ordenamos por la fecha normalizada de forma descendente (más reciente primero)
            {"$sort": {"sort_date": -1}},
            {"$limit": limit},
            # Proyectamos solo los campos necesarios para no sobrecargar la memoria
            {"$project": {
                "timestamp": 1,
                "text": 1,
                "key_concepts": 1,
                "concept_graph": 1,
                "analysis_type": 1,
                "_id": 1
            }}
        ]

        # Ejecutamos una única vez la consulta
        results = list(collection.aggregate(pipeline))
        
        logger.info(f"Recuperados {len(results)} análisis 'live' para {username}")
        return results

    except PyMongoError as e:
        logger.error(f"Error de MongoDB en live analysis: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado en live analysis: {str(e)}")
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