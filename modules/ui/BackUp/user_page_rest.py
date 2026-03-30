# modules/ui/user_page.py

import streamlit as st
import logging
from datetime import datetime, timezone
from dateutil.parser import parse

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#Importaciones locales.

from ...utils.widget_utils import generate_unique_key

from session_state import initialize_session_state, logout

from translations import get_translations

from ...auth.auth import authenticate_user, authenticate_student, authenticate_admin

from ...admin.admin_ui import admin_page

from ...chatbot import display_sidebar_chat

# Students activities

from ...studentact.student_activities_v2 import display_student_activities

#from ..studentact.current_situation_interface import display_current_situation_interface
#from ..studentact.current_situation_analysis import analyze_text_dimensions


##Importaciones desde la configuración de bases datos #######

from ...database.sql_db import (
    get_user,
    get_admin_user,
    get_student_user,
    get_teacher_user,
    create_user,
    create_student_user,
    create_teacher_user,
    create_admin_user,
    update_student_user,  # Agregada
    delete_student_user,  # Agregada
    record_login,
    record_logout,
    get_recent_sessions,
    get_user_total_time, 
    store_application_request,
    store_student_feedback
)

from ...database.mongo_db import (
    get_collection,
    insert_document,
    find_documents,
    update_document,
    delete_document
)

from ...database.semantic_mongo_db import (
    store_student_semantic_result,
    get_student_semantic_analysis,
    update_student_semantic_analysis,
    delete_student_semantic_analysis,
    get_student_semantic_data
)

from ...database.semantic_mongo_live_db import get_student_semantic_live_analysis

from ...database.chat_mongo_db import store_chat_history, get_chat_history

##Importaciones desde los análisis #######

from ...semantic.semantic_live_interface import display_semantic_live_interface

from ...semantic.semantic_interface import (
    display_semantic_interface, 
    display_semantic_results
)

from ...discourse.discourse_interface import (    # Agregar esta importación
    display_discourse_interface,
    display_discourse_results
)


