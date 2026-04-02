# /modules/database/chat_mongo_db.py
from .mongo_db import insert_document, find_documents, get_collection
from datetime import datetime, timezone
import logging
import re

logger = logging.getLogger(__name__)
COLLECTION_NAME = 'chat_history-v3'

def clean_text_content(text: str) -> str:
    """
    Limpia y normaliza el texto para almacenamiento seguro en UTF-8.
    
    Args:
        text: Texto a limpiar
        
    Returns:
        str: Texto limpio y normalizado
    """
    if not text:
        return text
    
    # Caracteres especiales a eliminar (incluyendo los bloques y otros caracteres problemáticos)
    special_chars = ["▌", "\u2588", "\u2580", "\u2584", "\u258C", "\u2590"]
    
    # Eliminar caracteres especiales
    for char in special_chars:
        text = text.replace(char, "")
    
    # Normalizar espacios y saltos de línea
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Asegurar codificación UTF-8
    try:
        text = text.encode('utf-8', errors='strict').decode('utf-8')
    except UnicodeError:
        text = text.encode('utf-8', errors='ignore').decode('utf-8')
        logger.warning("Se encontraron caracteres no UTF-8 en el texto")
    
    return text

#######################################################################
def get_chat_history(username: str = None, group_id: str = None, analysis_type: str = 'sidebar', limit: int = None) -> list:
    try:
        collection = get_collection(COLLECTION_NAME)
        # Búsqueda flexible
        query = {"$or": [{"analysis_type": analysis_type}, {"analysis_type": None}]}
        if group_id: query["group_id"] = group_id
        else: query["username"] = username

        cursor = collection.find(query).sort("timestamp", -1)
        if limit: cursor = cursor.limit(limit)
            
        conversations = []
        for chat in cursor:
            try:
                # 1. Asegurar timestamp del documento
                doc_ts = chat.get('timestamp')
                if not doc_ts:
                    doc_ts = datetime.now(timezone.utc)
                
                # 2. Limpiar mensajes y asegurar que tengan timestamp
                cleaned_messages = []
                for msg in chat.get('messages', []):
                    msg_ts = msg.get('timestamp', doc_ts)
                    # Forzar a string para Streamlit
                    if isinstance(msg_ts, datetime):
                        msg_ts = msg_ts.strftime("%Y-%m-%d %H:%M:%S")
                    
                    cleaned_messages.append({
                        'role': msg.get('role', 'unknown'),
                        'content': clean_text_content(str(msg.get('content', ''))),
                        'timestamp': msg_ts
                    })
                
                conversations.append({
                    'timestamp': doc_ts,
                    'messages': cleaned_messages,
                    'visual_graph': chat.get('visual_graph'), # Aquí recuperamos el grafo del chat
                    'analysis_type': chat.get('analysis_type')
                })
            except Exception as e:
                logger.error(f"Fallo en documento individual: {e}")
                continue
        return conversations
    except Exception as e:
        logger.error(f"Error crítico en recuperación: {e}")
        return []

##############################################

def store_chat_history(username, group_id, messages, analysis_type, metadata=None):
    try:
        collection = get_collection(COLLECTION_NAME)
        
        formatted_messages = []
        for msg in messages:
            # Aseguramos que el timestamp sea consistente
            ts = msg.get('timestamp')
            if isinstance(ts, datetime):
                ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            formatted_messages.append({
                'role': msg.get('role', 'unknown'),
                'content': clean_text_content(msg.get('content', '')),
                'timestamp': ts_str # Guardamos como string para el UI
            })
        
        chat_document = {
            'username': username,
            'group_id': group_id,  
            'timestamp': datetime.now(timezone.utc), # Meta-timestamp de la sesión
            'messages': formatted_messages,
            'analysis_type': analysis_type,
            'visual_graph': metadata.get('visual_graph') if metadata else None, # Nuevo campo
            'metadata': metadata or {}
        }
        
        result = collection.insert_one(chat_document)
        return True if result.inserted_id else False
    except Exception as e:
        logger.error(f"Error al guardar historial: {str(e)}")
        return False