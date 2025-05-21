# Importaciones generales
import streamlit as st
import re
import io
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import time
from datetime import datetime
from streamlit_player import st_player  # Necesitarás instalar esta librería: pip install streamlit-player
from spacy import displacy
import logging
import random

######################################################
# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

######################################################
# Importaciones locales
from ..email.email import send_email_notification

######################################################
# Importaciones locales de autenticación y base de datos
from ..auth.auth import (
    authenticate_user,
    register_user
)

######################################################
from ..database.database_oldFromV2 import (
    get_student_data,
    store_application_request,
    store_morphosyntax_result,
    store_semantic_result,
    store_discourse_analysis_result,
    store_chat_history,
    create_admin_user,
    create_student_user,
    store_user_feedback,
    export_analysis_and_chat
)

######################################################
# Importaciones locales de uiadmin
from ..admin.admin_ui import admin_page

######################################################
# Importaciones locales funciones de análisis
from ..text_analysis.morpho_analysis import (
    generate_arc_diagram,
    get_repeated_words_colors,
    highlight_repeated_words,
    POS_COLORS,
    POS_TRANSLATIONS,
    perform_advanced_morphosyntactic_analysis
)

######################################################
from ..text_analysis.semantic_analysis import (
    #visualize_semantic_relations,
    perform_semantic_analysis,
    create_concept_graph,
    visualize_concept_graph
)

######################################################
from ..text_analysis.discourse_analysis import (
    perform_discourse_analysis,
    display_discourse_analysis_results
)

######################################################
from ..chatbot.chatbot import (
    initialize_chatbot,
    get_chatbot_response,
    process_chat_input,
    TEXT_TYPES
)

##################################################################################################
def initialize_session_state():
    if 'initialized' not in st.session_state:
        st.session_state.clear()
        st.session_state.initialized = True
        st.session_state.logged_in = False
        st.session_state.page = 'login'
        st.session_state.username = None
        st.session_state.role = None

##################################################################################################
def main():
    initialize_session_state()

    print(f"Página actual: {st.session_state.page}")
    print(f"Rol del usuario: {st.session_state.role}")

    if st.session_state.page == 'login':
        login_register_page()
    elif st.session_state.page == 'admin':
        print("Intentando mostrar página de admin")
        admin_page()
    elif st.session_state.page == 'user':
        user_page()
    else:
        print(f"Página no reconocida: {st.session_state.page}")

    print(f"Estado final de la sesión: {st.session_state}")

##################################################################################################
def login_register_page():
    st.title("AIdeaText")

    left_column, right_column = st.columns([1, 3])

    with left_column:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])

        with tab1:
            login_form()

        with tab2:
            register_form()

    with right_column:
        display_videos_and_info()

##################################################################################################

def login_form():
    username = st.text_input("Correo electrónico", key="login_username")
    password = st.text_input("Contraseña", type="password", key="login_password")

    if st.button("Iniciar Sesión", key="login_button"):
        success, role = authenticate_user(username, password)
        if success:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = role
            st.session_state.page = 'admin' if role == 'Administrador' else 'user'
            print(f"Inicio de sesión exitoso. Usuario: {username}, Rol: {role}")
            print(f"Estado de sesión después de login: {st.session_state}")
            st.rerun()
        else:
            st.error("Credenciales incorrectas")

##################################################################################################
def admin_page():
    st.title("Panel de Administración")
    st.write(f"Bienvenida, {st.session_state.username}")

    st.header("Crear Nuevo Usuario Estudiante")
    new_username = st.text_input("Correo electrónico del nuevo usuario", key="admin_new_username")
    new_password = st.text_input("Contraseña", type="password", key="admin_new_password")
    if st.button("Crear Usuario", key="admin_create_user"):
        if create_student_user(new_username, new_password):
            st.success(f"Usuario estudiante {new_username} creado exitosamente")
        else:
            st.error("Error al crear el usuario estudiante")

    # Aquí puedes añadir más funcionalidades para el panel de administración

##################################################################################################
def user_page():
    # Asumimos que el idioma seleccionado está almacenado en st.session_state.lang_code
    # Si no está definido, usamos 'es' como valor predeterminado
    lang_code = st.session_state.get('lang_code', 'es')

    translations = {
        'es': {
            'welcome': "Bienvenido a AIdeaText",
            'hello': "Hola",
            'chat_title': "Chat de Análisis",
            'results_title': "Resultados del Análisis",
            'export_button': "Exportar Análisis Actual",
            'no_analysis': "No hay análisis disponible. Utiliza el chat para realizar un análisis.",
            'export_success': "Análisis y chat exportados correctamente.",
            'export_error': "Hubo un problema al exportar el análisis y el chat.",
            'nothing_to_export': "No hay análisis o chat para exportar."
        },
        'en': {
            'welcome': "Welcome to AIdeaText",
            'hello': "Hello",
            'chat_title': "Analysis Chat",
            'results_title': "Analysis Results",
            'export_button': "Export Current Analysis",
            'no_analysis': "No analysis available. Use the chat to perform an analysis.",
            'export_success': "Analysis and chat exported successfully.",
            'export_error': "There was a problem exporting the analysis and chat.",
            'nothing_to_export': "No analysis or chat to export."
        },
        'fr': {
            'welcome': "Bienvenue à AIdeaText",
            'hello': "Bonjour",
            'chat_title': "Chat d'Analyse",
            'results_title': "Résultats de l'Analyse",
            'export_button': "Exporter l'Analyse Actuelle",
            'no_analysis': "Aucune analyse disponible. Utilisez le chat pour effectuer une analyse.",
            'export_success': "Analyse et chat exportés avec succès.",
            'export_error': "Un problème est survenu lors de l'exportation de l'analyse et du chat.",
            'nothing_to_export': "Aucune analyse ou chat à exporter."
        }
    }

    t = translations[lang_code]

    st.title(t['welcome'])
    st.write(f"{t['hello']}, {st.session_state.username}")

    # Dividir la pantalla en dos columnas
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(t['chat_title'])
        display_chatbot_interface(lang_code)

    with col2:
        st.subheader(t['results_title'])
        if 'current_analysis' in st.session_state and st.session_state.current_analysis is not None:
            display_analysis_results(st.session_state.current_analysis, lang_code)
            if st.button(t['export_button']):
                if export_analysis_and_chat(st.session_state.username, st.session_state.current_analysis, st.session_state.messages):
                    st.success(t['export_success'])
                else:
                    st.error(t['export_error'])
        else:
            st.info(t['no_analysis'])


