# modules/ui/user_page.py

import streamlit as st
import logging
from datetime import datetime, timezone
from dateutil.parser import parse

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- IMPORTACIONES LOCALES Y SESIÓN ---
from ..utils.widget_utils import generate_unique_key
from session_state import initialize_session_state, logout
from translations import get_translations
from ..auth.auth import authenticate_user, authenticate_student, authenticate_admin
from ..admin.admin_ui import admin_page
from ..chatbot import display_sidebar_chat
from ..studentact.student_activities_v2 import display_student_activities

# --- IMPORTACIONES DE BASES DE DATOS (SQL) ---
from ..database.sql_db import (
    get_user,
    get_admin_user,
    get_student_user,
    get_teacher_user,
    create_user,
    create_student_user,
    create_teacher_user,
    create_admin_user,
    update_student_user,
    delete_student_user,
    record_login,
    record_logout,
    get_recent_sessions,
    get_user_total_time, 
    store_application_request,
    store_student_feedback
)

# --- IMPORTACIONES DE BASES DE DATOS (NOSQL / MONGO) ---
from ..database.mongo_db import (
    get_collection, insert_document, find_documents, 
    update_document, delete_document
)
from ..database.semantic_mongo_db import (
    store_student_semantic_result,
    get_student_semantic_analysis,
    update_student_semantic_analysis,
    delete_student_semantic_analysis,
    get_student_semantic_data
)
from ..database.semantic_mongo_live_db import get_student_semantic_live_analysis
from ..database.chat_mongo_db import store_chat_history, get_chat_history

# --- IMPORTACIONES DE INTERFACES DE ANÁLISIS ---
from ..semantic.semantic_live_interface import display_semantic_live_interface
from ..semantic.semantic_interface import (
    display_semantic_interface, 
    display_semantic_results
)
from ..discourse.discourse_interface import (
    display_discourse_interface,
    display_discourse_results
)

def user_page(username, lang_code, t):
    """
    Página principal del estudiante. 
    Acepta 3 argumentos para evitar el TypeError reportado.
    """
    logger.info(f"Cargando User Page para: {username}")

    # --- 1. CARGA INICIAL DE DATOS ---
    # Obtenemos los datos del estudiante desde SQL para tener el perfil completo
    student_user = get_student_user(username)
    
    # --- 2. BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        try:
            st.image("assets/logo_aideatext.png", use_container_width=True)
        except:
            st.title("📚 AIdeaText")
        
        st.divider()
        
        # El Tutor Virtual (Sidebar Chat persistente)
        st.subheader(t.get('tutor_title', 'Tutor Virtual'))
        display_sidebar_chat(username, lang_code)
        
        st.divider()
        if st.button(t.get('logout', 'Cerrar Sesión'), key="btn_logout_main"):
            logout()
            st.rerun()

    # --- 3. CUERPO PRINCIPAL ---
    st.title(f"🚀 {t.get('welcome', 'Bienvenido')}, {username}")

    # Definición de nombres de Tabs según tus traducciones
    tab_names = [
        t.get('semantic_live_tab', 'Análisis Semántico (Texto Directo)'),
        t.get('semantic_tab', 'Análisis Semántico'),
        t.get('discourse_tab', 'Análisis comparado de textos'),
        t.get('activities_tab', 'Registro de mis actividades'),
        t.get('feedback_tab', 'Formulario de Comentarios')
    ]
    
    tabs = st.tabs(tab_names)

    # Preparar diccionarios de traducción específicos para las interfaces
    # Si 't' no los tiene, pasamos 't' completo o un dict vacío según requiera el módulo
    semantic_t = t.get('SEMANTIC', t) # verficar
    discourse_t = t.get('DISCOURSE', t) # verificar

    # --- TAB 0: Análisis Semántico Directo ---
    with tabs[0]:
        display_semantic_live_interface(username, lang_code)

    # --- TAB 1: Análisis Semántico (Histórico/Archivos) ---
    with tabs[1]:
        display_semantic_interface(username, lang_code)

    # --- TAB 2: Análisis Comparado (Métrica M1) ---
    with tabs[2]:
        # Aquí es donde conectaremos el "Match" entre Chat y Escrito
        display_discourse_interface(username, lang_code)

    # --- TAB 3: Registro de Actividades (Piloto UNIFE) ---
    with tabs[3]:
        display_student_activities(username, lang_code, t)

    # --- TAB 4: Feedback ---
    with tabs[4]:
        display_feedback_form(lang_code, t)

def display_feedback_form(lang_code, t):
    """Interfaz para envío de comentarios"""
    feedback_t = t.get('FEEDBACK', t)
    
    with st.form("user_feedback_form"):
        name = st.text_input(feedback_t.get('name', 'Nombre'))
        email = st.text_input(feedback_t.get('email', 'Correo electrónico'))
        feedback = st.text_area(feedback_t.get('feedback', 'Retroalimentación'))
        
        submit = st.form_submit_button(feedback_t.get('submit', 'Enviar'))
        
        if submit:
            if name and email and feedback:
                if store_student_feedback(st.session_state.username, name, email, feedback):
                    st.success(feedback_t.get('feedback_success', 'Gracias por tu respuesta'))
                else:
                    st.error("Error al guardar el feedback.")
            else:
                st.warning("Por favor completa todos los campos.")