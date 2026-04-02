##############
###modules/studentact/student_activities_v2.py

import streamlit as st
import re
import io
import base64
from datetime import datetime, timedelta
import logging

from ..database.semantic_mongo_live_db import get_student_semantic_live_analysis
from ..database.semantic_mongo_db import get_student_semantic_analysis
from ..database.discourse_mongo_db import get_student_discourse_analysis
from ..database.chat_mongo_db import get_chat_history
from ..utils.widget_utils import generate_unique_key

logger = logging.getLogger(__name__)

###################################################################################

def display_student_activities(username: str, lang_code: str, t: dict):
    """Muestra todas las actividades del estudiante ordenadas en sub-pestañas."""
    try:
        tabs = st.tabs([
            t.get('semantic_live_activities', 'Análisis en vivo'),
            t.get('semantic_activities', 'Análisis Semánticos'),
            t.get('discourse_activities', 'Análisis Comparados'),
            t.get('chat_activities', 'Conversaciones con Tutor')
        ])

        with tabs[0]: display_semantic_live_activities(username, t)
        with tabs[1]: display_semantic_activities(username, t)
        with tabs[2]: display_discourse_activities(username, t)
        with tabs[3]: display_chat_activities(username, t)

    except Exception as e:
        logger.error(f"Error mostrando actividades: {str(e)}")
        st.error(t.get('error_loading_activities', 'Error al cargar las actividades'))

###############################################################################################
def display_semantic_live_activities(username: str, t: dict):
    try:
        analyses = get_student_semantic_live_analysis(username)
        if not analyses:
            st.info(t.get('no_semantic_live_analyses', 'No hay análisis semánticos en vivo registrados'))
            return

        for i, analysis in enumerate(analyses):
            ts_raw = analysis.get('timestamp')
            timestamp = ts_raw if isinstance(ts_raw, datetime) else datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00')) if ts_raw else datetime.now()
                
            formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
            unique_id = str(analysis.get('_id', i))
            
            with st.expander(f"{t.get('analysis_date', 'Fecha')}: {formatted_date}", expanded=False):
                st.text_area(
                    t.get('analyzed_text', 'Texto analizado'),
                    value=analysis.get('text', '')[:500],
                    height=150,
                    disabled=True,
                    key=generate_unique_key("sem_live", "text", username, suffix=unique_id)
                )
                
                if analysis.get('concept_graph'):
                    try:
                        graph_data = analysis['concept_graph']
                        image_to_show = None # <--- SOLUCIÓN AL ERROR DE VARIABLE LOCAL
                        
                        if isinstance(graph_data, bytes):
                            image_to_show = graph_data
                        elif isinstance(graph_data, str):
                            image_to_show = base64.b64decode(graph_data)
                        
                        if image_to_show:
                            st.image(image_to_show, caption=t.get('concept_network', 'Red de Conceptos'), use_container_width=True)
                    except Exception as img_error:
                        logger.error(f"Error procesando gráfico: {str(img_error)}")
                        st.error(t.get('error_loading_graph', 'Error al cargar el gráfico'))

    except Exception as e:
        logger.error(f"Error general en semantic live: {str(e)}")

###############################################################################################
def display_semantic_activities(username: str, t: dict):
    try:
        analyses = get_student_semantic_analysis(username)
        if not analyses:
            st.info(t.get('no_semantic_analyses', 'No hay análisis semánticos registrados'))
            return

        for i, analysis in enumerate(analyses):
            if not all(key in analysis for key in ['timestamp', 'concept_graph']): continue
            
            ts_raw = analysis['timestamp']
            timestamp = ts_raw if isinstance(ts_raw, datetime) else datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00'))
            
            with st.expander(f"{t.get('analysis_date', 'Fecha')}: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}", expanded=False):
                if analysis.get('concept_graph'):
                    try:
                        image_data = analysis['concept_graph']
                        image_bytes = image_data if isinstance(image_data, bytes) else base64.b64decode(image_data)
                        st.image(image_bytes, caption=t.get('concept_network', 'Red de Conceptos'), width='stretch')
                    except Exception as img_error:
                        st.error(t.get('error_loading_graph', 'Error al cargar el gráfico'))
                else:
                    st.info(t.get('no_graph', 'No hay visualización disponible'))
    except Exception as e:
        logger.error(f"Error en semantic activities: {str(e)}")

