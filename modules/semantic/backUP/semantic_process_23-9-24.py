import logging
import io
import base64
import matplotlib.pyplot as plt
from ..text_analysis.semantic_analysis import perform_semantic_analysis
from .flexible_analysis_handler import FlexibleAnalysisHandler

logger = logging.getLogger(__name__)

def encode_image_to_base64(image_data):
    if isinstance(image_data, str):  # Si es una ruta de archivo
        with open(image_data, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    elif isinstance(image_data, bytes):  # Si son datos de imagen en memoria
        encoded_string = base64.b64encode(image_data).decode("utf-8")
    else:
        raise ValueError("Invalid image data type. Expected string (file path) or bytes.")
    return encoded_string  #

def process_semantic_analysis(file_contents, nlp_model, lang_code):
    logger.info(f"Starting semantic analysis processing for language: {lang_code}")
    try:
        result = perform_semantic_analysis(file_contents, nlp_model, lang_code)
        #handler = FlexibleAnalysisHandler(result)

        #concept_graph = handler.get_graph('concept_graph')
        #entity_graph = handler.get_graph('entity_graph')
        #key_concepts = handler.get_key_concepts()

        concept_graph = result['concept_graph']
        entity_graph = result['entity_graph']
        key_concepts = result['key_concepts']

        # Convertir los gráficos a base64
        concept_graph_base64 = fig_to_base64(concept_graph) if concept_graph else None
        entity_graph_base64 = fig_to_base64(entity_graph) if entity_graph else None

        logger.info("Semantic analysis processing completed successfully")
        return concept_graph_base64, entity_graph_base64, key_concepts
    except Exception as e:
        logger.error(f"Error in semantic analysis processing: {str(e)}")
        return None, None, []  # Retorna valores vacíos en caso de error

'''
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def process_semantic_analysis(file_contents, nlp_model, lang_code):
    logger.info(f"Starting semantic analysis for language: {lang_code}")
    try:
        logger.debug("Calling perform_semantic_analysis")
        result = perform_semantic_analysis(file_contents, nlp_model, lang_code)
        logger.debug(f"Result keys: {result.keys()}")
        logger.debug(f"Type of concept_graph: {type(result['concept_graph'])}")
        logger.debug(f"Type of entity_graph: {type(result['entity_graph'])}")
        logger.debug(f"Number of key_concepts: {len(result['key_concepts'])}")
        logger.info("Semantic analysis completed successfully")
        return result['concept_graph'], result['entity_graph'], result['key_concepts']
    except Exception as e:
        logger.error(f"Error in semantic analysis: {str(e)}")
        raise
'''