##################################################################################################
def display_analysis_results(analysis, lang_code):
    translations = {
        'es': {
            'morphosyntactic_title': "Análisis Morfosintáctico",
            'semantic_title': "Análisis Semántico",
            'discourse_title': "Análisis del Discurso",
            'no_analysis': "No hay análisis disponible.",
            'legend': "Leyenda: Categorías gramaticales",
            'repeated_words': "Palabras repetidas",
            'sentence_structure': "Estructura de oraciones",
            'repeated_words': "Palabras repetidas",
            'pos_analysis': "Análisis de categorías gramaticales",
            'morphological_analysis': "Análisis morfológico",
            'arc_diagram': "Análisis sintáctico: Diagrama de arco",
            'sentence': "Oración",
            'root': "Raíz",
            'subjects': "Sujetos",
            'objects': "Objetos",
            'verbs': "Verbos",
            'success_message': "Análisis guardado correctamente.", #categorias adicionales
            'error_message': "Hubo un problema al guardar el análisis. Por favor, inténtelo de nuevo.", #categorias adicionales
            'warning_message': "Por favor, ingrese un texto para analizar.", #categorias adicionales
            'initial_message': "Ingrese un texto y presione 'Analizar texto' para comenzar.", #categorias adicionales
            'no_results': "No hay resultados disponibles. Por favor, realice un análisis primero.", #categorias adicionales
            'word': "Palabra", #categorias adicionales
            'count': "Cantidad", #categorias adicionales
            'percentage': "Porcentaje", #categorias adicionales
            'examples': "Ejemplos", #categorias adicionales
            'lemma': "Lema", #categorias adicionales
            'tag': "Etiqueta", #categorias adicionales
            'dep': "Dependencia", #categorias adicionales
            'morph': "Morfología", #categorias adicionales
            'grammatical_category': "Categoría gramatical", #categorias adicionales
            'dependency': "Dependencia", #categorias adicionales
            'morphology': "Morfología", #categorias adicionales
            'conceptual_relations': "Relaciones Conceptuales",
            'identified_entities': "Entidades Identificadas",
            'key_concepts': "Conceptos Clave",
            'success_message': "Análisis semántico guardado correctamente.",
            'error_message': "Hubo un problema al guardar el análisis semántico. Por favor, inténtelo de nuevo.",
            'warning_message': "Por favor, ingrese un texto o cargue un archivo para analizar.",
            'initial_message': "Ingrese un texto y presione 'Analizar texto' para comenzar.",
            'no_results': "No hay resultados disponibles. Por favor, realice un análisis primero.",
            'comparison': "Comparación de Relaciones Semánticas",
            'success_message': "Análisis del discurso guardado correctamente.",
            'error_message': "Hubo un problema al guardar el análisis del discurso. Por favor, inténtelo de nuevo.",
            'warning_message': "Por favor, cargue ambos archivos para analizar.",
            'initial_message': "Ingrese un texto y presione 'Analizar texto' para comenzar.",
            'no_results': "No hay resultados disponibles. Por favor, realice un análisis primero.",
            'key_concepts': "Conceptos Clave",
            'graph_not_available': "El gráfico no está disponible.",
            'concepts_not_available': "Los conceptos clave no están disponibles.",
            'comparison_not_available': "La comparación no está disponible."

        },
        'en': {
            'morphosyntactic_title': "Morphosyntactic Analysis",
            'semantic_title': "Semantic Analysis",
            'discourse_title': "Discourse Analysis",
            'no_analysis': "No analysis available.",
            'legend': "Legend: Grammatical categories",
            'sentence_structure': "Sentence Structure",
            'repeated_words': "Repeated words",
            'pos_analysis': "Part of Speech Analysis",
            'morphological_analysis': "Morphological Analysis",
            'arc_diagram': "Syntactic analysis: Arc diagram",
            'sentence': "Sentence",
            'root': "Root",
            'subjects': "Subjects",
            'objects': "Objects",
            'verbs': "Verbs",
            'success_message': "Analysis saved successfully.",
            'error_message': "There was a problem saving the analysis. Please try again.",
            'warning_message': "Please enter a text to analyze.",
            'initial_message': "Enter a text and press 'Analyze text' to start.",
            'no_results': "No results available. Please perform an analysis first.",
            'word': "Word",
            'count': "Count",
            'percentage': "Percentage",
            'examples': "Examples",
            'lemma': "Lemma",
            'tag': "Tag",
            'dep': "Dependency",
            'morph': "Morphology",
            'grammatical_category': "Grammatical category",
            'dependency': "Dependency",
            'morphology': "Morphology",
            'conceptual_relations': "Conceptual Relations",
            'identified_entities': "Identified Entities",
            'key_concepts': "Key Concepts",
            'success_message': "Semantic analysis saved successfully.",
            'error_message': "There was a problem saving the semantic analysis. Please try again.",
            'warning_message': "Please enter a text or upload a file to analyze.",
            'initial_message': "Enter a text and press 'Analyze text' to start.",
            'no_results': "No results available. Please perform an analysis first.",
            'comparison': "Comparison of Semantic Relations",
            'success_message': "Discourse analysis saved successfully.",
            'error_message': "There was a problem saving the discourse analysis. Please try again.",
            'warning_message': "Please upload both files to analyze.",
            'initial_message': "Enter a text and press 'Analyze text' to start.",
            'no_results': "No results available. Please perform an analysis first.",
            'key_concepts': "Key Concepts",
            'graph_not_available': "The graph is not available.",
            'concepts_not_available': "Key concepts are not available.",
            'comparison_not_available': "The comparison is not available."
        },
        'fr': {
            'morphosyntactic_title': "Analyse Morphosyntaxique",
            'semantic_title': "Analyse Sémantique",
            'discourse_title': "Analyse du Discours",
            'no_analysis': "Aucune analyse disponible.",
            'legend': "Légende : Catégories grammaticales",
            'sentence_structure': "Structure des phrases",
            'repeated_words': "Mots répétés",
            'pos_analysis': "Analyse des parties du discours",
            'morphological_analysis': "Analyse morphologique",
            'arc_diagram': "Analyse syntaxique : Diagramme en arc",
            'sentence': "Phrase",
            'root': "Racine",
            'subjects': "Sujets",
            'objects': "Objets",
            'verbs': "Verbes",
            'success_message': "Analyse enregistrée avec succès.",
            'error_message': "Un problème est survenu lors de l'enregistrement de l'analyse. Veuillez réessayer.",
            'warning_message': "Veuillez entrer un texte à analyser.",
            'initial_message': "Entrez un texte et appuyez sur 'Analyser le texte' pour commencer.",
            'no_results': "Aucun résultat disponible. Veuillez d'abord effectuer une analyse.",
            'word': "Mot",
            'count': "Nombre",
            'percentage': "Pourcentage",
            'examples': "Exemples",
            'lemma': "Lemme",
            'tag': "Étiquette",
            'dep': "Dépendance",
            'morph': "Morphologie",
            'grammatical_category': "Catégorie grammaticale",
            'dependency': "Dépendance",
            'morphology': "Morphologie",
            'conceptual_relations': "Relations Conceptuelles",
            'identified_entities': "Entités Identifiées",
            'key_concepts': "Concepts Clés",
            'success_message': "Analyse sémantique enregistrée avec succès.",
            'error_message': "Un problème est survenu lors de l'enregistrement de l'analyse sémantique. Veuillez réessayer.",
            'warning_message': "Veuillez entrer un texte ou télécharger un fichier à analyser.",
            'initial_message': "Entrez un texte et appuyez sur 'Analyser le texte' pour commencer.",
            'no_results': "Aucun résultat disponible. Veuillez d'abord effectuer une analyse.",
            'comparison': "Comparaison des Relations Sémantiques",
            'success_message': "Analyse du discours enregistrée avec succès.",
            'error_message': "Un problème est survenu lors de l'enregistrement de l'analyse du discours. Veuillez réessayer.",
            'warning_message': "Veuillez télécharger les deux fichiers à analyser.",
            'initial_message': "Entrez un texte et appuyez sur 'Analyser le texte' pour commencer.",
            'no_results': "Aucun résultat disponible. Veuillez d'abord effectuer une analyse.",
            'key_concepts': "Concepts Clés",
            'graph_not_available': "Le graphique n'est pas disponible.",
            'concepts_not_available': "Les concepts clés ne sont pas disponibles.",
            'comparison_not_available': "La comparaison n'est pas disponible."
        }
    }

    t = translations[lang_code]

    if analysis is None:
        st.warning(t['no_analysis'])
        return

    if analysis['type'] == 'morphosyntactic':
        st.subheader(t['morphosyntactic_title'])
        display_morphosyntax_results(analysis['result'], lang_code, t)
    elif analysis['type'] == 'semantic':
        st.subheader(t['semantic_title'])
        display_semantic_results(analysis['result'], lang_code, t)
    elif analysis['type'] == 'discourse':
        st.subheader(t['discourse_title'])
        display_discourse_results(analysis['result'], lang_code, t)
    else:
        st.warning(t['no_analysis'])

