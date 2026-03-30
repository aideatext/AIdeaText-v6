# modules/database/discourse_mongo_db.py
import base64
import logging
from datetime import datetime, timezone
from ..database.mongo_db import get_collection, insert_document, find_documents

logger = logging.getLogger(__name__)

COLLECTION_NAME = 'student_discourse_analysis'

def store_student_discourse_result(username, group_id, text1, text2, analysis_result, mode="evolution"):
    """
    Guarda el resultado del análisis de discurso en MongoDB vinculado al grupo.
    """
    try:
        if not analysis_result.get('success', False):
            return False
        
        collection = get_collection(COLLECTION_NAME)
        if collection is None: return False

        document = {
            'username': username,
            'group_id': group_id,
            'mode': mode,
            'timestamp': datetime.now(timezone.utc),
            'text1': text1,
            'text2': text2,
            'key_concepts1': analysis_result.get('key_concepts1', []),
            'key_concepts2': analysis_result.get('key_concepts2', []),
            'metrics': analysis_result.get('metrics', {})
        }
        
        for graph_key in ['graph1', 'graph2', 'combined_graph']:
            if graph_key in analysis_result and analysis_result[graph_key] is not None:
                if isinstance(analysis_result[graph_key], bytes):
                    document[graph_key] = base64.b64encode(analysis_result[graph_key]).decode('utf-8')
                else:
                    document[graph_key] = analysis_result[graph_key]
            
        result = collection.insert_one(document)
        return True
    except Exception as e:
        logger.error(f"Error guardando análisis: {e}")
        return False

# --- FUNCIÓN RESTAURADA Y MEJORADA ---
def get_student_discourse_analysis(username=None, group_id=None, limit=100):
    """
    Recupera los análisis de discurso. 
    Puede filtrar por usuario (estudiante) o por grupo (profesor).
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None: return []
            
        query = {}
        if username:
            query["username"] = username
        if group_id:
            query["group_id"] = group_id
            
        documents = list(collection.find(query).sort("timestamp", -1).limit(limit))
        
        # Decodificación de gráficos (Lógica del BackUp preservada)
        for doc in documents:
            for graph_key in ['graph1', 'graph2', 'combined_graph']:
                if graph_key in doc and isinstance(doc[graph_key], str):
                    try:
                        doc[graph_key] = base64.b64decode(doc[graph_key])
                    except:
                        doc[graph_key] = None
        return documents
    except Exception as e:
        logger.error(f"Error recuperando análisis: {e}")
        return []

def get_student_discourse_data(username):
    """Obtiene un resumen formateado para interfaces de historial."""
    try:
        analyses = get_student_discourse_analysis(username=username, limit=10)
        return {'entries': [{
            'timestamp': a['timestamp'],
            'text1': a.get('text1', ''),
            'text2': a.get('text2', ''),
            'key_concepts1': a.get('key_concepts1', []),
            'key_concepts2': a.get('key_concepts2', [])
        } for a in analyses]}
    except:
        return {'entries': []}