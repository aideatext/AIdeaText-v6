#/modules/database/morphosintax_mongo_db.py
from ..mongo_db import insert_document, find_documents, update_document, delete_document
from ...utils.svg_to_png_converter import process_and_save_svg_diagrams
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

COLLECTION_NAME = 'student_morphosyntax_analysis'

def store_student_morphosyntax_result(username, text, arc_diagrams):
    analysis_document = {
        'username': username,
        'timestamp': datetime.now(timezone.utc), # Mejor práctica
        'text': text,
        'arc_diagrams': arc_diagrams,
        'analysis_type': 'morphosyntax'
    }

    result = insert_document(COLLECTION_NAME, analysis_document)
    if result:
        # Procesar y guardar los diagramas SVG como PNG
        png_ids = process_and_save_svg_diagrams(username, str(result), arc_diagrams)

        # Actualizar el documento con los IDs de los PNGs
        update_document(COLLECTION_NAME, {'_id': result}, {'$set': {'png_diagram_ids': png_ids}})

        logger.info(f"Análisis morfosintáctico del estudiante guardado con ID: {result} para el usuario: {username}")
        return True
    return False

def get_student_morphosyntax_analysis(username, limit=10):
    query = {"username": username, "analysis_type": "morphosyntax"}
    return find_documents(COLLECTION_NAME, query, sort=[("timestamp", -1)], limit=limit)

def update_student_morphosyntax_analysis(analysis_id, update_data):
    query = {"_id": analysis_id}
    update = {"$set": update_data}
    return update_document(COLLECTION_NAME, query, update)

def delete_student_morphosyntax_analysis(analysis_id):
    query = {"_id": analysis_id}
    return delete_document(COLLECTION_NAME, query)

def get_student_morphosyntax_data(username):
    analyses = get_student_morphosyntax_analysis(username, limit=None)  # Obtener todos los análisis
    return {
        'entries': analyses
    }