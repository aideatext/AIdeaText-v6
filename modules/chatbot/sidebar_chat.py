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


# ─── Entry point llamado desde user_page.py ──────────────────────────────────

def display_sidebar_chat(lang_code: str, chatbot_t: dict):
    """
    Tutor Virtual en el sidebar.
    - El contexto semántico se aplica automáticamente cuando el estudiante analiza.
    - El cálculo M1/M2 y el guardado ocurren solo al presionar 'Guardar punto de revisión'.
    """
    if not isinstance(chatbot_t, dict):
        logger.error(f"chatbot_t no es dict, es {type(chatbot_t)}. Usando fallback.")
        chatbot_t = {}

    with st.sidebar:
        st.markdown(
            "<style>.chat-container{max-height:60vh;overflow-y:auto;padding:10px;}</style>",
            unsafe_allow_html=True,
        )

        try:
            # 1. Inicializar procesador
            if 'chat_processor' not in st.session_state:
                st.session_state.chat_processor = ChatProcessor()

            # 2. Sincronizar contexto semántico con el ChatProcessor
            #    Se hace en cada rerun para capturar el análisis más reciente.
            #    Solo resetea la conversación cuando el texto analizado cambia.
            _sync_semantic_context(lang_code)

            # 3. Inicializar historial
            if 'sidebar_messages' not in st.session_state:
                initial_msg = {
                    'en': "Hello! I'm ready to discuss your analysis.",
                    'es': "¡Hola! Estoy listo para discutir tu análisis.",
                    'pt': "Olá! Estou pronto para discutir sua análise.",
                    'fr': "Bonjour! Je suis prêt à discuter de votre analyse.",
                }.get(lang_code, "¡Hola!")
                st.session_state.sidebar_messages = [{"role": "assistant", "content": initial_msg}]

            # 4. Chat UI
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
                            response_stream = st.session_state.chat_processor.process_chat_input(
                                user_input, lang_code
                            )
                            full_response = st.write_stream(response_stream)

                    st.session_state.sidebar_messages.append(
                        {"role": "assistant", "content": full_response}
                    )
                    st.session_state['chat_has_unsaved'] = True
                    st.rerun()

            # 5. Botón de punto de revisión (visible tras el primer turno real)
            n_user_msgs = sum(1 for m in st.session_state.sidebar_messages if m["role"] == "user")

            if n_user_msgs > 0:
                if st.session_state.get('chat_has_unsaved', False):
                    st.caption(chatbot_t.get('unsaved_hint', "💬 Conversación activa — aún no guardada"))

                if st.button(
                    "📊 " + chatbot_t.get('save_checkpoint', "Guardar punto de revisión"),
                    key="btn_checkpoint",
                    type="primary",
                    use_container_width=True,
                ):
                    _compute_and_save_checkpoint(lang_code, chatbot_t)

                # Mostrar último checkpoint
                if st.session_state.get('last_checkpoint'):
                    _display_checkpoint_result(st.session_state['last_checkpoint'], chatbot_t)

            # 6. Botón reiniciar
            if st.button("🔄 " + chatbot_t.get('reset_chat', "Reiniciar"), key="btn_reset_chat"):
                st.session_state.sidebar_messages = []
                st.session_state.pop('last_checkpoint', None)
                st.session_state.pop('chat_has_unsaved', None)
                # Limpiar contexto del processor para forzar resincronización
                st.session_state.chat_processor.semantic_context = None
                st.rerun()

        except Exception as e:
            logger.error(f"Error fatal en sidebar_chat: {e}", exc_info=True)


# ─── Sincronización de contexto ───────────────────────────────────────────────

