import streamlit as st
import logging
from PIL import Image

from translations import get_translations
from modules.ui.user_page import user_page
from modules.admin.admin_ui import admin_page  # Importamos Admin
from modules.ui.professor.professor_ui import professor_page  # Importamos Profesor
from modules.auth.auth import authenticate_user
from modules.database.sql_db import execute_query, create_user_expanded

logger = logging.getLogger(__name__)

def show_landing_content(t):
    """Muestra el contenido informativo (Landing Page)"""
    st.markdown(f"## {t.get('welcome_title', 'Welcome to AIdeaText')}")
    
    tab1, tab2, tab3 = st.tabs(["Propósito", "Investigación", "Eventos"])
    
    with tab1:
        st.write("AIdeaText es una plataforma diseñada para el desarrollo de habilidades de argumentación y lectoescritura mediante IA.")
    
    with tab2:
        st.info("Piloto actual: UNIFE, Lima, Perú. Investigación longitudinal sobre el progreso académico.")
        
    with tab3:
        st.write("Próximos eventos 2026: Participación en paneles de IA y Democracia.")

def login_register_page(lang_code, t):
    """Interfaz que combina Landing Page + Login"""
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        show_landing_content(t)
        
    with col2:
        st.markdown("### Acceso")
        with st.form("login_form"):
            username = st.text_input(t.get('username', 'Usuario')).strip()
            password = st.text_input(t.get('password', 'Contraseña'), type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user['username']
                    st.session_state.role = user['role']
                    st.session_state.page = 'user'
                    st.success("Acceso concedido")
                    st.rerun()
                else:
                    st.error("Credenciales no válidas")

def login_register_page(lang_code, t):
    """Interfaz que combina Landing Page + Login"""
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        show_landing_content(t)
        
    with col2:
        st.markdown("### Acceso")
        with st.form("login_form"):
            username = st.text_input(t.get('username', 'Usuario')).strip()
            password = st.text_input(t.get('password', 'Contraseña'), type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                user = authenticate_user(username, password)
                if user:
                    # Guardamos TODO el contexto en la sesión para el enrutamiento
                    st.session_state.logged_in = True
                    st.session_state.username = user.get('id')
                    st.session_state.role = user.get('role')
                    st.session_state.class_id = user.get('class_id')
                    st.session_state.institution = user.get('institution')
                    st.session_state.page = 'user'
                    st.success(f"Bienvenido, {st.session_state.role}")
                    st.rerun()
                else:
                    st.error("Credenciales no válidas")

def main():
    # Inicialización de estados básicos
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    lang_code = st.session_state.get('lang_code', 'es')
    t = get_translations(lang_code)

    if not st.session_state.logged_in:
        login_register_page(lang_code, t)
    else:
        # --- SISTEMA DE ENRUTAMIENTO POR ROL ---
        role = st.session_state.get('role')
        
        if role == 'Admin' or role == 'Administrador':
            from modules.admin.admin_ui import admin_page
            admin_page()
        
        elif role == 'Profesor':
            from modules.ui.professor.professor_ui import professor_page
            professor_page()
            
        elif role == 'Estudiante':
            from modules.ui.user_page import user_page
            user_page(st.session_state.username, lang_code, t)
            
        else:
            st.error(f"Rol '{role}' no reconocido. Contacte a soporte.")