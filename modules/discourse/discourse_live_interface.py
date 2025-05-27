# modules/discourse/discourse/discourse_live_interface.py

import streamlit as st
from streamlit_float import *
from streamlit_antd_components import *
import pandas as pd
import logging
import io
import matplotlib.pyplot as plt

# Configuración del logger
logger = logging.getLogger(__name__)

# Importaciones locales
from .discourse_process import perform_discourse_analysis
from .discourse_interface import display_discourse_results  # Añadida esta importación
from ..utils.widget_utils import generate_unique_key
from ..database.discourse_mongo_db import store_student_discourse_result
from ..database.chat_mongo_db import store_chat_history, get_chat_history


#####################################################################################################
def fig_to_bytes(fig):
    """Convierte una figura de matplotlib a bytes."""
    try:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Error en fig_to_bytes: {str(e)}")
        return None

#################################################################################################
def display_discourse_live_interface(lang_code, nlp_models, discourse_t):
    """
    Interfaz para el análisis del discurso en vivo con layout mejorado
    """
    try:
        if 'discourse_live_state' not in st.session_state:
            st.session_state.discourse_live_state = {
                'analysis_count': 0,
                'current_text1': '',
                'current_text2': '',
                'last_result': None,
                'text_changed': False
            }

        # Título
        st.subheader(discourse_t.get('enter_text', 'Ingrese sus textos'))

        # Área de entrada de textos en dos columnas
        text_col1, text_col2 = st.columns(2)

        # Texto 1
        with text_col1:
            st.markdown("**Texto 1 (Patrón)**")
            text_input1 = st.text_area(
                "Texto 1",
                height=200,
                key="discourse_live_text1",
                value=st.session_state.discourse_live_state.get('current_text1', ''),
                label_visibility="collapsed"
            )
            st.session_state.discourse_live_state['current_text1'] = text_input1

        # Texto 2
        with text_col2:
            st.markdown("**Texto 2 (Comparación)**")
            text_input2 = st.text_area(
                "Texto 2",
                height=200,
                key="discourse_live_text2",
                value=st.session_state.discourse_live_state.get('current_text2', ''),
                label_visibility="collapsed"
            )
            st.session_state.discourse_live_state['current_text2'] = text_input2

        # Botón de análisis centrado
        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            analyze_button = st.button(
                discourse_t.get('analyze_button', 'Analizar'),
                key="discourse_live_analyze",
                type="primary",
                icon="🔍",
                disabled=not (text_input1 and text_input2),
                use_container_width=True
            )

        # Proceso y visualización de resultados
        if analyze_button and text_input1 and text_input2:
            try:
                with st.spinner(discourse_t.get('processing', 'Procesando...')):
                    result = perform_discourse_analysis(
                        text_input1,
                        text_input2,
                        nlp_models[lang_code],
                        lang_code
                    )

                    if result['success']:
                        # Procesar ambos gráficos
                        for graph_key in ['graph1', 'graph2']:
                            if graph_key in result and result[graph_key] is not None:
                                bytes_key = f'{graph_key}_bytes'
                                graph_bytes = fig_to_bytes(result[graph_key])
                                if graph_bytes:
                                    result[bytes_key] = graph_bytes
                                plt.close(result[graph_key])

                        st.session_state.discourse_live_state['last_result'] = result
                        st.session_state.discourse_live_state['analysis_count'] += 1
                        
                        store_student_discourse_result(
                            st.session_state.username,
                            text_input1,
                            text_input2,
                            result
                        )

                        # Mostrar resultados
                        st.markdown("---")
                        st.subheader(discourse_t.get('results_title', 'Resultados del Análisis'))
                        display_discourse_results(result, lang_code, discourse_t)

                    else:
                        st.error(result.get('message', 'Error en el análisis'))

            except Exception as e:
                logger.error(f"Error en análisis: {str(e)}")
                st.error(discourse_t.get('error_processing', f'Error al procesar el texto: {str(e)}'))

        # Mostrar resultados previos si existen
        elif 'last_result' in st.session_state.discourse_live_state and \
             st.session_state.discourse_live_state['last_result'] is not None:
            
            st.markdown("---")
            st.subheader(discourse_t.get('previous_results', 'Resultados del Análisis Anterior'))
            display_discourse_results(
                st.session_state.discourse_live_state['last_result'],
                lang_code,
                discourse_t
            )

    except Exception as e:
        logger.error(f"Error general en interfaz del discurso en vivo: {str(e)}")
        st.error(discourse_t.get('general_error', "Se produjo un error. Por favor, intente de nuevo."))



