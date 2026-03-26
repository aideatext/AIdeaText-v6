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
    # Inicializar el chatbot al principio de la función
    if 'semantic_chatbot' not in st.session_state:
        st.session_state.semantic_chatbot = initialize_chatbot('semantic')

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
        .file-management-container {
            position: sticky;
            top: 0;
            z-index: 999;
            background-color: white;
            padding: 10px;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
        }
        .file-management-item {
            flex: 1;
            margin: 0 5px;
        }
        .stButton > button {
            width: 100%;
            height: 3em;
        }
        .stSelectbox {
            margin-top: -5px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="semantic-initial-message">
        {get_translation(t, 'semantic_initial_message', 'Welcome to the semantic analysis interface.')}
        </div>
    """, unsafe_allow_html=True)

        # File management container
    st.markdown('<div class="file-management-container">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Upload File", key=generate_unique_key('semantic', 'upload_button')):
            st.session_state.show_uploader = True

    with col2:
        user_files = get_user_files(st.session_state.username, 'semantic')
        file_options = [get_translation(t, 'select_saved_file', 'Select a saved file')] + [file['file_name'] for file in user_files]
        selected_file = st.selectbox("", options=file_options, key=generate_unique_key('semantic', 'file_selector'))

    with col3:
        analyze_button = st.button("Analyze Document", key=generate_unique_key('semantic', 'analyze_document'))

    with col4:
        delete_button = st.button("Delete File", key=generate_unique_key('semantic', 'delete_file'))

    st.markdown('</div>', unsafe_allow_html=True)

    # File uploader (hidden by default)
    if st.session_state.get('show_uploader', False):
        uploaded_file = st.file_uploader("Choose a file", type=['txt', 'pdf', 'docx', 'doc', 'odt'], key=generate_unique_key('semantic', 'file_uploader'))
        if uploaded_file is not None:
            file_contents = uploaded_file.getvalue().decode('utf-8')
            if store_file_semantic_contents(st.session_state.username, uploaded_file.name, file_contents):
                st.session_state.file_contents = file_contents
                st.success(get_translation(t, 'file_uploaded_success', 'File uploaded and saved successfully'))
                st.session_state.show_uploader = False  # Hide uploader after successful upload
            else:
                st.error(get_translation(t, 'file_upload_error', 'Error uploading file'))


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