import streamlit as st
import logging
from ..studentact.student_activities_v2 import display_student_activities

logger = logging.getLogger(__name__)

def user_page(username, lang_code, t):
    logger.info(f"Renderizando página para el usuario: {username}")
    st.title(f"{t.get('welcome', 'Bienvenido')}, {username}")
    
    tab1, tab2 = st.tabs([t.get('activities', 'Actividades'), t.get('contact', 'Contacto')])
    
    with tab1:
        # Aquí es donde se conectará con DocumentDB usando el username
        display_student_activities(username, lang_code, t)
    
    with tab2:
        st.write("Soporte técnico UNIFE")