####################################################################################
def user_page(lang_code, t):
    logger.info(f"Entrando en user_page para el estudiante: {st.session_state.username}")

    # Inicializar el tab seleccionado si no existe
    if 'selected_tab' not in st.session_state:
        st.session_state.selected_tab = 0

    # Manejar la carga inicial de datos del usuario
    if 'user_data' not in st.session_state:
        with st.spinner(t.get('loading_data', "Cargando tus datos...")):
            try:
                # Obtener datos semánticos
                semantic_data = get_student_semantic_data(st.session_state.username)
                
                # Verificar si la operación fue exitosa
                if semantic_data.get('status') == 'error':
                    raise Exception(semantic_data.get('error', 'Error desconocido al obtener datos'))
                
                # Almacenar datos en session_state
                st.session_state.user_data = {
                    'semantic_analyses': semantic_data.get('entries', []),
                    'analysis_count': semantic_data.get('count', 0),
                    'last_analysis': semantic_data['entries'][0] if semantic_data['entries'] else None,
                    'username': st.session_state.username,
                    'loaded_at': datetime.now(timezone.utc).isoformat()
                }
                
                st.session_state.last_data_fetch = datetime.now(timezone.utc).isoformat()
                
            except Exception as e:
                logger.error(f"Error al obtener datos del usuario: {str(e)}")
                # Crear estructura vacía para evitar errores
                st.session_state.user_data = {
                    'semantic_analyses': [],
                    'analysis_count': 0,
                    'last_analysis': None,
                    'username': st.session_state.username,
                    'error': str(e)
                }
                st.error(t.get('data_load_error', "Hubo un problema al cargar tus datos. Algunas funciones pueden estar limitadas."))
                # No hacer return aquí para permitir que la aplicación continúe

    logger.info(f"Idioma actual: {st.session_state.lang_code}")
    logger.info(f"Modelos NLP cargados: {'nlp_models' in st.session_state}")

    # Configuración de idiomas disponibles
    languages = {'Español': 'es', 'English': 'en', 'Français': 'fr', 'Português': 'pt'}

    # Estilos CSS personalizados
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

    # Barra superior con información del usuario y controles
    with st.container():
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.markdown(f"<h3 style='margin-bottom: 0; padding-top: 10px;'>{t['welcome']}, {st.session_state.username}</h3>", 
                       unsafe_allow_html=True)
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
                st.rerun()
        with col3:
            if st.button(t['logout'], 
                        key=f"logout_button_{st.session_state.username}_{st.session_state.lang_code}"):
                st.session_state.clear()
                st.rerun()

    st.markdown("---")

    # Asegurarse de que tenemos las traducciones del chatbot
    chatbot_t = t.get('CHATBOT_TRANSLATIONS', {}).get(lang_code, {})
    
    # Mostrar chatbot en sidebar
    display_sidebar_chat(lang_code, chatbot_t)

    # Inicializar estados para todos los tabs
    if 'tab_states' not in st.session_state:
        st.session_state.tab_states = {
            'semantic_live_active': False,
            'semantic_active': False,
            'discourse_active': False,
            'activities_active': False,
            'feedback_active': False
        }
    
    # Sistema de tabs
    tab_names = [
        t.get('semantic_live_tab', 'Análisis Semántico (Texto Directo)'),
        t.get('semantic_tab', 'Análisis Semántico'),
        t.get('discourse_tab', 'Análisis comparado de textos'),
        t.get('activities_tab', 'Registro de mis actividades'),
        t.get('feedback_tab', 'Formulario de Comentarios')
    ]
    
    tabs = st.tabs(tab_names)

    # Manejar el contenido de cada tab
    for index, tab in enumerate(tabs):
        with tab:
            try:
                # Actualizar el tab seleccionado solo si no hay un análisis activo
                if tab.selected and st.session_state.selected_tab != index:
                    can_switch = True
                    for state_key in st.session_state.tab_states.keys():
                        if st.session_state.tab_states[state_key] and index != get_tab_index(state_key):
                            can_switch = False
                            break
                    if can_switch:
                        st.session_state.selected_tab = index

                if index == 0:  # Semántico Live
                    st.session_state.tab_states['semantic_live_active'] = True
                    display_semantic_live_interface(
                        st.session_state.lang_code,
                        st.session_state.nlp_models,
                        t
                    )
                
                elif index == 1:  # Semántico
                    st.session_state.tab_states['semantic_active'] = True
                    display_semantic_interface(
                        st.session_state.lang_code,
                        st.session_state.nlp_models,
                        t  # Pasamos todo el diccionario de traducciones
                    )
                
                elif index == 2:  # Discurso
                    st.session_state.tab_states['discourse_active'] = True
                    display_discourse_interface(
                        st.session_state.lang_code,
                        st.session_state.nlp_models,
                        t  # Pasamos todo el diccionario de traducciones
                    )

                elif index == 3:  # Actividades
                    st.session_state.tab_states['activities_active'] = True
                    display_student_activities(
                        username=st.session_state.username,
                        lang_code=st.session_state.lang_code,
                        t=t  # Pasamos todo el diccionario de traducciones
                    )

                elif index == 4:  # Feedback
                    st.session_state.tab_states['feedback_active'] = True
                    display_feedback_form(
                        st.session_state.lang_code,
                        t  # Ya estaba recibiendo el diccionario completo
                    )

            except Exception as e:
                # Desactivar el estado en caso de error
                state_key = get_state_key_for_index(index)
                if state_key:
                    st.session_state.tab_states[state_key] = False
                logger.error(f"Error en tab {index}: {str(e)}")
                st.error(t.get('tab_error', 'Error al cargar esta sección'))

    # Panel de depuración (solo visible en desarrollo)
    if st.session_state.get('debug_mode', False):
        with st.expander("Debug Info"):
            st.write(f"Página actual: {st.session_state.page}")
            st.write(f"Usuario: {st.session_state.get('username', 'No logueado')}")
            st.write(f"Rol: {st.session_state.get('role', 'No definido')}")
            st.write(f"Idioma: {st.session_state.lang_code}")
            st.write(f"Tab seleccionado: {st.session_state.selected_tab}")
            st.write(f"Última actualización de datos: {st.session_state.get('last_data_fetch', 'Nunca')}")
            st.write(f"Traducciones disponibles: {list(t.keys())}")


def get_tab_index(state_key):
    """Obtiene el índice del tab basado en la clave de estado"""
    index_map = {
        'semantic_live_active': 0,
        'semantic_active': 1,
        'discourse_active': 2,
        'activities_active': 3,
        'feedback_active': 4
    }
    return index_map.get(state_key, -1)

def get_state_key_for_index(index):
    """Obtiene la clave de estado basada en el índice del tab"""
    state_map = {
        0: 'semantic_live_active',
        1: 'semantic_active',
        2: 'discourse_active',
        3: 'activities_active',
        4: 'feedback_active'
    }
    return state_map.get(index)

###################################
######################################################################    
def display_feedback_form(lang_code, t):
    """
    Muestra el formulario de retroalimentación
    Args:
        lang_code: Código de idioma
        t: Diccionario de traducciones
    """
    logging.info(f"display_feedback_form called with lang_code: {lang_code}")

    # Obtener traducciones específicas para el formulario de feedback
    feedback_t = t.get('FEEDBACK', {})
    
    # Si no hay traducciones específicas, usar el diccionario general
    if not feedback_t:
        feedback_t = t

    #st.header(feedback_t.get('feedback_title', 'Formulario de Opinión'))

    name = st.text_input(feedback_t.get('name', 'Nombre'))
    email = st.text_input(feedback_t.get('email', 'Correo electrónico'))
    feedback = st.text_area(feedback_t.get('feedback', 'Retroalimentación'))

    if st.button(feedback_t.get('submit', 'Enviar')):
        if name and email and feedback:
            if store_student_feedback(st.session_state.username, name, email, feedback):
                st.success(feedback_t.get('feedback_success', 'Gracias por tu respuesta'))
            else:
                st.error(feedback_t.get('feedback_error', 'Hubo un problema al enviar el formulario. Por favor, intenta de nuevo.'))
        else:
            st.warning(feedback_t.get('complete_all_fields', 'Por favor, completa todos los campos'))