##################################################################################################
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

##################################################################################################
def register_form():
    st.header("Solicitar prueba de la aplicación")

    name = st.text_input("Nombre completo")
    email = st.text_input("Correo electrónico institucional")
    institution = st.text_input("Institución")
    role = st.selectbox("Rol", ["Estudiante", "Profesor", "Investigador", "Otro"])
    reason = st.text_area("¿Por qué estás interesado en probar AIdeaText?")

    if st.button("Enviar solicitud"):
        logger.info(f"Attempting to submit application for {email}")
        logger.debug(f"Form data: name={name}, email={email}, institution={institution}, role={role}, reason={reason}")

        if not name or not email or not institution or not reason:
            logger.warning("Incomplete form submission")
            st.error("Por favor, completa todos los campos.")
        elif not is_institutional_email(email):
            logger.warning(f"Non-institutional email used: {email}")
            st.error("Por favor, utiliza un correo electrónico institucional.")
        else:
            logger.info(f"Attempting to store application for {email}")
            success = store_application_request(name, email, institution, role, reason)
            if success:
                st.success("Tu solicitud ha sido enviada. Te contactaremos pronto.")
                logger.info(f"Application request stored successfully for {email}")
            else:
                st.error("Hubo un problema al enviar tu solicitud. Por favor, intenta de nuevo más tarde.")
                logger.error(f"Failed to store application request for {email}")

################################################################################
def display_feedback_form(lang_code):
    logging.info(f"display_feedback_form called with lang_code: {lang_code}")
    translations = {
        'es': {
            'title': "Formulario de Retroalimentación",
            'name': "Nombre",
            'email': "Correo electrónico",
            'feedback': "Tu retroalimentación",
            'submit': "Enviar",
            'success': "¡Gracias por tu retroalimentación!",
            'error': "Hubo un problema al enviar el formulario. Por favor, intenta de nuevo."
        },
        'en': {
            'title': "Feedback Form",
            'name': "Name",
            'email': "Email",
            'feedback': "Your feedback",
            'submit': "Submit",
            'success': "Thank you for your feedback!",
            'error': "There was a problem submitting the form. Please try again."
        },
        'fr': {
            'title': "Formulaire de Rétroaction",
            'name': "Nom",
            'email': "Adresse e-mail",
            'feedback': "Votre rétroaction",
            'submit': "Envoyer",
            'success': "Merci pour votre rétroaction !",
            'error': "Un problème est survenu lors de l'envoi du formulaire. Veuillez réessayer."
        }
    }

    t = translations[lang_code]

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

################################################################################
def is_institutional_email(email):
    forbidden_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
    return not any(domain in email.lower() for domain in forbidden_domains)
################################################################################

def display_student_progress(username, lang_code='es'):
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

##################################################################################################
def display_morphosyntax_analysis_interface(nlp_models, lang_code):
    translations = {
        'es': {
            'title': "AIdeaText - Análisis morfológico y sintáctico",
            'input_label': "Ingrese un texto para analizar (máximo 5,000 palabras",
            'input_placeholder': "Esta funcionalidad le ayudará con dos competencias:\n"
                                 "[1] \"Escribe diversos tipos de textos en su lengua materna\"\n"
                                 "[2] \"Lee diversos tipos de textos escritos en su lengua materna\"\n\n"
                                 "Ingrese su texto aquí para analizar...",
            'analyze_button': "Analizar texto",
            'repeated_words': "Palabras repetidas",
            'legend': "Leyenda: Categorías gramaticales",
            'arc_diagram': "Análisis sintáctico: Diagrama de arco",
            'sentence': "Oración",
            'success_message': "Análisis guardado correctamente.",
            'error_message': "Hubo un problema al guardar el análisis. Por favor, inténtelo de nuevo.",
            'warning_message': "Por favor, ingrese un texto para analizar.",
            'initial_message': "Ingrese un texto y presione 'Analizar texto' para comenzar.",
            'no_results': "No hay resultados disponibles. Por favor, realice un análisis primero.",
            'pos_analysis': "Análisis de categorías gramaticales",
            'morphological_analysis': "Análisis morfológico",
            'sentence_structure': "Estructura de oraciones",
            'word': "Palabra",
            'count': "Cantidad",
            'percentage': "Porcentaje",
            'examples': "Ejemplos",
            'lemma': "Lema",
            'tag': "Etiqueta",
            'dep': "Dependencia",
            'morph': "Morfología",
            'root': "Raíz",
            'subjects': "Sujetos",
            'objects': "Objetos",
            'verbs': "Verbos",
            'grammatical_category': "Categoría gramatical",
            'dependency': "Dependencia",
            'morphology': "Morfología"
        },
        'en': {
            'title': "AIdeaText - Morphological and Syntactic Analysis",
            'input_label': "Enter a text to analyze (max 5,000 words):",
            'input_placeholder': "This functionality will help you with two competencies:\n"
                             "[1] \"Write various types of texts in your native language\"\n"
                             "[2] \"Read various types of written texts in your native language\"\n\n"
                             "Enter your text here to analyze...",
            'analyze_button': "Analyze text",
            'repeated_words': "Repeated words",
            'legend': "Legend: Grammatical categories",
            'arc_diagram': "Syntactic analysis: Arc diagram",
            'sentence': "Sentence",
            'success_message': "Analysis saved successfully.",
            'error_message': "There was a problem saving the analysis. Please try again.",
            'warning_message': "Please enter a text to analyze.",
            'initial_message': "Enter a text and press 'Analyze text' to start.",
            'no_results': "No results available. Please perform an analysis first.",
            'pos_analysis': "Part of Speech Analysis",
            'morphological_analysis': "Morphological Analysis",
            'sentence_structure': "Sentence Structure",
            'word': "Word",
            'count': "Count",
            'percentage': "Percentage",
            'examples': "Examples",
            'lemma': "Lemma",
            'tag': "Tag",
            'dep': "Dependency",
            'morph': "Morphology",
            'root': "Root",
            'subjects': "Subjects",
            'objects': "Objects",
            'verbs': "Verbs",
            'grammatical_category': "Grammatical category",
            'dependency': "Dependency",
            'morphology': "Morphology"
        },
        'fr': {
            'title': "AIdeaText - Analyse morphologique et syntaxique",
            'input_label': "Entrez un texte à analyser (max 5 000 mots) :",
            'input_placeholder': "Cette fonctionnalité vous aidera avec deux compétences :\n"
                             "[1] \"Écrire divers types de textes dans votre langue maternelle\"\n"
                             "[2] \"Lire divers types de textes écrits dans votre langue maternelle\"\n\n"
                             "Entrez votre texte ici pour l'analyser...",
            'analyze_button': "Analyser le texte",
            'repeated_words': "Mots répétés",
            'legend': "Légende : Catégories grammaticales",
            'arc_diagram': "Analyse syntaxique : Diagramme en arc",
            'sentence': "Phrase",
            'success_message': "Analyse enregistrée avec succès.",
            'error_message': "Un problème est survenu lors de l'enregistrement de l'analyse. Veuillez réessayer.",
            'warning_message': "Veuillez entrer un texte à analyser.",
            'initial_message': "Entrez un texte et appuyez sur 'Analyser le texte' pour commencer.",
            'no_results': "Aucun résultat disponible. Veuillez d'abord effectuer une analyse.",
            'pos_analysis': "Analyse des parties du discours",
            'morphological_analysis': "Analyse morphologique",
            'sentence_structure': "Structure des phrases",
            'word': "Mot",
            'count': "Nombre",
            'percentage': "Pourcentage",
            'examples': "Exemples",
            'lemma': "Lemme",
            'tag': "Étiquette",
            'dep': "Dépendance",
            'morph': "Morphologie",
            'root': "Racine",
            'subjects': "Sujets",
            'objects': "Objets",
            'verbs': "Verbes",
            'grammatical_category': "Catégorie grammaticale",
            'dependency': "Dépendance",
            'morphology': "Morphologie"
        }
    }

    t = translations[lang_code]

    input_key = f"morphosyntax_input_{lang_code}"

    if input_key not in st.session_state:
        st.session_state[input_key] = ""

    sentence_input = st.text_area(
        t['input_label'],
        height=150,
        placeholder=t['input_placeholder'],
        value=st.session_state[input_key],
        key=f"text_area_{lang_code}",
        on_change=lambda: setattr(st.session_state, input_key, st.session_state[f"text_area_{lang_code}"])
    )

    if st.button(t['analyze_button'], key=f"analyze_button_{lang_code}"):
        current_input = st.session_state[input_key]
        if current_input:
            doc = nlp_models[lang_code](current_input)

            # Análisis morfosintáctico avanzado
            advanced_analysis = perform_advanced_morphosyntactic_analysis(current_input, nlp_models[lang_code])

            # Guardar el resultado en el estado de la sesión
            st.session_state.morphosyntax_result = {
                'doc': doc,
                'advanced_analysis': advanced_analysis
            }

            # Mostrar resultados
            display_morphosyntax_results(st.session_state.morphosyntax_result, lang_code, t)

            # Guardar resultados
            if store_morphosyntax_result(
                st.session_state.username,
                current_input,
                get_repeated_words_colors(doc),
                advanced_analysis['arc_diagram'],
                advanced_analysis['pos_analysis'],
                advanced_analysis['morphological_analysis'],
                advanced_analysis['sentence_structure']
            ):
                st.success(t['success_message'])
            else:
                st.error(t['error_message'])
        else:
            st.warning(t['warning_message'])
    elif 'morphosyntax_result' in st.session_state and st.session_state.morphosyntax_result is not None:

        # Si hay un resultado guardado, mostrarlo
        display_morphosyntax_results(st.session_state.morphosyntax_result, lang_code, t)
    else:
        st.info(t['initial_message'])  # Añade esta traducción a tu diccionario

