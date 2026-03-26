# modules/ui/user_page.py

import streamlit as st
import logging
from datetime import datetime
import requests  # Para conectar con el motor NLP en el puerto 8080

# Importaciones locales manteniendo la consistencia con user_page_rest.py
from ..utils.widget_utils import generate_unique_key
from ..auth.auth import logout
from ..chatbot import display_sidebar_chat # El Tutor Virtual
from ..studentact.student_activities_v2 import display_student_activities

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def user_page(username, lang_code, t):
    """
    Interfaz principal del estudiante.
    Mantiene la coherencia de variables de user_page_rest.py
    """
    logger.info(f"Renderizando página para el estudiante: {username}")

    # --- BARRA LATERAL (SIDEBAR) ---
    with st.sidebar:
        # 1. Logo de AIdeaText
        try:
            st.image("assets/logo_aideatext.png", use_container_width=True)
        except Exception:
            st.title("📚 AIdeaText")
        
        st.divider()

        # 2. Tutor Virtual (Interacción escrita)
        st.subheader(t.get('tutor_title', 'Tutor Virtual'))
        # Usamos la función que ya tenías importada en el rest
        display_sidebar_chat(username, lang_code)
        
        st.divider()
        
        # 3. Botón de Salida
        if st.button(t.get('logout', 'Cerrar Sesión'), key="logout_btn"):
            logout()
            st.rerun()

    # --- CUERPO PRINCIPAL ---
    st.title(f"🚀 {t.get('welcome', 'Panel de Aprendizaje')}")
    st.caption(f"Estudiante: {username} | Piloto UNIFE")

    # Definición de pestañas para organizar los análisis y tareas
    tab_act, tab_quick, tab_sem, tab_m1 = st.tabs([
        t.get('activities', 'Mis Tareas'),
        "⚡ Análisis Rápido",
        "🧠 Análisis Semántico",
        "⚖️ Coherencia (M1)"
    ])

    with tab_act:
        st.header("Tareas Asignadas")
        # Conexión directa a DocumentDB para ver actividades
        display_student_activities(username, lang_code, t)
        
        # Bloque de feedback del profesor (Histórico)
        st.divider()
        st.subheader("💬 Comentarios del Profesor")
        st.info("Aquí aparecerán las observaciones que tu profesor realice sobre tus avances.")

    with tab_quick:
        st.header("Revisión Instantánea")
        st.write("Análisis de ortografía y estructura gramatical.")
        # Aquí se invocará el módulo de quick_analysis
        st.warning("Módulo en fase de conexión...")

    with tab_sem:
        st.header("Mapa de Conceptos")
        st.write("Visualiza la red semántica de tus ideas.")
        # Aquí se invocará el módulo de semantic_analysis (Grafos)
        st.warning("Módulo en fase de conexión...")

    with tab_m1:
        st.header("Métrica M1: Coherencia Argumentativa")
        st.write("Esta sección compara lo que escribiste en tu tarea contra lo que conversaste con el Tutor Virtual.")
        
        if st.button("Calcular Consistencia Semántica", key="calc_m1"):
            # Lógica compacta: Enviamos texto vs chat al puerto 8080
            st.info("Comparando tu escrito con el historial del chat...")
            # Placeholder para la llamada al microservicio
            # response = requests.post("http://localhost:8080/analyze_m1", json={...})
            st.success("Cálculo completado (Simulación): 85% de coherencia.")

# Nota: Esta estructura permite que el profesor vea datos reales 
# una vez que el estudiante interactúe con estas pestañas.