def _sync_semantic_context(lang_code: str):
    """
    Aplica semantic_agent_data al ChatProcessor cuando hay un análisis activo.
    Solo resetea la conversación si el texto analizado cambió (nuevo análisis).
    """
    agent_data = st.session_state.get('semantic_agent_data')
    processor = st.session_state.chat_processor

    if not agent_data:
        return  # Sin análisis aún — el processor sigue con semantic_context=None

    new_text = agent_data.get('text', '')
    current_full_text = (processor.semantic_context or {}).get('full_text', '')

    if new_text and new_text != current_full_text:
        # Texto nuevo → actualizar contexto (resetea conversación interna del processor)
        try:
            processor.set_semantic_context(
                text=new_text,
                metrics=agent_data.get('metrics', {}),
                graph_data=agent_data.get('graph_data'),
                lang_code=lang_code,
            )
            # Resetear también el historial visible en la UI
            initial_msg = {
                'en': "Hello! I've received your analysis. What would you like to explore?",
                'es': "¡Hola! Recibí tu análisis. ¿Qué quieres explorar?",
                'pt': "Olá! Recebi sua análise. O que gostaria de explorar?",
                'fr': "Bonjour! J'ai reçu votre analyse. Que souhaitez-vous explorer?",
            }.get(lang_code, "¡Hola! Recibí tu análisis.")
            st.session_state.sidebar_messages = [{"role": "assistant", "content": initial_msg}]
            st.session_state.pop('last_checkpoint', None)
            st.session_state.pop('chat_has_unsaved', None)
            logger.info("[sidebar] Contexto semántico sincronizado con nuevo análisis.")
        except Exception as e:
            logger.error(f"[sidebar] Error sincronizando contexto: {e}")


# ─── Checkpoint: cálculo + visualización + guardado ──────────────────────────

def _compute_and_save_checkpoint(lang_code: str, chatbot_t: dict):
    """
    Calcula M1/M2 sobre la conversación completa, genera el grafo híbrido
    con el pipeline NLP correcto (via AnalysisService), y guarda en MongoDB.
    Solo se ejecuta cuando el estudiante presiona el botón.
    """
    nlp_models = st.session_state.get('nlp_models', {})
    nlp_model = nlp_models.get(lang_code)
    if not nlp_model:
        st.warning(chatbot_t.get('nlp_not_ready', "Modelo de lenguaje no disponible."))
        return

    messages = st.session_state.sidebar_messages
    texto_u = " ".join([m["content"] for m in messages if m["role"] == "user"])
    texto_a = " ".join([m["content"] for m in messages if m["role"] == "assistant"])

    if not texto_u.strip():
        st.warning(chatbot_t.get('no_conversation', "No hay conversación para guardar."))
        return

    with st.spinner(chatbot_t.get('computing_checkpoint', "Calculando métricas...")):
        try:
            # Grafo híbrido via AnalysisService (mismo pipeline que el análisis de tesis)
            grafo_bytes, g_interaccion = generate_hybrid_graph_and_object(
                texto_u, texto_a, nlp_models, lang_code
            )

            # Grafo de referencia del texto analizado (G_Escrito)
            g_tesis = (
                st.session_state.get('semantic_agent_data', {})
                .get('metrics', {})
                .get('concept_graph_nx')
            )

            # Métricas
            m1_val = calculate_M1(g_tesis, g_interaccion, nlp_model) if g_tesis else None
            m2_data = calculate_M2(g_interaccion)
            m1_interp = interpret_M1(m1_val if m1_val is not None else 0.0)

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

            st.session_state['last_checkpoint'] = {
                'grafo_bytes': grafo_bytes,
                'm1_val': m1_val,
                'm2_data': m2_data,
                'm1_interp': m1_interp,
                'n_turns': sum(1 for m in messages if m["role"] == "user"),
                'g_tesis_available': g_tesis is not None,
            }
            st.session_state['chat_has_unsaved'] = False

            logger.info(
                f"[checkpoint] M1={m1_val} M2={m2_data.get('M2_density')} "
                f"turns={st.session_state['last_checkpoint']['n_turns']}"
            )
            st.rerun()

        except Exception as e:
            logger.error(f"Error en checkpoint: {e}", exc_info=True)
            st.error(chatbot_t.get('checkpoint_error', f"Error al guardar: {e}"))


