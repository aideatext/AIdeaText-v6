# modules/semantic/semantic_process.py
import streamlit as st
import matplotlib.pyplot as plt
import io
import base64
import logging

from ..text_analysis.semantic_analysis import (
    perform_semantic_analysis,
    identify_key_concepts,
    create_concept_graph,
    visualize_concept_graph
)
from ..database.semantic_mongo_db import store_student_semantic_result

logger = logging.getLogger(__name__)

def process_semantic_input(text, lang_code, nlp_models, t):
    """
    Procesa el texto ingresado para realizar el análisis semántico.
    """
    try:
        logger.info(f"Iniciando análisis semántico para texto de {len(text)} caracteres")
        
        # Realizar el análisis semántico
        nlp = nlp_models[lang_code]
        analysis_result = perform_semantic_analysis(text, nlp, lang_code)
        
        if not analysis_result['success']:
            return {
                'success': False,
                'message': analysis_result['error'],
                'analysis': None
            }
            
        logger.info("Análisis semántico completado. Guardando resultados...")
        
        # Intentar guardar en la base de datos
        try:
            store_result = store_student_semantic_result(
                st.session_state.username,
                text,
                analysis_result,
                lang_code
            )
            if not store_result:
                logger.warning("No se pudo guardar el análisis en la base de datos")
        except Exception as db_error:
            logger.error(f"Error al guardar en base de datos: {str(db_error)}")
        
        # Devolver el resultado incluso si falla el guardado
        return {
            'success': True,
            'message': t.get('success_message', 'Analysis completed successfully'),
            'analysis': {
                'key_concepts': analysis_result['key_concepts'],
                'concept_graph': analysis_result['concept_graph']
            }
        }
        
    except Exception as e:
        logger.error(f"Error en process_semantic_input: {str(e)}")
        return {
            'success': False,
            'message': str(e),
            'analysis': None
        }

def format_semantic_results(analysis_result, t):
    """
    Formatea los resultados del análisis para su visualización.
    """
    try:
        if not analysis_result['success']:
            return {
                'formatted_text': analysis_result['message'],
                'visualizations': None
            }
            
        formatted_sections = []
        analysis = analysis_result['analysis']
        
        # Formatear conceptos clave
        if 'key_concepts' in analysis:
            concepts_section = [f"### {t.get('key_concepts', 'Key Concepts')}"]
            concepts_section.extend([
                f"- {concept}: {frequency:.2f}"
                for concept, frequency in analysis['key_concepts']
            ])
            formatted_sections.append('\n'.join(concepts_section))
        
        return {
            'formatted_text': '\n\n'.join(formatted_sections),
            'visualizations': {
                'concept_graph': analysis.get('concept_graph')
            }
        }
        
    except Exception as e:
        logger.error(f"Error en format_semantic_results: {str(e)}")
        return {
            'formatted_text': str(e),
            'visualizations': None
        }

__all__ = [
    'process_semantic_input',
    'format_semantic_results'
]