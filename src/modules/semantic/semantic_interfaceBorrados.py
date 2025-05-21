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
    # Inicializar el chatbot y el historial del chat al principio de la función
    if 'semantic_chatbot' not in st.session_state:
        st.session_state.semantic_chatbot = initialize_chatbot('semantic')

    if 'semantic_chat_history' not in st.session_state:
        st.session_state.semantic_chat_history = []

    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #F0F2F6;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #FFFFFF;
        }
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
        .file-item:last-child {
            border-bottom: none;
        }
        .chat-message-container {
            margin-bottom: 10px;
            max-height: 400px;
            overflow-y: auto;
        }
        .stButton {
            margin-top: 0 !important;
        }
        .graph-container {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 10px;
        }
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

        st.markdown("---")  # Línea separadora

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
        st.subheader("Select File for Analysis")
        user_files = get_user_files(st.session_state.username, 'semantic')
        file_options = [get_translation(t, 'select_saved_file', 'Select a saved file')] + [file['file_name'] for file in user_files]
        selected_file = st.selectbox("", options=file_options, key=generate_unique_key('semantic', 'file_selector'))

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

        # Chat and Visualization
        with st.container():
            col_chat, col_graph = st.columns([1, 1])

            with col_chat:
                st.subheader("Chat with AI")

                chat_container = st.container()
                with chat_container:
                    for message in st.session_state.semantic_chat_history:
                        with st.chat_message(message["role"]):
                            st.markdown(message["content"])

                user_input = st.text_input("Type your message here...", key=generate_unique_key('semantic', 'chat_input'))
                col1, col2 = st.columns([3, 1])
                with col1:
                    send_button = st.button("Send", key=generate_unique_key('semantic', 'send_message'))
                with col2:
                    clear_button = st.button("Clear Chat", key=generate_unique_key('semantic', 'clear_chat'))

                if send_button and user_input:
                    st.session_state.semantic_chat_history.append({"role": "user", "content": user_input})

                    if user_input.startswith('/analyze_current'):
                        response = process_semantic_chat_input(user_input, lang_code, nlp_models[lang_code], st.session_state.get('file_contents', ''))
                    else:
                        response = st.session_state.semantic_chatbot.generate_response(user_input, lang_code, context=st.session_state.get('file_contents', ''))

                    st.session_state.semantic_chat_history.append({"role": "assistant", "content": response})
                    st.rerun()

                if clear_button:
                    st.session_state.semantic_chat_history = []
                    st.rerun()

            with col_graph:
                st.subheader("Visualization")
                if 'key_concepts' in st.session_state:
                    st.write("Key Concepts:")
                    st.write(', '.join([f"{concept}: {freq:.2f}" for concept, freq in st.session_state.key_concepts]))

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
