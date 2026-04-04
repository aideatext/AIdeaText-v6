# modules/chatbot/sidebar_chat.py

import streamlit as st
import logging
import io
import networkx as nx
import matplotlib.pyplot as plt
from .chat_process import ChatProcessor
from ..database.chat_mongo_db import store_chat_history
from ..metrics.m1_m2 import calculate_M1, calculate_M2, interpret_M1

logger = logging.getLogger(__name__)


def display_sidebar_chat(lang_code: str, chatbot_t: dict):
    """
    Chatbot con motor de métricas M1/M2.
    El cálculo, visualización y guardado ocurren cuando el estudiante
    presiona explícitamente el botón 'Guardar punto de revisión'.
    """
    if not isinstance(chatbot_t, dict):
        logger.error(f"chatbot_t no es dict, es {type(chatbot_t)}. Usando fallback.")
        chatbot_t = {}

    with st.sidebar:
        st.markdown("""<style>.chat-container { max-height: 60vh; overflow-y: auto; padding: 10px; }</style>""",
                    unsafe_allow_html=True)

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
                    # A. Mensaje del usuario
                    st.session_state.sidebar_messages.append({"role": "user", "content": user_input})
                    with chat_container:
                        st.chat_message("user").write(user_input)

                    # B. Respuesta del asistente (streaming)
                    with chat_container:
                        with st.chat_message("assistant"):
                            response_stream = st.session_state.chat_processor.process_chat_input(user_input, lang_code)
                            full_response = st.write_stream(response_stream)

                    st.session_state.sidebar_messages.append({"role": "assistant", "content": full_response})
                    # Marcar que hay conversación nueva sin guardar
                    st.session_state['chat_has_unsaved'] = True
                    st.rerun()

            # 3. BOTÓN DE PUNTO DE REVISIÓN
            # Solo visible cuando hay al menos un intercambio real (más del saludo inicial)
            n_user_msgs = sum(1 for m in st.session_state.sidebar_messages if m["role"] == "user")

            if n_user_msgs > 0:
                # Indicador visual de estado
                if st.session_state.get('chat_has_unsaved', False):
                    st.caption(chatbot_t.get('unsaved_hint', "💬 Conversación activa — aún no guardada"))

                if st.button(
                    "📊 " + chatbot_t.get('save_checkpoint', "Guardar punto de revisión"),
                    key="btn_checkpoint",
                    type="primary",
                    use_container_width=True,
                ):
                    _compute_and_save_checkpoint(lang_code, chatbot_t)

                # Mostrar último checkpoint guardado (si existe)
                if st.session_state.get('last_checkpoint'):
                    _display_checkpoint_result(st.session_state['last_checkpoint'], chatbot_t)

            # 4. Botón de reinicio
            if st.button("🔄 " + chatbot_t.get('reset_chat', "Reiniciar"), key="btn_reset_chat"):
                st.session_state.sidebar_messages = []
                st.session_state.pop('last_checkpoint', None)
                st.session_state.pop('chat_has_unsaved', None)
                st.rerun()

        except Exception as e:
            logger.error(f"Error fatal en sidebar_chat: {e}")


# ─── Lógica del checkpoint ────────────────────────────────────────────────────

def _compute_and_save_checkpoint(lang_code: str, chatbot_t: dict):
    """
    Calcula M1/M2, genera el grafo híbrido, muestra resultados y guarda en MongoDB.
    Se llama solo cuando el estudiante presiona el botón.
    """
    nlp_model = st.session_state.get('nlp_models', {}).get(lang_code)
    if not nlp_model:
        st.warning(chatbot_t.get('nlp_not_ready', "Modelo de lenguaje no disponible aún."))
        return

    messages = st.session_state.sidebar_messages
    texto_u = " ".join([m["content"] for m in messages if m["role"] == "user"])
    texto_a = " ".join([m["content"] for m in messages if m["role"] == "assistant"])

    if not texto_u.strip():
        st.warning(chatbot_t.get('no_conversation', "No hay conversación para guardar."))
        return

    with st.spinner(chatbot_t.get('computing_checkpoint', "Calculando métricas...")):
        try:
            # Grafo híbrido de la interacción (estudiante + tutor)
            grafo_bytes, g_interaccion = generate_hybrid_graph_and_object(texto_u, texto_a, nlp_model)

            # Grafo de referencia del texto analizado (G_Escrito)
            g_tesis = (
                st.session_state.get('semantic_agent_data', {})
                .get('metrics', {})
                .get('concept_graph_nx')
            )

            # Métricas
            m1_val = calculate_M1(g_tesis, g_interaccion, nlp_model) if g_tesis else None
            m2_data = calculate_M2(g_interaccion)
            m1_interpretation = interpret_M1(m1_val if m1_val is not None else 0.0)

            # Guardar en MongoDB
            store_chat_history(
                username=st.session_state.username,
                group_id=st.session_state.get('class_id', 'GENERAL'),
                messages=messages,
                analysis_type='chat_interaction',
                metadata={
                    'visual_graph': grafo_bytes,
                    'm1_score': float(m1_val) if m1_val is not None else 0.0,
                    'm2_score': m2_data.get('M2_density', 0.0),
                    'avg_degree': m2_data.get('M2_average_degree', 0.0),
                },
                lang_code=lang_code,
            )

            # Guardar en session_state para mostrar sin recalcular
            st.session_state['last_checkpoint'] = {
                'grafo_bytes': grafo_bytes,
                'm1_val': m1_val,
                'm2_data': m2_data,
                'm1_interpretation': m1_interpretation,
                'n_turns': sum(1 for m in messages if m["role"] == "user"),
                'g_tesis_available': g_tesis is not None,
            }
            st.session_state['chat_has_unsaved'] = False

            logger.info(f"[checkpoint] M1={m1_val} M2={m2_data.get('M2_density')} turns={st.session_state['last_checkpoint']['n_turns']}")
            st.rerun()

        except Exception as e:
            logger.error(f"Error en checkpoint: {e}")
            st.error(chatbot_t.get('checkpoint_error', f"Error al guardar: {e}"))


