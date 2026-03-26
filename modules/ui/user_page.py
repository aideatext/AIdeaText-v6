# modules/ui/user_page.py

import streamlit as st
import logging
from datetime import datetime, timezone
from dateutil.parser import parse

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importaciones locales
from ..utils.widget_utils import generate_unique_key
from session_state import logout
from ..chatbot import display_sidebar_chat
from ..studentact.student_activities_v2 import display_student_activities

# Importaciones de base de datos (SQL y NoSQL según tu estructura)
from ..database.sql_db import (
    get_student_user,
    update_student_user
)
from ..database.database_oldFromV2 import (
    get_student_data,
    store_user_feedback # Ajustado según tus archivos
)

def user_page(username, lang_code, t):
    """
    Página principal del estudiante con carga de datos e interfaz de pestañas.
    """
    logger.info(f"Cargando interfaz de usuario para: {username}")

    # --- CARGA INICIAL DE DATOS ---
    # Intentamos obtener datos existentes del estudiante para pre-cargar la interfaz
    student_data = get_student_data(username)
    
    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        try:
            st.image("assets/logo_aideatext.png", use_container_width=True)
        except:
            st.title("📚 AIdeaText")
        
        st.divider()
        
        # El Tutor Virtual (Bloque persistente)
        st.subheader(t.get('tutor_title', 'Tutor Virtual'))
        display_sidebar_chat(username, lang_code)
        
        st.divider()
        if st.button(t.get('logout', 'Cerrar Sesión'), key="logout_btn_user"):
            logout()
            st.rerun()

    # --- CUERPO PRINCIPAL ---
    st.title(f"🚀 {t.get('welcome', 'Panel de Control')}")

    # Sistema de tabs solicitado
    tab_names = [
        t.get('semantic_live_tab', 'Análisis Semántico (Texto Directo)'),
        t.get('semantic_tab', 'Análisis Semántico'),
        t.get('discourse_tab', 'Análisis comparado de textos'),
        t.get('activities_tab', 'Registro de mis actividades'),
        t.get('feedback_tab', 'Formulario de Comentarios')
    ]
    
    tabs = st.tabs(tab_names)

    # --- CONTENIDO DE LAS TABS ---

    with tabs[0]: # Análisis Semántico (Texto Directo)
        st.header(tab_names[0])
        st.info("Escribe o pega tu texto aquí para un análisis inmediato.")
        # Aquí irá la lógica de live analysis

    with tabs[1]: # Análisis Semántico
        st.header(tab_names[1])
        # Lógica de carga de archivos o grafos guardados

    with tabs[2]: # Análisis comparado de textos (Métrica M1)
        st.header(tab_names[2])
        st.write("Comparativa entre versiones de texto o Chat vs. Escrito.")

    with tabs[3]: # Registro de mis actividades
        st.header(tab_names[3])
        # Conexión con DocumentDB para el piloto UNIFE
        display_student_activities(username, lang_code, t)

    with tabs[4]: # Formulario de Comentarios
        st.header(tab_names[4])
        display_feedback_form(lang_code, t)

def display_feedback_form(lang_code, t):
    """
    Muestra el formulario de retroalimentación restaurado
    """
    feedback_t = t.get('FEEDBACK', t)
    
    with st.container():
        name = st.text_input(feedback_t.get('name', 'Nombre'), key="fb_name")
        email = st.text_input(feedback_t.get('email', 'Correo electrónico'), key="fb_email")
        feedback = st.text_area(feedback_t.get('feedback', 'Retroalimentación'), key="fb_text")

        if st.button(feedback_t.get('submit', 'Enviar Feedback')):
            if name and email and feedback:
                # Aquí llamarías a tu función de guardado
                st.success(feedback_t.get('feedback_success', 'Gracias por tus comentarios.'))
            else:
                st.error("Por favor, completa todos los campos.")