###################################################################################################
def display_discourse_activities(username: str, t: dict):
    try:
        analyses = get_student_discourse_analysis(username)
        if not analyses:
            st.info(t.get('no_discourse_analyses', 'No hay análisis comparados registrados'))
            return

        for i, analysis in enumerate(analyses):
            if 'timestamp' not in analysis: continue
            ts_raw = analysis['timestamp']
            timestamp = ts_raw if isinstance(ts_raw, datetime) else datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00'))
            
            with st.expander(f"{t.get('analysis_date', 'Fecha')}: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(t.get('doc1_title', 'Documento 1'))
                    if 'key_concepts1' in analysis and analysis['key_concepts1']:
                        st.write(", ".join([f"{c[0]} ({c[1]:.2f})" for c in analysis['key_concepts1'][:10]]))
                    if analysis.get('graph1'):
                        st.image(analysis['graph1'], width='stretch')

                with col2:
                    st.subheader(t.get('doc2_title', 'Documento 2'))
                    if 'key_concepts2' in analysis and analysis['key_concepts2']:
                        st.write(", ".join([f"{c[0]} ({c[1]:.2f})" for c in analysis['key_concepts2'][:10]]))
                    if analysis.get('graph2'):
                        st.image(analysis['graph2'], width='stretch')
    except Exception as e:
        logger.error(f"Error en discourse activities: {str(e)}")

#################################################################################   
def clean_chat_content(content: str) -> str:
    if not content: return content
    for char in ["▌", "\u2588", "\u2580", "\u2584", "\u258C", "\u2590"]:
        content = content.replace(char, "")
    return re.sub(r'\s+', ' ', content).strip()

#################################################################################   
def display_chat_activities(username: str, t: dict):
    """Muestra historial de conversaciones y SUS GRAFOS HÍBRIDOS"""
    try:
        chat_history = get_chat_history(username=username, limit=50)
        
        if not chat_history:
            st.info(t.get('no_chat_history', 'No hay conversaciones registradas'))
            return

        for i, chat in enumerate(chat_history):
            ts_raw = chat.get('timestamp')
            timestamp = ts_raw if isinstance(ts_raw, datetime) else datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00')) if ts_raw else datetime.now()
            
            with st.expander(f"💬 Conversación: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}", expanded=False):
                # 1. MOSTRAR EL GRAFO HÍBRIDO SI EXISTE (El que tiene nodos Oro/Verde/Azul)
                if chat.get('visual_graph'):
                    st.markdown("**Sincronía Conceptual de la Sesión**")
                    try:
                        graph_data = chat['visual_graph']
                        image_bytes = graph_data if isinstance(graph_data, bytes) else base64.b64decode(graph_data)
                        st.image(image_bytes, use_container_width=True)
                        st.divider()
                    except Exception as e:
                        logger.error(f"Error renderizando grafo de chat: {e}")

                # 2. MOSTRAR LOS MENSAJES
                if 'messages' in chat and chat['messages']:
                    for msg_idx, message in enumerate(chat['messages']):
                        role = message.get('role', 'unknown')
                        content = clean_chat_content(str(message.get('content', '')))
                        
                        with st.chat_message(role):
                            st.markdown(content)
                        if msg_idx < len(chat['messages']) - 1:
                            st.divider()
                else:
                    st.warning("Historial vacío para esta sesión.")
                    
    except Exception as e:
        logger.error(f"Error mostrando historial del chat: {str(e)}")
        st.error(t.get('error_chat', 'Error al mostrar historial del chat'))