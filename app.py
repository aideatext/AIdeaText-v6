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

# --- IMPORTACIONES DE BASE DE DATOS Y AUTH ---
from modules.database.database_init import initialize_database_connections

# Importamos lo esencial de SQL
from modules.database.sql_db import (
     get_user,
     record_login,
     record_logout
)

# Importamos los controladores de MongoDB (Asegúrate de usar el archivo corregido)
from modules.database.discourse_mongo_db import (
    store_student_discourse_result,
    get_student_discourse_analysis,
    update_student_discourse_analysis,
    delete_student_discourse_analysis
)

# Importamos el motor de enrutamiento y autenticación
from modules.ui.ui import main as ui_main
from modules.auth.auth import authenticate_user


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
        # 1. Inicialización de Estados
        if 'initialized' not in st.session_state:
            initialize_session_state()
            st.session_state.initialized = True

        # 2. Conexiones a DB y Modelos NLP
        if 'db_initialized' not in st.session_state:
            st.session_state.db_initialized = initialize_database_connections()

        if 'nlp_models' not in st.session_state:
            st.session_state.nlp_models = initialize_nlp_models()

        # 3. Delegar TODO el control visual al enrutador de UI
        # ui_main() decidirá si mostrar Login, Admin, Profesor o Estudiante
        ui_main()

    except Exception as e:
        logger.error(f"Error crítico en app_main: {str(e)}", exc_info=True)
        st.error("Error al cargar los módulos base.")

if __name__ == "__main__":
    app_main()
