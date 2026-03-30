# 1. modules/database/database_init.py

import os
import logging
from azure.cosmos import CosmosClient
from pymongo import MongoClient
import certifi

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Variables globales para Cosmos DB SQL API
cosmos_client = None
user_database = None
user_container = None
application_requests_container = None
user_feedback_container = None
user_sessions_container = None

# Variables globales para Cosmos DB MongoDB API
mongo_client = None
mongo_db = None

###################################################################
def verify_container_partition_key(container, expected_path):
    """Verifica la configuración de partition key de un contenedor"""
    try:
        container_props = container.read()
        partition_key_paths = container_props['partitionKey']['paths']
        logger.info(f"Container: {container.id}, Partition Key Paths: {partition_key_paths}")
        return expected_path in partition_key_paths
    except Exception as e:
        logger.error(f"Error verificando partition key en {container.id}: {str(e)}")
        return False

###################################################################
def get_container(container_name):
    """Obtiene un contenedor específico"""
    logger.info(f"Solicitando contenedor: {container_name}")
    
    if not initialize_cosmos_sql_connection():
        logger.error("No se pudo inicializar la conexión")
        return None
    
    # Verificar estado de los contenedores
    containers_status = {
        "users": user_container is not None,
        "users_sessions": user_sessions_container is not None,
        "application_requests": application_requests_container is not None,
        "user_feedback": user_feedback_container is not None  # Añadido
    }
    
    logger.info(f"Estado actual de los contenedores: {containers_status}")
    
    # Mapear nombres a contenedores
    containers = {
        "users": user_container,
        "users_sessions": user_sessions_container,
        "application_requests": application_requests_container,
        "user_feedback": user_feedback_container  # Añadido
    }
    
    container = containers.get(container_name)
    
    if container is None:
        logger.error(f"Contenedor '{container_name}' no encontrado o no inicializado")
        logger.error(f"Contenedores disponibles: {[k for k, v in containers_status.items() if v]}")
        return None
        
    logger.info(f"Contenedor '{container_name}' obtenido exitosamente")
    return container
###################################################################

def initialize_cosmos_sql_connection():
    """Inicializa la conexión a Cosmos DB SQL API"""
    global cosmos_client, user_database, user_container, user_sessions_container, application_requests_container, user_feedback_container  # Añadida aquí user_feedback_container

    try:
        # Verificar conexión existente
        if all([
            cosmos_client,
            user_database, 
            user_container,
            user_sessions_container,
            application_requests_container,
            user_feedback_container
        ]):
            logger.debug("Todas las conexiones ya están inicializadas")
            return True

        # Obtener credenciales
        cosmos_endpoint = os.environ.get("COSMOS_ENDPOINT")
        cosmos_key = os.environ.get("COSMOS_KEY")
        
        if not cosmos_endpoint or not cosmos_key:
            raise ValueError("COSMOS_ENDPOINT y COSMOS_KEY deben estar configurados")

        # Inicializar cliente y base de datos
        cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
        user_database = cosmos_client.get_database_client("user_database")
        
        # Inicializar contenedores
        try:
            user_container = user_database.get_container_client("users")
            logger.info("Contenedor 'users' inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando contenedor 'users': {str(e)}")
            user_container = None

        try:
            user_sessions_container = user_database.get_container_client("users_sessions")
            logger.info("Contenedor 'users_sessions' inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando contenedor 'users_sessions': {str(e)}")
            user_sessions_container = None

        try:
            application_requests_container = user_database.get_container_client("application_requests")
            logger.info("Contenedor 'application_requests' inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando contenedor 'application_requests': {str(e)}")
            application_requests_container = None

        try:
            user_feedback_container = user_database.get_container_client("user_feedback")
            logger.info("Contenedor 'user_feedback' inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando contenedor 'user_feedback': {str(e)}")
            user_feedback_container = None

        # Verificar el estado de los contenedores
        containers_status = {
            'users': user_container is not None,
            'users_sessions': user_sessions_container is not None,
            'application_requests': application_requests_container is not None,
            'user_feedback': user_feedback_container is not None
        }
        
        logger.info(f"Estado de los contenedores: {containers_status}")
        
        if all(containers_status.values()):
            logger.info("Todos los contenedores inicializados correctamente")
            return True
        else:
            logger.error("No se pudieron inicializar todos los contenedores")
            return False

    except Exception as e:
        logger.error(f"Error al conectar con Cosmos DB SQL API: {str(e)}")
        return False


###################################################################
def initialize_mongodb_connection():
    """Inicializa la conexión a MongoDB"""
    global mongo_client, mongo_db
    try:
        connection_string = os.getenv("MONGODB_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("MONGODB_CONNECTION_STRING debe estar configurado")

        mongo_client = MongoClient(
            connection_string,
            tls=True,
            tlsCAFile=certifi.where(),
            retryWrites=False,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        
        mongo_db = mongo_client['aideatext_db']
        return True
    except Exception as e:
        logger.error(f"Error conectando a MongoDB: {str(e)}")
        return False

###################################################################
def initialize_database_connections():
    """Inicializa todas las conexiones"""
    return initialize_cosmos_sql_connection() and initialize_mongodb_connection()

###################################################################
def get_mongodb():
    """Obtiene la conexión MongoDB"""
    if mongo_db is None:
        initialize_mongodb_connection()
    return mongo_db