# modules/ui/user_page.py

import streamlit as st
import logging
from session_state import logout

# --- IMPORTACIONES DE INTERFACES DE ANÁLISIS ---
from ..semantic.semantic_live_interface import display_semantic_live_interface
from ..semantic.semantic_interface import display_semantic_interface
from ..discourse.discourse_interface import display_discourse_interface
from ..studentact.student_activities_v2 import display_student_activities
from ..chatbot import display_sidebar_chat

# --- IMPORTACIONES DE BASE DE DATOS (SQL para feedback) ---
from ..database.sql_db import store_student_feedback

logger = logging.getLogger(__name__)

def user_page(username, lang_code, t):
    """
    Página principal del usuario (Estudiante).
    TAB 3 ahora se limita exclusivamente al historial de Chats con el Tutor.
    """
    logger.info(f"Renderizando User Page para: {username}")
    
    # Recuperar modelos NLP cargados en la sesión
    nlp_models = st.session_state.get('nlp_models')

    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        try:
            st.image("assets/logo_aideatext.png", width=250) 
        except:
            st.title("📚 AIdeaText")
        
        st.divider()
        st.subheader(t.get('tutor_title', 'Tutor Virtual'))
        display_sidebar_chat(username, lang_code)
        
        st.divider()
        if st.button(t.get('logout', 'Cerrar Sesión'), key="logout_btn"):
            logout()
            st.rerun()

    # --- CUERPO PRINCIPAL ---
    st.title(f"🚀 {t.get('welcome', 'Panel de Control')}")

    # Definición de etiquetas de pestañas
    tab_labels = [
        t.get('semantic_live_tab', 'Análisis Rápido'),      # TAB 0
        t.get('semantic_tab', 'Análisis Semántico'),       # TAB 1
        t.get('discourse_tab', 'Análisis Comparado'),      # TAB 2
        t.get('activities_tab', 'Mi Historial Completo'),  # <--- CAMBIADO (TAB 3)
        t.get('feedback_tab', 'Feedback')                  # TAB 4
    ]
    
    tabs = st.tabs(tab_labels)

    # Diccionarios de traducción
    semantic_t = t.get('SEMANTIC', t)
    discourse_t = t.get('DISCOURSE', t)

    # --- TAB 0: Análisis Rápido (Texto Directo) ---
    with tabs[0]:
        display_semantic_live_interface(lang_code, nlp_models, semantic_t)

    # --- TAB 1: Análisis Semántico (Documentos) ---
    with tabs[1]:
        display_semantic_interface(lang_code, nlp_models, semantic_t)

    # --- TAB 2: Análisis Comparado (Dual) ---
    with tabs[2]:
        display_discourse_interface(lang_code, nlp_models, discourse_t)

    # --- TAB 3: Registro de Actividades (SOLO CHATS) ---
    with tabs[3]:
        st.subheader(t.get('chat_history_title', 'Registro Histórico de Actividades'))
        # Esta función cargará las 4 sub-pestañas internas (Live, Semántico, Comparado, Chat)
        display_student_activities(username, lang_code, t)

    # --- TAB 4: Formulario de Feedback ---
    with tabs[4]:
        display_feedback_form(lang_code, t)

def display_feedback_form(lang_code, t):
    feedback_t = t.get('FEEDBACK', t)
    st.subheader(feedback_t.get('feedback_title', 'Formulario de Opinión'))
    
    name = st.text_input(feedback_t.get('name', 'Nombre'), key="fb_name")
    email = st.text_input(feedback_t.get('email', 'Correo'), key="fb_email")
    feedback = st.text_area(feedback_t.get('feedback', 'Comentarios'), key="fb_text")

    if st.button(feedback_t.get('submit', 'Enviar'), key="fb_submit"):
        if name and email and feedback:
            if store_student_feedback(st.session_state.username, name, email, feedback):
                st.success(feedback_t.get('feedback_success', 'Gracias.'))
            else:
                st.error("Error al guardar.")