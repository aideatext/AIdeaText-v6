import streamlit as st
from streamlit_float import *
import logging
import sys
import io
from io import BytesIO
from datetime import datetime
import re
import base64
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from .flexible_analysis_handler import FlexibleAnalysisHandler

from .semantic_float_reset import semantic_float_init, float_graph, toggle_float_visibility, update_float_content

from .semantic_process import process_semantic_analysis

from ..chatbot.chatbot import initialize_chatbot, process_semantic_chat_input
from ..database.database_oldFromV2 import manage_file_contents, delete_file, get_user_files
from ..utils.widget_utils import generate_unique_key


semantic_float_init()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_translation(t, key, default):
    return t.get(key, default)


##
def fig_to_base64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode()
    return f'<img src="data:image/png;base64,{img_str}" />'
##


def display_semantic_interface(lang_code, nlp_models, t):
    #st.set_page_config(layout="wide")

    if 'semantic_chatbot' not in st.session_state:
        st.session_state.semantic_chatbot = initialize_chatbot('semantic')

    if 'semantic_chat_history' not in st.session_state:
        st.session_state.semantic_chat_history = []

    if 'show_graph' not in st.session_state:
        st.session_state.show_graph = False

    if 'graph_id' not in st.session_state:
        st.session_state.graph_id = None

    if 'semantic_chatbot' not in st.session_state:
        st.session_state.semantic_chatbot = initialize_chatbot('semantic')

    if 'semantic_chat_history' not in st.session_state:
        st.session_state.semantic_chat_history = []

    if 'show_graph' not in st.session_state:
        st.session_state.show_graph = False

    st.markdown("""
        <style>
        .chat-message-container {
            height: calc(100vh - 200px);
            overflow-y: auto;
            display: flex;
            flex-direction: column-reverse;
        }
        .chat-input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 1rem;
            background-color: white;
            z-index: 1000;
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

    st.markdown(f"""
        <div class="semantic-initial-message">
        {t['semantic_initial_message']}
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Chat with AI")

        chat_container = st.container()
        with chat_container:
            st.markdown('<div class="chat-message-container">', unsafe_allow_html=True)
            for message in reversed(st.session_state.semantic_chat_history):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
        user_input = st.text_input("Type your message here...", key=generate_unique_key('semantic', 'chat_input'))
        send_button = st.button("Send", key=generate_unique_key('semantic', 'send_message'))
        clear_button = st.button("Clear Chat", key=generate_unique_key('semantic', 'clear_chat'))
        st.markdown('</div>', unsafe_allow_html=True)

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

    with col2:
        st.subheader("Document Analysis")
        user_files = get_user_files(st.session_state.username, 'semantic')
        file_options = [get_translation(t, 'select_saved_file', 'Select a saved file')] + [file['file_name'] for file in user_files]
        selected_file = st.selectbox("Select a file to analyze", options=file_options, key=generate_unique_key('semantic', 'file_selector'))

    if st.button("Analyze Document", key=generate_unique_key('semantic', 'analyze_document')):
        if selected_file and selected_file != get_translation(t, 'select_saved_file', 'Select a saved file'):
            file_contents = manage_file_contents(st.session_state.username, selected_file, 'semantic')
            if file_contents:
                st.session_state.file_contents = file_contents
                with st.spinner("Analyzing..."):
                    try:
                        nlp_model = nlp_models[lang_code]
                        logger.debug("Calling process_semantic_analysis")
                        analysis_result = process_semantic_analysis(file_contents, nlp_model, lang_code)

                        # Crear una instancia de FlexibleAnalysisHandler con los resultados del análisis
                        handler = FlexibleAnalysisHandler(analysis_result)

                        logger.debug(f"Type of analysis_result: {type(analysis_result)}")
                        logger.debug(f"Keys in analysis_result: {analysis_result.keys() if isinstance(analysis_result, dict) else 'Not a dict'}")

                        st.session_state.concept_graph = handler.get_concept_graph()
                        st.session_state.entity_graph = handler.get_entity_graph()
                        st.session_state.key_concepts = handler.get_key_concepts()
                        st.session_state.show_graph = True
                        st.success("Analysis completed successfully")
                    except Exception as e:
                        logger.error(f"Error during analysis: {str(e)}")
                        st.error(f"Error during analysis: {str(e)}")
            else:
                st.error("Error loading file contents")
        else:
            st.error("Please select a file to analyze")

        st.subheader("File Management")

        uploaded_file = st.file_uploader("Choose a file to upload", type=['txt', 'pdf', 'docx', 'doc', 'odt'], key=generate_unique_key('semantic', 'file_uploader'))
        if uploaded_file is not None:
            file_contents = uploaded_file.getvalue().decode('utf-8')
            if manage_file_contents(st.session_state.username, uploaded_file.name, file_contents):
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

    #########################################################################################################################
    # Floating graph visualization
    if st.session_state.show_graph:
        if st.session_state.graph_id is None:
            st.session_state.graph_id = float_graph(
                content="<div id='semantic-graph'>Loading graph...</div>",
                width="40%",
                height="60%",
                position="bottom-right",
                shadow=2,
                transition=1
            )

        graph_id = st.session_state.graph_id

        if 'key_concepts' in st.session_state:
            key_concepts_html = "<h3>Key Concepts:</h3><p>" + ', '.join([f"{concept}: {freq:.2f}" for concept, freq in st.session_state.key_concepts]) + "</p>"
            update_float_content(graph_id, key_concepts_html)

        tab_concept, tab_entity = st.tabs(["Concept Graph", "Entity Graph"])

        with tab_concept:
            if 'concept_graph' in st.session_state:
                update_float_content(graph_id, st.session_state.concept_graph)
            else:
                update_float_content(graph_id, "No concept graph available.")

        with tab_entity:
            if 'entity_graph' in st.session_state:
                update_float_content(graph_id, st.session_state.entity_graph)
            else:
                update_float_content(graph_id, "No entity graph available.")

        if st.button("Close Graph", key="close_graph"):
            toggle_float_visibility(graph_id, False)
            st.session_state.show_graph = False
            st.session_state.graph_id = None
            st.rerun()