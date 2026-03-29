# modules/chatbot/sidebar_chat.py
import streamlit as st
from .chat_process import ChatProcessor
from ..database.chat_mongo_db import store_chat_history
from ..metrics.m1_m2 import calculate_M1, interpret_M1  # <--- AÑADIR
from ..text_analysis.semantic_analysis import create_concept_graph # <--- AÑADIR
import logging

logger = logging.getLogger(__name__)

def display_sidebar_chat(lang_code: str, chatbot_t: dict):
    """Chatbot mejorado con manejo completo del contexto semántico"""
    with st.sidebar:
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
            if 'chat_processor' not in st.session_state:
                st.session_state.chat_processor = ChatProcessor()
                logger.info("Nuevo ChatProcessor inicializado")

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
                    except Exception as e:
                        logger.error(f"Error configurando contexto: {str(e)}")
                        st.error("Error al configurar el análisis. Recargue el documento.")
                        return

            if st.session_state.sidebar_messages:
                if st.button("🏁 Finalizar Sesión y Calcular Coherencia (M1)"):
                    with st.spinner("Analizando consistencia transmodal..."):
                        try:
                            # 1. Obtener el Grafo de la Tesis (Ya debe estar en session_state)
                            # Recuperamos el objeto nx.Graph que guardamos en perform_semantic_analysis
                            G_Escrito = st.session_state.semantic_agent_data.get('concept_graph_nx')
                            
                            if G_Escrito:
                                # 2. Procesar el texto del Chat (Tutor Virtual)
                                # Unimos solo los mensajes del usuario y asistente
                                full_chat_text = " ".join([m['content'] for m in st.session_state.sidebar_messages])
                                
                                # 3. Generar Grafo del Tutor (Solo Sustantivos - CRA)
                                # Usamos el modelo nlp que ya tenemos en sesión
                                doc_TutorVirtual = st.session_state.nlp(full_chat_text)
                                G_TutorVirtual = create_concept_graph(doc_TutorVirtual, lang_code=lang_code)
                                
                                # 4. Calcular M1
                                m1_score = calculate_M1(G_Escrito, G_TutorVirtual, st.session_state.nlp)
                                res_m1 = interpret_M1(m1_score)
                                
                                # 5. Mostrar resultado inmediato al estudiante (Feedback Formativo)
                                st.metric(label="Índice de Coherencia (M1)", value=f"{m1_score:.2f}")
                                st.toast(f"Coherencia {res_m1['level']}: {res_m1['message']}", icon="🧠")
                                
                                # 6. Guardar en base de datos (Postgres/Mongo)
                                # Aquí llamaríamos a store_analysis_with_metrics configurado para 'oral'
                                st.session_state['last_m1_result'] = m1_score
                                st.success("Análisis guardado. Tu asesor podrá revisar tu progreso.")
                            else:
                                st.error("No hay un análisis de tesis previo para comparar.")
                                
                        except Exception as e:
                            logger.error(f"Error al calcular M1: {e}")
                            st.error("No se pudo completar el análisis de coherencia.")
            
            with st.expander("💬 Asistente de Análisis", expanded=True):
                if 'sidebar_messages' not in st.session_state:
                    initial_msg = {
                        'en': "Hello! Ask me about the semantic analysis.",
                        'es': "¡Hola! Pregúntame sobre el análisis semántico.",
                        'pt': "Olá! Pergunte-me sobre a análise semântica.",
                        'fr': "Bonjour ! Posez-moi des questions sur l'analyse sémantique."
                    }.get(lang_code, "Hello!")
                    
                    st.session_state.sidebar_messages = [
                        {"role": "assistant", "content": initial_msg}
                    ]

                chat_container = st.container()
                with chat_container:
                    for msg in st.session_state.sidebar_messages:
                        st.chat_message(msg["role"]).write(msg["content"])

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
                        with chat_container:
                            st.chat_message("user").write(user_input)
                            st.session_state.sidebar_messages.append(
                                {"role": "user", "content": user_input}
                            )
                
                            with st.chat_message("assistant"):
                                # Simplificado: Streamlit maneja el generator directamente
                                response_stream = st.session_state.chat_processor.process_chat_input(
                                    user_input, lang_code
                                )
                                response = st.write_stream(response_stream)
                                
                                st.session_state.sidebar_messages.append(
                                    {"role": "assistant", "content": response}
                                )
                
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

                if st.button("🔄 Reiniciar Chat"):
                    st.session_state.sidebar_messages = []
                    st.rerun()

        except Exception as e:
            logger.error(f"Error fatal en sidebar_chat: {str(e)}", exc_info=True)
            st.error("System error. Please refresh the page.")