#################################################################################################
#################################################################################################
def display_morphosyntax_results(result, lang_code, t):
    if result is None:
        st.warning(t['no_results'])  # Añade esta traducción a tu diccionario
        return

    # doc = result['doc']
    # advanced_analysis = result['advanced_analysis']
    advanced_analysis = result

    # Mostrar leyenda (código existente)
    st.markdown(f"##### {t['legend']}")
    legend_html = "<div style='display: flex; flex-wrap: wrap;'>"
    for pos, color in POS_COLORS.items():
        if pos in POS_TRANSLATIONS[lang_code]:
            legend_html += f"<div style='margin-right: 10px;'><span style='background-color: {color}; padding: 2px 5px;'>{POS_TRANSLATIONS[lang_code][pos]}</span></div>"
    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

    # Mostrar análisis de palabras repetidas (código existente)
    if 'repeated_words' in advanced_analysis:
        with st.expander(t['repeated_words'], expanded=True):
            st.markdown(advanced_analysis['repeated_words'], unsafe_allow_html=True)

    # Mostrar estructura de oraciones
    if 'sentence_structure' in advanced_analysis:
        with st.expander(t['sentence_structure'], expanded=True):
            for i, sent_analysis in enumerate(advanced_analysis['sentence_structure']):
                sentence_str = (
                    f"**{t['sentence']} {i+1}** "
                    f"{t['root']}: {sent_analysis['root']} ({sent_analysis['root_pos']}) -- "
                    f"{t['subjects']}: {', '.join(sent_analysis['subjects'])} -- "
                    f"{t['objects']}: {', '.join(sent_analysis['objects'])} -- "
                    f"{t['verbs']}: {', '.join(sent_analysis['verbs'])}"
                )
                st.markdown(sentence_str)
    else:
        st.warning("No se encontró información sobre la estructura de las oraciones.")


    # Mostrar análisis de categorías gramaticales # Mostrar análisis morfológico
    col1, col2 = st.columns(2)

    with col1:
        with st.expander(t['pos_analysis'], expanded=True):
            pos_df = pd.DataFrame(advanced_analysis['pos_analysis'])

            # Traducir las etiquetas POS a sus nombres en el idioma seleccionado
            pos_df['pos'] = pos_df['pos'].map(lambda x: POS_TRANSLATIONS[lang_code].get(x, x))

            # Renombrar las columnas para mayor claridad
            pos_df = pos_df.rename(columns={
                'pos': t['grammatical_category'],
                'count': t['count'],
                'percentage': t['percentage'],
                'examples': t['examples']
            })

            # Mostrar el dataframe
            st.dataframe(pos_df)

    with col2:
        with st.expander(t['morphological_analysis'], expanded=True):
            morph_df = pd.DataFrame(advanced_analysis['morphological_analysis'])

            # Definir el mapeo de columnas
            column_mapping = {
                'text': t['word'],
                'lemma': t['lemma'],
                'pos': t['grammatical_category'],
                'dep': t['dependency'],
                'morph': t['morphology']
            }

            # Renombrar las columnas existentes
            morph_df = morph_df.rename(columns={col: new_name for col, new_name in column_mapping.items() if col in morph_df.columns})

            # Traducir las categorías gramaticales
            morph_df[t['grammatical_category']] = morph_df[t['grammatical_category']].map(lambda x: POS_TRANSLATIONS[lang_code].get(x, x))

            # Traducir las dependencias
            dep_translations = {
                'es': {
                    'ROOT': 'RAÍZ', 'nsubj': 'sujeto nominal', 'obj': 'objeto', 'iobj': 'objeto indirecto',
                    'csubj': 'sujeto clausal', 'ccomp': 'complemento clausal', 'xcomp': 'complemento clausal abierto',
                    'obl': 'oblicuo', 'vocative': 'vocativo', 'expl': 'expletivo', 'dislocated': 'dislocado',
                    'advcl': 'cláusula adverbial', 'advmod': 'modificador adverbial', 'discourse': 'discurso',
                    'aux': 'auxiliar', 'cop': 'cópula', 'mark': 'marcador', 'nmod': 'modificador nominal',
                    'appos': 'aposición', 'nummod': 'modificador numeral', 'acl': 'cláusula adjetiva',
                    'amod': 'modificador adjetival', 'det': 'determinante', 'clf': 'clasificador',
                    'case': 'caso', 'conj': 'conjunción', 'cc': 'coordinante', 'fixed': 'fijo',
                    'flat': 'plano', 'compound': 'compuesto', 'list': 'lista', 'parataxis': 'parataxis',
                    'orphan': 'huérfano', 'goeswith': 'va con', 'reparandum': 'reparación', 'punct': 'puntuación'
                },
                'en': {
                    'ROOT': 'ROOT', 'nsubj': 'nominal subject', 'obj': 'object',
                    'iobj': 'indirect object', 'csubj': 'clausal subject', 'ccomp': 'clausal complement', 'xcomp': 'open clausal complement',
                    'obl': 'oblique', 'vocative': 'vocative', 'expl': 'expletive', 'dislocated': 'dislocated', 'advcl': 'adverbial clause modifier',
                    'advmod': 'adverbial modifier', 'discourse': 'discourse element', 'aux': 'auxiliary', 'cop': 'copula', 'mark': 'marker',
                    'nmod': 'nominal modifier', 'appos': 'appositional modifier', 'nummod': 'numeric modifier', 'acl': 'clausal modifier of noun',
                    'amod': 'adjectival modifier', 'det': 'determiner', 'clf': 'classifier', 'case': 'case marking',
                    'conj': 'conjunct', 'cc': 'coordinating conjunction', 'fixed': 'fixed multiword expression',
                    'flat': 'flat multiword expression', 'compound': 'compound', 'list': 'list', 'parataxis': 'parataxis', 'orphan': 'orphan',
                    'goeswith': 'goes with', 'reparandum': 'reparandum', 'punct': 'punctuation'
                },
                'fr': {
                    'ROOT': 'RACINE', 'nsubj': 'sujet nominal', 'obj': 'objet', 'iobj': 'objet indirect',
                    'csubj': 'sujet phrastique', 'ccomp': 'complément phrastique', 'xcomp': 'complément phrastique ouvert', 'obl': 'oblique',
                    'vocative': 'vocatif', 'expl': 'explétif', 'dislocated': 'disloqué', 'advcl': 'clause adverbiale', 'advmod': 'modifieur adverbial',
                    'discourse': 'élément de discours', 'aux': 'auxiliaire', 'cop': 'copule', 'mark': 'marqueur', 'nmod': 'modifieur nominal',
                    'appos': 'apposition', 'nummod': 'modifieur numéral', 'acl': 'clause relative', 'amod': 'modifieur adjectival', 'det': 'déterminant',
                    'clf': 'classificateur', 'case': 'marqueur de cas', 'conj': 'conjonction', 'cc': 'coordination', 'fixed': 'expression figée',
                    'flat': 'construction plate', 'compound': 'composé', 'list': 'liste', 'parataxis': 'parataxe', 'orphan': 'orphelin',
                    'goeswith': 'va avec', 'reparandum': 'réparation', 'punct': 'ponctuation'
                }
            }
            morph_df[t['dependency']] = morph_df[t['dependency']].map(lambda x: dep_translations[lang_code].get(x, x))

            # Traducir la morfología
            def translate_morph(morph_string, lang_code):
                morph_translations = {
                    'es': {
                        'Gender': 'Género', 'Number': 'Número', 'Case': 'Caso', 'Definite': 'Definido',
                        'PronType': 'Tipo de Pronombre', 'Person': 'Persona', 'Mood': 'Modo',
                        'Tense': 'Tiempo', 'VerbForm': 'Forma Verbal', 'Voice': 'Voz',
                        'Fem': 'Femenino', 'Masc': 'Masculino', 'Sing': 'Singular', 'Plur': 'Plural',
                        'Ind': 'Indicativo', 'Sub': 'Subjuntivo', 'Imp': 'Imperativo', 'Inf': 'Infinitivo',
                        'Part': 'Participio', 'Ger': 'Gerundio', 'Pres': 'Presente', 'Past': 'Pasado',
                        'Fut': 'Futuro', 'Perf': 'Perfecto', 'Imp': 'Imperfecto'
                    },
                    'en': {
                        'Gender': 'Gender', 'Number': 'Number', 'Case': 'Case', 'Definite': 'Definite', 'PronType': 'Pronoun Type', 'Person': 'Person',
                        'Mood': 'Mood', 'Tense': 'Tense', 'VerbForm': 'Verb Form', 'Voice': 'Voice',
                        'Fem': 'Feminine', 'Masc': 'Masculine', 'Sing': 'Singular', 'Plur': 'Plural', 'Ind': 'Indicative',
                        'Sub': 'Subjunctive', 'Imp': 'Imperative', 'Inf': 'Infinitive', 'Part': 'Participle',
                        'Ger': 'Gerund', 'Pres': 'Present', 'Past': 'Past', 'Fut': 'Future', 'Perf': 'Perfect', 'Imp': 'Imperfect'
                    },
                    'fr': {
                        'Gender': 'Genre', 'Number': 'Nombre', 'Case': 'Cas', 'Definite': 'Défini', 'PronType': 'Type de Pronom',
                        'Person': 'Personne', 'Mood': 'Mode', 'Tense': 'Temps', 'VerbForm': 'Forme Verbale', 'Voice': 'Voix',
                        'Fem': 'Féminin', 'Masc': 'Masculin', 'Sing': 'Singulier', 'Plur': 'Pluriel', 'Ind': 'Indicatif',
                        'Sub': 'Subjonctif', 'Imp': 'Impératif', 'Inf': 'Infinitif', 'Part': 'Participe',
                        'Ger': 'Gérondif', 'Pres': 'Présent', 'Past': 'Passé', 'Fut': 'Futur', 'Perf': 'Parfait', 'Imp': 'Imparfait'
                    }
                }
                for key, value in morph_translations[lang_code].items():
                    morph_string = morph_string.replace(key, value)
                return morph_string

            morph_df[t['morphology']] = morph_df[t['morphology']].apply(lambda x: translate_morph(x, lang_code))

            # Seleccionar y ordenar las columnas a mostrar
            columns_to_display = [t['word'], t['lemma'], t['grammatical_category'], t['dependency'], t['morphology']]
            columns_to_display = [col for col in columns_to_display if col in morph_df.columns]

            # Mostrar el DataFrame
            st.dataframe(morph_df[columns_to_display])

    # Mostrar diagramas de arco (código existente)
    #with st.expander(t['arc_diagram'], expanded=True):
    #    sentences = list(doc.sents)
    #    arc_diagrams = []
    #    for i, sent in enumerate(sentences):
    #        st.subheader(f"{t['sentence']} {i+1}")
    #        html = displacy.render(sent, style="dep", options={"distance": 100})
    #        html = html.replace('height="375"', 'height="200"')
    #        html = re.sub(r'<svg[^>]*>', lambda m: m.group(0).replace('height="450"', 'height="300"'), html)
    #        html = re.sub(r'<g [^>]*transform="translate\((\d+),(\d+)\)"', lambda m: f'<g transform="translate({m.group(1)},50)"', html)
    #        st.write(html, unsafe_allow_html=True)
    #        arc_diagrams.append(html)

    # Mostrar diagramas de arco
    with st.expander(t['arc_diagram'], expanded=True):
        for i, arc_diagram in enumerate(advanced_analysis['arc_diagram']):
            st.subheader(f"{t['sentence']} {i+1}")
            st.write(arc_diagram, unsafe_allow_html=True)

