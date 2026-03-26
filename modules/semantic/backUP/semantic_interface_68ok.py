import streamlit as st
import logging
from ..database.database_oldFromV2 import manage_file_contents, delete_file, get_user_files
from ..utils.widget_utils import generate_unique_key

logger = logging.getLogger(__name__)



def display_semantic_interface(lang_code, nlp_models, t):
    st.subheader(t['semantic_title'])

    text_input = st.text_area(
        t['warning_message'],
        height=150,
        key=generate_unique_key("semantic", "text_area")
    )

    if st.button(
        t['results_title'],
        key=generate_unique_key("semantic", "analyze_button")
    ):
        if text_input:
            # Aquí iría tu lógica de análisis morfosintáctico
            # Por ahora, solo mostraremos un mensaje de placeholder
            st.info(t['analysis_placeholder'])
        else:
            st.warning(t['no_text_warning'])


'''
def display_semantic_interface(lang_code, nlp_models, t):
    st.title("Semantic Analysis")

    tab1, tab2 = st.tabs(["File Management", "Analysis"])

    with tab1:
        display_file_management(lang_code, t)

    with tab2:
        # Aquí irá el código para el análisis semántico (lo implementaremos después)
        st.write("Semantic analysis section will be implemented here.")

def display_file_management(lang_code, t):
    st.header("File Management")

    # File Upload Section
    st.subheader("Upload New File")
    uploaded_file = st.file_uploader(
        "Choose a file to upload",
        type=['txt', 'pdf', 'docx', 'doc', 'odt'],
        key=generate_unique_key('semantic', 'file_uploader')
    )
    if uploaded_file is not None:
        file_contents = uploaded_file.getvalue().decode('utf-8')
        if manage_file_contents(st.session_state.username, uploaded_file.name, file_contents, 'semantic'):
            st.success(f"File {uploaded_file.name} uploaded and saved successfully")
        else:
            st.error("Error uploading file")

    st.markdown("---")


    # File Management Section
    st.subheader("Manage Uploaded Files")
    user_files = get_user_files(st.session_state.username, 'semantic')
    if user_files:
        for file in user_files:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(file['file_name'])
            with col2:
                if st.button("Delete", key=f"delete_{file['file_name']}", help=f"Delete {file['file_name']}"):
                    try:
                        logger.info(f"Attempting to delete file: {file['file_name']} for user: {st.session_state.username}")
                        if delete_file(st.session_state.username, file['file_name'], 'semantic'):
                            st.success(f"File {file['file_name']} deleted successfully")
                            logger.info(f"File {file['file_name']} deleted successfully for user: {st.session_state.username}")
                            st.rerun()
                        else:
                            st.error(f"Error deleting file {file['file_name']}")
                            logger.error(f"Failed to delete file {file['file_name']} for user: {st.session_state.username}")
                    except Exception as e:
                        st.error(f"An error occurred while deleting file {file['file_name']}: {str(e)}")
                        logger.exception(f"Exception occurred while deleting file {file['file_name']} for user: {st.session_state.username}")

    else:
        st.info("No files uploaded yet.")

if __name__ == "__main__":
    # This is just for testing purposes
    class MockTranslation(dict):
        def __getitem__(self, key):
            return key

    display_semantic_interface('en', {}, MockTranslation())

    '''