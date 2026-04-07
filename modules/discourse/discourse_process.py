from ..text_analysis.discourse_analysis import perform_discourse_analysis, compare_semantic_analysis
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def process_discourse_input(text1, text2, nlp_models, lang_code):
    """
    Procesa la entrada para el análisis del discurso
    Args:
        text1: Texto del primer documento
        text2: Texto del segundo documento
        nlp_models: Diccionario de modelos de spaCy
        lang_code: Código del idioma actual
    Returns:
        dict: Resultados del análisis
    """
    try:
        # Obtener el modelo específico del idioma
        nlp = nlp_models[lang_code]
        
        # Realizar el análisis
        analysis_result = perform_discourse_analysis(text1, text2, nlp, lang_code)
        
        if analysis_result['success']:
            return {
                'success': True,
                'analysis': analysis_result
            }
        else:
            return {
                'success': False,
                'error': 'Error en el análisis del discurso'
            }
            
    except Exception as e:
        logger.error(f"Error en process_discourse_input: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def format_discourse_results(result):
    """
    Formatea los resultados del análisis para su visualización
    Args:
        result: Resultado del análisis
    Returns:
        dict: Resultados formateados
    """
    try:
        if not result['success']:
            return result

        analysis = result['analysis']
        return {
            'success': True,
            'graph1': analysis['graph1'],
            'graph2': analysis['graph2'],
            'key_concepts1': analysis['key_concepts1'],
            'key_concepts2': analysis['key_concepts2'],
            'table1': analysis['table1'],
            'table2': analysis['table2']
        }
        
    except Exception as e:
        logger.error(f"Error en format_discourse_results: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }