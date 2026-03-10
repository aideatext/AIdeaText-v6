# database.py
# database.py de la versión 3 al 26-9-2024
import streamlit as st
import logging
import os
import pandas as pd
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
from pymongo import MongoClient
import certifi
from datetime import datetime, timezone
from io import BytesIO
import base64
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import bcrypt
print(f"Bcrypt version: {bcrypt.__version__}")
import uuid
import plotly.graph_objects as go  # Para manejar el diagrama de Sankey
import numpy as np  # Puede ser necesario para algunas operaciones
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Variables globales para Cosmos DB SQL API
application_requests_container = None
cosmos_client = None
user_database = None
user_container = None
user_feedback_container = None

# Variables globales para Cosmos DB MongoDB API
mongo_client = None
mongo_db = None
analysis_collection = None
chat_collection = None  # Nueva variable global


##############################################################################--- INICIO DE LAS BASES DE DATOS --- ###############################
def initialize_database_connections():
    try:
        print("Iniciando conexión a MongoDB")
        mongodb_success = initialize_mongodb_connection()
        print(f"Conexión a MongoDB: {'exitosa' if mongodb_success else 'fallida'}")
    except Exception as e:
        print(f"Error al conectar con MongoDB: {str(e)}")
        mongodb_success = False

    try:
        print("Iniciando conexión a Cosmos DB SQL API")
        sql_success = initialize_cosmos_sql_connection()
        print(f"Conexión a Cosmos DB SQL API: {'exitosa' if sql_success else 'fallida'}")
    except Exception as e:
        print(f"Error al conectar con Cosmos DB SQL API: {str(e)}")
        sql_success = False

    return {
        "mongodb": mongodb_success,
        "cosmos_sql": sql_success
    }

#####################################################################################33
def initialize_cosmos_sql_connection():
    global cosmos_client, user_database, user_container, application_requests_container, user_feedback_container
    logger.info("Initializing Cosmos DB SQL API connection")
    try:
        cosmos_endpoint = os.environ.get("COSMOS_ENDPOINT")
        cosmos_key = os.environ.get("COSMOS_KEY")
        logger.info(f"Cosmos Endpoint: {cosmos_endpoint}")
        logger.info(f"Cosmos Key: {'*' * len(cosmos_key) if cosmos_key else 'Not set'}")

        if not cosmos_endpoint or not cosmos_key:
            logger.error("COSMOS_ENDPOINT or COSMOS_KEY environment variables are not set")
            raise ValueError("Las variables de entorno COSMOS_ENDPOINT y COSMOS_KEY deben estar configuradas")

        cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
        user_database = cosmos_client.get_database_client("user_database")
        user_container = user_database.get_container_client("users")
        application_requests_container = user_database.get_container_client("application_requests")
        user_feedback_container = user_database.get_container_client("user_feedback")

        logger.info(f"user_container initialized: {user_container is not None}")
        logger.info(f"application_requests_container initialized: {application_requests_container is not None}")
        logger.info(f"user_feedback_container initialized: {user_feedback_container is not None}")

        logger.info("Conexión a Cosmos DB SQL API exitosa")
        return True
    except Exception as e:
        logger.error(f"Error al conectar con Cosmos DB SQL API: {str(e)}", exc_info=True)
        return False

############################################################################################3
def initialize_mongodb_connection():
    global mongo_client, mongo_db, analysis_collection, chat_collection
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
        # export = mongo_db['export']
        analysis_collection = mongo_db['text_analysis']
        chat_collection = mongo_db['chat_history']  # Inicializar la nueva colección

        # Verificar la conexión
        mongo_client.admin.command('ping')

        logger.info("Conexión a Cosmos DB MongoDB API exitosa")
        return True
    except Exception as e:
        logger.error(f"Error al conectar con Cosmos DB MongoDB API: {str(e)}", exc_info=True)
        return False

##############################################################################--- FIN DEL INICIO DE LAS BASES DE DATOS  --- ################################################################################################################################
########################################################## -- INICIO DE GESTION DE USUARIOS ---##########################################################
def create_user(username, password, role):
    global user_container
    try:
        print(f"Attempting to create user: {username} with role: {role}")
        if user_container is None:
            print("Error: user_container is None. Attempting to reinitialize connection.")
            if not initialize_cosmos_sql_connection():
                raise Exception("Failed to initialize SQL connection")

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"Password hashed successfully for user: {username}")
        user_data = {
            'id': username,
            'password': hashed_password,
            'role': role,
            'timestamp':datetime.now(timezone.utc).isoformat(),
        }
        user_container.create_item(body=user_data)
        print(f"Usuario {role} creado: {username}")  # Log para depuración
        return True
    except Exception as e:
        print(f"Detailed error in create_user: {str(e)}")
        return False

#######################################################################################################
def create_admin_user(username, password):
    return create_user(username, password, 'Administrador')

