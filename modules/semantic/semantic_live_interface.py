# modules/semantic/semantic_live_interface.py
import streamlit as st
from streamlit_float import *
from streamlit_antd_components import *
import pandas as pd
import logging

# Configuración del logger
logger = logging.getLogger(__name__)

# Importaciones locales
from .semantic_process import (
    process_semantic_input,
    format_semantic_results
)

from ..utils.widget_utils import generate_unique_key

from ..database.semantic_mongo_live_db import store_student_semantic_live_result

from ..database.chat_mongo_db import store_chat_history, get_chat_history

def display_semantic_live_interface(lang_code, nlp_models, semantic_t):
    """
    Interfaz para el análisis semántico en vivo con proporciones de columna ajustadas
    """
    try:
        # 1. Inicializar el estado de la sesión de manera más robusta
        if 'semantic_live_state' not in st.session_state:
            st.session_state.semantic_live_state = {
                'analysis_count': 0,
                'current_text': '',
                'last_result': None,
                'text_changed': False,
                'pending_analysis': False  # Nuevo flag para análisis pendiente
            }

        # 2. Función para manejar cambios en el texto
        def on_text_change():
            current_text = st.session_state.semantic_live_text
            st.session_state.semantic_live_state['current_text'] = current_text
            st.session_state.semantic_live_state['text_changed'] = True

        # 3. Crear columnas con nueva proporción (1:3)
        input_col, result_col = st.columns([1, 3])

        # Columna izquierda: Entrada de texto
        with input_col:
            st.subheader(semantic_t.get('enter_text', 'Ingrese su texto'))
            
            # Área de texto con manejo de eventos
            text_input = st.text_area(
                semantic_t.get('text_input_label', 'Escriba o pegue su texto aquí'),
                height=500,
                key="semantic_live_text",
                value=st.session_state.semantic_live_state.get('current_text', ''),
                on_change=on_text_change,
                label_visibility="collapsed"
            )

            # Botón de análisis y procesamiento
            analyze_button = st.button(
                semantic_t.get('analyze_button', 'Analizar'),
                key="semantic_live_analyze",
                type="primary",
                icon="🔍",
                disabled=not text_input,
                use_container_width=True
            )

            # 4. Procesar análisis cuando se presiona el botón
            if analyze_button and text_input:
                st.session_state.semantic_live_state['pending_analysis'] = True
                st.session_state.semantic_live_state['current_text'] = text_input  # Guardar texto actual
                st.rerun()

            # 5. Manejar análisis pendiente
            if st.session_state.semantic_live_state.get('pending_analysis', False):
                try:
                    with st.spinner(semantic_t.get('processing', 'Procesando...')):
                        analysis_result = process_semantic_input(
                            text_input,
                            lang_code,
                            nlp_models,
                            semantic_t
                        )

                        if analysis_result['success']:
                            st.session_state.semantic_live_state['last_result'] = analysis_result
                            st.session_state.semantic_live_state['analysis_count'] += 1
                            st.session_state.semantic_live_state['text_changed'] = False
                            
                            # USAR PARÁMETROS NOMBRADOS PARA EVITAR EL ERROR DE 'STR' OBJECT
                            store_result = store_student_semantic_live_result(
                                    username=st.session_state.username,
                                    text=text_input,
                                    analysis_data=analysis_result['analysis'], # Aquí estaba el cruce
                                    lang_code=lang_code
                                )
                            
                            if not store_result:
                                st.error(semantic_t.get('error_saving', 'Error al guardar el análisis'))
                            else:
                                st.success(semantic_t.get('analysis_saved', 'Análisis guardado correctamente'))
                        else:
                           st.error(analysis_result.get('message', 'Error en el análisis'))

                except Exception as e:
                    logger.error(f"Error en análisis: {str(e)}")
                    st.error(semantic_t.get('error_processing', 'Error al procesar el texto'))
                finally:
                    st.session_state.semantic_live_state['pending_analysis'] = False

        # Columna derecha: Visualización de resultados
        with result_col:
            # st.subheader(semantic_t.get('live_results', 'Resultados en vivo'))

            if 'last_result' in st.session_state.semantic_live_state and \
               st.session_state.semantic_live_state['last_result'] is not None:
                
                analysis = st.session_state.semantic_live_state['last_result']['analysis']

                if 'key_concepts' in analysis and analysis['key_concepts'] and \
                   'concept_graph' in analysis and analysis['concept_graph'] is not None:
                    
                    st.markdown("""
                        <style>
                        .unified-container {
                            background-color: white;
                            border-radius: 10px;
                            overflow: hidden;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                            width: 100%;
                            margin-bottom: 1rem;
                        }
                        .concept-table {
                            display: flex;
                            flex-wrap: nowrap;
                            gap: 6px;
                            padding: 10px;
                            background-color: #f8f9fa;
                            overflow-x: auto;
                            white-space: nowrap;
                        }
                        .concept-item {
                            background-color: white;
                            border-radius: 4px;
                            padding: 4px 8px;
                            display: inline-flex;
                            align-items: center;
                            gap: 4px;
                            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
                            flex-shrink: 0;
                        }
                        .concept-name { 
                            font-weight: 500; 
                            color: #1f2937;
                            font-size: 0.8em;
                        }
                        .concept-freq { 
                            color: #6b7280; 
                            font-size: 0.75em;
                        }
                        .graph-section { 
                            padding: 20px;
                            background-color: white;
                        }
                        </style>
                    """, unsafe_allow_html=True)

                    with st.container():
                        # Conceptos en una sola línea
                        concepts_html = """
                        <div class="unified-container">
                            <div class="concept-table">
                        """
                        concepts_html += ''.join(
                            f'<div class="concept-item"><span class="concept-name">{concept}</span>'
                            f'<span class="concept-freq">({freq:.2f})</span></div>'
                            for concept, freq in analysis['key_concepts']
                        )
                        concepts_html += "</div></div>"
                        st.markdown(concepts_html, unsafe_allow_html=True)
                        
                        # Grafo
                        if 'concept_graph' in analysis and analysis['concept_graph'] is not None:
                            st.image(
                                analysis['concept_graph'],
                                use_container_width=True
                            )

                        # Controles en dos columnas
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            # Botón para consultar con el asistente (CORREGIDO)
                            if st.button("💬 Consultar con Asistente", 
                                       key="semantic_live_chat_button",
                                       use_container_width=True):
                                if 'last_result' not in st.session_state.semantic_live_state:
                                    st.error("Primero complete el análisis semántico")
                                else:
                                    st.session_state.semantic_agent_data = {
                                        'text': st.session_state.semantic_live_state['current_text'],
                                        'metrics': analysis,
                                        'graph_data': analysis.get('concept_graph')
                                    }
                                    st.session_state.semantic_agent_active = True
                                    st.rerun()
                            
                            # Botón de descarga
                            if 'concept_graph' in analysis:  # Verificar existencia
                                st.download_button(
                                    label="📥 " + semantic_t.get('download_graph', "Descargar"),
                                    data=analysis['concept_graph'],
                                    file_name="semantic_live_graph.png",
                                    mime="image/png",
                                    use_container_width=True
                                )
                        
                        # Notificación si el agente está activo
                        if st.session_state.get('semantic_agent_active', False):
                            st.success(semantic_t.get('semantic_agent_ready_message', 
                                                    'El agente virtual está listo. Abre el chat en la barra lateral.'))
                        
                        with st.expander("📊 " + semantic_t.get('graph_help', "Interpretación del gráfico")):
                            st.markdown("""
                                - 🔀 Las flechas indican la dirección de la relación entre conceptos
                                - 🎨 Los colores más intensos indican conceptos más centrales
                                - ⭕ El tamaño de los nodos representa la frecuencia del concepto
                                - ↔️ El grosor de las líneas indica la fuerza de la conexión
                            """)
                else:
                    st.info(semantic_t.get('no_graph', 'No hay datos para mostrar'))
            else:
                st.info(semantic_t.get('analysis_prompt', 'Realice un análisis para ver los resultados'))

    except Exception as e:
        logger.error(f"Error general en interfaz semántica en vivo: {str(e)}")
        st.error(semantic_t.get('general_error', "Se produjo un error. Por favor, intente de nuevo."))