def _display_checkpoint_result(cp: dict, chatbot_t: dict):
    """Muestra el resultado del último checkpoint guardado en el sidebar."""
    st.markdown("---")
    st.markdown(f"**{chatbot_t.get('checkpoint_title', '📌 Último punto de revisión')}**")

    # Grafo híbrido
    if cp.get('grafo_bytes'):
        st.image(
            cp['grafo_bytes'],
            width='stretch',
            caption=chatbot_t.get('graph_caption', "🔵 Estudiante · 🟡 Compartido · 🟢 Tutor"),
        )

    # M1
    m1_val = cp.get('m1_val')
    interp = cp.get('m1_interp', {})
    icon_map = {'green': '🟢', 'orange': '🟡', 'red': '🔴', 'gray': '⚪'}
    icon = icon_map.get(interp.get('color', 'gray'), '⚪')

    if not cp.get('g_tesis_available'):
        st.info(chatbot_t.get('m1_no_reference', "M1: analiza un texto primero para calcular coherencia."))
    else:
        m1_display = f"{m1_val:.3f}" if m1_val is not None else "—"
        st.metric(
            label=f"{icon} M1 — {interp.get('level', '')}",
            value=m1_display,
            help=interp.get('message', ''),
        )

    # M2
    m2 = cp.get('m2_data', {})
    col1, col2 = st.columns(2)
    col1.metric("M2 Densidad", f"{m2.get('M2_density', 0.0):.3f}")
    col2.metric("Grado Prom.", f"{m2.get('M2_average_degree', 0.0):.1f}")

    st.caption(
        chatbot_t.get('checkpoint_saved', f"✅ Guardado · {cp.get('n_turns', 0)} turnos")
    )


# ─── Generación del grafo híbrido via AnalysisService ────────────────────────

def generate_hybrid_graph_and_object(
    user_text: str,
    tutor_text: str,
    nlp_models: dict,
    lang_code: str = 'es',
) -> tuple:
    """
    Construye el grafo híbrido estudiante-tutor usando AnalysisService.analyze_text_only().

    Garantía de investigación: MISMO pipeline NLP para todos los inputs del sistema
    (tesis, análisis live, interacción con tutor). Misma limpieza, mismos filtros
    POS (NOUN/PROPN), mismos pesos — las métricas M1/M2 son comparables entre sí.

    Colores del grafo híbrido:
      🔵 #87CEFA — nodos exclusivos del estudiante
      🟡 #FFD700 — nodos compartidos (sincronía semántica)
      🟢 #90EE90 — nodos exclusivos del tutor

    Args:
        user_text:   Concatenación de todos los mensajes del estudiante
        tutor_text:  Concatenación de todas las respuestas del tutor
        nlp_models:  Dict {lang_code: spacy_model} de session_state
        lang_code:   Idioma activo

    Returns:
        (bytes_png, nx.Graph) — imagen del grafo + objeto NX para calcular M1
    """
    from ..services.analysis_service import AnalysisService

    svc = AnalysisService(nlp_models=nlp_models)

    # Pipeline completo para el texto del estudiante (sin persistir)
    res_u = svc.analyze_text_only(user_text, lang_code)
    G_u = res_u.get('concept_graph_nx') or nx.Graph()

    # Pipeline completo para el texto del tutor (sin persistir)
    res_t = svc.analyze_text_only(tutor_text, lang_code)
    G_t = res_t.get('concept_graph_nx') or nx.Graph()

    nodes_u = set(G_u.nodes())
    nodes_t = set(G_t.nodes())

    # Grafo híbrido: unión con color según origen del concepto
    G_hybrid = nx.Graph()

    for node in nodes_u | nodes_t:
        if node in nodes_u and node in nodes_t:
            color = "#FFD700"   # Compartido — sincronía semántica
        elif node in nodes_u:
            color = "#87CEFA"   # Solo estudiante
        else:
            color = "#90EE90"   # Solo tutor
        G_hybrid.add_node(node, color=color)

    # Aristas con pesos combinados
    for u, v, d in G_u.edges(data=True):
        G_hybrid.add_edge(u, v, weight=d.get('weight', 1))
    for u, v, d in G_t.edges(data=True):
        if G_hybrid.has_edge(u, v):
            G_hybrid[u][v]['weight'] += d.get('weight', 1)
        else:
            G_hybrid.add_edge(u, v, weight=d.get('weight', 1))

    # Visualización
    fig = plt.figure(figsize=(5, 4))
    if G_hybrid.number_of_nodes() > 0:
        pos = nx.spring_layout(G_hybrid, k=0.6, seed=42)
        node_colors = [G_hybrid.nodes[n]['color'] for n in G_hybrid.nodes()]
        nx.draw(
            G_hybrid, pos,
            labels={n: n for n in G_hybrid.nodes()},
            with_labels=True,
            node_color=node_colors,
            node_size=700, font_size=7, font_weight='bold',
            edge_color='#CCCCCC', width=1.5,
        )
    else:
        fig.text(0.5, 0.5, 'Sin conceptos extraídos', ha='center', va='center', color='gray')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=120, transparent=True)
    plt.close(fig)

    return buf.getvalue(), G_hybrid
