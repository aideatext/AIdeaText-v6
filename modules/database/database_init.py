import os
import pg8000.native
from pymongo import MongoClient
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def get_mongodb():
    try:
        uri = os.getenv("MONGO_URI")
        ca_path = "/home/ec2-user/app/global-bundle.pem"
        client = MongoClient(uri, tlsCAFile=ca_path if os.path.exists(ca_path) else None)
        return client[os.getenv("MONGO_DB_NAME", "aideatext")]
    except Exception as e:
        logger.error(f"Error DocumentDB: {e}")
        return None

def get_pg_connection():
    try:
        # Leemos las variables del .env
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        host = os.getenv("DB_HOST")
        database = os.getenv("DB_DATABASE")

        if not user or not password:
            logger.error("❌ Credenciales RDS incompletas en .env")
            return None

        # Conexión nativa de pg8000
        conn = pg8000.native.Connection(
            user=user,
            password=password,
            host=host,
            port=5432,
            database=database,
            timeout=15
        )
        return conn
    except Exception as e:
        logger.error(f"❌ Error de autenticación RDS: {e}")
        return None

def release_pg_connection(conn):
    if conn:
        try:
            conn.close()
        except:
            pass

def initialize_database_connections():
    mongo_ok = get_mongodb() is not None
    pg_ok = get_pg_connection() is not None
    return mongo_ok and pg_ok

def get_container(name):
    # En Postgres, "container" es una tabla. 
    # Esta función se mantiene para compatibilidad de nombres.
    return name 
