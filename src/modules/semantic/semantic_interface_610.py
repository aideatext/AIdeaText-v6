import streamlit as st
import logging
from .semantic_process import process_semantic_analysis
from ..chatbot.chatbot import initialize_chatbot, process_semantic_chat_input
from ..database.database_oldFromV2 import store_file_semantic_contents, retrieve_file_contents, delete_file, get_user_files
from ..utils.widget_utils import generate_unique_key
from .semantic_float_reset import *

logger = logging.getLogger(__name__)
semantic_float_init()

def get_translation(t, key, default):
    return t.get(key, default)

def display_semantic_interface(lang_code, nlp_models, t):
    # Inicialización del chatbot y el historial del chat
    if 'semantic_chatbot' not in st.session_state:
        st.session_state.semantic_chatbot = initialize_chatbot('semantic')
    if 'semantic_chat_history' not in st.session_state:
        st.session_state.semantic_chat_history = []

    # Inicializar el estado del grafo si no existe
    if 'graph_visible' not in st.session_state:
        st.session_state.graph_visible = False
    if 'graph_content' not in st.session_state:
        st.session_state.graph_content = ""

    st.markdown("""
        <style>
        .user-message {
            background-color: #e6f3ff;
            text-align: right;
        }
        .assistant-message {
            background-color: #f0f0f0;
            text-align: left;
        }
        .chat-input {
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            z-index: 1000;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='semantic-initial-message'>{t['semantic_initial_message']}</div>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Upload", "Analyze"])

    with tab1:
        st.subheader("File Management")
        uploaded_file = st.file_uploader("Choose a file to upload", type=['txt', 'pdf', 'docx', 'doc', 'odt'], key=generate_unique_key('semantic', 'file_uploader'))
        if uploaded_file is not None:
            file_contents = uploaded_file.getvalue().decode('utf-8')
            if store_file_semantic_contents(st.session_state.username, uploaded_file.name, file_contents):
                st.success(f"File {uploaded_file.name} uploaded and saved successfully")
            else:
                st.error("Error uploading file")

        st.markdown("---")
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

    with tab2:
        st.subheader("Semantic Analysis")

        st.subheader("File Selection and Analysis")
        user_files = get_user_files(st.session_state.username, 'semantic')
        file_options = [get_translation(t, 'select_saved_file', 'Select a saved file')] + [file['file_name'] for file in user_files]
        selected_file = st.selectbox("", options=file_options, key=generate_unique_key('semantic', 'file_selector'))

    if st.button("Analyze Document"):
        if selected_file and selected_file != get_translation(t, 'select_saved_file', 'Select a saved file'):
            file_contents = retrieve_file_contents(st.session_state.username, selected_file, 'semantic')
            if file_contents:
                with st.spinner("Analyzing..."):
                    try:
                        nlp_model = nlp_models[lang_code]
                        concept_graph, entity_graph, key_concepts = process_semantic_analysis(file_contents, nlp_model, lang_code)
                        st.session_state.concept_graph = concept_graph
                        st.session_state.entity_graph = entity_graph
                        st.session_state.key_concepts = key_concepts
                        st.session_state.current_file_contents = file_contents
                        st.success("Analysis completed successfully")

                        # Crear o actualizar el elemento flotante con el grafo
                        graph_content = f"""
                            <h3>Key Concepts:</h3>
                            <p>{', '.join([f"{concept}: {freq:.2f}" for concept, freq in key_concepts])}</p>
                            <img src="data:image/png;base64,{concept_graph}" alt="Concept Graph" style="width:100%; height:auto;"/>
                        """
                        st.session_state.graph_id = float_graph(graph_content, width="30%", height="80%", position="center-right", shadow=2)
                        st.session_state.graph_visible = True

                        # Depuración: Mostrar los primeros 100 caracteres del grafo
                        st.write(f"Debug: Concept graph base64 (first 100 chars): {concept_graph[:100]}")
                        st.write(f"Debug: Graph ID: {st.session_state.graph_id}")

                    except Exception as e:
                        st.error(f"Error during analysis: {str(e)}")
                        st.session_state.concept_graph = None
                        st.session_state.entity_graph = None
                        st.session_state.key_concepts = []
            else:
                st.error("Error loading file contents")
        else:
            st.error("Please select a file to analyze")

        st.subheader("Chat with AI")

        # Mostrar el historial del chat
        for message in st.session_state.semantic_chat_history:
            message_class = "user-message" if message["role"] == "user" else "assistant-message"
            st.markdown(f'<div class="chat-message {message_class}">{message["content"]}</div>', unsafe_allow_html=True)

        # Colocar la entrada de usuario y los botones en la parte inferior
        st.markdown('<div class="chat-input">', unsafe_allow_html=True)
        user_input = st.text_input("Type your message here...", key=generate_unique_key('semantic', 'chat_input'))
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            send_button = st.button("Send", key=generate_unique_key('semantic', 'send_message'))
        with col2:
            clear_button = st.button("Clear Chat", key=generate_unique_key('semantic', 'clear_chat'))
        with col3:
            if 'graph_id' in st.session_state:
                toggle_button = st.button("Toggle Graph", key="toggle_graph")
                if toggle_button:
                    st.session_state.graph_visible = not st.session_state.get('graph_visible', True)
                    toggle_float_visibility(st.session_state.graph_id, st.session_state.graph_visible)
        st.markdown('</div>', unsafe_allow_html=True)

        if send_button and user_input:
            st.session_state.semantic_chat_history.append({"role": "user", "content": user_input})
            if user_input.startswith('/analyze_current'):
                response = process_semantic_chat_input(user_input, lang_code, nlp_models[lang_code], st.session_state.get('current_file_contents', ''))
            else:
                response = st.session_state.semantic_chatbot.generate_response(user_input, lang_code, context=st.session_state.get('current_file_contents', ''))
            st.session_state.semantic_chat_history.append({"role": "assistant", "content": response})
            st.rerun()

        if clear_button:
            st.session_state.semantic_chat_history = []
            st.rerun()

    # Asegurarse de que el grafo flotante permanezca visible después de las interacciones
    if 'graph_id' in st.session_state and st.session_state.get('graph_visible', False):
        toggle_float_visibility(st.session_state.graph_id, True)


# Al final del archivo, después de todo el código:
if 'graph_id' in st.session_state and st.session_state.get('graph_visible', False):
    components.html(f"""
    <script>
        var element = document.getElementById('{st.session_state.graph_id}');
        if (element) {{
            element.style.display = 'block';
        }} else {{
            console.error('Graph element not found');
        }}
    </script>
    """, height=0)

# Añadir un botón para alternar la visibilidad del grafo
if st.button("Toggle Graph Visibility"):
    st.session_state.graph_visible = not st.session_state.get('graph_visible', False)
    if st.session_state.graph_visible:
        st.write("Graph should be visible now")
    else:
        st.write("Graph should be hidden now")
    st.experimental_rerun()