###############################################################################################################
def display_semantic_analysis_interface(nlp_models, lang_code):
    translations = {
        'es': {
            'title': "AIdeaText - Análisis semántico",
            'text_input_label': "Ingrese un texto para analizar (máx. 5,000 palabras):",
            'text_input_placeholder': "El objetivo de esta aplicación es que mejore sus habilidades de redacción...",
            'file_uploader': "O cargue un archivo de texto",
            'analyze_button': "Analizar texto",
            'conceptual_relations': "Relaciones Conceptuales",
            'identified_entities': "Entidades Identificadas",
            'key_concepts': "Conceptos Clave",
            'success_message': "Análisis semántico guardado correctamente.",
            'error_message': "Hubo un problema al guardar el análisis semántico. Por favor, inténtelo de nuevo.",
            'warning_message': "Por favor, ingrese un texto o cargue un archivo para analizar.",
            'initial_message': "Ingrese un texto y presione 'Analizar texto' para comenzar.",
            'no_results': "No hay resultados disponibles. Por favor, realice un análisis primero."
        },
        'en': {
            'title': "AIdeaText - Semantic Analysis",
            'text_input_label': "Enter a text to analyze (max. 5,000 words):",
            'text_input_placeholder': "The goal of this application is to improve your writing skills...",
            'file_uploader': "Or upload a text file",
            'analyze_button': "Analyze text",
            'conceptual_relations': "Conceptual Relations",
            'identified_entities': "Identified Entities",
            'key_concepts': "Key Concepts",
            'success_message': "Semantic analysis saved successfully.",
            'error_message': "There was a problem saving the semantic analysis. Please try again.",
            'warning_message': "Please enter a text or upload a file to analyze.",
            'initial_message': "Enter a text and press 'Analyze text' to start.",
            'no_results': "No results available. Please perform an analysis first."
        },
        'fr': {
            'title': "AIdeaText - Analyse sémantique",
            'text_input_label': "Entrez un texte à analyser (max. 5 000 mots) :",
            'text_input_placeholder': "L'objectif de cette application est d'améliorer vos compétences en rédaction...",
            'file_uploader': "Ou téléchargez un fichier texte",
            'analyze_button': "Analyser le texte",
            'conceptual_relations': "Relations Conceptuelles",
            'identified_entities': "Entités Identifiées",
            'key_concepts': "Concepts Clés",
            'success_message': "Analyse sémantique enregistrée avec succès.",
            'error_message': "Un problème est survenu lors de l'enregistrement de l'analyse sémantique. Veuillez réessayer.",
            'warning_message': "Veuillez entrer un texte ou télécharger un fichier à analyser.",
            'initial_message': "Entrez un texte et appuyez sur 'Analyser le texte' pour commencer.",
            'no_results': "Aucun résultat disponible. Veuillez d'abord effectuer une analyse."
        }
    }

    t = translations[lang_code]

    st.header(t['title'])

    # Opción para introducir texto
    text_input = st.text_area(
        t['text_input_label'],
        height=150,
        placeholder=t['text_input_placeholder'],
    )

    # Opción para cargar archivo
    uploaded_file = st.file_uploader(t['file_uploader'], type=['txt'])

    if st.button(t['analyze_button']):
        if text_input or uploaded_file is not None:
            if uploaded_file:
                text_content = uploaded_file.getvalue().decode('utf-8')
            else:
                text_content = text_input

            # Realizar el análisis
            analysis_result = perform_semantic_analysis(text_content, nlp_models[lang_code], lang_code)

            # Guardar el resultado en el estado de la sesión
            st.session_state.semantic_result = analysis_result

            # Mostrar resultados
            display_semantic_results(st.session_state.semantic_result, lang_code, t)

            # Guardar el resultado del análisis
            if store_semantic_result(st.session_state.username, text_content, analysis_result):
                st.success(t['success_message'])
            else:
                st.error(t['error_message'])
        else:
            st.warning(t['warning_message'])

    elif 'semantic_result' in st.session_state:

        # Si hay un resultado guardado, mostrarlo
        display_semantic_results(st.session_state.semantic_result, lang_code, t)

    else:
        st.info(t['initial_message'])  # Asegúrate de que 'initial_message' esté en tus traducciones

