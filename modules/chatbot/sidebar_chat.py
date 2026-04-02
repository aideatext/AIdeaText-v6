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

######
# modules/chatbot/sidebar_chat.py

def display_sidebar_chat(lang_code: str, chatbot_t: dict):
    """Chatbot optimizado: Genera y guarda el grafo híbrido en cada mensaje"""
    with st.sidebar:
        st.markdown("""<style>.chat-container { max-height: 60vh; overflow-y: auto; padding: 10px; }</style>""", unsafe_allow_html=True)

        try:
            # 1. Inicialización de componentes
            if 'chat_processor' not in st.session_state:
                st.session_state.chat_processor = ChatProcessor()
            
            if 'sidebar_messages' not in st.session_state:
                initial_msg = {'en': "Hello!", 'es': "¡Hola!", 'pt': "Olá!", 'fr': "Bonjour!"}.get(lang_code, "Hola!")
                st.session_state.sidebar_messages = [{"role": "assistant", "content": initial_msg}]

            # 2. Validación de Contexto Semántico (Evita el mensaje de error "Contexto no configurado")
            semantic_ready = False
            if st.session_state.get('semantic_agent_active', False):
                semantic_data = st.session_state.get('semantic_agent_data')
                if semantic_data and 'metrics' in semantic_data:
                    try:
                        st.session_state.chat_processor.set_semantic_context(
                            text=semantic_data['text'],
                            metrics=semantic_data['metrics'],
                            graph_data=semantic_data.get('graph_data'),
                            lang_code=lang_code
                        )
                        semantic_ready = True
                    except Exception as e:
                        logger.error(f"Error en contexto: {e}")

            # 3. Botón de Finalización (M1)
            if semantic_ready:
                if st.button("🏁 Finalizar Sesión y Calcular Coherencia (M1)"):
                    # ... (Tu lógica de M1 se mantiene igual)
                    pass

            # 4. Renderizado y Lógica del Chat
            with st.expander("💬 Asistente de Análisis", expanded=True):
                chat_container = st.container()
                with chat_container:
                    for msg in st.session_state.sidebar_messages:
                        st.chat_message(msg["role"]).write(msg["content"])

                user_input = st.chat_input("Escribe aquí...")

                if user_input:
                    with chat_container:
                        st.chat_message("user").write(user_input)
                        st.session_state.sidebar_messages.append({"role": "user", "content": user_input})
                
                        with st.chat_message("assistant"):
                            # Usamos write_stream para capturar la respuesta completa
                            response_stream = st.session_state.chat_processor.process_chat_input(user_input, lang_code)
                            full_response = st.write_stream(response_stream)
                            
                            st.session_state.sidebar_messages.append({"role": "assistant", "content": full_response})

                    # --- CRÍTICO: GUARDADO POST-INTERACCIÓN ---
                    if 'username' in st.session_state:
                        try:
                            # Importamos la función que definimos antes
                            # from ..text_analysis.semantic_analysis import generate_hybrid_graph_bytes
                            
                            # Recuperamos el modelo NLP que cargaste en el arranque de la app
                            nlp_model = st.session_state.get('nlp_models', {}).get(lang_code)
                            
                            # Generar el grafo híbrido
                            graph_png = None
                            if nlp_model:
                                graph_png = generate_hybrid_graph_bytes(user_input, full_response, nlp_model)
                            
                            # Guardar en Mongo (con el metadata del grafo)
                            store_chat_history(
                                username=st.session_state.username,
                                group_id=st.session_state.get('group_id', 'default'),
                                messages=st.session_state.sidebar_messages,
                                analysis_type='semantic_interaction',
                                metadata={
                                    'visual_graph': graph_png, # <--- El grafo ahora sí se guarda
                                    'text_sample': user_input[:200]
                                }
                            )
                            logger.info(f"✅ Chat y Grafo guardados para {st.session_state.username}")
                            
                        except Exception as e:
                            logger.error(f"Error en persistencia: {e}")

                if st.button("🔄 Reiniciar Chat"):
                    st.session_state.sidebar_messages = []
                    st.rerun()

        except Exception as e:
            logger.error(f"Error fatal: {e}")
            st.error("Error del sistema. Recargue la página.")

# Nueva función 
def generate_hybrid_graph_bytes(user_text, tutor_text, nlp):
    """
    Versión optimizada para la App del generador de grafos híbridos.
    Usa los mismos colores que definiste en tu script de población.
    """
    # Limpiar figuras previas para evitar superposiciones en el servidor
    plt.clf()
    G = nx.Graph()

    def get_lemmas(text):
        doc = nlp(text)
        return {t.lemma_.lower(): t.text for t in doc if t.pos_ in ['NOUN', 'PROPN'] and not t.is_stop}

    c_u = get_lemmas(user_text)
    c_t = get_lemmas(tutor_text)
    all_l = set(c_u.keys()) | set(c_t.keys())

    for lemma in all_l:
        if lemma in c_u and lemma in c_t:
            color, label = "#FFD700", c_u[lemma] # ORO
        elif lemma in c_u:
            color, label = "#87CEFA", c_u[lemma] # AZUL
        else:
            color, label = "#90EE90", c_t[lemma] # VERDE
        G.add_node(lemma, label=label, color=color)

    # Conexiones mínimas para visualización
    nodes = list(G.nodes())
    for i in range(len(nodes)-1):
        G.add_edge(nodes[i], nodes[i+1])

    pos = nx.spring_layout(G, k=0.6)
    nx.draw(G, pos, with_labels=True, 
            labels=nx.get_node_attributes(G, 'label'),
            node_color=[G.nodes[n]['color'] for n in G.nodes],
            node_size=700, font_size=7, edge_color='#EEEEEE')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close()
    return buf.getvalue()