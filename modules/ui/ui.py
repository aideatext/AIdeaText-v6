import streamlit as st
import logging
from PIL import Image
from translations import get_translations
from modules.ui.user_page import user_page
from modules.auth.auth import authenticate_user

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

def main():
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    lang_code = st.session_state.get('lang_code', 'es')
    t = get_translations(lang_code)

    if not st.session_state.logged_in:
        login_register_page(lang_code, t)
    else:
        # Si ya está logueado, vamos a la página de usuario
        user_page(st.session_state.username, lang_code, t)

if __name__ == "__main__":
    main()