def display_semantic_results(result, lang_code, t):
    if result is None:
        st.warning(t['no_results'])  # Asegúrate de que 'no_results' esté en tus traducciones
        return

    # Mostrar conceptos clave
    with st.expander(t['key_concepts'], expanded=True):
        concept_text = " | ".join([f"{concept} ({frequency:.2f})" for concept, frequency in result['key_concepts']])
        st.write(concept_text)

    # Mostrar el gráfico de relaciones conceptuales
    with st.expander(t['conceptual_relations'], expanded=True):
        st.pyplot(result['relations_graph'])

##################################################################################################
def display_discourse_analysis_interface(nlp_models, lang_code):
    translations = {
        'es': {
            'title': "AIdeaText - Análisis del discurso",
            'file_uploader1': "Cargar archivo de texto 1 (Patrón)",
            'file_uploader2': "Cargar archivo de texto 2 (Comparación)",
            'analyze_button': "Analizar textos",
            'comparison': "Comparación de Relaciones Semánticas",
            'success_message': "Análisis del discurso guardado correctamente.",
            'error_message': "Hubo un problema al guardar el análisis del discurso. Por favor, inténtelo de nuevo.",
            'warning_message': "Por favor, cargue ambos archivos para analizar.",
            'initial_message': "Ingrese un texto y presione 'Analizar texto' para comenzar.",
            'no_results': "No hay resultados disponibles. Por favor, realice un análisis primero.",
            'key_concepts': "Conceptos Clave",
            'graph_not_available': "El gráfico no está disponible.",
            'concepts_not_available': "Los conceptos clave no están disponibles.",
            'comparison_not_available': "La comparación no está disponible."
        },
        'en': {
            'title': "AIdeaText - Discourse Analysis",
            'file_uploader1': "Upload text file 1 (Pattern)",
            'file_uploader2': "Upload text file 2 (Comparison)",
            'analyze_button': "Analyze texts",
            'comparison': "Comparison of Semantic Relations",
            'success_message': "Discourse analysis saved successfully.",
            'error_message': "There was a problem saving the discourse analysis. Please try again.",
            'warning_message': "Please upload both files to analyze.",
            'initial_message': "Enter a text and press 'Analyze text' to start.",
            'no_results': "No results available. Please perform an analysis first.",
            'key_concepts': "Key Concepts",
            'graph_not_available': "The graph is not available.",
            'concepts_not_available': "Key concepts are not available.",
            'comparison_not_available': "The comparison is not available."
        },
        'fr': {
            'title': "AIdeaText - Analyse du discours",
            'file_uploader1': "Télécharger le fichier texte 1 (Modèle)",
            'file_uploader2': "Télécharger le fichier texte 2 (Comparaison)",
            'analyze_button': "Analyser les textes",
            'comparison': "Comparaison des Relations Sémantiques",
            'success_message': "Analyse du discours enregistrée avec succès.",
            'error_message': "Un problème est survenu lors de l'enregistrement de l'analyse du discours. Veuillez réessayer.",
            'warning_message': "Veuillez télécharger les deux fichiers à analyser.",
            'initial_message': "Entrez un texte et appuyez sur 'Analyser le texte' pour commencer.",
            'no_results': "Aucun résultat disponible. Veuillez d'abord effectuer une analyse.",
            'key_concepts': "Concepts Clés",
            'graph_not_available': "Le graphique n'est pas disponible.",
            'concepts_not_available': "Les concepts clés ne sont pas disponibles.",
            'comparison_not_available': "La comparaison n'est pas disponible."
        }
    }

    t = translations[lang_code]
    st.header(t['title'])

    col1, col2 = st.columns(2)
    with col1:
        uploaded_file1 = st.file_uploader(t['file_uploader1'], type=['txt'])
    with col2:
        uploaded_file2 = st.file_uploader(t['file_uploader2'], type=['txt'])

    if st.button(t['analyze_button']):
        if uploaded_file1 is not None and uploaded_file2 is not None:
            text_content1 = uploaded_file1.getvalue().decode('utf-8')
            text_content2 = uploaded_file2.getvalue().decode('utf-8')

            # Realizar el análisis
            analysis_result = perform_discourse_analysis(text_content1, text_content2, nlp_models[lang_code], lang_code)

            # Guardar el resultado en el estado de la sesión
            st.session_state.discourse_result = analysis_result

            # Mostrar los resultados del análisis
            display_discourse_results(st.session_state.discourse_result, lang_code, t)

            # Guardar el resultado del análisis
            if store_discourse_analysis_result(st.session_state.username, text_content1, text_content2, analysis_result):
                st.success(t['success_message'])
            else:
                st.error(t['error_message'])
        else:
            st.warning(t['warning_message'])
    elif 'discourse_result' in st.session_state and st.session_state.discourse_result is not None:
        # Si hay un resultado guardado, mostrarlo
        display_discourse_results(st.session_state.discourse_result, lang_code, t)
    else:
        st.info(t['initial_message'])  # Asegúrate de que 'initial_message' esté en tus traducciones

