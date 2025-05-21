# /modules/database/chat_mongo_db.py
from .mongo_db import insert_document, find_documents, get_collection
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
COLLECTION_NAME = 'chat_history-v3'

def get_chat_history(username: str, analysis_type: str = 'sidebar', limit: int = None) -> list:
    """
    Recupera el historial del chat.
    
    Args:
        username: Nombre del usuario
        analysis_type: Tipo de análisis ('sidebar' por defecto)
        limit: Límite de conversaciones a recuperar
        
    Returns:
        list: Lista de conversaciones con formato
    """
    try:
        query = {
            "username": username,
            "analysis_type": analysis_type
        }
        
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección de chat")
            return []
            
        # Obtener y formatear conversaciones
        cursor = collection.find(query).sort("timestamp", -1)
        if limit:
            cursor = cursor.limit(limit)
            
        conversations = []
        for chat in cursor:
            try:
                formatted_chat = {
                    'timestamp': chat['timestamp'],
                    'messages': [
                        {
                            'role': msg.get('role', 'unknown'),
                            'content': msg.get('content', '')
                        }
                        for msg in chat.get('messages', [])
                    ]
                }
                conversations.append(formatted_chat)
            except Exception as e:
                logger.error(f"Error formateando chat: {str(e)}")
                continue
                
        return conversations
        
    except Exception as e:
        logger.error(f"Error al recuperar historial de chat: {str(e)}")
        return []

def store_chat_history(username: str, messages: list, analysis_type: str = 'sidebar') -> bool:
    """
    Guarda el historial del chat.
    
    Args:
        username: Nombre del usuario
        messages: Lista de mensajes a guardar
        analysis_type: Tipo de análisis
    
    Returns:
        bool: True si se guardó correctamente
    """
    try:
        collection = get_collection(COLLECTION_NAME)
        if collection is None:
            logger.error("No se pudo obtener la colección de chat")
            return False
            
        # Formatear mensajes antes de guardar
        formatted_messages = [
            {
                'role': msg.get('role', 'unknown'),
                'content': msg.get('content', ''),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            for msg in messages
        ]
        
        chat_document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'messages': formatted_messages,
            'analysis_type': analysis_type,
            'metadata': metadata or {}  # Nuevo campo 18-5-2025
        }
        
        result = collection.insert_one(chat_document)
        if result.inserted_id:
            logger.info(f"Historial de chat guardado con ID: {result.inserted_id} para el usuario: {username}")
            return True
            
        logger.error("No se pudo insertar el documento")
        return False
        
    except Exception as e:
        logger.error(f"Error al guardar historial de chat: {str(e)}")
        return False
        
        
        #def get_chat_history(username, analysis_type=None, limit=10):
#    query = {"username": username}
#    if analysis_type:
#        query["analysis_type"] = analysis_type

#    return find_documents(COLLECTION_NAME, query, sort=[("timestamp", -1)], limit=limit)

# Agregar funciones para actualizar y eliminar chat si es necesario