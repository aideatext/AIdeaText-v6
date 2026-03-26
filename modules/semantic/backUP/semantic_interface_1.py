import streamlit as st
from .semantic_process import process_semantic_analysis
from ..chatbot.chatbot import initialize_chatbot
from ..database.database_oldFromV2 import store_semantic_result
from ..text_analysis.semantic_analysis import perform_semantic_analysis
from ..utils.widget_utils import generate_unique_key

def display_semantic_interface(lang_code, nlp_models, t):
    st.subheader(t['title'])

    # Inicializar el chatbot si no existe
    if 'semantic_chatbot' not in st.session_state:
        st.session_state.semantic_chatbot = initialize_chatbot('semantic')

    # Sección para cargar archivo
    uploaded_file = st.file_uploader(t['file_uploader'], type=['txt', 'pdf', 'docx', 'doc', 'odt'])
    if uploaded_file:
        file_contents = uploaded_file.getvalue().decode('utf-8')
        st.session_state.file_contents = file_contents

    # Mostrar el historial del chat
    chat_history = st.session_state.get('semantic_chat_history', [])
    for message in chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if "visualization" in message:
                st.pyplot(message["visualization"])

    # Input del usuario
    user_input = st.chat_input(t['semantic_initial_message'], key=generate_unique_key('semantic', st.session_state.username))

    if user_input:
        # Procesar el input del usuario
        response, visualization = process_semantic_analysis(user_input, lang_code, nlp_models[lang_code], st.session_state.get('file_contents'), t)

        # Actualizar el historial del chat
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({"role": "assistant", "content": response, "visualization": visualization})
        st.session_state.semantic_chat_history = chat_history

        # Mostrar el resultado más reciente
        with st.chat_message("assistant"):
            st.write(response)
            if visualization:
                st.pyplot(visualization)

        # Guardar el resultado en la base de datos si es un análisis
        if user_input.startswith('/analisis_semantico'):
            result = perform_semantic_analysis(st.session_state.file_contents, nlp_models[lang_code], lang_code)
            store_semantic_result(st.session_state.username, st.session_state.file_contents, result)

    # Botón para limpiar el historial del chat
    if st.button(t['clear_chat'], key=generate_unique_key('semantic', 'clear_chat')):
        st.session_state.semantic_chat_history = []
        st.rerun()