#################################################

def display_discourse_results(result, lang_code, t):
    if result is None:
        st.warning(t.get('no_results', "No hay resultados disponibles."))
        return

    col1, col2 = st.columns(2)

    with col1:
        with st.expander(t.get('file_uploader1', "Documento 1"), expanded=True):
            st.subheader(t.get('key_concepts', "Conceptos Clave"))
            if 'key_concepts1' in result:
                df1 = pd.DataFrame(result['key_concepts1'], columns=['Concepto', 'Frecuencia'])
                df1['Frecuencia'] = df1['Frecuencia'].round(2)
                st.table(df1)
            else:
                st.warning(t.get('concepts_not_available', "Los conceptos clave no están disponibles."))

            if 'graph1' in result:
                st.pyplot(result['graph1'])
            else:
                st.warning(t.get('graph_not_available', "El gráfico no está disponible."))

    with col2:
        with st.expander(t.get('file_uploader2', "Documento 2"), expanded=True):
            st.subheader(t.get('key_concepts', "Conceptos Clave"))
            if 'key_concepts2' in result:
                df2 = pd.DataFrame(result['key_concepts2'], columns=['Concepto', 'Frecuencia'])
                df2['Frecuencia'] = df2['Frecuencia'].round(2)
                st.table(df2)
            else:
                st.warning(t.get('concepts_not_available', "Los conceptos clave no están disponibles."))

            if 'graph2' in result:
                st.pyplot(result['graph2'])
            else:
                st.warning(t.get('graph_not_available', "El gráfico no está disponible."))

    # Relación de conceptos entre ambos documentos (Diagrama de Sankey)
    st.subheader(t.get('comparison', "Relación de conceptos entre ambos documentos"))
    if 'key_concepts1' in result and 'key_concepts2' in result:
        df1 = pd.DataFrame(result['key_concepts1'], columns=['Concepto', 'Frecuencia'])
        df2 = pd.DataFrame(result['key_concepts2'], columns=['Concepto', 'Frecuencia'])

        # Crear una lista de todos los conceptos únicos
        all_concepts = list(set(df1['Concepto'].tolist() + df2['Concepto'].tolist()))

        # Crear un diccionario de colores para cada concepto
        color_scale = [f'rgb({random.randint(50,255)},{random.randint(50,255)},{random.randint(50,255)})' for _ in range(len(all_concepts))]
        color_map = dict(zip(all_concepts, color_scale))

        # Crear el diagrama de Sankey
        source = [0] * len(df1) + list(range(2, 2 + len(df1)))
        target = list(range(2, 2 + len(df1))) + [1] * len(df2)
        value = list(df1['Frecuencia']) + list(df2['Frecuencia'])

        node_colors = ['blue', 'red'] + [color_map[concept] for concept in df1['Concepto']] + [color_map[concept] for concept in df2['Concepto']]
        link_colors = [color_map[concept] for concept in df1['Concepto']] + [color_map[concept] for concept in df2['Concepto']]

        fig = go.Figure(data=[go.Sankey(
            node = dict(
              pad = 15,
              thickness = 20,
              line = dict(color = "black", width = 0.5),
              label = [t.get('file_uploader1', "Documento 1"), t.get('file_uploader2', "Documento 2")] + list(df1['Concepto']) + list(df2['Concepto']),
              color = node_colors
            ),
            link = dict(
              source = source,
              target = target,
              value = value,
              color = link_colors
          ))])

        fig.update_layout(title_text="Relación de conceptos entre documentos", font_size=10)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(t.get('comparison_not_available', "La comparación no está disponible."))

    # Aquí puedes agregar el código para mostrar los gráficos si es necesario

##################################################################################################
#def display_saved_discourse_analysis(analysis_data):
#    img_bytes = base64.b64decode(analysis_data['combined_graph'])
#    img = plt.imread(io.BytesIO(img_bytes), format='png')

#    st.image(img, use_column_width=True)
#    st.write("Texto del documento patrón:")
#    st.write(analysis_data['text1'])
#    st.write("Texto del documento comparado:")
#    st.write(analysis_data['text2'])

