import streamlit as st
import logging
from .semantic_process import process_semantic_analysis
from ..chatbot.chatbot import initialize_chatbot, process_semantic_chat_input
from ..database.database_oldFromV2 import store_file_semantic_contents, retrieve_file_contents, delete_file, get_user_files
from ..utils.widget_utils import generate_unique_key

logger = logging.getLogger(__name__)

def get_translation(t, key, default):
    return t.get(key, default)

def display_semantic_interface(lang_code, nlp_models, t):
    st.markdown("""
        <style>
        .semantic-initial-message {
            background-color: #f0f2f6;
            border-left: 5px solid #4CAF50;
            padding: 10px;
            border-radius: 5px;
            font-size: 16px;
            margin-bottom: 20px;
        }
        .stButton > button {
            width: 100%;
            height: 3em;
        }
        .chat-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
        }
        .file-management-container, .analysis-container {
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .horizontal-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .graph-container {
            height: 500px;
            overflow-y: auto;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="semantic-initial-message">
        {get_translation(t, 'semantic_initial_message', 'Welcome to the semantic analysis interface.')}
        </div>
    """, unsafe_allow_html=True)

    if 'semantic_chatbot' not in st.session_state:
        st.session_state.semantic_chatbot = initialize_chatbot('semantic')

    # Contenedor para la gestión de archivos
    with st.container():
        st.markdown('<div class="file-management-container">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            uploaded_file = st.file_uploader(get_translation(t, 'upload_file', 'Upload File'), type=['txt', 'pdf', 'docx', 'doc', 'odt'], key=generate_unique_key('semantic', 'file_uploader'))
            if uploaded_file is not None:
                file_contents = uploaded_file.getvalue().decode('utf-8')
                if store_file_semantic_contents(st.session_state.username, uploaded_file.name, file_contents):
                    st.session_state.file_contents = file_contents
                    st.success(get_translation(t, 'file_uploaded_success', 'File uploaded and saved successfully'))
                    st.rerun()
                else:
                    st.error(get_translation(t, 'file_upload_error', 'Error uploading file'))

        with col2:
            user_files = get_user_files(st.session_state.username, 'semantic')
            file_options = [get_translation(t, 'select_saved_file', 'Select a saved file')] + [file['file_name'] for file in user_files]
            selected_file = st.selectbox("", options=file_options, key=generate_unique_key('semantic', 'file_selector'))
            if selected_file and selected_file != get_translation(t, 'select_saved_file', 'Select a saved file'):
                file_contents = retrieve_file_contents(st.session_state.username, selected_file, 'semantic')
                if file_contents:
                    st.session_state.file_contents = file_contents
                    st.success(get_translation(t, 'file_loaded_success', 'File loaded successfully'))
                else:
                    st.error(get_translation(t, 'file_load_error', 'Error loading file'))

        with col3:
            if st.button(get_translation(t, 'analyze_document', 'Analyze Document'), key=generate_unique_key('semantic', 'analyze_document')):
                if 'file_contents' in st.session_state:
                    with st.spinner(get_translation(t, 'analyzing', 'Analyzing...')):
                        try:
                            nlp_model = nlp_models[lang_code]
                            concept_graph, entity_graph, key_concepts = process_semantic_analysis(st.session_state.file_contents, nlp_model, lang_code)
                            st.session_state.concept_graph = concept_graph
                            st.session_state.entity_graph = entity_graph
                            st.session_state.key_concepts = key_concepts
                            st.success(get_translation(t, 'analysis_completed', 'Analysis completed'))
                        except Exception as e:
                            logger.error(f"Error during analysis: {str(e)}")
                            st.error(f"Error during analysis: {str(e)}")
                else:
                    st.error(get_translation(t, 'no_file_uploaded', 'No file uploaded'))

        with col4:
            if st.button(get_translation(t, 'delete_file', 'Delete File'), key=generate_unique_key('semantic', 'delete_file')):
                if selected_file and selected_file != get_translation(t, 'select_saved_file', 'Select a saved file'):
                    if delete_file(st.session_state.username, selected_file, 'semantic'):
                        st.success(get_translation(t, 'file_deleted_success', 'File deleted successfully'))
                        if 'file_contents' in st.session_state:
                            del st.session_state.file_contents
                        st.rerun()
                    else:
                        st.error(get_translation(t, 'file_delete_error', 'Error deleting file'))
                else:
                    st.error(get_translation(t, 'no_file_selected', 'No file selected'))

        st.markdown('</div>', unsafe_allow_html=True)

    # Contenedor para la sección de análisis
    st.markdown('<div class="analysis-container">', unsafe_allow_html=True)
    col_chat, col_graph = st.columns([1, 1])

    with col_chat:
        st.subheader(get_translation(t, 'chat_title', 'Semantic Analysis Chat'))
        chat_container = st.container()

        with chat_container:
            chat_history = st.session_state.get('semantic_chat_history', [])
            for message in chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        user_input = st.chat_input(get_translation(t, 'semantic_chat_input', 'Type your message here...'), key=generate_unique_key('semantic', 'chat_input'))

        if user_input:
            chat_history.append({"role": "user", "content": user_input})

            if user_input.startswith('/analyze_current'):
                response = process_semantic_chat_input(user_input, lang_code, nlp_models[lang_code], st.session_state.get('file_contents', ''))
            else:
                response = st.session_state.semantic_chatbot.generate_response(user_input, lang_code)

            chat_history.append({"role": "assistant", "content": response})
            st.session_state.semantic_chat_history = chat_history

    with col_graph:
        st.subheader(get_translation(t, 'graph_title', 'Semantic Graphs'))

        # Mostrar conceptos clave y entidades horizontalmente
        if 'key_concepts' in st.session_state:
            st.write(get_translation(t, 'key_concepts_title', 'Key Concepts'))
            st.markdown('<div class="horizontal-list">', unsafe_allow_html=True)
            for concept, freq in st.session_state.key_concepts:
                st.markdown(f'<span style="margin-right: 10px;">{concept}: {freq:.2f}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        if 'entities' in st.session_state:
            st.write(get_translation(t, 'entities_title', 'Entities'))
            st.markdown('<div class="horizontal-list">', unsafe_allow_html=True)
            for entity, type in st.session_state.entities.items():
                st.markdown(f'<span style="margin-right: 10px;">{entity}: {type}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Usar pestañas para mostrar los gráficos
        tab1, tab2 = st.tabs(["Concept Graph", "Entity Graph"])

        with tab1:
            if 'concept_graph' in st.session_state:
                st.pyplot(st.session_state.concept_graph)

        with tab2:
            if 'entity_graph' in st.session_state:
                st.pyplot(st.session_state.entity_graph)

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button(get_translation(t, 'clear_chat', 'Clear chat'), key=generate_unique_key('semantic', 'clear_chat')):
        st.session_state.semantic_chat_history = []
        st.rerun()