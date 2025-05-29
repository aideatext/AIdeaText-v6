# AIdeaText v3
# app.py
import logging
import streamlit as st
import sys
import os
from dotenv import load_dotenv
from datetime import datetime
from PIL import Image

# Configuración básica
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración básica de la página
st.set_page_config(
    page_title="AIdeaText",
    layout="wide",
    initial_sidebar_state="collapsed"  # Para dar más espacio al logo
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importaciones locales
from translations import get_translations, get_landing_translations
from session_state import initialize_session_state
from modules.ui.ui import main as ui_main
from modules.utils.spacy_utils import load_spacy_models
from modules.utils.widget_utils import generate_unique_key

# Importaciones de interfaces
from modules.semantic.semantic_interface import (
    display_semantic_interface, 
    display_semantic_results
)

from modules.discourse.discourse_interface import (
    display_discourse_interface, 
    display_discourse_results
)

# Importaciones de base de datos

from modules.database.database_init import initialize_database_connections

from modules.database.sql_db import (
     get_user,
     get_admin_user,
     get_student_user,
     get_teacher_user,
     create_user,
     create_student_user,
     create_teacher_user,
     create_admin_user,
     update_student_user,  # Agregada
     delete_student_user,  # Agregada
     record_login,
     record_logout,
     get_recent_sessions,
     get_user_total_time,
     store_application_request,
     store_student_feedback
)

from modules.database.mongo_db import (
    get_collection,
    insert_document,
    find_documents,
    update_document,
    delete_document
)

###########SEMANTIC
from modules.database.semantic_mongo_db import (
    store_student_semantic_result,
    get_student_semantic_analysis
)

from modules.database.discourse_mongo_db import (
    store_student_discourse_result,
    get_student_discourse_analysis
)

from modules.database.chat_mongo_db import ( 
    store_chat_history,
    get_chat_history
)

# Importaciones de base de datos
from modules.studentact.student_activities_v2 import display_student_activities
# from modules.studentact.current_situation_interface import display_current_situation_interface

from modules.auth.auth import (
    authenticate_student,
    register_student,
    update_student_info,
    delete_student
)
from modules.admin.admin_ui import admin_page

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource(show_spinner=False)
def initialize_nlp_models():
    logger.info("Cargando modelos de spaCy")
    models = load_spacy_models()
    logger.info("Modelos de spaCy cargados exitosamente")
    return models

def app_main():
    try:
        logger.info("Entrando en app_main()")

        # Inicializar el estado de la sesión
        if 'initialized' not in st.session_state:
            initialize_session_state()
            st.session_state.initialized = True

        # Inicializar conexiones a bases de datos si no se ha hecho
        if 'db_initialized' not in st.session_state:
            st.session_state.db_initialized = initialize_database_connections()

        # Cargar modelos NLP si no se ha hecho
        if 'nlp_models' not in st.session_state:
            logger.info("Inicializando modelos NLP en la sesión")
            st.session_state.nlp_models = initialize_nlp_models()
            logger.info("Modelos NLP inicializados y almacenados en la sesión")

        # Inicializar estados de análisis si no existen
        if 'semantic_state' not in st.session_state:
            st.session_state.semantic_state = {
                'last_analysis': None,
                'analysis_count': 0
            }
            
        if 'discourse_state' not in st.session_state:
            st.session_state.discourse_state = {
                'last_analysis': None,
                'analysis_count': 0
            }

        # Configurar la página inicial si no está configurada
        if 'page' not in st.session_state:
            st.session_state.page = 'login'

        # Prevenir reinicios innecesarios preservando el estado
        if 'selected_tab' not in st.session_state:
            st.session_state.selected_tab = 0

        logger.info(f"Página actual: {st.session_state.page}")
        logger.info(f"Rol del usuario: {st.session_state.role}")

        # Dirigir el flujo a la interfaz de usuario principal
        logger.info(f"Llamando a ui_main() desde app_main()")
        ui_main()

    except Exception as e:
        logger.error(f"Error en app_main: {str(e)}", exc_info=True)
        st.error("Se ha producido un error en la aplicación. Por favor, inténtelo de nuevo más tarde.")
        if st.button("Reiniciar aplicación", 
                    key=generate_unique_key("app", "reset_button")):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    app_main()