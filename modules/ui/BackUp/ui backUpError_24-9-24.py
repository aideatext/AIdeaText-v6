# Importaciones generales
import streamlit as st
from streamlit_player import st_player  # Necesitarás instalar esta librería: pip install streamlit-player
from streamlit_float import *
from streamlit_antd_components import *
from streamlit_option_menu import *
from streamlit_chat import *
import logging
import time
from datetime import datetime
import re
import io
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from spacy import displacy
import random

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importaciones locales
from translations import get_translations

# Importaciones locales
from ..studentact.student_activities_v2 import display_student_progress

# Importaciones directas de los módulos necesarios
from ..auth.auth import authenticate_user, register_user


from ..database.database_oldFromV2 import (
    get_student_data,
    store_application_request,
    store_morphosyntax_result,
    store_semantic_result,
    store_discourse_analysis_result,
    store_chat_history,
    create_admin_user,
    create_student_user,
    store_user_feedback
)

from ..admin.admin_ui import admin_page

from ..morphosyntax.morphosyntax_interface import display_morphosyntax_interface

from ..semantic.semantic_interface_68ok import display_semantic_interface

from ..discourse.discourse_interface import display_discourse_interface

# Nueva importación para semantic_float_init
#from ..semantic.semantic_float import semantic_float_init
from ..semantic.semantic_float68ok import semantic_float_init


############### Iniciar sesión ######################


def initialize_session_state():
    if 'initialized' not in st.session_state:
        st.session_state.clear()
        st.session_state.initialized = True
        st.session_state.logged_in = False
        st.session_state.page = 'login'
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.lang_code = 'es'  # Idioma por defecto

def main():
    logger.info(f"Entrando en main() - Página actual: {st.session_state.page}")

    if 'nlp_models' not in st.session_state:
        st.error("Los modelos NLP no están inicializados. Por favor, reinicie la aplicación.")
        return

    semantic_float_init()

    if st.session_state.page == 'login':
        login_register_page()
    elif st.session_state.page == 'admin':
        logger.info("Mostrando página de admin")
        admin_page()
    elif st.session_state.page == 'user':
        user_page()
    else:
        logger.warning(f"Página no reconocida: {st.session_state.page}")
        st.error(f"Página no reconocida: {st.session_state.page}")

    logger.info(f"Saliendo de main() - Estado final de la sesión: {st.session_state}")

############### Después de iniciar sesión ######################

