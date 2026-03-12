# modules/chatbot/sidebar_chat.py
import streamlit as st
from .chat_process import ChatProcessor
from ..database.chat_mongo_db import store_chat_history
import logging

logger = logging.getLogger(__name__)

def display_sidebar_chat(lang_code: str, chatbot_t: dict):
    """Chatbot mejorado con manejo completo del contexto semántico"""
    with st.sidebar:
        # Configuración de estilos
        st.markdown("""
        <style>
            .chat-container {
                max-height: 60vh;
                overflow-y: auto;
                padding: 10px;
            }
            .chat-message { margin-bottom: 15px; }
        </style>
        """, unsafe_allow_html=True)

        try:
            # Inicialización del procesador
            if 'chat_processor' not in st.session_state:
                st.session_state.chat_processor = ChatProcessor()
                logger.info("Nuevo ChatProcessor inicializado")

            # Configurar contexto semántico si está activo
            if st.session_state.get('semantic_agent_active', False):
                semantic_data = st.session_state.get('semantic_agent_data')
                if semantic_data and all(k in semantic_data for k in ['text', 'metrics']):
                    try:
                        st.session_state.chat_processor.set_semantic_context(
                            text=semantic_data['text'],
                            metrics=semantic_data['metrics'],
                            graph_data=semantic_data.get('graph_data'),
                            lang_code=lang_code
                        )
                        logger.info("Contexto semántico configurado en el chat")
                    except Exception as e:
                        logger.error(f"Error configurando contexto: {str(e)}")
                        st.error("Error al configurar el análisis. Recargue el documento.")
                        return

            # Interfaz del chat
            with st.expander("💬 Asistente de Análisis", expanded=True):
                # Inicializar historial si no existe
                if 'sidebar_messages' not in st.session_state:
                    initial_msg = {
                        'en': "Hello! Ask me about the semantic analysis.",
                        'es': "¡Hola! Pregúntame sobre el análisis semántico.",
                        'pt': "Olá! Pergunte-me sobre a análise semântica."
                    }.get(lang_code, "Hello!")
                    
                    st.session_state.sidebar_messages = [
                        {"role": "assistant", "content": initial_msg}
                    ]

                # Mostrar historial
                chat_container = st.container()
                with chat_container:
                    for msg in st.session_state.sidebar_messages:
                        st.chat_message(msg["role"]).write(msg["content"])

                # Manejo de mensajes nuevos
                user_input = st.chat_input(
                    {
                        'en': "Ask about the analysis...",
                        'es': "Pregunta sobre el análisis...",
                        'fr': "Question sur l'analyse...",
                        'pt': "Pergunte sobre a análise..."
                    }.get(lang_code, "Message...")
                )

                if user_input:
                    try:
                        # Mostrar mensaje del usuario
                        with chat_container:
                            st.chat_message("user").write(user_input)
                            st.session_state.sidebar_messages.append(
                                {"role": "user", "content": user_input}
                            )
                
                            # Obtener y mostrar respuesta (con limpieza de caracteres)
                            with st.chat_message("assistant"):
                                response_stream = st.session_state.chat_processor.process_chat_input(
                                    user_input, lang_code
                                )
                                
                                # Limpiar el stream de respuesta
                                def clean_response_stream(stream):
                                    for chunk in stream:
                                        yield chunk.replace("▌", "")
                                
                                response = st.write_stream(clean_response_stream(response_stream))
                                
                                # Guardar respuesta limpia
                                clean_response = response.replace("▌", "")
                                st.session_state.sidebar_messages.append(
                                    {"role": "assistant", "content": clean_response}
                                )
                
                        # Guardar en base de datos (con texto limpio)
                        if 'username' in st.session_state:
                            store_chat_history(
                                username=st.session_state.username,
                                messages=st.session_state.sidebar_messages,
                                analysis_type='semantic_analysis',
                                metadata={
                                    'text_sample': st.session_state.semantic_agent_data['text'][:500],
                                    'concepts': st.session_state.semantic_agent_data['metrics']['key_concepts'][:5]
                                }
                            )
                            
                    except Exception as e:
                        logger.error(f"Error en conversación: {str(e)}", exc_info=True)
                        st.error({
                            'en': "Error processing request. Try again.",
                            'es': "Error al procesar. Intente nuevamente.",
                            'fr': "Erreur de traitement. Veuillez réessayer.",
                            'pt': "Erro ao processar. Tente novamente."
                        }.get(lang_code, "Error"))

                # Botón para reiniciar
                if st.button("🔄 Reiniciar Chat"):
                    st.session_state.sidebar_messages = []
                    st.rerun()

        except Exception as e:
            logger.error(f"Error fatal en sidebar_chat: {str(e)}", exc_info=True)
            st.error("System error. Please refresh the page.")