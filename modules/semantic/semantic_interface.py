#modules/semantic/semantic_interface.py
import streamlit as st
from streamlit_float import *
from streamlit_antd_components import *
from streamlit.components.v1 import html
import spacy_streamlit
import io
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import pandas as pd
import re

import logging

# Configuración del logger
logger = logging.getLogger(__name__)

# Importaciones locales
from modules.semantic.semantic_process import (
    process_semantic_input,
    format_semantic_results
)

from modules.utils.widget_utils import generate_unique_key
from modules.database.semantic_mongo_db import store_student_semantic_result
from modules.database.chat_mongo_db import store_chat_history, get_chat_history

from modules.semantic.semantic_agent_interaction import display_semantic_chat
from modules.chatbot.sidebar_chat import display_sidebar_chat

# from ..database.semantic_export import export_user_interactions

###############################

def display_semantic_interface(lang_code, nlp_models, semantic_t):
    try:
        # 1. Inicializar el estado de la sesión
        if 'semantic_state' not in st.session_state:
            st.session_state.semantic_state = {
                'analysis_count': 0,
                'last_analysis': None,
                'current_file': None,
                'pending_analysis': False  # Nuevo flag para controlar el análisis pendiente
            }

        # 2. Área de carga de archivo con mensaje informativo            
        uploaded_file = st.file_uploader(
            semantic_t.get('semantic_file_uploader', 'Upload a text file for semantic analysis'),
            type=['txt'],
            key=f"semantic_file_uploader_{st.session_state.semantic_state['analysis_count']}"
        )

        # 2.1 Verificar si hay un archivo cargado y un análisis pendiente
        
        if uploaded_file is not None and st.session_state.semantic_state.get('pending_analysis', False):
        
            try:
                with st.spinner(semantic_t.get('processing', 'Processing...')):
                    # Realizar análisis
                    text_content = uploaded_file.getvalue().decode('utf-8')
                    st.session_state.semantic_state['text_content'] = text_content  # <-- Guardar el texto
                    
                    analysis_result = process_semantic_input(
                        text_content, 
                        lang_code,
                        nlp_models,
                        semantic_t
                    )
                    
                    if analysis_result['success']:
                        # Guardar resultado
                        st.session_state.semantic_result = analysis_result
                        st.session_state.semantic_state['analysis_count'] += 1
                        st.session_state.semantic_state['current_file'] = uploaded_file.name

                        # Preparar datos para MongoDB
                        analysis_data = {
                            'key_concepts': analysis_result['analysis'].get('key_concepts', []),
                            'concept_centrality': analysis_result['analysis'].get('concept_centrality', {}),
                            'concept_graph': analysis_result['analysis'].get('concept_graph')
                        }
                        
                        # Guardar en base de datos
                        storage_success = store_student_semantic_result(
                            st.session_state.username,
                            text_content,
                            analysis_result['analysis'],
                            lang_code  # Pasamos el código de idioma directamente
                        )
                        
                        if storage_success:
                            st.success(
                                semantic_t.get('analysis_complete', 
                                'Análisis completado y guardado. Para realizar un nuevo análisis, cargue otro archivo.')
                            )
                        else:
                            st.error(semantic_t.get('error_message', 'Error saving analysis'))
                    else:
                        st.error(analysis_result['message'])
                    
                # Restablecer el flag de análisis pendiente
                st.session_state.semantic_state['pending_analysis'] = False
                    
            except Exception as e:
                logger.error(f"Error en análisis semántico: {str(e)}")
                st.error(semantic_t.get('error_processing', f'Error processing text: {str(e)}'))
                # Restablecer el flag de análisis pendiente en caso de error
                st.session_state.semantic_state['pending_analysis'] = False

        # 3. Columnas para los botones y mensajes
        col1, col2 = st.columns([1,4])
        
        # 4. Botón de análisis
        with col1:
            analyze_button = st.button(
                semantic_t.get('semantic_analyze_button', 'Analyze'),
                key=f"semantic_analyze_button_{st.session_state.semantic_state['analysis_count']}",
                type="primary",
                icon="🔍",
                disabled=uploaded_file is None,
                use_container_width=True
            )

        # 5. Procesar análisis
        if analyze_button and uploaded_file is not None:
            # En lugar de realizar el análisis inmediatamente, establecer el flag
            st.session_state.semantic_state['pending_analysis'] = True
            # Forzar la recarga de la aplicación
            st.rerun()
        
        # 6. Mostrar resultados previos o mensaje inicial
        elif 'semantic_result' in st.session_state and st.session_state.semantic_result is not None:
            # Mostrar mensaje sobre el análisis actual
            #st.info(
            #    semantic_t.get('current_analysis_message', 
            #    'Mostrando análisis del archivo: {}. Para realizar un nuevo análisis, cargue otro archivo.'
            #    ).format(st.session_state.semantic_state["current_file"])
            #)
                        
            display_semantic_results(
                st.session_state.semantic_result,
                lang_code,
                semantic_t
            )
            
            # --- BOTÓN PARA ACTIVAR EL AGENTE VIRTUAL (NUEVA POSICIÓN CORRECTA) ---
            if st.button("💬 Consultar con Asistente"):
                if 'semantic_result' not in st.session_state:
                    st.error("Primero complete el análisis semántico")
                    return
                    
                # Guardar TODOS los datos necesarios
                st.session_state.semantic_agent_data = {
                    'text': st.session_state.semantic_state['text_content'],  # Texto completo
                    'metrics': st.session_state.semantic_result['analysis'],  # Métricas
                    'graph_data': st.session_state.semantic_result['analysis'].get('concept_graph')
                }
                st.session_state.semantic_agent_active = True
                st.rerun()
            
            # Mostrar notificación si el agente está activo
            if st.session_state.get('semantic_agent_active', False):
                st.success(semantic_t.get('semantic_agent_ready_message', 'El agente virtual está listo. Abre el chat en la barra lateral.'))
                
        else:
            st.info(semantic_t.get('upload_prompt', 'Cargue un archivo para comenzar el análisis'))

    except Exception as e:
        logger.error(f"Error general en interfaz semántica: {str(e)}")
        st.error(semantic_t.get('general_error', "Se produjo un error. Por favor, intente de nuevo."))


