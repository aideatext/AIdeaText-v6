# modules/chatbot/sidebar_chat.py

import streamlit as st
import logging
import io
import networkx as nx
import matplotlib.pyplot as plt
from .chat_process import ChatProcessor
from ..database.chat_mongo_db import store_chat_history
# Importamos el motor de métricas que revisamos
from ..metrics.m1_m2 import calculate_M1, calculate_M2, interpret_M1 

logger = logging.getLogger(__name__)

def display_sidebar_chat(lang_code: str, chatbot_t: dict):
    """Chatbot con motor de métricas M1/M2 integrado"""
    # --- VALIDACIÓN ANTICRASHEO ---
    if not isinstance(chatbot_t, dict):
        logger.error(f"chatbot_t no es dict, es {type(chatbot_t)}. Usando fallback.")
        chatbot_t = {} 
    # ------------------------------
    with st.sidebar:
        st.markdown("""<style>.chat-container { max-height: 60vh; overflow-y: auto; padding: 10px; }</style>""", unsafe_allow_html=True)

        try:
            # 1. Inicialización
            if 'chat_processor' not in st.session_state:
                st.session_state.chat_processor = ChatProcessor()
            
            if 'sidebar_messages' not in st.session_state:
                initial_msg = {'en': "Hello!", 'es': "¡Hola!", 'pt': "Olá!", 'fr': "Bonjour!"}.get(lang_code, "Hola!")
                st.session_state.sidebar_messages = [{"role": "assistant", "content": initial_msg}]

            # 2. Renderizado del Chat
            with st.expander("💬 " + chatbot_t.get('assistant_title', "Asistente"), expanded=True):
                chat_container = st.container()
                with chat_container:
                    for msg in st.session_state.sidebar_messages:
                        st.chat_message(msg["role"]).write(msg["content"])

                user_input = st.chat_input(chatbot_t.get('input_placeholder', "Escribe..."))

                if user_input:
                    # A. Usuario
                    st.session_state.sidebar_messages.append({"role": "user", "content": user_input})
                    with chat_container: st.chat_message("user").write(user_input)
                
                    # B. Assistant (Stream)
                    with chat_container:
                        with st.chat_message("assistant"):
                            response_stream = st.session_state.chat_processor.process_chat_input(user_input, lang_code)
                            full_response = st.write_stream(response_stream)
                    
                    st.session_state.sidebar_messages.append({"role": "assistant", "content": full_response})

                    # C. CÁLCULO DE MÉTRICAS Y GUARDADO
                    try:
                        texto_u = " ".join([m["content"] for m in st.session_state.sidebar_messages if m["role"] == "user"])
                        texto_a = " ".join([m["content"] for m in st.session_state.sidebar_messages if m["role"] == "assistant"])
                        nlp_model = st.session_state.get('nlp_models', {}).get(lang_code)

                        if nlp_model:
                            # Obtenemos AMBOS: la imagen y el objeto Graph
                            grafo_bytes, g_interaccion = generate_hybrid_graph_and_object(texto_u, texto_a, nlp_model)
                            
                            # Recuperamos el grafo de la tesis/texto base (G1)
                            # semantic_process.py guarda el grafo bajo 'metrics'.'concept_graph_nx'
                            g_tesis = (
                                st.session_state.get('semantic_agent_data', {})
                                .get('metrics', {})
                                .get('concept_graph_nx')
                            )
                            
                            # Calculamos M1 (Coherencia Transmodal) y M2 (Robustez)
                            m1_val = calculate_M1(g_tesis, g_interaccion) if g_tesis else 0.0
                            m2_data = calculate_M2(g_interaccion)
                            
                            # Guardamos en Mongo con la estructura que espera metrics_processor.py
                            store_chat_history(
                                username=st.session_state.username,
                                group_id=st.session_state.get('class_id', 'GENERAL'),
                                messages=st.session_state.sidebar_messages,
                                analysis_type='chat_interaction',
                                metadata={
                                    'visual_graph': grafo_bytes,
                                    'm1_score': m1_val,
                                    'm2_score': m2_data.get('M2_density', 0.0),
                                    'avg_degree': m2_data.get('M2_avg_degree', 0.0)
                                },
                                lang_code=lang_code
                            )
                            logger.info(f"📊 Métrica M1 calculada: {m1_val:.4f}")
                        
                        st.rerun()

                    except Exception as e:
                        logger.error(f"Error calculando métricas: {e}")

                if st.button("🔄 " + chatbot_t.get('reset_chat', "Reiniciar")):
                    st.session_state.sidebar_messages = []
                    st.rerun()

        except Exception as e:
            logger.error(f"Error fatal: {e}")

def generate_hybrid_graph_and_object(user_text, tutor_text, nlp):
    """Retorna (bytes_png, nx_graph_object)"""
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
            color, label = "#FFD700", c_u[lemma] # ORO (Sincronía)
        elif lemma in c_u:
            color, label = "#87CEFA", c_u[lemma] # AZUL (Estudiante)
        else:
            color, label = "#90EE90", c_t[lemma] # VERDE (Tutor)
        G.add_node(lemma, label=label, color=color)

    # Estructura del grafo
    nodes = list(G.nodes())
    if len(nodes) > 1:
        for i in range(len(nodes)-1):
            G.add_edge(nodes[i], nodes[i+1])

    # Generar Imagen
    fig = plt.figure(figsize=(5, 4))
    pos = nx.spring_layout(G, k=0.5, seed=42)
    nx.draw(G, pos, labels=nx.get_node_attributes(G, 'label'), with_labels=True,
            node_color=[G.nodes[n]['color'] for n in G.nodes],
            node_size=800, font_size=8, font_weight='bold', edge_color='#DDDDDD')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120, transparent=True)
    plt.close(fig)
    
    return buf.getvalue(), G