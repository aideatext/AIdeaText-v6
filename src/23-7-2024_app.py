## app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from modules.database import initialize_mongodb_connection, get_student_data, store_analysis_result
from modules.auth import authenticate_user, get_user_role
from modules.ui import login_page, register_page, display_chat_interface, display_student_progress, display_text_analysis_interface
from modules.morpho_analysis import get_repeated_words_colors, highlight_repeated_words, POS_COLORS, POS_TRANSLATIONS
from modules.syntax_analysis import visualize_syntax
from modules.spacy_utils import load_spacy_models

st.set_page_config(page_title="AIdeaText", layout="wide", page_icon="random")

def main_app():
    nlp_models = load_spacy_models()
    
    languages = {'Español': 'es', 'English': 'en', 'Français': 'fr'}
    selected_lang = st.sidebar.selectbox("Select Language / Seleccione el idioma / Choisissez la langue", list(languages.keys()))
    lang_code = languages[selected_lang]
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        display_chat_interface()
    
    with col2:
        st.markdown("### AIdeaText - Análisis morfológico y sintáctico")
        
        if st.session_state.role == "Estudiante":
            tabs = st.tabs(["Análisis de Texto", "Mi Progreso"])
            with tabs[0]:
                display_text_analysis_interface(nlp_models, lang_code)
            with tabs[1]:
                display_student_progress(st.session_state.username)
        elif st.session_state.role == "Profesor":
            st.write("Bienvenido, profesor. Aquí podrás ver el progreso de tus estudiantes.")
            # Agregar lógica para mostrar el progreso de los estudiantes

def main():
    if not initialize_mongodb_connection():
        st.warning("La conexión a la base de datos MongoDB no está disponible. Algunas funciones pueden no estar operativas.")
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        menu = ["Iniciar Sesión", "Registrarse"]
        choice = st.sidebar.selectbox("Menu", menu)
        if choice == "Iniciar Sesión":
            login_page()
        elif choice == "Registrarse":
            register_page()
    else:
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state.logged_in = False
            st.rerun()
        main_app()

if __name__ == "__main__":
    main()