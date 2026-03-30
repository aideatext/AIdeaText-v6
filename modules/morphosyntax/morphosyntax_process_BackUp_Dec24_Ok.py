#modules/morphosyntax/morphosyntax_process.py
import streamlit as st

from ..text_analysis.morpho_analysis import (
    get_repeated_words_colors,
    highlight_repeated_words,
    generate_arc_diagram,
    get_detailed_pos_analysis,
    get_morphological_analysis,
    get_sentence_structure_analysis,
    perform_advanced_morphosyntactic_analysis,
    POS_COLORS,
    POS_TRANSLATIONS
)

from ..database.backUp.morphosintax_mongo_db import store_student_morphosyntax_result

import logging
logger = logging.getLogger(__name__)


def process_morphosyntactic_input(text, lang_code, nlp_models, t):
    """
    Procesa el texto ingresado para realizar el análisis morfosintáctico.
    
    Args:
        text: Texto a analizar
        lang_code: Código del idioma
        nlp_models: Diccionario de modelos spaCy
        t: Diccionario de traducciones
    
    Returns:
        tuple: (análisis, visualizaciones, texto_resaltado, mensaje)
    """
    try:
        # Realizar el análisis morfosintáctico
        doc = nlp_models[lang_code](text)
        
        # Obtener el análisis avanzado
        analysis = perform_advanced_morphosyntactic_analysis(text, nlp_models[lang_code])
        
        # Generar visualizaciones - AQUÍ ESTÁ EL CAMBIO
        arc_diagrams = generate_arc_diagram(doc)  # Quitamos lang_code
        
        # Obtener palabras repetidas y texto resaltado
        word_colors = get_repeated_words_colors(doc)
        highlighted_text = highlight_repeated_words(doc, word_colors)
        
        # Guardar el análisis en la base de datos
        store_student_morphosyntax_result(
            st.session_state.username,
            text,
            {
                'arc_diagrams': arc_diagrams,
                'pos_analysis': analysis['pos_analysis'],
                'morphological_analysis': analysis['morphological_analysis'],
                'sentence_structure': analysis['sentence_structure']
            }
        )
        
        return {
            'analysis': analysis,
            'visualizations': arc_diagrams,
            'highlighted_text': highlighted_text,
            'success': True,
            'message': t.get('MORPHOSYNTACTIC', {}).get('success_message', 'Analysis completed successfully')
        }
        
    except Exception as e:
        logger.error(f"Error en el análisis morfosintáctico: {str(e)}")
        return {
            'analysis': None,
            'visualizations': None,
            'highlighted_text': None,
            'success': False,
            'message': t.get('MORPHOSYNTACTIC', {}).get('error_message', f'Error in analysis: {str(e)}')
        }


def format_analysis_results(analysis_result, t):
    """
    Formatea los resultados del análisis para su visualización.
    
    Args:
        analysis_result: Resultado del análisis morfosintáctico
        t: Diccionario de traducciones
    
    Returns:
        dict: Resultados formateados para visualización
    """
    morpho_t = t.get('MORPHOSYNTACTIC', {})
    
    if not analysis_result['success']:
        return {
            'formatted_text': analysis_result['message'],
            'visualizations': None
        }
        
    formatted_sections = []
    
    # Formato para análisis POS
    if 'pos_analysis' in analysis_result['analysis']:
        pos_section = [f"### {morpho_t.get('pos_analysis', 'Part of Speech Analysis')}"]
        for pos_item in analysis_result['analysis']['pos_analysis']:
            pos_section.append(
                f"- {morpho_t.get(pos_item['pos'], pos_item['pos'])}: "
                f"{pos_item['count']} ({pos_item['percentage']}%)\n  "
                f"Ejemplos: {', '.join(pos_item['examples'])}"
            )
        formatted_sections.append('\n'.join(pos_section))
    
    # Agregar otras secciones de formato según sea necesario
    
    return {
        'formatted_text': '\n\n'.join(formatted_sections),
        'visualizations': analysis_result['visualizations'],
        'highlighted_text': analysis_result['highlighted_text']
    }

# Re-exportar las funciones y constantes necesarias
__all__ = [
    'process_morphosyntactic_input',
    'highlight_repeated_words',
    'generate_arc_diagram',
    'get_repeated_words_colors',
    'get_detailed_pos_analysis',
    'get_morphological_analysis',
    'get_sentence_structure_analysis',
    'perform_advanced_morphosyntactic_analysis',
    'POS_COLORS',
    'POS_TRANSLATIONS'
]