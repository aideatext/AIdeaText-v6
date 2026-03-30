#modules/morphosyntax/morphosyntax_interface.py

import streamlit as st
from streamlit_float import *
from streamlit_antd_components import *
from streamlit.components.v1 import html
import spacy
from spacy import displacy
import spacy_streamlit
import pandas as pd
import base64
import re

from .morphosyntax_process import (
    process_morphosyntactic_input,
    format_analysis_results,
    perform_advanced_morphosyntactic_analysis,
    get_repeated_words_colors,
    highlight_repeated_words,
    POS_COLORS,
    POS_TRANSLATIONS
)

from ..utils.widget_utils import generate_unique_key
from ..database.backUp.morphosintax_mongo_db import store_student_morphosyntax_result
from ..database.chat_mongo_db import store_chat_history, get_chat_history

import logging
logger = logging.getLogger(__name__)


def display_morphosyntax_interface(lang_code, nlp_models, morpho_t):
    try:
        # Inicializar el estado si no existe
        if 'morphosyntax_state' not in st.session_state:
            st.session_state.morphosyntax_state = {
                'analysis_count': 0,
                'current_text': '',  # Almacenar el texto actual
                'last_analysis': None,
                'needs_update': False  # Flag para actualización
            }

        # Campo de entrada de texto que mantiene su valor
        text_key = "morpho_text_input"
        
        # Función para manejar cambios en el texto
        def on_text_change():
            st.session_state.morphosyntax_state['current_text'] = st.session_state[text_key]
            st.session_state.morphosyntax_state['needs_update'] = True
        
        # Recuperar el texto anterior si existe
        default_text = st.session_state.morphosyntax_state.get('current_text', '')
        
        sentence_input = st.text_area(
            morpho_t.get('morpho_input_label', 'Enter text to analyze'),
            value=default_text,  # Usar el texto guardado
            height=150,
            key=text_key,
            on_change=on_text_change,
            placeholder=morpho_t.get('morpho_input_placeholder', 'Enter your text here...')
        )

        # Botón de análisis
        col1, col2, col3 = st.columns([2,1,2])
        with col1:
            analyze_button = st.button(
                morpho_t.get('morpho_analyze_button', 'Analyze Morphosyntax'),
                key=f"morpho_button_{st.session_state.morphosyntax_state['analysis_count']}",
                type="primary",
                icon="🔍",
                disabled=not bool(sentence_input.strip()),
                use_container_width=True
            )

        # Procesar análisis solo cuando sea necesario
        if (analyze_button or st.session_state.morphosyntax_state['needs_update']) and sentence_input.strip():
            try:
                with st.spinner(morpho_t.get('processing', 'Processing...')):
                    doc = nlp_models[lang_code](sentence_input)
                    advanced_analysis = perform_advanced_morphosyntactic_analysis(
                        sentence_input,
                        nlp_models[lang_code]
                    )

                    st.session_state.morphosyntax_result = {
                        'doc': doc,
                        'advanced_analysis': advanced_analysis
                    }
                    
                    # Solo guardar en DB si fue un click en el botón
                    if analyze_button:
                        if store_student_morphosyntax_result(
                            username=st.session_state.username,
                            text=sentence_input,
                            arc_diagrams=advanced_analysis['arc_diagrams']
                        ):
                            st.success(morpho_t.get('success_message', 'Analysis saved successfully'))
                            st.session_state.morphosyntax_state['analysis_count'] += 1
                    
                    st.session_state.morphosyntax_state['needs_update'] = False
                    
                    # Mostrar resultados en un contenedor específico
                    with st.container():
                        display_morphosyntax_results(
                            st.session_state.morphosyntax_result,
                            lang_code,
                            morpho_t
                        )

            except Exception as e:
                logger.error(f"Error en análisis morfosintáctico: {str(e)}")
                st.error(morpho_t.get('error_processing', f'Error processing text: {str(e)}'))
        
        # Mostrar resultados previos si existen
        elif 'morphosyntax_result' in st.session_state and st.session_state.morphosyntax_result:
            with st.container():
                display_morphosyntax_results(
                    st.session_state.morphosyntax_result,
                    lang_code,
                    morpho_t
                )

    except Exception as e:
        logger.error(f"Error general en display_morphosyntax_interface: {str(e)}")
        st.error("Se produjo un error. Por favor, intente de nuevo.")



def display_morphosyntax_results(result, lang_code, morpho_t):
    """
    Muestra solo el análisis sintáctico con diagramas de arco.
    """
    if result is None:
        st.warning(morpho_t.get('no_results', 'No results available'))
        return

    doc = result['doc']

    # Análisis sintáctico (diagramas de arco)
    st.markdown(f"### {morpho_t.get('arc_diagram', 'Syntactic analysis: Arc diagram')}")
    
    with st.container():
        sentences = list(doc.sents)
        for i, sent in enumerate(sentences):
            with st.container():
                st.subheader(f"{morpho_t.get('sentence', 'Sentence')} {i+1}")
                try:
                    html = displacy.render(sent, style="dep", options={
                        "distance": 100,
                        "arrow_spacing": 20,
                        "word_spacing": 30
                    })
                    # Ajustar dimensiones del SVG
                    html = html.replace('height="375"', 'height="200"')
                    html = re.sub(r'<svg[^>]*>', lambda m: m.group(0).replace('height="450"', 'height="300"'), html)
                    html = re.sub(r'<g [^>]*transform="translate\((\d+),(\d+)\)"', 
                                lambda m: f'<g transform="translate({m.group(1)},50)"', html)
                    
                    # Envolver en un div con clase para estilos
                    html = f'<div class="arc-diagram-container">{html}</div>'
                    st.write(html, unsafe_allow_html=True)
                except Exception as e:
                    logger.error(f"Error rendering sentence {i}: {str(e)}")
                    st.error(f"Error displaying diagram for sentence {i+1}")
