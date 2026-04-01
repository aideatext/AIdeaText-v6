import pymongo
import logging
from modules.database.sql_db import execute_query

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN DE CONEXIÓN (IMPORTANTE) ---
# Asegúrate de haber descargado el certificado: 
# wget https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem
USER = "adminunifedocdb"
PASS = "yhnBGT-62xz"
ENDPOINT = "aideatext-documentdb-cluster.cluster-c1sowo2islad.us-east-2.docdb.amazonaws.com"
DB_NAME = "aideatext"

MONGO_URI = f"mongodb://{USER}:{PASS}@{ENDPOINT}:27017/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"

# Borrar lo que tiene el ID viejo/incorrecto
def delete_incorrect_data():
    try:
        # 1. Conectar al cliente
        client = pymongo.MongoClient(MONGO_URI)
        
        # 2. DEFINIR EL OBJETO DB (Esto es lo que faltaba)
        db = client[DB_NAME]
        
        # ID que queremos borrar porque se cargó mal
        OLD_GROUP_ID = "MG-EDU-UNIFE-LIM"
        
        # Listado de colecciones a limpiar
        collections = [
            'student_semantic_analysis',
            'student_semantic_live_analysis',
            'chat_history-v3'
        ]
        
        print(f"🗑️  Iniciando limpieza del grupo incorrecto: {OLD_GROUP_ID}")
        
        for col_name in collections:
            col = db[col_name]
            
            # En el caso de chat_history-v3, el filtro podría ser diferente si no usa group_id, 
            # pero basándonos en tu carga, buscaremos por username o group_id
            result = col.delete_many({"group_id": OLD_GROUP_ID})
            
            print(f"  - {col_name}: Se eliminaron {result.deleted_count} documentos.")

        client.close()
        print("✅ Limpieza terminada con éxito.")

    except Exception as e:
        print(f"❌ Error durante la eliminación: {e}")

if __name__ == "__main__":
    delete_incorrect_data()
