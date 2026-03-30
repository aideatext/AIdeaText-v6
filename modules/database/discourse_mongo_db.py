# modules/database/discourse_mongo_db.py
import base64
import logging
from datetime import datetime, timezone
from ..database.mongo_db import get_collection, insert_document, find_documents

logger = logging.getLogger(__name__)

COLLECTION_NAME = 'student_discourse_analysis'

########################################################################

def store_student_discourse_result(username, text1, text2, analysis_result):
    """
    Guarda el resultado del análisis de discurso en MongoDB.
    """
    try:
        # Verificar que el resultado sea válido
        if not analysis_result.get('success', False):
            logger.error("No se puede guardar un análisis fallido")
            return False
            
        logger.info(f"Almacenando análisis de discurso para {username}")
        
        # Preparar el documento para MongoDB
        document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc), # Mejor práctica
            'text1': text1,
            'text2': text2,
            'key_concepts1': analysis_result.get('key_concepts1', []),
            'key_concepts2': analysis_result.get('key_concepts2', [])
        }
        
        # Codificar gráficos a base64 para almacenamiento
        for graph_key in ['graph1', 'graph2', 'combined_graph']:
            if graph_key in analysis_result and analysis_result[graph_key] is not None:
                if isinstance(analysis_result[graph_key], bytes):
                    logger.info(f"Codificando {graph_key} como base64")
                    document[graph_key] = base64.b64encode(analysis_result[graph_key]).decode('utf-8')
                    logger.info(f"{graph_key} codificado correctamente, longitud: {len(document[graph_key])}")
                else:
                    logger.warning(f"{graph_key} no es de tipo bytes, es: {type(analysis_result[graph_key])}")
            else:
                logger.info(f"{graph_key} no presente en el resultado del análisis")
        
        # Almacenar el documento en MongoDB
        collection = get_collection(COLLECTION_NAME)
        if collection is None:  # CORREGIDO: Usar 'is None' en lugar de valor booleano
            logger.error("No se pudo obtener la colección")
            return False
            
        result = collection.insert_one(document)
        logger.info(f"Análisis de discurso guardado con ID: {result.inserted_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error guardando análisis de discurso: {str(e)}")
        return False

#################################################################################

# Corrección 1: Actualizar get_student_discourse_analysis para recuperar todos los campos necesarios

def store_student_discourse_result(username, group_id, text1, text2, analysis_result, mode="evolution"):
    """
    Guarda el resultado del análisis de discurso en MongoDB vinculado al grupo.
    mode="evolution": Comparación de borradores propios.
    mode="contrast": Comparación de fuentes externas.
    """
    try:
        # 1. Verificar validez del análisis y datos mínimos
        if not analysis_result.get('success', False):
            logger.error("No se puede guardar un análisis fallido")
            return False
        
        if not all([username, group_id, text1, text2]):
            logger.error(f"Datos insuficientes para guardar (Grupo: {group_id})")
            return False
            
        logger.info(f"Almacenando análisis de discurso ({mode}) para usuario {username} del grupo {group_id}")
        
        # 2. Preparar el documento base
        document = {
            'username': username,
            'group_id': group_id,      # Identificador del equipo
            'mode': mode,              # Diferenciador pedagógico
            'timestamp': datetime.now(timezone.utc),
            'text1': text1,
            'text2': text2,
            'key_concepts1': analysis_result.get('key_concepts1', []),
            'key_concepts2': analysis_result.get('key_concepts2', []),
            'metrics': analysis_result.get('metrics', {}) # Métricas de coherencia/avance
        }
        
        # 3. Codificar gráficos a base64 (TU LÓGICA PRESERVADA)
        for graph_key in ['graph1', 'graph2', 'combined_graph']:
            if graph_key in analysis_result and analysis_result[graph_key] is not None:
                if isinstance(analysis_result[graph_key], bytes):
                    logger.info(f"Codificando {graph_key} como base64")
                    # Codificamos a base64 y pasamos a string utf-8 para Mongo
                    document[graph_key] = base64.b64encode(analysis_result[graph_key]).decode('utf-8')
                    logger.info(f"{graph_key} codificado correctamente, longitud: {len(document[graph_key])}")
                else:
                    # Si ya viene como string (por ejemplo de un proceso previo), lo guardamos directo
                    logger.warning(f"{graph_key} no es de tipo bytes, es: {type(analysis_result[graph_key])}")
                    document[graph_key] = analysis_result[graph_key]
            else:
                logger.info(f"{graph_key} no presente en el resultado del análisis")
        
        # 4. Almacenar en MongoDB
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección de discurso")
            return False
            
        result = collection.insert_one(document)
        logger.info(f"Análisis de discurso ({mode}) guardado con ID: {result.inserted_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error guardando análisis de discurso: {str(e)}")
        return False
        
#####################################################################################
        
def get_student_discourse_data(username):
    """
    Obtiene un resumen de los análisis del discurso de un estudiante.
    """
    try:
        analyses = get_student_discourse_analysis(username, limit=None)
        formatted_analyses = []
        
        for analysis in analyses:
            formatted_analysis = {
                'timestamp': analysis['timestamp'],
                'text1': analysis.get('text1', ''),
                'text2': analysis.get('text2', ''),
                'key_concepts1': analysis.get('key_concepts1', []),
                'key_concepts2': analysis.get('key_concepts2', [])
            }
            formatted_analyses.append(formatted_analysis)
            
        return {'entries': formatted_analyses}
        
    except Exception as e:
        logger.error(f"Error al obtener datos del discurso: {str(e)}")
        return {'entries': []}

###########################################################################
def update_student_discourse_analysis(analysis_id, update_data):
    """
    Actualiza un análisis del discurso existente.
    """
    try:
        query = {"_id": analysis_id}
        update = {"$set": update_data}
        return update_document(COLLECTION_NAME, query, update)
    except Exception as e:
        logger.error(f"Error al actualizar análisis del discurso: {str(e)}")
        return False

###########################################################################
def delete_student_discourse_analysis(analysis_id):
    """
    Elimina un análisis del discurso.
    """
    try:
        query = {"_id": analysis_id}
        return delete_document(COLLECTION_NAME, query)
    except Exception as e:
        logger.error(f"Error al eliminar análisis del discurso: {str(e)}")
        return False