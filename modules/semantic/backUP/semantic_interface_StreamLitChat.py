import streamlit as st
import logging
from streamlit_chat import message
from .semantic_process import process_semantic_analysis
from ..chatbot.chatbot import initialize_chatbot, process_semantic_chat_input
from ..database.database_oldFromV2 import store_file_semantic_contents, retrieve_file_contents, delete_file, get_user_files
from ..utils.widget_utils import generate_unique_key

logger = logging.getLogger(__name__)

def get_translation(t, key, default):
    return t.get(key, default)

def display_semantic_interface(lang_code, nlp_models, t):
    # Inicializar el chatbot y el historial del chat al principio de la función
    if 'semantic_chatbot' not in st.session_state:
        st.session_state.semantic_chatbot = initialize_chatbot('semantic')

    if 'messages' not in st.session_state:
        st.session_state.messages = []

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
        </style>
    """, unsafe_allow_html=True)

    # Mostrar el mensaje inicial como un párrafo estilizado
    st.markdown(f"""
        <div class="morpho-initial-message">
        {t['semantic_initial_message']}
        </div>
    """, unsafe_allow_html=True)


    st.title("Semantic Analysis")

    # Crear dos columnas principales: una para el chat y otra para la visualización
    chat_col, viz_col = st.columns([1, 1])

    with chat_col:
        st.subheader("Chat with AI")

        # Contenedor para los mensajes del chat
        chat_container = st.container()

        # Input para el chat
        user_input = st.text_input("Type your message here...", key=generate_unique_key('semantic', 'chat_input'))

        if user_input:
            # Añadir mensaje del usuario
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Generar respuesta del asistente
            if user_input.startswith('/analyze_current'):
                response = process_semantic_chat_input(user_input, lang_code, nlp_models[lang_code], st.session_state.get('file_contents', ''))
            else:
                response = st.session_state.semantic_chatbot.generate_response(user_input, lang_code, context=st.session_state.get('file_contents', ''))

            # Añadir respuesta del asistente
            st.session_state.messages.append({"role": "assistant", "content": response})

        # Mostrar mensajes en el contenedor del chat
        with chat_container:
            for i, msg in enumerate(st.session_state.messages):
                message(msg['content'], is_user=msg['role'] == 'user', key=f"{i}_{msg['role']}")

        # Botón para limpiar el chat
        if st.button("Clear Chat", key=generate_unique_key('semantic', 'clear_chat')):
            st.session_state.messages = []
            st.rerun()

    with viz_col:
        st.subheader("Visualization")

        # Selector de archivo y botón de análisis
        user_files = get_user_files(st.session_state.username, 'semantic')
        file_options = [get_translation(t, 'select_saved_file', 'Select a saved file')] + [file['file_name'] for file in user_files]
        selected_file = st.selectbox("Select a file to analyze", options=file_options, key=generate_unique_key('semantic', 'file_selector'))

        if st.button("Analyze Document", key=generate_unique_key('semantic', 'analyze_document')):
            if selected_file and selected_file != get_translation(t, 'select_saved_file', 'Select a saved file'):
                file_contents = retrieve_file_contents(st.session_state.username, selected_file, 'semantic')
                if file_contents:
                    st.session_state.file_contents = file_contents
                    with st.spinner("Analyzing..."):
                        try:
                            nlp_model = nlp_models[lang_code]
                            concept_graph, entity_graph, key_concepts = process_semantic_analysis(file_contents, nlp_model, lang_code)
                            st.session_state.concept_graph = concept_graph
                            st.session_state.entity_graph = entity_graph
                            st.session_state.key_concepts = key_concepts
                            st.success("Analysis completed successfully")
                        except Exception as e:
                            logger.error(f"Error during analysis: {str(e)}")
                            st.error(f"Error during analysis: {str(e)}")
                else:
                    st.error("Error loading file contents")
            else:
                st.error("Please select a file to analyze")

        # Visualización de conceptos clave
        if 'key_concepts' in st.session_state:
            st.write("Key Concepts:")
            st.write(', '.join([f"{concept}: {freq:.2f}" for concept, freq in st.session_state.key_concepts]))

        # Pestañas para los gráficos
        tab_concept, tab_entity = st.tabs(["Concept Graph", "Entity Graph"])

        with tab_concept:
            if 'concept_graph' in st.session_state:
                st.pyplot(st.session_state.concept_graph)
            else:
                st.info("No concept graph available. Please analyze a document first.")

        with tab_entity:
            if 'entity_graph' in st.session_state:
                st.pyplot(st.session_state.entity_graph)
            else:
                st.info("No entity graph available. Please analyze a document first.")

    # Sección de carga de archivos
    st.subheader("File Management")
    uploaded_file = st.file_uploader("Choose a file to upload", type=['txt', 'pdf', 'docx', 'doc', 'odt'], key=generate_unique_key('semantic', 'file_uploader'))
    if uploaded_file is not None:
        file_contents = uploaded_file.getvalue().decode('utf-8')
        if store_file_semantic_contents(st.session_state.username, uploaded_file.name, file_contents):
            st.success(f"File {uploaded_file.name} uploaded and saved successfully")
        else:
            st.error("Error uploading file")

    st.markdown("---")

    # Gestión de archivos cargados
    st.subheader("Manage Uploaded Files")
    user_files = get_user_files(st.session_state.username, 'semantic')
    if user_files:
        for file in user_files:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(file['file_name'])
            with col2:
                if st.button("Delete", key=f"delete_{file['file_name']}", help=f"Delete {file['file_name']}"):
                    if delete_file(st.session_state.username, file['file_name'], 'semantic'):
                        st.success(f"File {file['file_name']} deleted successfully")
                        st.rerun()
                    else:
                        st.error(f"Error deleting file {file['file_name']}")
    else:
        st.info("No files uploaded yet.")