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
from ..metrics.m1_m2 import calculate_M2

logger = logging.getLogger(__name__)

def process_semantic_input(text, lang_code, nlp_models, t):
    """
    Procesa el texto ingresado y activa el contexto para el Chatbot.
    """
    try:
        logger.info(f"Iniciando análisis semántico para texto de {len(text)} caracteres")

        # 1. Realizar el análisis semántico
        nlp = nlp_models[lang_code]
        analysis_result = perform_semantic_analysis(text, nlp, lang_code)

        if not analysis_result['success']:
            return {
                'success': False,
                'message': analysis_result['error'],
                'analysis': None
            }

        # 2. Calcular M2 si hay grafo NetworkX disponible (CRÍTICO para el dashboard)
        graph_nx = analysis_result.get('concept_graph_nx')
        if graph_nx is not None:
            m2_metrics = calculate_M2(graph_nx)
            analysis_result['m2_score'] = m2_metrics.get('M2_density', 0.0)
            analysis_result['m2_metrics'] = m2_metrics
        else:
            analysis_result['m2_score'] = 0.0
            analysis_result['m2_metrics'] = {}
        # M1 requiere comparación con el chat — arranca en 0
        analysis_result['m1_score'] = 0.0

        logger.info(f"M2={analysis_result['m2_score']:.4f} calculado. Guardando resultados...")

        # 3. Guardar en base de datos (parámetros con nombre para evitar bugs de orden)
        try:
            group_id = st.session_state.get('class_id') or st.session_state.get('group_id', 'GENERAL')
            store_student_semantic_result(
                username=st.session_state.username,
                group_id=group_id,
                text=text,
                analysis_result=analysis_result,
                lang_code=lang_code
            )
        except Exception as db_error:
            logger.error(f"Error al guardar en base de datos: {str(db_error)}")
        
        # --- CRÍTICO: ACTIVAR EL AGENTE SEMÁNTICO PARA EL SIDEBAR ---
        # Esto es lo que 'sidebar_chat.py' busca para evitar el error de contexto
        st.session_state.semantic_agent_active = True
        st.session_state.semantic_agent_data = {
            'text': text,
            'metrics': {
                'key_concepts': analysis_result.get('key_concepts', []),
                # Guardamos el objeto nx.Graph para el cálculo de M1 posterior
                'concept_graph_nx': analysis_result.get('concept_graph_nx') 
            }
        }
        # ----------------------------------------------------------

        return {
            'success': True,
            'message': t.get('success_message', 'Analysis completed successfully'),
            'analysis': {
                'key_concepts': analysis_result['key_concepts'],
                'concept_graph': analysis_result['concept_graph'],
                # Métricas incluidas para que el store de live y discourse las use
                'm1_score': analysis_result.get('m1_score', 0.0),
                'm2_score': analysis_result.get('m2_score', 0.0),
                'm2_metrics': analysis_result.get('m2_metrics', {}),
            }
        }
        
    except Exception as e:
        logger.error(f"Error en process_semantic_input: {str(e)}")
        return {'success': False, 'message': str(e), 'analysis': None}

def format_semantic_results(analysis_result, t):
    """Formatea los resultados para la interfaz de usuario"""
    try:
        if not analysis_result['success']:
            return {'formatted_text': analysis_result['message'], 'visualizations': None}
            
        analysis = analysis_result['analysis']
        formatted_sections = []
        
        if 'key_concepts' in analysis:
            concepts_section = [f"### {t.get('key_concepts', 'Key Concepts')}"]
            concepts_section.extend([
                f"- {concept}: {frequency:.2f}"
                for concept, frequency in analysis['key_concepts']
            ])
            formatted_sections.append('\n'.join(concepts_section))
        
        return {
            'formatted_text': '\n\n'.join(formatted_sections),
            'visualizations': {'concept_graph': analysis.get('concept_graph')}
        }
        
    except Exception as e:
        logger.error(f"Error en format_semantic_results: {str(e)}")
        return {'formatted_text': str(e), 'visualizations': None}

__all__ = ['process_semantic_input', 'format_semantic_results']