#######################################################################################################
def create_student_user(username, password):
    return create_user(username, password, 'Estudiante')

#######################################################################################################
# Funciones para Cosmos DB SQL API (manejo de usuarios)
def get_user(username):
    try:
        query = f"SELECT * FROM c WHERE c.id = '{username}'"
        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        user = items[0] if items else None
        if user:
            print(f"Usuario encontrado: {username}, Rol: {user.get('role')}")  # Log añadido
        else:
            print(f"Usuario no encontrado: {username}")  # Log añadido
        return user
    except Exception as e:
        print(f"Error al obtener usuario {username}: {str(e)}")
        return None

########################################################## -- FIN DE GESTION DE USUARIOS ---##########################################################

########################################################## -- INICIO GESTION DE ARCHIVOS ---##########################################################

def manage_file_contents(username, file_name, analysis_type, file_contents=None):
    if user_container is None:
        logger.error("La conexión a Cosmos DB SQL API no está inicializada")
        return None

    item_id = f"{analysis_type}_{file_name}"

    try:
        if file_contents is not None:
            # Storing or updating file
            document = {
                'id': item_id,
                'username': username,
                'file_name': file_name,
                'analysis_type': analysis_type,
                'file_contents': file_contents,
                'timestamp': datetime.now(timezone.utc),.isoformat()
            }
            user_container.upsert_item(body=document, partition_key=username)
            logger.info(f"Contenido del archivo guardado/actualizado para el usuario: {username}, tipo de análisis: {analysis_type}")
            return True
        else:
            # Retrieving file
            item = user_container.read_item(item=item_id, partition_key=username)
            return item['file_contents']
    except CosmosHttpResponseError as e:
        if e.status_code == 404:
            logger.info(f"No se encontró el archivo para el usuario: {username}, tipo de análisis: {analysis_type}")
            return None
        else:
            logger.error(f"Error de Cosmos DB al manejar el archivo para el usuario {username}: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error al manejar el archivo para el usuario {username}: {str(e)}")
        return None


def get_user_files(username, analysis_type=None):
    if user_container is None:
        logger.error("La conexión a Cosmos DB SQL API no está inicializada")
        return []
    try:
        if analysis_type:
            query = f"SELECT c.file_name, c.analysis_type, c.timestamp FROM c WHERE c.username = '{username}' AND c.analysis_type = '{analysis_type}'"
        else:
            query = f"SELECT c.file_name, c.analysis_type, c.timestamp FROM c WHERE c.username = '{username}'"

        items = list(user_container.query_items(query=query, enable_cross_partition_query=True))
        return items
    except Exception as e:
        logger.error(f"Error al obtener la lista de archivos del usuario {username}: {str(e)}")
        return []



def delete_file(username, file_name, analysis_type):
    if user_container is None:
        logger.error("La conexión a Cosmos DB SQL API no está inicializada")
        return False

    try:
        item_id = f"{analysis_type}_{file_name}"
        user_container.delete_item(item=item_id, partition_key=username)
        logger.info(f"Archivo eliminado para el usuario: {username}, tipo de análisis: {analysis_type}, nombre: {file_name}")
        return True

        if success:
            # Invalidar caché
            cache_key = f"student_data_{username}"
            if cache_key in st.session_state:
                del st.session_state[cache_key]



    except CosmosHttpResponseError as e:
        logger.error(f"Cosmos DB error al eliminar el archivo para el usuario {username}: {str(e)}")
        return False

    except Exception as e:
        logger.error(f"Error al eliminar el archivo para el usuario {username}: {str(e)}")
        return False

########################################################## -- FIN GESTION DE ARCHIVOS ---##########################################################

########################################################## -- INICIO GESTION DE FORMULARIOS ---##########################################################
def store_application_request(name, email, institution, role, reason):
    global application_requests_container
    logger.info("Entering store_application_request function")
    try:
        logger.info("Checking application_requests_container")
        if application_requests_container is None:
            logger.error("application_requests_container is not initialized")
            return False

        logger.info("Creating application request document")
        application_request = {
            "id": str(uuid.uuid4()),
            "name": name,
            "email": email,
            "institution": institution,
            "role": role,
            "reason": reason,
            "requestDate": datetime.utcnow().isoformat()
        }

        logger.info(f"Attempting to store document: {application_request}")
        application_requests_container.create_item(body=application_request)
        logger.info(f"Application request stored for email: {email}")
        return True
    except Exception as e:
        logger.error(f"Error storing application request: {str(e)}")
        return False

#######################################################################################################
def store_user_feedback(username, name, email, feedback):
    global user_feedback_container
    logger.info(f"Attempting to store user feedback for user: {username}")
    try:
        if user_feedback_container is None:
            logger.error("user_feedback_container is not initialized")
            return False

        feedback_item = {
            "id": str(uuid.uuid4()),
            "username": username,
            "name": name,
            "email": email,
            "feedback": feedback,
            'timestamp':datetime.now(timezone.utc).isoformat(),
        }

        result = user_feedback_container.create_item(body=feedback_item)
        logger.info(f"User feedback stored with ID: {result['id']} for user: {username}")
        return True
    except Exception as e:
        logger.error(f"Error storing user feedback for user {username}: {str(e)}")
        return False

