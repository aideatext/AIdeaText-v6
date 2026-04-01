import pymongo
from modules.database.sql_db import execute_query
# Asumiendo que tienes tu URI de DocumentDB en variables de entorno o config
MONGO_URI = "aideatext-documentdb-cluster.cluster-c1sowo2islad.us-east-2.docdb.amazonaws.com" 

def migrate_to_5_parts_standard():
    print("🚀 Iniciando migración al estándar de 5 partes (MG-G1-2025-1-t1)...")

    # 1. ACTUALIZACIÓN EN SQL
    # Buscamos alumnos cuyo ID tenga el formato de 5 partes
    query_get_users = "SELECT id FROM users WHERE role = 'Estudiante' AND id LIKE '%-%-%-%-%'"
    users = execute_query(query_get_users)

    if users:
        print(f"📦 Procesando {len(users)} usuarios en SQL...")
        for user in users:
            full_id = user['id']
            parts = full_id.split('-')
            # El ID del grupo son las primeras 4 partes: MG-G1-2025-1
            group_id = "-".join(parts[0:4])
            
            update_sql = "UPDATE users SET class_id = %s WHERE id = %s"
            execute_query(update_sql, (group_id, full_id))
        print("✅ SQL actualizado: class_id ahora contiene el ID del Grupo.")

    # 2. ACTUALIZACIÓN EN MONGODB
    try:
        client = pymongo.MongoClient(MONGO_URI)
        db = client['tu_base_de_datos']
        collection = db['semantic']

        # Buscamos todos los registros
        cursor = collection.find({})
        updated_count = 0

        for doc in cursor:
            username = doc.get('username', '')
            parts = username.split('-')
            
            if len(parts) >= 5:
                new_group_id = "-".join(parts[0:4])
                collection.update_one(
                    {'_id': doc['_id']},
                    {'$set': {'group_id': new_group_id}}
                )
                updated_count += 1

        print(f"✅ MongoDB actualizado: {updated_count} registros normalizados.")

    except Exception as e:
        print(f"❌ Error en MongoDB: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    migrate_to_5_parts_standard()
