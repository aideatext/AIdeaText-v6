from modules.database.mongo_db import get_collection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def nuke_and_verify():
    # 1. Lista de colecciones a limpiar
    collections_to_clear = [
        'student_semantic_analysis', 
        'student_semantic_live_analysis', 
        'chat_history-v3'
    ]
    
    for coll_name in collections_to_clear:
        collection = get_collection(coll_name)
        if collection is not None:
            # Borrar todo
            stats = collection.delete_many({})
            logger.info(f"🗑️ Colección '{coll_name}': {stats.deleted_count} registros borrados.")
            
            # Verificar vaciado
            count = collection.count_documents({})
            if count == 0:
                logger.info(f"✅ Confirmado: '{coll_name}' está limpia.")
            else:
                logger.error(f"❌ Error: '{coll_name}' aún tiene {count} documentos.")

if __name__ == "__main__":
    nuke_and_verify()