########################################################## -- FIN GESTION DE FORMULARIOS ---##########################################################

########################################################## -- INICIO ALMACENAMIENTO ANÁLISIS MORFOSINTÁCTICO ---##########################################################

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
            'timestamp':datetime.now(timezone.utc).isoformat(),
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
        logger.info(f"Análisis guardado con ID: {result.inserted_id} para el usuario: {username}")
        return True
    except Exception as e:
        logger.error(f"Error al guardar el análisis para el usuario {username}: {str(e)}")
        return False


################################################-- INICIO DE LA SECCIÓN DEL CHATBOT --- ###############################################################
def store_chat_history(username, messages):
    try:
        logger.info(f"Attempting to save chat history for user: {username}")
        logger.debug(f"Messages to save: {messages}")

        chat_document = {
            'username': username,
            'timestamp':datetime.now(timezone.utc).isoformat(),
            'messages': messages
        }
        result = chat_collection.insert_one(chat_document)
        logger.info(f"Chat history saved with ID: {result.inserted_id} for user: {username}")
        logger.debug(f"Chat content: {messages}")
        return True
    except Exception as e:
        logger.error(f"Error saving chat history for user {username}: {str(e)}")
        return False

#######################################################################################################
def export_analysis_and_chat(username, analysis_data, chat_data):
    try:
        export_data = {
            "username": username,
            'timestamp':datetime.now(timezone.utc).isoformat(),
            "analysis": analysis_data,
            "chat": chat_data
        }

        # Aquí puedes decidir cómo quieres exportar los datos
        # Por ejemplo, podrías guardarlos en una nueva colección en MongoDB
        export_collection = mongo_db['exports']
        result = export_collection.insert_one(export_data)

        # También podrías generar un archivo JSON o CSV y guardarlo en Azure Blob Storage

        return True
    except Exception as e:
        logger.error(f"Error al exportar análisis y chat para {username}: {str(e)}")
        return False

################################################-- FIN DE LA SECCIÓN DEL CHATBOT --- ###############################################################
########--- STUDENT DATA -------

def get_student_data(username):
    if analysis_collection is None or chat_collection is None:
        logger.error("La conexión a MongoDB no está inicializada")
        return None
    formatted_data = {
        "username": username,
        "entries": [],
        "entries_count": 0,
        "word_count": {},
        "semantic_analyses": [],
        "discourse_analyses": [],
        "chat_history": []
    }
    try:
        logger.info(f"Buscando datos de análisis para el usuario: {username}")
        cursor = analysis_collection.find({"username": username})

        for entry in cursor:
            formatted_entry = {
                'timestamp':datetime.now(timezone.utc).isoformat(),
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

            elif formatted_entry["analysis_type"] == "semantic":
                formatted_entry.update({
                    "key_concepts": entry.get("key_concepts", []),
                    "graph": entry.get("graph", "")
                })
                formatted_data["semantic_analyses"].append(formatted_entry)

            elif formatted_entry["analysis_type"] == "discourse":
                formatted_entry.update({
                    "text1": entry.get("text1", ""),
                    "text2": entry.get("text2", ""),
                    "key_concepts1": entry.get("key_concepts1", []),
                    "key_concepts2": entry.get("key_concepts2", []),
                    "graph1": entry.get("graph1", ""),
                    "graph2": entry.get("graph2", ""),
                    "combined_graph": entry.get("combined_graph", "")
                })
                formatted_data["discourse_analyses"].append(formatted_entry)

            formatted_data["entries"].append(formatted_entry)

        formatted_data["entries_count"] = len(formatted_data["entries"])
        formatted_data["entries"].sort(key=lambda x: x["timestamp"], reverse=True)

        for entry in formatted_data["entries"]:
            entry["timestamp"] = entry["timestamp"].isoformat()

    except Exception as e:
        logger.error(f"Error al obtener datos de análisis del estudiante {username}: {str(e)}")

    try:
        logger.info(f"Buscando historial de chat para el usuario: {username}")
        chat_cursor = chat_collection.find({"username": username})
        for chat in chat_cursor:
            formatted_chat = {
                "timestamp": chat["timestamp"].isoformat(),
                "messages": chat["messages"]
            }
            formatted_data["chat_history"].append(formatted_chat)

        formatted_data["chat_history"].sort(key=lambda x: x["timestamp"], reverse=True)

    except Exception as e:
        logger.error(f"Error al obtener historial de chat del estudiante {username}: {str(e)}")
    logger.info(f"Datos formateados para {username}: {formatted_data}")
    return formatted_data
