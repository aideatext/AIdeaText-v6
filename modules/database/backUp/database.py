# database.py
# Versión 3 actualizada para manejar chat_history_v3

import streamlit as st
import logging
import os
from pymongo import MongoClient
import certifi
from datetime import datetime, timezone
import uuid

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Variables globales para Cosmos DB MongoDB API
mongo_client = None
mongo_db = None
analysis_collection = None
chat_collection_v3 = None  # Nueva variable global para chat_history_v3

def initialize_mongodb_connection():
    global mongo_client, mongo_db, analysis_collection, chat_collection_v3
    try:
        cosmos_mongodb_connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        if not cosmos_mongodb_connection_string:
            logger.error("La variable de entorno MONGODB_CONNECTION_STRING no está configurada")
            return False

        mongo_client = MongoClient(cosmos_mongodb_connection_string,
                                   tls=True,
                                   tlsCAFile=certifi.where(),
                                   retryWrites=False,
                                   serverSelectionTimeoutMS=5000,
                                   connectTimeoutMS=10000,
                                   socketTimeoutMS=10000)

        mongo_client.admin.command('ping')

        mongo_db = mongo_client['aideatext_db']
        analysis_collection = mongo_db['text_analysis']
        chat_collection_v3 = mongo_db['chat_history_v3']  # Inicializar la nueva colección

        # Crear índices para chat_history_v3
        chat_collection_v3.create_index([("username", 1), ("timestamp", -1)])
        chat_collection_v3.create_index([("username", 1), ("analysis_type", 1), ("timestamp", -1)])

        logger.info("Conexión a Cosmos DB MongoDB API exitosa")
        return True
    except Exception as e:
        logger.error(f"Error al conectar con Cosmos DB MongoDB API: {str(e)}", exc_info=True)
        return False

def store_chat_history_v3(username, messages, analysis_type):
    try:
        logger.info(f"Guardando historial de chat para el usuario: {username}, tipo de análisis: {analysis_type}")
        logger.debug(f"Mensajes a guardar: {messages}")

        chat_document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc), # Mejor práctica
            'analysis_type': analysis_type,
            'messages': messages
        }
        result = chat_collection_v3.insert_one(chat_document)
        logger.info(f"Historial de chat guardado con ID: {result.inserted_id} para el usuario: {username}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar el historial de chat para el usuario {username}: {str(e)}")
        return False

def get_chat_history_v3(username, analysis_type=None, limit=10):
    try:
        logger.info(f"Obteniendo historial de chat para el usuario: {username}, tipo de análisis: {analysis_type}")

        query = {"username": username}
        if analysis_type:
            query["analysis_type"] = analysis_type

        cursor = chat_collection_v3.find(query).sort("timestamp", -1).limit(limit)

        chat_history = []
        for chat in cursor:
            chat_history.append({
                "timestamp": chat["timestamp"],
                "analysis_type": chat["analysis_type"],
                "messages": chat["messages"]
            })

        logger.info(f"Se obtuvieron {len(chat_history)} entradas de chat para el usuario: {username}")
        return chat_history
    except Exception as e:
        logger.error(f"Error al obtener el historial de chat para el usuario {username}: {str(e)}")
        return []

def delete_chat_history_v3(username, analysis_type=None):
    try:
        logger.info(f"Eliminando historial de chat para el usuario: {username}, tipo de análisis: {analysis_type}")

        query = {"username": username}
        if analysis_type:
            query["analysis_type"] = analysis_type

        result = chat_collection_v3.delete_many(query)

        logger.info(f"Se eliminaron {result.deleted_count} entradas de chat para el usuario: {username}")
        return True
    except Exception as e:
        logger.error(f"Error al eliminar el historial de chat para el usuario {username}: {str(e)}")
        return False

def export_chat_history_v3(username, analysis_type=None):
    try:
        logger.info(f"Exportando historial de chat para el usuario: {username}, tipo de análisis: {analysis_type}")

        query = {"username": username}
        if analysis_type:
            query["analysis_type"] = analysis_type

        cursor = chat_collection_v3.find(query).sort("timestamp", -1)

        export_data = list(cursor)

        logger.info(f"Se exportaron {len(export_data)} entradas de chat para el usuario: {username}")
        return export_data
    except Exception as e:
        logger.error(f"Error al exportar el historial de chat para el usuario {username}: {str(e)}")
        return []

# Funciones específicas para cada tipo de análisis

def store_morphosyntax_result(username, text, repeated_words, arc_diagrams, pos_analysis, morphological_analysis, sentence_structure):
    if analysis_collection is None:
        logger.error("La conexión a MongoDB no está inicializada")
        return False

    try:
        word_count = {}
        for word, color in repeated_words.items():
            category = color  # Asumiendo que 'color' es la categoría gramatical
            word_count[category] = word_count.get(category, 0) + 1

        analysis_document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc), # Mejor práctica
            'text': text,
            'repeated_words': repeated_words,
            'word_count': word_count,
            'arc_diagrams': arc_diagrams,
            'pos_analysis': pos_analysis,
            'morphological_analysis': morphological_analysis,
            'sentence_structure': sentence_structure,
            'analysis_type': 'morphosyntax'
        }

        result = analysis_collection.insert_one(analysis_document)
        logger.info(f"Análisis morfosintáctico guardado con ID: {result.inserted_id} para el usuario: {username}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar el análisis morfosintáctico para el usuario {username}: {str(e)}")
        return False

# Aquí puedes agregar funciones similares para análisis semántico y de discurso

def get_student_data(username):
    if analysis_collection is None or chat_collection_v3 is None:
        logger.error("La conexión a MongoDB no está inicializada")
        return None

    formatted_data = {
        "username": username,
        "entries": [],
        "entries_count": 0,
        "word_count": {},
        "chat_history": {
            "morphosyntax": [],
            "semantic": [],
            "discourse": []
        }
    }

    try:
        logger.info(f"Buscando datos de análisis para el usuario: {username}")
        cursor = analysis_collection.find({"username": username})

        for entry in cursor:
            formatted_entry = {
                'timestamp': entry.get("timestamp"),
                "analysis_type": entry.get("analysis_type", "morphosyntax")
            }

            if formatted_entry["analysis_type"] == "morphosyntax":
                formatted_entry.update({
                    "text": entry.get("text", ""),
                    "word_count": entry.get("word_count", {}),
                    "arc_diagrams": entry.get("arc_diagrams", [])
                })
                for category, count in formatted_entry["word_count"].items():
                    formatted_data["word_count"][category] = formatted_data["word_count"].get(category, 0) + count

            formatted_data["entries"].append(formatted_entry)

        formatted_data["entries_count"] = len(formatted_data["entries"])
        formatted_data["entries"].sort(key=lambda x: x["timestamp"], reverse=True)

        # Obtener historial de chat para cada tipo de análisis
        for analysis_type in ["morphosyntax", "semantic", "discourse"]:
            chat_history = get_chat_history_v3(username, analysis_type)
            formatted_data["chat_history"][analysis_type] = chat_history

    except Exception as e:
        logger.error(f"Error al obtener datos del estudiante {username}: {str(e)}")

    logger.info(f"Datos formateados para {username}: {formatted_data}")
    return formatted_data

# Puedes agregar más funciones según sea necesario para manejar otros tipos de datos o análisis