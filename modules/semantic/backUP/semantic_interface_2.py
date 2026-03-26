import streamlit as st
from .semantic_process import process_semantic_analysis
from ..chatbot.chatbot import initialize_chatbot
from ..database.database_oldFromV2 import store_file_semantic_contents, retrieve_file_contents, delete_file, get_user_files
from ..utils.widget_utils import generate_unique_key

def get_translation(t, key, default):
    return t.get(key, default)

def display_semantic_interface(lang_code, nlp_models, t):
    #st.set_page_config(layout="wide")

    # Estilo CSS personalizado
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
        }
        .chat-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
        }
        .file-management-container {
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
        </style>
    """, unsafe_allow_html=True)

    # Mostrar el mensaje inicial como un párrafo estilizado
    st.markdown(f"""
        <div class="semantic-initial-message">
        {get_translation(t, 'semantic_initial_message', 'Welcome to the semantic analysis interface.')}
        </div>
    """, unsafe_allow_html=True)

    # Inicializar el chatbot si no existe
    if 'semantic_chatbot' not in st.session_state:
        st.session_state.semantic_chatbot = initialize_chatbot('semantic')

    # Contenedor para la gestión de archivos
    with st.container():
        st.markdown('<div class="file-management-container">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button(get_translation(t, 'upload_file', 'Upload File'), key=generate_unique_key('semantic', 'upload_button')):
                uploaded_file = st.file_uploader(get_translation(t, 'file_uploader', 'Choose a file'), type=['txt', 'pdf', 'docx', 'doc', 'odt'], key=generate_unique_key('semantic', 'file_uploader'))
                if uploaded_file is not None:
                    file_contents = uploaded_file.getvalue().decode('utf-8')
                    if store_file_semantic_contents(st.session_state.username, uploaded_file.name, file_contents):
                        st.success(get_translation(t, 'file_uploaded_success', 'File uploaded and saved to database successfully'))
                        st.session_state.file_contents = file_contents
                        st.rerun()
                    else:
                        st.error(get_translation(t, 'file_upload_error', 'Error uploading file'))

        with col2:
            user_files = get_user_files(st.session_state.username, 'semantic')
            file_options = [get_translation(t, 'select_file', 'Select a file')] + [file['file_name'] for file in user_files]
            selected_file = st.selectbox(get_translation(t, 'file_list', 'File List'), options=file_options, key=generate_unique_key('semantic', 'file_selector'))
            if selected_file != get_translation(t, 'select_file', 'Select a file'):
                if st.button(get_translation(t, 'load_file', 'Load File'), key=generate_unique_key('semantic', 'load_file')):
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
                        graph, key_concepts = process_semantic_analysis(st.session_state.file_contents, nlp_models[lang_code], lang_code)
                    st.session_state.graph = graph
                    st.session_state.key_concepts = key_concepts
                    st.success(get_translation(t, 'analysis_completed', 'Analysis completed'))
                else:
                    st.error(get_translation(t, 'no_file_uploaded', 'No file uploaded'))

        with col4:
            if st.button(get_translation(t, 'delete_file', 'Delete File'), key=generate_unique_key('semantic', 'delete_file')):
                if selected_file and selected_file != get_translation(t, 'select_file', 'Select a file'):
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

    # Crear dos columnas: una para el chat y otra para la visualización
    col_chat, col_graph = st.columns([1, 1])

    with col_chat:
        st.subheader(get_translation(t, 'chat_title', 'Semantic Analysis Chat'))
        # Chat interface
        chat_container = st.container()

        with chat_container:
            # Mostrar el historial del chat
            chat_history = st.session_state.get('semantic_chat_history', [])
            for message in chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # Input del usuario
        user_input = st.chat_input(get_translation(t, 'semantic_chat_input', 'Type your message here...'), key=generate_unique_key('semantic', 'chat_input'))

        if user_input:
            # Añadir el mensaje del usuario al historial
            chat_history.append({"role": "user", "content": user_input})

            # Generar respuesta del chatbot
            chatbot = st.session_state.semantic_chatbot
            response = chatbot.generate_response(user_input, lang_code, context=st.session_state.get('file_contents'))

            # Añadir la respuesta del chatbot al historial
            chat_history.append({"role": "assistant", "content": response})

            # Actualizar el historial en session_state
            st.session_state.semantic_chat_history = chat_history

            # Forzar la actualización de la interfaz
            st.rerun()

    with col_graph:
        st.subheader(get_translation(t, 'graph_title', 'Semantic Graph'))

        # Mostrar conceptos clave en un expander horizontal
        with st.expander(get_translation(t, 'key_concepts_title', 'Key Concepts'), expanded=True):
            if 'key_concepts' in st.session_state:
                st.markdown('<div class="horizontal-list">', unsafe_allow_html=True)
                for concept, freq in st.session_state.key_concepts:
                    st.markdown(f'<span style="margin-right: 10px;">{concept}: {freq:.2f}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        if 'graph' in st.session_state:
            st.pyplot(st.session_state.graph)

    # Botón para limpiar el historial del chat
    if st.button(get_translation(t, 'clear_chat', 'Clear chat'), key=generate_unique_key('semantic', 'clear_chat')):
        st.session_state.semantic_chat_history = []
        st.rerun()