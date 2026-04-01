# modules/database/discourse_mongo_db.py
import base64
import logging
from datetime import datetime, timezone
from bson import ObjectId
from ..database.mongo_db import get_collection, insert_document, find_documents, update_document, delete_document

logger = logging.getLogger(__name__)

COLLECTION_NAME = 'student_discourse_analysis'

########################################################################
def store_student_discourse_result(username, text1, text2, analysis_result, group_id=None):
    """
    Guarda el resultado del análisis de discurso en MongoDB vinculado al grupo.
    """
    try:
        if not analysis_result.get('success', False):
            logger.error("No se puede guardar un análisis fallido")
            return False
            
        collection = get_collection(COLLECTION_NAME)
        if collection is None: return False

        # Si no viene group_id, intentamos sacarlo del session_state (opcional)
        import streamlit as st
        gid = group_id or st.session_state.get('class_id') or 'GENERAL'

        document = {
            'username': username,
            'group_id': gid,
            'timestamp': datetime.now(timezone.utc),
            'text1': text1,
            'text2': text2,
            'key_concepts1': analysis_result.get('key_concepts1', []),
            'key_concepts2': analysis_result.get('key_concepts2', []),
            'metrics': analysis_result.get('metrics', {})
        }
        
        # Codificar gráficos a base64
        for graph_key in ['graph1', 'graph2', 'combined_graph']:
            if graph_key in analysis_result and analysis_result[graph_key] is not None:
                if isinstance(analysis_result[graph_key], bytes):
                    document[graph_key] = base64.b64encode(analysis_result[graph_key]).decode('utf-8')
                else:
                    document[graph_key] = analysis_result[graph_key]
            
        result = collection.insert_one(document)
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error guardando análisis en MongoDB: {e}")
        return False

###########################################################################
def get_student_discourse_analysis(username=None, group_id=None, limit=10):
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None: return []
            
        query = {}
        # Prioridad al grupo para visualización colectiva
        if group_id: 
            query["group_id"] = group_id
        elif username: 
            query["username"] = username
            
        documents = list(collection.find(query).sort("timestamp", -1).limit(limit))
        
        # Decodificación de gráficos
        for doc in documents:
            doc['id'] = str(doc['_id'])
            for graph_key in ['graph1', 'graph2', 'combined_graph']:
                if graph_key in doc and isinstance(doc[graph_key], str):
                    try:
                        doc[graph_key] = base64.b64decode(doc[graph_key])
                    except:
                        pass
        return documents
    except Exception as e:
        logger.error(f"Error recuperando análisis: {e}")
        return []

###########################################################################
def get_student_discourse_data(username):
    """
    Versión formateada para el historial de la interfaz de usuario.
    """
    try:
        analyses = get_student_discourse_analysis(username=username, limit=10)
        formatted = []
        for a in analyses:
            formatted.append({
                'timestamp': a['timestamp'],
                'text1': a.get('text1', ''),
                'text2': a.get('text2', ''),
                'key_concepts1': a.get('key_concepts1', []),
                'key_concepts2': a.get('key_concepts2', [])
            })
        return {'entries': formatted}
    except Exception as e:
        logger.error(f"Error en get_student_discourse_data: {e}")
        return {'entries': []}

###########################################################################
def update_student_discourse_analysis(analysis_id, update_data):
    """
    Restaura la función solicitada por el ImportError.
    """
    try:
        query = {"_id": ObjectId(analysis_id) if isinstance(analysis_id, str) else analysis_id}
        update = {"$set": update_data}
        collection = get_collection(COLLECTION_NAME)
        result = collection.update_one(query, update)
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error al actualizar análisis: {e}")
        return False

###########################################################################
def delete_student_discourse_analysis(analysis_id):
    """
    Restaura la función de eliminación.
    """
    try:
        query = {"_id": ObjectId(analysis_id) if isinstance(analysis_id, str) else analysis_id}
        collection = get_collection(COLLECTION_NAME)
        result = collection.delete_one(query)
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error al eliminar análisis: {e}")
        return False