import streamlit as st
import logging
from io import BytesIO
import base64
from .semantic_float_reset import semantic_float_init, float_graph, toggle_float_visibility, update_float_content
from .semantic_process import process_semantic_analysis
from ..chatbot.chatbot import initialize_chatbot, process_semantic_chat_input
from ..database.database_oldFromV2 import (
        initialize_mongodb_connection,
        initialize_database_connections,
        create_admin_user,
        create_student_user,
        get_user,
        get_student_data,
        store_file_contents,
        retrieve_file_contents,
        get_user_files,
        delete_file,
        store_application_request,
        store_user_feedback,
        store_morphosyntax_result,
        store_semantic_result,
        store_discourse_analysis_result,
        store_chat_history,
        export_analysis_and_chat,
        get_user_analysis_summary,
        get_user_recents_chats,
        get_user_analysis_details
    )

from ..utils.widget_utils import generate_unique_key
from .flexible_analysis_handler import FlexibleAnalysisHandler

semantic_float_init()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_translation(t, key, default):
    return t.get(key, default)

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode()
    return f'<img src="data:image/png;base64,{img_str}" />'

def display_semantic_interface(lang_code, nlp_models, t):
    st.set_page_config(layout="wide")

    if 'semantic_chatbot' not in st.session_state:
        st.session_state.semantic_chatbot = initialize_chatbot('semantic')
    if 'semantic_chat_history' not in st.session_state:
        st.session_state.semantic_chat_history = []
    if 'show_graph' not in st.session_state:
        st.session_state.show_graph = False
    if 'graph_id' not in st.session_state:
        st.session_state.graph_id = None

    st.header(t['title'])

    # Opción para introducir texto
    text_input = st.text_area(
        t['text_input_label'],
        height=150,
        placeholder=t['text_input_placeholder'],
    )

    # Opción para cargar archivo
    uploaded_file = st.file_uploader(t['file_uploader'], type=['txt'])

    if st.button(t['analyze_button']):
        if text_input or uploaded_file is not None:
            if uploaded_file:
                text_content = uploaded_file.getvalue().decode('utf-8')
            else:
                text_content = text_input

            # Realizar el análisis
            analysis_result = process_semantic_analysis(text_content, nlp_models[lang_code], lang_code)

            # Guardar el resultado en el estado de la sesión
            st.session_state.semantic_result = analysis_result

            # Mostrar resultados
            display_semantic_results(st.session_state.semantic_result, lang_code, t)

            # Guardar el resultado del análisis
            if store_semantic_result(st.session_state.username, text_content, analysis_result):
                st.success(t['success_message'])
            else:
                st.error(t['error_message'])
        else:
            st.warning(t['warning_message'])

    elif 'semantic_result' in st.session_state:

        # Si hay un resultado guardado, mostrarlo
        display_semantic_results(st.session_state.semantic_result, lang_code, t)

    else:
        st.info(t['initial_message'])  # Asegúrate de que 'initial_message' esté en tus traducciones

def display_semantic_results(result, lang_code, t):
    if result is None:
        st.warning(t['no_results'])  # Asegúrate de que 'no_results' esté en tus traducciones
        return

    # Mostrar conceptos clave
    with st.expander(t['key_concepts'], expanded=True):
        concept_text = " | ".join([f"{concept} ({frequency:.2f})" for concept, frequency in result['key_concepts']])
        st.write(concept_text)

    # Mostrar el gráfico de relaciones conceptuales
    with st.expander(t['conceptual_relations'], expanded=True):
        st.pyplot(result['relations_graph'])