def _display_checkpoint_result(cp: dict, chatbot_t: dict):
    """Muestra el resultado del último checkpoint guardado."""
    st.markdown("---")
    st.markdown(f"**{chatbot_t.get('checkpoint_title', '📌 Último punto de revisión')}**")

    # Grafo híbrido
    if cp.get('grafo_bytes'):
        st.image(cp['grafo_bytes'], use_container_width=True,
                 caption=chatbot_t.get('graph_caption',
                                       "🔵 Estudiante · 🟡 Compartido · 🟢 Tutor"))

    # M1
    m1_val = cp.get('m1_val')
    interp = cp.get('m1_interpretation', {})
    color_map = {'green': '🟢', 'orange': '🟡', 'red': '🔴', 'gray': '⚪'}
    icon = color_map.get(interp.get('color', 'gray'), '⚪')

    if not cp.get('g_tesis_available'):
        st.info(chatbot_t.get('m1_no_reference',
                              "M1: sin texto de referencia analizado aún."))
    else:
        m1_display = f"{m1_val:.3f}" if m1_val is not None else "—"
        st.metric(
            label=f"{icon} M1 — {interp.get('level', '')}",
            value=m1_display,
            help=interp.get('message', '')
        )

    # M2
    m2 = cp.get('m2_data', {})
    col1, col2 = st.columns(2)
    col1.metric("M2 Densidad", f"{m2.get('M2_density', 0.0):.3f}")
    col2.metric("Grado Prom.", f"{m2.get('M2_average_degree', 0.0):.1f}")

    st.caption(chatbot_t.get('checkpoint_saved',
                             f"✅ Guardado · {cp.get('n_turns', 0)} turnos"))


# ─── Generación del grafo híbrido ────────────────────────────────────────────

def generate_hybrid_graph_and_object(user_text, tutor_text, nlp):
    """Retorna (bytes_png, nx_graph_object) del grafo híbrido estudiante-tutor."""
    G = nx.Graph()

    def get_lemmas(text):
        doc = nlp(text)
        return {t.lemma_.lower(): t.text for t in doc if t.pos_ in ['NOUN', 'PROPN'] and not t.is_stop}

    c_u = get_lemmas(user_text)
    c_t = get_lemmas(tutor_text)
    all_l = set(c_u.keys()) | set(c_t.keys())

    for lemma in all_l:
        if lemma in c_u and lemma in c_t:
            color, label = "#FFD700", c_u[lemma]   # ORO  — Sincronía
        elif lemma in c_u:
            color, label = "#87CEFA", c_u[lemma]   # AZUL — Estudiante
        else:
            color, label = "#90EE90", c_t[lemma]   # VERDE — Tutor
        G.add_node(lemma, label=label, color=color)

    nodes = list(G.nodes())
    if len(nodes) > 1:
        for i in range(len(nodes) - 1):
            G.add_edge(nodes[i], nodes[i + 1])

    fig = plt.figure(figsize=(5, 4))
    pos = nx.spring_layout(G, k=0.5, seed=42)
    nx.draw(G, pos,
            labels=nx.get_node_attributes(G, 'label'),
            with_labels=True,
            node_color=[G.nodes[n]['color'] for n in G.nodes],
            node_size=800, font_size=8, font_weight='bold', edge_color='#DDDDDD')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120, transparent=True)
    plt.close(fig)

    return buf.getvalue(), G
