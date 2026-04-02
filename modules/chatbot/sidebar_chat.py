# modules/chatbot/sidebar_chat.py

import streamlit as st
from .chat_process import ChatProcessor
from ..database.chat_mongo_db import store_chat_history

# Estas son las que necesitan el __init__.py
from ..metrics.m1_m2 import calculate_M1, interpret_M1  # <--- AÑADIR
from ..text_analysis.semantic_analysis import create_concept_graph # <--- AÑADIR
import logging

#Importaciones para grafos 
import io
import networkx as nx
import matplotlib.pyplot as plt

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
            # 1. INICIALIZAR SIEMPRE TODO PRIMERO
            if 'chat_processor' not in st.session_state:
                st.session_state.chat_processor = ChatProcessor()
                logger.info("Nuevo ChatProcessor inicializado")

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
                logger.info("sidebar_messages inicializado")

            # 2. CONFIGURAR CONTEXTO SEMÁNTICO
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

            # 3. AHORA SÍ PUEDES USAR LA VARIABLE SIN MIEDO A ERRORES
            if st.session_state.sidebar_messages:
                if st.button("🏁 Finalizar Sesión y Calcular Coherencia (M1)"):
                    with st.spinner("Analizando consistencia"):
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
            
            # 4. RENDERIZAR EL EXPANDER DE CHAT
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
                            # Obtenemos el NLP del estado o lo cargamos
                            from ..text_analysis.semantic_analysis import nlp 
                            
                            # 1. Generamos el grafo de la interacción actual
                            user_input = prompt # El último mensaje del usuario
                            try:
                                graph_png = generate_hybrid_graph_bytes(user_input, full_response, nlp)
                            except Exception as e:
                                logger.error(f"Error visual: {e}")
                                graph_png = None

                            # 2. Guardamos todo en Mongo
                            store_chat_history(
                                username=st.session_state.username,
                                group_id=st.session_state.get('group_id', 'default'),
                                messages=st.session_state.sidebar_messages,
                                analysis_type='semantic_interaction',
                                metadata={
                                    'visual_graph': graph_png,
                                    'text_sample': user_input[:200]
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

# Nueva función 
def generate_hybrid_graph_bytes(user_text, tutor_text, nlp):
    """Genera la imagen del grafo con estilo Azul/Verde/Oro"""
    plt.figure(figsize=(6, 4))
    G = nx.Graph()
    
    # Extraer conceptos de ambos
    def get_c(t): return {tok.lemma_.lower(): tok.text for tok in nlp(t) 
                          if tok.pos_ in ['NOUN', 'PROPN'] and not tok.is_stop}
    
    c_u = get_c(user_text)
    c_t = get_c(tutor_text)
    all_l = set(c_u.keys()) | set(c_t.keys())
    
    for l in all_l:
        if l in c_u and l in c_t: color = "#FFD700" # Oro
        elif l in c_u: color = "#87CEFA" # Azul
        else: color = "#90EE90" # Verde
        G.add_node(l, label=c_u.get(l, c_t.get(l)), color=color)
    
    # Aristas (co-ocurrencia básica)
    nodes = list(G.nodes())
    for i in range(len(nodes)-1): G.add_edge(nodes[i], nodes[i+1])
    
    pos = nx.spring_layout(G)
    colors = [G.nodes[n]['color'] for n in G.nodes]
    nx.draw(G, pos, with_labels=True, labels=nx.get_node_attributes(G, 'label'),
            node_color=colors, node_size=600, font_size=7, edge_color='#EEEEEE')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    return buf.getvalue()


