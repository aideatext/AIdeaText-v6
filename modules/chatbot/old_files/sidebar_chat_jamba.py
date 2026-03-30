# modules/chatbot/sidebar_chat.py
import streamlit as st
import logging
from modules.chatbot.chat_process import ChatProcessor
from modules.database.chat_mongo_db import store_chat_history

logger = logging.getLogger(__name__)

def display_sidebar_chat(lang_code: str, chatbot_t: dict):
    """Chatbot mejorado con manejo completo del contexto semántico"""
    
    # --- PASO 1: INICIALIZACIÓN TEMPRANA (Crucial) ---
    if 'sidebar_messages' not in st.session_state:
        st.session_state.sidebar_messages = []
        # Agregar mensaje de bienvenida inicial
        initial_msg = {
            'en': "Hello! Ask me about the semantic analysis.",
            'es': "¡Hola! Pregúntame sobre el análisis semántico.",
            'pt': "Olá! Pergunte-me sobre a análise semântica.",
            'fr': "Bonjour! Demandez-moi sur l'analyse sémantique."
        }.get(lang_code, "Hello!")
        st.session_state.sidebar_messages.append({"role": "assistant", "content": initial_msg})
        logger.info("Historial sidebar_messages inicializado")

    if 'chat_processor' not in st.session_state:
        st.session_state.chat_processor = ChatProcessor()
        logger.info("ChatProcessor inicializado para AWS Bedrock")

    with st.sidebar:
        st.markdown("""<style>.chat-container { max-height: 60vh; overflow-y: auto; }</style>""", unsafe_allow_html=True)

        try:
            # --- PASO 2: CONFIGURAR CONTEXTO (Si el agente está activo) ---
            if st.session_state.get('semantic_agent_active', False):
                semantic_data = st.session_state.get('semantic_agent_data')
                if semantic_data and all(k in semantic_data for k in ['text', 'metrics']):
                    st.session_state.chat_processor.set_semantic_context(
                        text=semantic_data['text'],
                        metrics=semantic_data['metrics'],
                        graph_data=semantic_data.get('graph_data'),
                        lang_code=lang_code
                    )
                    if semantic_data.get('graph_data'):
                        st.info("📊 Grafo disponible para el asistente")

            # --- PASO 3: INTERFAZ DEL CHAT ---
            with st.expander("💬 Asistente de Análisis", expanded=True):
                chat_container = st.container()
                with chat_container:
                    for msg in st.session_state.sidebar_messages:
                        st.chat_message(msg["role"]).write(msg["content"])

                user_input = st.chat_input(chatbot_t.get('ask_placeholder', "Pregunta..."))

                if user_input:
                    with chat_container:
                        st.chat_message("user").write(user_input)
                        st.session_state.sidebar_messages.append({"role": "user", "content": user_input})
                        
                        with st.chat_message("assistant"):
                            stream = st.session_state.chat_processor.process_chat_input(user_input, lang_code)
                            response = st.write_stream(stream)
                            st.session_state.sidebar_messages.append({"role": "assistant", "content": response})

                    # Guardar en DB
                    if 'username' in st.session_state and st.session_state.get('semantic_agent_data'):
                        store_chat_history(
                            username=st.session_state.username,
                            messages=st.session_state.sidebar_messages,
                            analysis_type='semantic_analysis'
                        )

                if st.button("🔄 Reiniciar Chat"):
                    st.session_state.sidebar_messages = []
                    st.rerun()

        except Exception as e:
            logger.error(f"Error en sidebar_chat: {str(e)}", exc_info=True)
            st.error("Error en el chat. Por favor, recargue la página.")