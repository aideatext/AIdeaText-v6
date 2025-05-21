import streamlit as st
import logging
from .semantic_process import process_semantic_analysis
from ..chatbot.chatbot import initialize_chatbot, process_semantic_chat_input
from ..database.database_oldFromV2 import store_file_semantic_contents, retrieve_file_contents, delete_file, get_user_files
from ..utils.widget_utils import generate_unique_key
from .semantic_float_reset import semantic_float_init, float_graph, toggle_float_visibility, update_float_content

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

    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #F0F2F6;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] { background-color: #FFFFFF; }
        .file-list {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            margin-top: 20px;
        }
        .file-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }
        .file-item:last-child { border-bottom: none; }
        .chat-container {
            height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            margin-bottom: 10px;
        }
        .chat-input { border-top: 1px solid #ddd; padding-top: 10px; }
        .stButton { margin-top: 0 !important; }
        .graph-container {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
            height: 500px;
            overflow-y: auto;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<div class='semantic-initial-message'>{t['semantic_initial_message']}</div>", unsafe_allow_html=True)

    # Barra de progreso
    progress_bar = st.progress(0)

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
        col_left, col_right = st.columns([2, 3])  # Invertimos las proporciones

        with col_left:
            st.subheader("File Selection and Chat")
            user_files = get_user_files(st.session_state.username, 'semantic')
            file_options = [get_translation(t, 'select_saved_file', 'Select a saved file')] + [file['file_name'] for file in user_files]
            selected_file = st.selectbox("", options=file_options, key=generate_unique_key('semantic', 'file_selector'))

            if st.button("Analyze Document"):
                if selected_file and selected_file != get_translation(t, 'select_saved_file', 'Select a saved file'):
                    file_contents = retrieve_file_contents(st.session_state.username, selected_file, 'semantic')
                    if file_contents:
                        progress_bar.progress(10)
                        with st.spinner("Analyzing..."):
                            try:
                                nlp_model = nlp_models[lang_code]
                                progress_bar.progress(30)
                                concept_graph, entity_graph, key_concepts = process_semantic_analysis(file_contents, nlp_model, lang_code)
                                progress_bar.progress(70)
                                st.session_state.concept_graph = concept_graph
                                st.session_state.entity_graph = entity_graph
                                st.session_state.key_concepts = key_concepts
                                st.session_state.current_file_contents = file_contents
                                progress_bar.progress(100)
                                st.success("Analysis completed successfully")

                                # Crear o actualizar el grafo flotante
                                if 'graph_id' not in st.session_state:
                                    st.session_state.graph_id = float_graph(
                                        content="<div id='semantic-graph'>Loading graph...</div>",
                                        width="40%",
                                        height="60%",
                                        position="bottom-right",
                                        shadow=2,
                                        transition=1
                                    )
                                update_float_content(st.session_state.graph_id, f"""
                                    <h3>Key Concepts:</h3>
                                    <p>{', '.join([f"{concept}: {freq:.2f}" for concept, freq in key_concepts])}</p>
                                    <img src="data:image/png;base64,{concept_graph}" alt="Concept Graph" style="width:100%"/>
                                """)
                                st.session_state.graph_visible = True
                            except Exception as e:
                                logger.error(f"Error during analysis: {str(e)}")
                                st.error(f"Error during analysis: {str(e)}")
                                st.session_state.concept_graph = None
                                st.session_state.entity_graph = None
                                st.session_state.key_concepts = []
                            finally:
                                progress_bar.empty()
                    else:
                        st.error("Error loading file contents")
                else:
                    st.error("Please select a file to analyze")

            st.subheader("Chat with AI")
            chat_container = st.container()
            with chat_container:
                st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                for message in st.session_state.semantic_chat_history:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                st.markdown('</div>', unsafe_allow_html=True)

            user_input = st.text_input("Type your message here...", key=generate_unique_key('semantic', 'chat_input'))
            col1, col2 = st.columns([3, 1])
            with col1:
                send_button = st.button("Send", key=generate_unique_key('semantic', 'send_message'))
            with col2:
                clear_button = st.button("Clear Chat and Graph", key=generate_unique_key('semantic', 'clear_chat'))

            if send_button and user_input:
                st.session_state.semantic_chat_history.append({"role": "user", "content": user_input})
                if user_input.startswith('/analyze_current'):
                    response = process_semantic_chat_input(user_input, lang_code, nlp_models[lang_code], st.session_state.get('current_file_contents', ''))
                else:
                    response = st.session_state.semantic_chatbot.generate_response(user_input, lang_code, context=st.session_state.get('current_file_contents', ''))
                st.session_state.semantic_chat_history.append({"role": "assistant", "content": response})
                st.rerun()

            if clear_button:
                if st.session_state.semantic_chat_history:
                    if st.button("Do you want to export the analysis before clearing?"):
                        # Aquí puedes implementar la lógica para exportar el análisis
                        st.success("Analysis exported successfully")
                st.session_state.semantic_chat_history = []
                if 'graph_id' in st.session_state:
                    toggle_float_visibility(st.session_state.graph_id, False)
                    del st.session_state.graph_id
                st.session_state.concept_graph = None
                st.session_state.entity_graph = None
                st.session_state.key_concepts = []
                st.rerun()

        with col_right:
            st.subheader("Visualization")
            if 'key_concepts' in st.session_state and st.session_state.key_concepts:
                st.write("Key Concepts:")
                st.write(', '.join([f"{concept}: {freq:.2f}" for concept, freq in st.session_state.key_concepts]))

            tab_concept, tab_entity = st.tabs(["Concept Graph", "Entity Graph"])
            with tab_concept:
                if 'concept_graph' in st.session_state and st.session_state.concept_graph:
                    st.image(st.session_state.concept_graph)
                else:
                    st.info("No concept graph available. Please analyze a document first.")
            with tab_entity:
                if 'entity_graph' in st.session_state and st.session_state.entity_graph:
                    st.image(st.session_state.entity_graph)
                else:
                    st.info("No entity graph available. Please analyze a document first.")