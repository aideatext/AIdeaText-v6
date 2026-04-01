# Crea este archivo: init_collections.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

def init_db():
    uri = os.getenv("MONGO_URI")
    ca_path = "/home/ec2-user/app/global-bundle.pem"
    client = MongoClient(uri, tlsCAFile=ca_path)
    db = client[os.getenv("MONGO_DB_NAME", "aideatext")]
    
    # Definimos las colecciones que necesitamos
    collections_to_init = [
        'chat_history-v3',
        'student_semantic_analysis',
        'student_semantic_live_analysis',
        'student_discourse_analysis'
    ]
    
    print("--- Inicializando Colecciones para Trabajo en Equipo ---")
    for col_name in collections_to_init:
        col = db[col_name]
        # Insertamos un documento de control (luego lo podemos borrar o ignorar)
        init_doc = {
            'system_init': True,
            'description': f'Colección inicializada para {col_name}',
            'timestamp': datetime.now(timezone.utc),
            'version': '3.0-team'
        }
        col.insert_one(init_doc)
        print(f"✅ Colección '{col_name}' lista.")

if __name__ == "__main__":
    init_db()
