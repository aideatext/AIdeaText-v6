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
        </style>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Upload", "Analyze", "Results", "Chat", "Export"])

    with tab1:
        tab21, tab22 = st.tabs(["File Management", "File Analysis"])

        with tab21:
            st.subheader("Upload and Manage Files")
            uploaded_file = st.file_uploader("Choose a file to upload", type=['txt', 'pdf', 'docx', 'doc', 'odt'], key=generate_unique_key('semantic', 'file_uploader'))
            if uploaded_file is not None:
                file_contents = uploaded_file.getvalue().decode('utf-8')
                if store_file_semantic_contents(st.session_state.username, uploaded_file.name, file_contents):
                    st.success(f"File {uploaded_file.name} uploaded and saved successfully")
                else:
                    st.error("Error uploading file")

            st.subheader("Manage Uploaded Files")
            user_files = get_user_files(st.session_state.username, 'semantic')
            if user_files:
                for file in user_files:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(file['file_name'])
                    with col2:
                        if st.button("Delete", key=f"delete_{file['file_name']}"):
                            if delete_file(st.session_state.username, file['file_name'], 'semantic'):
                                st.success(f"File {file['file_name']} deleted successfully")
                                st.rerun()
                            else:
                                st.error(f"Error deleting file {file['file_name']}")
            else:
                st.write("No files uploaded yet.")

        with tab22:
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

    with tab2:
        st.subheader("Analysis Results")
        if 'key_concepts' in st.session_state:
            st.write("Key Concepts:")
            st.write(', '.join([f"{concept}: {freq:.2f}" for concept, freq in st.session_state.key_concepts]))

        col1, col2 = st.columns(2)
        with col1:
            if 'concept_graph' in st.session_state:
                st.subheader("Concept Graph")
                st.pyplot(st.session_state.concept_graph)
        with col2:
            if 'entity_graph' in st.session_state:
                st.subheader("Entity Graph")
                st.pyplot(st.session_state.entity_graph)

    with tab3:
        st.subheader("Chat with AI")
        chat_container = st.container()

        with chat_container:
            chat_history = st.session_state.get('semantic_chat_history', [])
            for message in chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        user_input = st.chat_input("Type your message here...", key=generate_unique_key('semantic', 'chat_input'))

        if user_input:
            chat_history.append({"role": "user", "content": user_input})

            if user_input.startswith('/analyze_current'):
                response = process_semantic_chat_input(user_input, lang_code, nlp_models[lang_code], st.session_state.get('file_contents', ''))
            else:
                response = st.session_state.semantic_chatbot.generate_response(user_input, lang_code)

            chat_history.append({"role": "assistant", "content": response})
            st.session_state.semantic_chat_history = chat_history

        if st.button("Clear Chat", key=generate_unique_key('semantic', 'clear_chat')):
            st.session_state.semantic_chat_history = []
            st.rerun()

    with tab4:
        st.subheader("Export Results")
        # Add export functionality here

    with tab5:
        st.subheader("Help")
        # Add help information here