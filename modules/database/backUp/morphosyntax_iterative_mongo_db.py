# modules/database/morphosyntax_iterative_mongo_db.py


from datetime import datetime, timezone
import logging
from bson import ObjectId  # <--- Importar ObjectId
from ..mongo_db import get_collection, insert_document, find_documents, update_document, delete_document

logger = logging.getLogger(__name__)

BASE_COLLECTION = 'student_morphosyntax_analysis_base'
ITERATION_COLLECTION = 'student_morphosyntax_iterations'

def store_student_morphosyntax_base(username, text, arc_diagrams):
    """Almacena el análisis morfosintáctico base y retorna su ObjectId."""
    try:
        base_document = {
            'username': username,
            'timestamp': datetime.now(timezone.utc), # Mejor práctica
            'text': text,
            'arc_diagrams': arc_diagrams,
            'analysis_type': 'morphosyntax_base',
            'has_iterations': False
        }
        collection = get_collection(BASE_COLLECTION)
        result = collection.insert_one(base_document)

        logger.info(f"Análisis base guardado para {username}")
        # Retornamos el ObjectId directamente (NO str)
        return result.inserted_id

    except Exception as e:
        logger.error(f"Error almacenando análisis base: {str(e)}")
        return None

def store_student_morphosyntax_iteration(username, base_id, original_text, iteration_text, arc_diagrams):
    """
    Almacena una iteración de análisis morfosintáctico.
    base_id: ObjectId de la base (o string convertible a ObjectId).
    """
    try:
        # Convertir a ObjectId si viene como string
        if isinstance(base_id, str):
            base_id = ObjectId(base_id)

        iteration_document = {
            'username': username,
            'base_id': base_id,  # Guardar el ObjectId en la iteración
            'timestamp': datetime.now(timezone.utc), # Mejor práctica
            'original_text': original_text,
            'iteration_text': iteration_text,
            'arc_diagrams': arc_diagrams,
            'analysis_type': 'morphosyntax_iteration'
        }
        collection = get_collection(ITERATION_COLLECTION)
        result = collection.insert_one(iteration_document)

        # Actualizar documento base (usando ObjectId)
        base_collection = get_collection(BASE_COLLECTION)
        base_collection.update_one(
            {'_id': base_id, 'username': username},
            {'$set': {'has_iterations': True}}
        )

        logger.info(f"Iteración guardada para {username}, base_id: {base_id}")
        return result.inserted_id  # Retornar el ObjectId de la iteración

    except Exception as e:
        logger.error(f"Error almacenando iteración: {str(e)}")
        return None

def get_student_morphosyntax_analysis(username, limit=10):
    """
    Obtiene los análisis base y sus iteraciones.
    Returns: Lista de análisis con sus iteraciones.
    """
    try:
        base_collection = get_collection(BASE_COLLECTION)
        base_query = {
            "username": username,
            "analysis_type": "morphosyntax_base"
        }
        base_analyses = list(
            base_collection.find(base_query).sort("timestamp", -1).limit(limit)
        )

        # Para cada análisis base, obtener sus iteraciones
        iteration_collection = get_collection(ITERATION_COLLECTION)
        for analysis in base_analyses:
            base_id = analysis['_id']
            # Buscar iteraciones con base_id = ObjectId
            iterations = list(
                iteration_collection.find({"base_id": base_id}).sort("timestamp", -1)
            )
            analysis['iterations'] = iterations

        return base_analyses

    except Exception as e:
        logger.error(f"Error obteniendo análisis: {str(e)}")
        return []

def update_student_morphosyntax_analysis(analysis_id, is_base, update_data):
    """
    Actualiza un análisis base o iteración.
    analysis_id puede ser un ObjectId o string.
    """
    from bson import ObjectId

    try:
        collection_name = BASE_COLLECTION if is_base else ITERATION_COLLECTION
        collection = get_collection(collection_name)

        if isinstance(analysis_id, str):
            analysis_id = ObjectId(analysis_id)

        query = {"_id": analysis_id}
        update = {"$set": update_data}

        result = update_document(collection_name, query, update)
        return result

    except Exception as e:
        logger.error(f"Error actualizando análisis: {str(e)}")
        return False

def delete_student_morphosyntax_analysis(analysis_id, is_base):
    """
    Elimina un análisis base o iteración.
    Si es base, también elimina todas sus iteraciones.
    """
    from bson import ObjectId

    try:
        if isinstance(analysis_id, str):
            analysis_id = ObjectId(analysis_id)

        if is_base:
            # Eliminar iteraciones vinculadas
            iteration_collection = get_collection(ITERATION_COLLECTION)
            iteration_collection.delete_many({"base_id": analysis_id})

            # Luego eliminar el análisis base
            collection = get_collection(BASE_COLLECTION)
        else:
            collection = get_collection(ITERATION_COLLECTION)

        query = {"_id": analysis_id}
        result = delete_document(collection.name, query)
        return result

    except Exception as e:
        logger.error(f"Error eliminando análisis: {str(e)}")
        return False

def get_student_morphosyntax_data(username):
    """
    Obtiene todos los datos de análisis morfosintáctico de un estudiante.
    Returns: Diccionario con todos los análisis y sus iteraciones.
    """
    try:
        analyses = get_student_morphosyntax_analysis(username, limit=None)
        return {
            'entries': analyses,
            'total_analyses': len(analyses),
            'has_iterations': any(a.get('has_iterations', False) for a in analyses)
        }

    except Exception as e:
        logger.error(f"Error obteniendo datos del estudiante: {str(e)}")
        return {'entries': [], 'total_analyses': 0, 'has_iterations': False}