#######################################

def display_semantic_results(semantic_result, lang_code, semantic_t):
    """
    Muestra los resultados del análisis semántico de conceptos clave.
    """
    if semantic_result is None or not semantic_result['success']:
        st.warning(semantic_t.get('no_results', 'No results available'))
        return

    analysis = semantic_result['analysis']

    # Mostrar conceptos clave en formato horizontal (se mantiene igual)
    st.subheader(semantic_t.get('key_concepts', 'Key Concepts'))
    if 'key_concepts' in analysis and analysis['key_concepts']:
        df = pd.DataFrame(
            analysis['key_concepts'],
            columns=[
                semantic_t.get('concept', 'Concept'),
                semantic_t.get('frequency', 'Frequency')
            ]
        )
        
        st.write(
            """
            <style>
            .concept-table {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-bottom: 20px;
            }
            .concept-item {
                background-color: #f0f2f6;
                border-radius: 5px;
                padding: 8px 12px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .concept-name {
                font-weight: bold;
            }
            .concept-freq {
                color: #666;
                font-size: 0.9em;
            }
            </style>
            <div class="concept-table">
            """ + 
            ''.join([
                f'<div class="concept-item"><span class="concept-name">{concept}</span>'
                f'<span class="concept-freq">({freq:.2f})</span></div>'
                for concept, freq in df.values
            ]) +
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.info(semantic_t.get('no_concepts', 'No key concepts found'))

    # Gráfico de conceptos (versión modificada)
    if 'concept_graph' in analysis and analysis['concept_graph'] is not None:
        try:
            # Sección del gráfico (sin div contenedor)
            st.image(
                analysis['concept_graph'],
                use_container_width=True
            )

            # --- SOLO ESTE BLOQUE ES NUEVO ---
            st.markdown("""
            <style>
            div[data-testid="stExpander"] div[role="button"] p {
                text-align: center;
                font-weight: bold;
            }
            </style>
            """, unsafe_allow_html=True)
            # ---------------------------------

            # Expandible con la interpretación (se mantiene igual)
            with st.expander("📊 " + semantic_t.get('semantic_graph_interpretation', "Interpretación del gráfico semántico")):
                 st.markdown(f"""
                    - 🔀 {semantic_t.get('semantic_arrow_meaning', 'Las flechas indican la dirección de la relación entre conceptos')}
                    - 🎨 {semantic_t.get('semantic_color_meaning', 'Los colores más intensos indican conceptos más centrales en el texto')}
                    - ⭕ {semantic_t.get('semantic_size_meaning', 'El tamaño de los nodos representa la frecuencia del concepto')}
                    - ↔️ {semantic_t.get('semantic_thickness_meaning', 'El grosor de las líneas indica la fuerza de la conexión')}
                """)
            
            # Contenedor para botones (se mantiene igual pero centrado)
            st.markdown("""
            <style>
            .download-btn-container {
                display: flex;
                justify-content: center;
                margin-top: 10px;
            }
            </style>
            <div class="download-btn-container">
            """, unsafe_allow_html=True)
            
            st.download_button(
                label="📥 " + semantic_t.get('download_semantic_network_graph', "Descargar gráfico de red semántica"),
                data=analysis['concept_graph'],
                file_name="semantic_graph.png",
                mime="image/png",
                use_container_width=True
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        except Exception as e:
            logger.error(f"Error displaying graph: {str(e)}")
            st.error(semantic_t.get('graph_error', 'Error displaying the graph'))
    else:
        st.info(semantic_t.get('no_graph', 'No concept graph available'))
