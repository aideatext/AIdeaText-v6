#modules/morphosyntax/morphosyntax_interface.py
import streamlit as st
from streamlit_float import *
from streamlit_antd_components import *
from streamlit.components.v1 import html
import base64
from .morphosyntax_process import process_morphosyntactic_input
from ..chatbot.chatbot import initialize_chatbot
from ..utils.widget_utils import generate_unique_key
from ..database.database_oldFromV2 import store_morphosyntax_result

import logging
logger = logging.getLogger(__name__)


####################### VERSION ANTERIOR A LAS 20:00 24-9-24

def display_morphosyntax_interface(lang_code, nlp_models, t):
    # Estilo CSS personalizado
    st.markdown("""
        <style>
        .morpho-initial-message {
            background-color: #f0f2f6;
            border-left: 5px solid #4CAF50;
            padding: 10px;
            border-radius: 5px;
            font-size: 16px;
            margin-bottom: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Mostrar el mensaje inicial como un párrafo estilizado
    st.markdown(f"""
        <div class="morpho-initial-message">
        {t['morpho_initial_message']}
        </div>
    """, unsafe_allow_html=True)

    # Inicializar el chatbot si no existe
    if 'morphosyntax_chatbot' not in st.session_state:
        st.session_state.morphosyntax_chatbot = initialize_chatbot('morphosyntactic')

    # Crear un contenedor para el chat
    chat_container = st.container()

    # Mostrar el historial del chat
    with chat_container:
        if 'morphosyntax_chat_history' not in st.session_state:
            st.session_state.morphosyntax_chat_history = []
        for i, message in enumerate(st.session_state.morphosyntax_chat_history):
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "visualizations" in message:
                    for viz in message["visualizations"]:
                        st.components.v1.html(
                            f"""
                            <div style="width: 100%; overflow-x: auto; white-space: nowrap;">
                                <div style="min-width: 1200px;">
                                    {viz}
                                </div>
                            </div>
                            """,
                            height=370,
                            scrolling=True
                        )


    # Input del usuario
    user_input = st.chat_input(
        t['morpho_input_label'],
        key=generate_unique_key('morphosyntax', "chat_input")
    )

    if user_input:
        # Añadir el mensaje del usuario al historial
        st.session_state.morphosyntax_chat_history.append({"role": "user", "content": user_input})

        # Mostrar indicador de carga
        with st.spinner(t.get('processing', 'Processing...')):
            try:
                # Procesar el input del usuario
                response, visualizations, result = process_morphosyntactic_input(user_input, lang_code, nlp_models, t)

                # Añadir la respuesta al historial
                message = {
                    "role": "assistant",
                    "content": response
                }
                if visualizations:
                    message["visualizations"] = visualizations
                st.session_state.morphosyntax_chat_history.append(message)

                # Mostrar la respuesta más reciente
                with st.chat_message("assistant"):
                    st.write(response)
                    if visualizations:
                        for i, viz in enumerate(visualizations):
                            st.components.v1.html(
                                f"""
                                <div style="width: 100%; overflow-x: auto; white-space: nowrap;">
                                    <div style="min-width: 1200px;">
                                        {viz}
                                    </div>
                                </div>
                                """,
                                height=350,
                                scrolling=True
                            )

                # Si es un análisis, guardarlo en la base de datos
                if user_input.startswith('/analisis_morfosintactico') and result:
                    store_morphosyntax_result(
                        st.session_state.username,
                        user_input.split('[', 1)[1].rsplit(']', 1)[0],  # texto analizado
                        result.get('repeated_words', {}),
                        visualizations,
                        result.get('pos_analysis', []),
                        result.get('morphological_analysis', []),
                        result.get('sentence_structure', [])
                    )

            except Exception as e:
                st.error(f"{t['error_processing']}: {str(e)}")

        # Si es un análisis, guardarlo en la base de datos
        if user_input.startswith('/analisis_morfosintactico') and result:
            store_morphosyntax_result(
                st.session_state.username,
                user_input.split('[', 1)[1].rsplit(']', 1)[0],  # texto analizado
                result['repeated_words'],
                visualizations,  # Ahora pasamos todas las visualizaciones
                result['pos_analysis'],
                result['morphological_analysis'],
                result['sentence_structure']
            )

    # Forzar la actualización de la interfaz
        st.rerun()

    # Botón para limpiar el historial del chat
    if st.button(t['clear_chat'], key=generate_unique_key('morphosyntax', 'clear_chat')):
        st.session_state.morphosyntax_chat_history = []
        st.rerun()



'''
############ MODULO PARA DEPURACIÓN Y PRUEBAS #####################################################
def display_morphosyntax_interface(lang_code, nlp_models, t):
    st.subheader(t['morpho_title'])

    text_input = st.text_area(
        t['warning_message'],
        height=150,
        key=generate_unique_key("morphosyntax", "text_area")
    )

    if st.button(
        t['results_title'],
        key=generate_unique_key("morphosyntax", "analyze_button")
    ):
        if text_input:
            # Aquí iría tu lógica de análisis morfosintáctico
            # Por ahora, solo mostraremos un mensaje de placeholder
            st.info(t['analysis_placeholder'])
        else:
            st.warning(t['no_text_warning'])
###
#################################################
'''