##################################################################################################
def display_chatbot_interface(lang_code, nlp_models):
    translations = {
        'es': {
            'input_placeholder': "Escribe tu respuesta aquí...",
            'initial_message': "¡Hola! Soy tu asistente de análisis. Para comenzar, escribe '/texto_descriptivo', '/texto_narrativo', etc.",
            'send_button': "Enviar",
            'current_diagram': "Diagrama de Arco Actual",
            'previous_diagram': "Diagrama de Arco Anterior",
            'current_question': "Pregunta actual",
            'text_construction': "Construcción de texto en progreso",
            'text_completed': "Has completado todas las preguntas. Texto final:",
            'improve_suggestion': "Ahora tienes que unir las oraciones con las conjunciones y conectores adecuados.",
            'generate_arc': "Generando diagrama de arco para tu texto...",
            'continue_iteration': "Puedes continuar mejorando tu texto. Escribe tu versión mejorada o usa '/analisis_morfosintactico [tu_texto]' para un nuevo análisis."
        },
        'en': {
            'input_placeholder': "Type your answer here...",
            'initial_message': "Hello! I'm your analysis assistant. To start, type '/texto_descriptivo', '/texto_narrativo', etc.",
            'send_button': "Send",
            'current_diagram': "Current Arc Diagram",
            'previous_diagram': "Previous Arc Diagram",
            'current_question': "Current question",
            'text_construction': "Text construction in progress",
            'text_completed': "You have completed all the questions. Final text:",
            'improve_suggestion': "Now you need to connect the sentences with appropriate conjunctions and connectors.",
            'generate_arc': "Generating arc diagram for your text...",
            'continue_iteration': "You can continue improving your text. Write your improved version or use '/analisis_morfosintactico [your_text]' for a new analysis."
        },
        'fr': {
            'input_placeholder': "Écrivez votre réponse ici...",
            'initial_message': "Bonjour! Je suis votre assistant d'analyse. Pour commencer, tapez '/texto_descriptivo', '/texto_narrativo', etc.",
            'send_button': "Envoyer",
            'current_diagram': "Diagramme d'Arc Actuel",
            'previous_diagram': "Diagramme d'Arc Précédent",
            'current_question': "Question actuelle",
            'text_construction': "Construction de texte en cours",
            'text_completed': "Vous avez répondu à toutes les questions. Texte final :",
            'improve_suggestion': "Maintenant, vous devez relier les phrases avec des conjonctions et des connecteurs appropriés.",
            'generate_arc': "Génération du diagramme d'arc pour votre texte...",
            'continue_iteration': "Vous pouvez continuer à améliorer votre texte. Écrivez votre version améliorée ou utilisez '/analisis_morfosintactico [votre_texte]' pour une nouvelle analyse."
        }
    }
    t = translations[lang_code]

    st.write("Debug: Function started")

    # Inicialización del estado de la sesión
    if 'messages' not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": t['initial_message']}]
    if 'current_text_type' not in st.session_state:
        st.session_state.current_text_type = None
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'user_responses' not in st.session_state:
        st.session_state.user_responses = []
    if 'current_arc_diagram' not in st.session_state:
        st.session_state.current_arc_diagram = None
    if 'previous_arc_diagram' not in st.session_state:
        st.session_state.previous_arc_diagram = None

    st.write(f"Debug: Current text type: {st.session_state.current_text_type}")
    st.write(f"Debug: Current question index: {st.session_state.current_question_index}")

    chat_container = st.empty()
    current_diagram_container = st.empty()
    previous_diagram_container = st.empty()

    # Mostrar la pregunta actual si estamos en modo de construcción de texto
    if st.session_state.current_text_type:
        st.subheader(t['text_construction'])
        current_question = TEXT_TYPES[st.session_state.current_text_type][st.session_state.current_question_index]
        st.write(f"{t['current_question']}: {current_question}")

    user_input = st.text_input(t['input_placeholder'], key="user_input")

    if st.button(t['send_button']):
        st.write("Debug: Send button pressed")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})

            if user_input.startswith('/texto_'):
                text_type = user_input.split('_')[1]
                if text_type in TEXT_TYPES:
                    st.session_state.current_text_type = text_type
                    st.session_state.current_question_index = 0
                    st.session_state.user_responses = []
                    response = f"Comenzando construcción de texto {text_type}. {TEXT_TYPES[text_type][0]}"
                else:
                    response = "Tipo de texto no reconocido. Por favor, intenta de nuevo."
            elif st.session_state.current_text_type:
                st.session_state.user_responses.append(user_input)
                st.session_state.current_question_index += 1

                if st.session_state.current_question_index < len(TEXT_TYPES[st.session_state.current_text_type]):
                    next_question = TEXT_TYPES[st.session_state.current_text_type][st.session_state.current_question_index]
                    response = f"Gracias. Siguiente pregunta: {next_question}"
                else:
                    final_text = " ".join(st.session_state.user_responses)
                    response = f"{t['text_completed']} {final_text}\n\n{t['improve_suggestion']}\n\n{t['generate_arc']}"

                    # Generar diagrama de arco
                    st.write(f"Debug: Generating arc diagram for final text: {final_text}")
                    st.session_state.previous_arc_diagram = st.session_state.current_arc_diagram
                    result = perform_advanced_morphosyntactic_analysis(final_text, nlp_models[lang_code])
                    st.write(f"Debug: Morphosyntactic analysis result: {result}")
                    if 'arc_diagram' in result:
                        st.session_state.current_arc_diagram = result['arc_diagram']
                        st.write(f"Debug: Arc diagram generated with {len(st.session_state.current_arc_diagram)} sentences")
                    else:
                        st.write("Debug: 'arc_diagram' not found in the result of morphosyntactic analysis")

                    response += f"\n\n{t['continue_iteration']}"

                    st.session_state.current_text_type = None
                    st.session_state.current_question_index = 0
            elif user_input.startswith('/analisis_morfosintactico'):
                text = user_input.split(' ', 1)[1].strip('[]')
                st.write(f"Debug: Performing morphosyntactic analysis on: {text}")
                result = perform_advanced_morphosyntactic_analysis(text, nlp_models[lang_code])
                st.write(f"Debug: Morphosyntactic analysis result: {result}")
                st.session_state.previous_arc_diagram = st.session_state.current_arc_diagram
                if 'arc_diagram' in result:
                    st.session_state.current_arc_diagram = result['arc_diagram']
                    st.write(f"Debug: Arc diagram generated with {len(st.session_state.current_arc_diagram)} sentences")
                    response = "Análisis morfosintáctico completado. Por favor, revisa los resultados en la sección de diagramas de arco."
                else:
                    st.write("Debug: 'arc_diagram' not found in the result of morphosyntactic analysis")
                    response = "Hubo un problema al generar el diagrama de arco. Por favor, intenta de nuevo."
            else:
                response = process_chat_input(user_input, lang_code, nlp_models)

            st.session_state.messages.append({"role": "assistant", "content": response})
            #st.experimental_rerun()

    # Mostrar diagramas de arco
    st.write(f"Debug: Current arc diagram: {st.session_state.current_arc_diagram is not None}")
    st.write(f"Debug: Previous arc diagram: {st.session_state.previous_arc_diagram is not None}")

    if st.session_state.current_arc_diagram:
        with current_diagram_container:
            st.subheader(t['current_diagram'])
            for i, arc_diagram in enumerate(st.session_state.current_arc_diagram):
                st.write(f"Oración {i+1}")
                st.write(arc_diagram, unsafe_allow_html=True)
        st.write("Debug: Current arc diagram displayed")
    else:
        st.write("Debug: No current arc diagram to display")

    if st.session_state.previous_arc_diagram:
        with previous_diagram_container:
            st.subheader(t['previous_diagram'])
            for i, arc_diagram in enumerate(st.session_state.previous_arc_diagram):
                st.write(f"Oración {i+1}")
                st.write(arc_diagram, unsafe_allow_html=True)
        st.write("Debug: Previous arc diagram displayed")
    else:
        st.write("Debug: No previous arc diagram to display")

    st.write("Debug: Function completed")
######################################################
if __name__ == "__main__":
    main()