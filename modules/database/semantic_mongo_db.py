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

###################################################
def store_student_semantic_result(username, group_id, text, analysis_result, lang_code='en'):
    """
    Guarda el análisis semántico (archivos) vinculándolo al GRUPO.
    Mantiene la compresión de imagen para evitar errores de tamaño (413).
    """
    try:
        # 1. Validación de datos mínimos (ahora incluye group_id)
        if not all([username, group_id, text, analysis_result]):
            logger.error(f"Datos insuficientes para guardar el análisis (Grupo: {group_id})")
            return False

        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            return False

        # 2. Procesamiento Único del Gráfico (TU LÓGICA PRESERVADA)
        concept_graph_data = analysis_result.get('concept_graph')
        final_graph_bytes = None

        if concept_graph_data:
            try:
                if isinstance(concept_graph_data, str):
                    final_graph_bytes = base64.b64decode(concept_graph_data)
                else:
                    final_graph_bytes = concept_graph_data

                # --- COMPRESIÓN PARA EVITAR ERROR 413 ---
                img = Image.open(io.BytesIO(final_graph_bytes))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                output = io.BytesIO()
                # Calidad 75% reduce el peso sin perder claridad
                img.save(output, format="JPEG", quality=75, optimize=True)
                final_graph_bytes = output.getvalue()
                
                logger.info(f"Grafo optimizado: {len(final_graph_bytes)} bytes")
            except Exception as e:
                logger.warning(f"Error procesando gráfico, se intentará guardar original: {str(e)}")
                if not final_graph_bytes and isinstance(concept_graph_data, bytes):
                    final_graph_bytes = concept_graph_data

        # 3. Gestión de 'Buzón para el Tutor' (is_latest)
        # Marcamos análisis anteriores del grupo como no-recientes
        try:
            collection.update_many(
                {'group_id': group_id, 'is_latest': True},
                {'$set': {'is_latest': False}}
            )
        except Exception as e:
            logger.warning(f"No se pudo actualizar is_latest anteriores: {e}")

        # 4. Preparar el documento (Estructura para Equipos)
        analysis_document = {
            'group_id': group_id,       # <--- NUEVO: Identificador de equipo
            'username': username,       # Quién subió/analizó
            'timestamp': datetime.now(timezone.utc),
            'text': text[:50000], 
            'language': lang_code,
            'is_latest': True,          # <--- NUEVO: Indica al Tutor cuál es el archivo activo
            'analysis_type': 'standard_semantic',
            'key_concepts': analysis_result.get('key_concepts', []),
            'entities': analysis_result.get('entities', []),
            'concept_graph': final_graph_bytes 
        }

        # 5. Inserción
        result = collection.insert_one(analysis_document)
        if result.inserted_id:
            logger.info(f"Análisis de archivo guardado para grupo {group_id}. ID: {result.inserted_id}")
            return True
        return False

    except Exception as e:
        logger.error(f"Error inesperado en store_student_semantic_result: {str(e)}", exc_info=True)
        return False

####################################################################################
def get_student_semantic_analysis(username=None, group_id=None, limit=None):
    """
    Recupera los análisis semánticos filtrando por usuario O por grupo.
    Mantiene la normalización de fechas y la integridad del pipeline de agregación.
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección semantic")
            return []

        # 1. Construcción dinámica del filtro (Query)
        # Siempre filtramos que el grafo exista
        query = {"concept_graph": {"$exists": True, "$ne": None}}
        
        if username:
            query["username"] = username
        if group_id:
            query["group_id"] = group_id

        # 2. Pipeline de agregación
        pipeline = [
            {"$match": query},
            {"$addFields": {
                "normalized_date": {
                    "$convert": {
                        "input": "$timestamp",
                        "to": "date",
                        "onError": None,
                        "onNull": None
                    }
                }
            }},
            # Orden cronológico descendente (más reciente primero)
            {"$sort": {"normalized_date": -1}}
        ]
        
        # Aplicamos el límite si se especifica
        if limit is not None:
            pipeline.append({"$limit": limit})
            
        # 3. Proyección de campos (IMPORTANTE: Se añade analysis_result para M1/M2)
        pipeline.append({
            "$project": {
                "username": 1,
                "group_id": 1,
                "timestamp": 1,
                "text": 1,
                "key_concepts": 1,
                "concept_graph": 1,
                "analysis_result": 1,  # <--- Crucial para el Dashboard
                "analysis_type": 1,
                "_id": 1
            }
        })
        
        results = list(collection.aggregate(pipeline))
        
        # Logging informativo
        contexto = f"grupo {group_id}" if group_id else f"usuario {username}"
        logger.info(f"Recuperados {len(results)} análisis para {contexto}")
        
        return results
        
    except PyMongoError as e:
        logger.error(f"Error de MongoDB en la agregación: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado al recuperar análisis: {str(e)}")
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