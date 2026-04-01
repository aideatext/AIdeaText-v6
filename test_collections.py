import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def verify_docdb():
    try:
        uri = os.getenv("MONGO_URI")
        # Usamos la ruta que ya tienes definida en database_init.py
        ca_path = "/home/ec2-user/app/global-bundle.pem"
        
        print("--- Intentando conectar a DocumentDB ---")
        client = MongoClient(uri, tlsCAFile=ca_path)
        db = client[os.getenv("MONGO_DB_NAME", "aideatext")]
        
        # Intentar listar colecciones
        collections = db.list_collection_names()
        
        print(f"✅ Conexión exitosa a la base de datos: {db.name}")
        print("\nColecciones encontradas:")
        for col in collections:
            count = db[col].count_documents({})
            print(f" - {col} ({count} documentos)")
            
        if not collections:
            print("⚠️ Conectado, pero no se encontraron colecciones (o están vacías).")
            
    except Exception as e:
        print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    verify_docdb()
