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
def store_student_semantic_result(username, group_id, text, analysis_result, lang_code='es', file_name="archivo_sin_nombre"):
    """
    Guarda el análisis semántico vinculado al GRUPO.
    Se eliminan las dependencias externas para evitar advertencias de VS Code.
    """
    try:
        # --- AÑADE ESTA VALIDACIÓN DE SEGURIDAD ---
        if isinstance(analysis_result, str):
            import json
            try:
                analysis_result = json.loads(analysis_result)
            except:
                logger.error("analysis_result llegó como string y no es JSON válido")
                return False
        # ------------------------------------------
        # 1. Validación de datos mínimos
        if not all([username, group_id, text, analysis_result]):
            logger.error(f"Datos insuficientes para guardar el análisis (Grupo: {group_id})")
            return False

        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            return False

        # 2. Procesamiento y Compresión del Gráfico
        concept_graph_data = analysis_result.get('concept_graph')
        final_graph_bytes = None

        if concept_graph_data:
            try:
                if isinstance(concept_graph_data, str):
                    final_graph_bytes = base64.b64decode(concept_graph_data)
                else:
                    final_graph_bytes = concept_graph_data

                # Compresión para evitar error 413 (Payload Too Large)
                img = Image.open(io.BytesIO(final_graph_bytes))
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=75, optimize=True)
                final_graph_bytes = output.getvalue()
                
            except Exception as e:
                logger.warning(f"Error optimizando gráfico: {str(e)}")
                if isinstance(concept_graph_data, bytes):
                    final_graph_bytes = concept_graph_data

        # 3. Gestión de Jerarquía (is_latest)
        collection.update_many(
            {'group_id': group_id, 'username': username, 'is_latest': True},
            {'$set': {'is_latest': False}}
        )

        # 4. Preparar el documento normalizado para semantic_mongo_db.py
        analysis_document = {
            'group_id': group_id,
            'username': username,
            'timestamp': datetime.now(timezone.utc),
            'analysis_type': 'standard_semantic',
            'is_latest': True,
            'language': lang_code,  # Usamos el parámetro pasado, no st.session_state
            'text': text[:50000], 
            'concept_graph': final_graph_bytes,
            'metadata': {
                'file_name': file_name 
            }
        }

        # 5. Inserción
        result = collection.insert_one(analysis_document)
        return bool(result.inserted_id)

    except Exception as e:
        logger.error(f"Error en store_student_semantic_result: {str(e)}", exc_info=True)
        return False

####################################################################################
def get_student_semantic_analysis(username=None, group_id=None, limit=None):
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None: return []

        # 1. Filtro dinámico: Si hay group_id, traemos a todos los del grupo
        query = {"concept_graph": {"$exists": True, "$ne": None}}
        if group_id:
            query["group_id"] = group_id
        elif username:
            query["username"] = username

        pipeline = [
            {"$match": query},
            {"$addFields": {
                "normalized_date": {"$convert": {"input": "$timestamp", "to": "date", "onError": None}}
            }},
            {"$sort": {"normalized_date": -1}}
        ]
        
        if limit: pipeline.append({"$limit": limit})
            
        pipeline.append({
            "$project": {
                "username": 1, "group_id": 1, "timestamp": 1,
                "text": 1, "key_concepts": 1, "concept_graph": 1,
                "analysis_result": 1, "_id": 1
            }
        })
        
        return list(collection.aggregate(pipeline))
    except Exception as e:
        logger.error(f"Error en semantic analysis: {e}")
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