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

def run_migration():
    print("🚀 Iniciando Migración Maestra de Coherencia Dialógica...")

    # 1. PARTE SQL: Normalizar class_id en la tabla de usuarios
    print("📦 Paso 1: Actualizando SQL (users)...")
    try:
        # Buscamos alumnos con el ID de 5 partes
        sql_users = execute_query("SELECT id FROM users WHERE role = 'Estudiante' AND id LIKE '%-%-%-%-%'")
        for u in sql_users:
            full_id = u['id']
            group_id = "-".join(full_id.split('-')[0:4]) # MG-G1-2025-1
            execute_query("UPDATE users SET class_id = %s WHERE id = %s", (group_id, full_id))
        print("✅ SQL actualizado.")
    except Exception as e:
        print(f"❌ Error en SQL: {e}")

    # 2. PARTE MONGODB: Las 4 Cubetas
    print("📦 Paso 2: Sincronizando las 4 cubetas en MongoDB...")
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client[DB_NAME]
        
        cubetas = [
            'student_semantic_live_analysis',
            'student_semantic_analysis',
            'student_discourse_analysis',
            'chat_history-v3'
        ]

        for nombre_col in cubetas:
            col = db[nombre_col]
            # Buscamos documentos que no tengan group_id o tengan el formato viejo
            cursor = col.find({})
            updated_count = 0
            
            for doc in cursor:
                updates = {}
                username = doc.get('username', '')
                parts = username.split('-')

                # A. Normalizar group_id a 4 partes (MG-G1-2025-1)
                if len(parts) >= 5:
                    new_group_id = "-".join(parts[0:4])
                    if doc.get('group_id') != new_group_id:
                        updates['group_id'] = new_group_id

                # B. Limpiar imágenes (Solo en colecciones semánticas)
                if 'analysis_result' in doc or 'concept_graph' in doc:
                    # Caso 1: Imagen en analysis_result.graph_image
                    res = doc.get('analysis_result', {})
                    img = res.get('graph_image') if isinstance(res, dict) else None
                    if isinstance(img, str) and "base64," in img:
                        updates['analysis_result.graph_image'] = img.split("base64,")[1]
                    
                    # Caso 2: Imagen directa en concept_graph
                    cg = doc.get('concept_graph')
                    if isinstance(cg, str) and "base64," in cg:
                        updates['concept_graph'] = cg.split("base64,")[1]

                if updates:
                    col.update_one({'_id': doc['_id']}, {'$set': updates})
                    updated_count += 1
            
            print(f"  - {nombre_col}: {updated_count} documentos normalizados.")

    except Exception as e:
        print(f"❌ Error en MongoDB: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_migration()
