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
        # 1. Configuración de la consulta
        query = {
            "$or": [{"analysis_type": analysis_type}, {"analysis_type": None}]
        }
        if group_id:
            query["group_id"] = group_id
        else:
            query["username"] = username

        collection = get_collection(COLLECTION_NAME)
        cursor = collection.find(query).sort("timestamp", -1)
        
        if limit:
            cursor = cursor.limit(limit)
            
        conversations = []
        for chat in cursor:
            try:
                # 2. Recuperar el timestamp principal del documento
                # Si no existe, usamos la hora actual para evitar el error 'timestamp'
                chat_ts = chat.get('timestamp', datetime.now(timezone.utc))
                
                cleaned_messages = []
                for msg in chat.get('messages', []):
                    try:
                        # Aseguramos que cada mensaje tenga un rol y contenido
                        cleaned_messages.append({
                            'role': msg.get('role', 'unknown'),
                            'content': clean_text_content(msg.get('content', '')),
                            # Si el mensaje no tiene timestamp interno, hereda el del chat
                            'timestamp': msg.get('timestamp', chat_ts)
                        })
                    except Exception as msg_error:
                        logger.error(f"Error procesando mensaje individual: {str(msg_error)}")
                        continue
                
                # 3. Construir el objeto de conversación incluyendo el grafo visual
                conversations.append({
                    'timestamp': chat_ts,
                    'messages': cleaned_messages,
                    'analysis_type': chat.get('analysis_type'),
                    'visual_graph': chat.get('visual_graph'), # <--- IMPORTANTE: Recuperamos el grafo
                    'username': chat.get('username'),
                    'group_id': chat.get('group_id')
                })
                
            except Exception as e:
                logger.error(f"Error formateando documento de chat: {str(e)}")
                continue
                
        return conversations
        
    except Exception as e:
        logger.error(f"Error general al recuperar historial de chat: {str(e)}")
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