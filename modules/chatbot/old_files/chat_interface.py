# chatbot/chat_interface.py
import streamlit as st
from .chatbot import AIdeaTextChatbot

def display_chat_interface(lang_code: str, chat_translations: Dict):
    """
    Muestra la interfaz del chat
    """
    # Inicializar chatbot si no existe
    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = AIdeaTextChatbot(lang_code)

    # Mostrar historial
    for msg in st.session_state.chatbot.get_conversation_history():
        with st.chat_message(msg[0]):
            st.write(msg[1])

    # Input del usuario
    if prompt := st.chat_input(chat_translations.get('chat_placeholder', 'Escribe tu mensaje...')):
        # Procesar mensaje
        response = st.session_state.chatbot.process_message(prompt)
        
        # Mostrar respuesta
        with st.chat_message("assistant"):
            st.write(response)