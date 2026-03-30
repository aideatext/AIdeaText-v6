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
def get_chat_history(username: str, analysis_type: str = 'sidebar', limit: int = None) -> list:
    """
    Recupera el historial del chat con codificación UTF-8 segura.
    """
    try:
        query = {
                    "username": username,
                    "$or": [
                        {"analysis_type": analysis_type},
                        {"analysis_type": {"$exists": False}},
                        {"analysis_type": None}
                    ]
                }
        
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección de chat")
            return []
            
        cursor = collection.find(query).sort("timestamp", -1)
        if limit:
            cursor = cursor.limit(limit)
            
        conversations = []
        for chat in cursor:
            try:
                # Limpiar y asegurar UTF-8 en cada mensaje
                cleaned_messages = []
                for msg in chat.get('messages', []):
                    try:
                        cleaned_messages.append({
                            'role': msg.get('role', 'unknown'),
                            'content': clean_text_content(msg.get('content', ''))
                        })
                    except Exception as msg_error:
                        logger.error(f"Error procesando mensaje: {str(msg_error)}")
                        continue
                
                conversations.append({
                    'timestamp': chat['timestamp'],
                    'messages': cleaned_messages
                })
                
            except Exception as e:
                logger.error(f"Error formateando chat: {str(e)}")
                continue
                
        return conversations
        
    except Exception as e:
        logger.error(f"Error al recuperar historial de chat: {str(e)}")
        return []

##############################################
def store_chat_history(username: str, messages: list, analysis_type: str = 'sidebar', metadata: dict = None) -> bool:
    """
    Guarda el historial del chat con codificación UTF-8 segura.
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección de chat")
            return False
            
        # Limpiar y formatear cada mensaje
        formatted_messages = []
        for msg in messages:
            try:
                formatted_messages.append({
                    'role': msg.get('role', 'unknown'),
                    'content': clean_text_content(msg.get('content', '')),
                    'timestamp': datetime.now(timezone.utc)
                })
            except Exception as msg_error:
                logger.error(f"Error procesando mensaje para almacenar: {str(msg_error)}")
                continue
        
        chat_document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc), # Mejor práctica
            'messages': formatted_messages,
            'analysis_type': analysis_type,
            'metadata': metadata or {}
        }
        
        # Verificación adicional de UTF-8 antes de insertar
        try:
            import json
            json.dumps(chat_document, ensure_ascii=False)
        except UnicodeEncodeError as e:
            logger.error(f"Error de codificación en documento: {str(e)}")
            return False
        
        result = collection.insert_one(chat_document)
        if result.inserted_id:
            logger.info(f"Chat guardado para {username} con ID: {result.inserted_id}")
            return True
            
        logger.error("No se pudo insertar el documento")
        return False
        
    except Exception as e:
        logger.error(f"Error al guardar historial: {str(e)}")
        return False