def user_page():
    logger.info(f"Entrando en user_page para el usuario: {st.session_state.username}")

    if 'user_data' not in st.session_state or time.time() - st.session_state.get('last_data_fetch', 0) > 60:
        with st.spinner("Cargando tus datos..."):
            try:
                st.session_state.user_data = get_student_data(st.session_state.username)
                st.session_state.last_data_fetch = time.time()
            except Exception as e:
                logger.error(f"Error al obtener datos del usuario: {str(e)}")
                st.error("Hubo un problema al cargar tus datos. Por favor, intenta recargar la página.")
                return

    logger.info(f"Idioma actual: {st.session_state.lang_code}")
    logger.info(f"Modelos NLP cargados: {'nlp_models' in st.session_state}")

    languages = {'Español': 'es', 'English': 'en', 'Français': 'fr'}

    if 'lang_code' not in st.session_state:
        st.session_state.lang_code = 'es'  # Idioma por defecto
    elif not isinstance(st.session_state.lang_code, str) or st.session_state.lang_code not in ['es', 'en', 'fr']:
        logger.warning(f"Invalid lang_code: {st.session_state.lang_code}. Setting to default 'es'")
        st.session_state.lang_code = 'es'

    # Obtener traducciones
    t = get_translations(st.session_state.lang_code)

    # Estilos CSS personalizados (mantener los estilos existentes)
    st.markdown("""
    <style>
    .stSelectbox > div > div {
        padding-top: 0px;
    }
    .stButton > button {
        padding-top: 2px;
        margin-top: 0px;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(3) {
        display: flex;
        justify-content: flex-end;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # Crear un contenedor para la barra superior
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"<h3 style='margin-bottom: 0; padding-top: 10px;'>{t['welcome']}, {st.session_state.username}</h3>", unsafe_allow_html=True)
        with col2:
            selected_lang = st.selectbox(
                t['select_language'],
                list(languages.keys()),
                index=list(languages.values()).index(st.session_state.lang_code),
                key=f"language_selector_{st.session_state.username}_{st.session_state.lang_code}"
            )
            new_lang_code = languages[selected_lang]
            if st.session_state.lang_code != new_lang_code:
                st.session_state.lang_code = new_lang_code
                st.rerun()  # Esto recargará la página con el nuevo idioma
        with col3:
            if st.button(t['logout'], key=f"logout_button_{st.session_state.username}_{st.session_state.lang_code}"):
                # Implementación temporal de logout
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

    st.markdown("---")

    # Mostrar resumen de análisis
    #st.subheader(t['analysis_summary'])
    #col1, col2, col3 = st.columns(3)
    #col1.metric(t['morpho_analyses'], len(st.session_state.user_data['morphosyntax_analyses']))
    #col2.metric(t['semantic_analyses'], len(st.session_state.user_data['semantic_analyses']))
    #col3.metric(t['discourse_analyses'], len(st.session_state.user_data['discourse_analyses']))


    # Opción para exportar datos
    #if st.button(t['export_all_analyses']):
    #    st.info(t['export_in_progress'])
    # Aquí iría la llamada a export_data cuando esté implementada
        # export_data(st.session_state.user_data, t)

    # Crear las pestañas
    tabs = st.tabs([
        t['morpho_tab'],
        t['semantic_tab'],
        t['discourse_tab'],
        t['activities_tab'],
        t['feedback_tab']
    ])

    # Usar las pestañas creadas
    for i, (tab, func) in enumerate(zip(tabs, [
        display_morphosyntax_interface,
        display_semantic_interface,
        display_discourse_interface,
        display_student_progress,
        display_feedback_form
    ])):
        with tab:
            try:
                if i < 5:  # Para las primeras tres pestañas (análisis)
                    func(st.session_state.lang_code, st.session_state.nlp_models, t, st.session_state.user_data)
                elif i == 3:  # Para la pestaña de progreso del estudiante
                    func(st.session_state.username, st.session_state.lang_code, t, st.session_state.user_data)
                else:  # Para la pestaña de feedback
                    func(st.session_state.lang_code, t)
            except Exception as e:
                st.error(f"Error al cargar la pestaña: {str(e)}")
                logger.error(f"Error en la pestaña {i}: {str(e)}", exc_info=True)

    logger.debug(f"Translations loaded: {t}")  # Log para depuración
    logger.info("Finalizada la renderización de user_page")



#####################################

def login_register_page():
    logger.info("Renderizando página de login/registro")
    st.title("AIdeaText")
    st.write("Bienvenido. Por favor, inicie sesión o regístrese.")

    left_column, right_column = st.columns([1, 3])

    with left_column:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])

        with tab1:
            login_form()

        with tab2:
            register_form()

    with right_column:
        display_videos_and_info()


###################################################
def login_form():
    with st.form("login_form"):
        username = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")
        submit_button = st.form_submit_button("Iniciar Sesión")

    if submit_button:
        success, role = authenticate_user(username, password)
        if success:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role
            st.session_state.page = 'admin' if role == 'Administrador' else 'user'
            st.rerun()
        else:
            st.error("Credenciales incorrectas")


###################################################
def register_form():
    st.header("Solicitar prueba de la aplicación")

    name = st.text_input("Nombre completo")
    email = st.text_input("Correo electrónico institucional")
    institution = st.text_input("Institución")
    role = st.selectbox("Rol", ["Estudiante", "Profesor", "Investigador", "Otro"])
    reason = st.text_area("¿Por qué estás interesado en probar AIdeaText?")

    if st.button("Enviar solicitud"):
        if not name or not email or not institution or not reason:
            st.error("Por favor, completa todos los campos.")
        elif not is_institutional_email(email):
            st.error("Por favor, utiliza un correo electrónico institucional.")
        else:
            success = store_application_request(name, email, institution, role, reason)
            if success:
                st.success("Tu solicitud ha sido enviada. Te contactaremos pronto.")
            else:
                st.error("Hubo un problema al enviar tu solicitud. Por favor, intenta de nuevo más tarde.")



###################################################
def is_institutional_email(email):
    forbidden_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
    return not any(domain in email.lower() for domain in forbidden_domains)


###################################################
def display_videos_and_info():
    st.header("Videos: pitch, demos, entrevistas, otros")

    videos = {
        "Presentación en PyCon Colombia, Medellín, 2024": "https://www.youtube.com/watch?v=Jn545-IKx5Q",
        "Presentación fundación Ser Maaestro": "https://www.youtube.com/watch?v=imc4TI1q164",
        "Pitch IFE Explora": "https://www.youtube.com/watch?v=Fqi4Di_Rj_s",
        "Entrevista Dr. Guillermo Ruíz": "https://www.youtube.com/watch?v=_ch8cRja3oc",
        "Demo versión desktop": "https://www.youtube.com/watch?v=nP6eXbog-ZY"
    }

    selected_title = st.selectbox("Selecciona un video tutorial:", list(videos.keys()))

    if selected_title in videos:
        try:
            st_player(videos[selected_title])
        except Exception as e:
            st.error(f"Error al cargar el video: {str(e)}")

    st.markdown("""
    ## Novedades de la versión actual
    - Nueva función de análisis semántico
    - Soporte para múltiples idiomas
    - Interfaz mejorada para una mejor experiencia de usuario
    """)

def display_feedback_form(lang_code, t):
    logging.info(f"display_feedback_form called with lang_code: {lang_code}")

    st.header(t['title'])

    name = st.text_input(t['name'], key=f"feedback_name_{lang_code}")
    email = st.text_input(t['email'], key=f"feedback_email_{lang_code}")
    feedback = st.text_area(t['feedback'], key=f"feedback_text_{lang_code}")

    if st.button(t['submit'], key=f"feedback_submit_{lang_code}"):
        if name and email and feedback:
            if store_user_feedback(st.session_state.username, name, email, feedback):
                st.success(t['success'])
            else:
                st.error(t['error'])
        else:
            st.warning("Por favor, completa todos los campos.")

'''
def display_student_progress(username, lang_code, t):
    student_data = get_student_data(username)

    if student_data is None or len(student_data['entries']) == 0:
        st.warning("No se encontraron datos para este estudiante.")
        st.info("Intenta realizar algunos análisis de texto primero.")
        return

    st.title(f"Progreso de {username}")

    with st.expander("Resumen de Actividades y Progreso", expanded=True):
        # Resumen de actividades
        total_entries = len(student_data['entries'])
        st.write(f"Total de análisis realizados: {total_entries}")

        # Gráfico de tipos de análisis
        analysis_types = [entry['analysis_type'] for entry in student_data['entries']]
        analysis_counts = pd.Series(analysis_types).value_counts()

        fig, ax = plt.subplots()
        analysis_counts.plot(kind='bar', ax=ax)
        ax.set_title("Tipos de análisis realizados")
        ax.set_xlabel("Tipo de análisis")
        ax.set_ylabel("Cantidad")
        st.pyplot(fig)

        # Progreso a lo largo del tiempo
        dates = [datetime.fromisoformat(entry['timestamp']) for entry in student_data['entries']]
        analysis_counts = pd.Series(dates).value_counts().sort_index()

        fig, ax = plt.subplots()
        analysis_counts.plot(kind='line', ax=ax)
        ax.set_title("Análisis realizados a lo largo del tiempo")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Cantidad de análisis")
        st.pyplot(fig)

##########################################################
    with st.expander("Histórico de Análisis Morfosintácticos"):
        morphosyntax_entries = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'morphosyntax']
        for entry in morphosyntax_entries:
            st.subheader(f"Análisis del {entry['timestamp']}")
            if entry['arc_diagrams']:
                st.write(entry['arc_diagrams'][0], unsafe_allow_html=True)


  ##########################################################
    with st.expander("Histórico de Análisis Semánticos"):
        semantic_entries = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'semantic']
        for entry in semantic_entries:
            st.subheader(f"Análisis del {entry['timestamp']}")

            # Mostrar conceptos clave
            if 'key_concepts' in entry:
                st.write("Conceptos clave:")
                concepts_str = " | ".join([f"{concept} ({frequency:.2f})" for concept, frequency in entry['key_concepts']])
                #st.write("Conceptos clave:")
                #st.write(concepts_str)
                st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{concepts_str}</div>", unsafe_allow_html=True)

            # Mostrar gráfico
            if 'graph' in entry:
                try:
                    img_bytes = base64.b64decode(entry['graph'])
                    st.image(img_bytes, caption="Gráfico de relaciones conceptuales")
                except Exception as e:
                    st.error(f"No se pudo mostrar el gráfico: {str(e)}")

##########################################################
    with st.expander("Histórico de Análisis Discursivos"):
        discourse_entries = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'discourse']
        for entry in discourse_entries:
            st.subheader(f"Análisis del {entry['timestamp']}")

            # Mostrar conceptos clave para ambos documentos
            if 'key_concepts1' in entry:
                concepts_str1 = " | ".join([f"{concept} ({frequency:.2f})" for concept, frequency in entry['key_concepts1']])
                st.write("Conceptos clave del documento 1:")
                #st.write(concepts_str1)
                st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{concepts_str1}</div>", unsafe_allow_html=True)

            if 'key_concepts2' in entry:
                concepts_str2 = " | ".join([f"{concept} ({frequency:.2f})" for concept, frequency in entry['key_concepts2']])
                st.write("Conceptos clave del documento 2:")
                #st.write(concepts_str2)
                st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{concepts_str2}</div>", unsafe_allow_html=True)

            try:
                if 'combined_graph' in entry and entry['combined_graph']:
                    img_bytes = base64.b64decode(entry['combined_graph'])
                    st.image(img_bytes)
                elif 'graph1' in entry and 'graph2' in entry:
                    col1, col2 = st.columns(2)
                    with col1:
                        if entry['graph1']:
                            img_bytes1 = base64.b64decode(entry['graph1'])
                            st.image(img_bytes1)
                    with col2:
                        if entry['graph2']:
                            img_bytes2 = base64.b64decode(entry['graph2'])
                            st.image(img_bytes2)
                else:
                    st.write("No se encontraron gráficos para este análisis.")
            except Exception as e:
                st.error(f"No se pudieron mostrar los gráficos: {str(e)}")
                st.write("Datos de los gráficos (para depuración):")
                if 'graph1' in entry:
                    st.write("Graph 1:", entry['graph1'][:100] + "...")
                if 'graph2' in entry:
                    st.write("Graph 2:", entry['graph2'][:100] + "...")
                if 'combined_graph' in entry:
                    st.write("Combined Graph:", entry['combined_graph'][:100] + "...")

##########################################################
    with st.expander("Histórico de Conversaciones con el ChatBot"):
        if 'chat_history' in student_data:
            for i, chat in enumerate(student_data['chat_history']):
                st.subheader(f"Conversación {i+1} - {chat['timestamp']}")
                for message in chat['messages']:
                    if message['role'] == 'user':
                        st.write("Usuario: " + message['content'])
                    else:
                        st.write("Asistente: " + message['content'])
                st.write("---")
        else:
            st.write("No se encontraron conversaciones con el ChatBot.")

    # Añadir logs para depuración
    if st.checkbox("Mostrar datos de depuración"):
        st.write("Datos del estudiante (para depuración):")
        st.json(student_data)


'''

# Definición de __all__ para especificar qué se exporta
__all__ = ['main', 'login_register_page', 'initialize_session_state']

# Bloque de ejecución condicional
if __name__ == "__main__":
    main()
