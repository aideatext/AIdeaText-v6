# Importaciones generales
import streamlit as st
import re
import io
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import time
from datetime import datetime
from streamlit_player import st_player  # Necesitarás instalar esta librería: pip install streamlit-player
from spacy import displacy
import logging

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
    store_user_feedback
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
    get_chatbot_response
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
            'tabs': ["Análisis Morfosintáctico", "Análisis Semántico", "Análisis del Discurso", "Chat", "Mi Progreso", "Formulario de Retroalimentación"]
        },
        'en': {
            'welcome': "Welcome to AIdeaText",
            'hello': "Hello",
            'tabs': ["Morphosyntactic Analysis", "Semantic Analysis", "Discourse Analysis", "Chat", "My Progress", "Feedback Form"]
        },
        'fr': {
            'welcome': "Bienvenue à AIdeaText",
            'hello': "Bonjour",
            'tabs': ["Analyse Morphosyntaxique", "Analyse Sémantique", "Analyse du Discours", "Chat", "Mon Progrès", "Formulaire de Rétroaction"]
        }
    }

    t = translations[lang_code]

    st.title(t['welcome'])
    st.write(f"{t['hello']}, {st.session_state.username}")

    tabs = st.tabs(t['tabs'])

    with tabs[0]:
        display_morphosyntax_analysis_interface(nlp_models, lang_code)
    with tabs[1]:
        display_semantic_analysis_interface(nlp_models, lang_code)
    with tabs[2]:
        display_discourse_analysis_interface(nlp_models, lang_code)
    with tabs[3]:
        display_chatbot_interface(lang_code)
    with tabs[4]:
        display_student_progress(st.session_state.username, lang_code)
    with tabs[5]:
        display_feedback_form(lang_code)

##################################################################################################
def display_videos_and_info():
    st.header("Videos: pitch, demos, entrevistas, otros")

    videos = {
        "Intro AideaText": "https://www.youtube.com/watch?v=UA-md1VxaRc",
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

    name = st.text_input(t['name'])
    email = st.text_input(t['email'])
    feedback = st.text_area(t['feedback'])

    if st.button(t['submit']):
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
        st.write(f"Número total de entradas semánticas: {len(semantic_entries)}")
        for entry in semantic_entries:
            st.subheader(f"Análisis del {entry['timestamp']}")
            st.write(f"Archivo analizado: {entry.get('filename', 'Nombre no disponible')}")
            st.write(f"Claves disponibles en esta entrada: {', '.join(entry.keys())}")

            # Verificar si 'relations_graph' está en entry antes de intentar acceder
            if 'network_diagram' in entry:
                try:
                    logger.info(f"Longitud de la imagen recuperada: {len(entry['network_diagram'])}")
                    st.image(f"data:image/png;base64,{entry['network_diagram']}")
                except Exception as e:
                    st.error(f"No se pudo mostrar la imagen: {str(e)}")
                    st.write("Datos de la imagen (para depuración):")
                    st.write(entry['network_diagram'][:100] + "...")
            else:
                logger.warning(f"No se encontró 'relations_graph' en la entrada: {entry.keys()}")
                st.write("No se encontró el gráfico para este análisis.")

##########################################################
    with st.expander("Histórico de Análisis Discursivos"):
        discourse_entries = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'discourse']
        for entry in discourse_entries:
            st.subheader(f"Análisis del {entry['timestamp']}")
            st.write(f"Archivo patrón: {entry.get('filename1', 'Nombre no disponible')}")
            st.write(f"Archivo comparado: {entry.get('filename2', 'Nombre no disponible')}")

            try:
                # Intentar obtener y combinar las dos imágenes
                if 'graph1' in entry and 'graph2' in entry:
                    img1 = Image.open(BytesIO(base64.b64decode(entry['graph1'])))
                    img2 = Image.open(BytesIO(base64.b64decode(entry['graph2'])))

                    # Crear una nueva imagen combinada
                    total_width = img1.width + img2.width
                    max_height = max(img1.height, img2.height)
                    combined_img = Image.new('RGB', (total_width, max_height))

                    # Pegar las dos imágenes lado a lado
                    combined_img.paste(img1, (0, 0))
                    combined_img.paste(img2, (img1.width, 0))

                    # Convertir la imagen combinada a bytes
                    buffered = BytesIO()
                    combined_img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()

                    # Mostrar la imagen combinada
                    st.image(f"data:image/png;base64,{img_str}")
                elif 'combined_graph' in entry:
                    # Si ya existe una imagen combinada, mostrarla directamente
                    img_bytes = base64.b64decode(entry['combined_graph'])
                    st.image(img_bytes)
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

def display_morphosyntax_results(result, lang_code, t):
    if result is None:
        st.warning(t['no_results'])  # Añade esta traducción a tu diccionario
        return

    doc = result['doc']
    advanced_analysis = result['advanced_analysis']

    # Mostrar leyenda (código existente)
    st.markdown(f"##### {t['legend']}")
    legend_html = "<div style='display: flex; flex-wrap: wrap;'>"
    for pos, color in POS_COLORS.items():
        if pos in POS_TRANSLATIONS[lang_code]:
            legend_html += f"<div style='margin-right: 10px;'><span style='background-color: {color}; padding: 2px 5px;'>{POS_TRANSLATIONS[lang_code][pos]}</span></div>"
    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

    # Mostrar análisis de palabras repetidas (código existente)
    word_colors = get_repeated_words_colors(doc)
    with st.expander(t['repeated_words'], expanded=True):
        highlighted_text = highlight_repeated_words(doc, word_colors)
        st.markdown(highlighted_text, unsafe_allow_html=True)

    # Mostrar estructura de oraciones
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
    with st.expander(t['arc_diagram'], expanded=True):
        sentences = list(doc.sents)
        arc_diagrams = []
        for i, sent in enumerate(sentences):
            st.subheader(f"{t['sentence']} {i+1}")
            html = displacy.render(sent, style="dep", options={"distance": 100})
            html = html.replace('height="375"', 'height="200"')
            html = re.sub(r'<svg[^>]*>', lambda m: m.group(0).replace('height="450"', 'height="300"'), html)
            html = re.sub(r'<g [^>]*transform="translate\((\d+),(\d+)\)"', lambda m: f'<g transform="translate({m.group(1)},50)"', html)
            st.write(html, unsafe_allow_html=True)
            arc_diagrams.append(html)

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

    def clean_and_convert(value):
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            try:
                return float(value.replace(',', '.'))
            except ValueError:
                return 0.0
        return 0.0

    def process_key_concepts(key_concepts):
        df = pd.DataFrame(key_concepts, columns=['Concepto', 'Frecuencia'])
        df['Frecuencia'] = df['Frecuencia'].apply(clean_and_convert)
        return df

    col1, col2 = st.columns(2)

    with col1:
        with st.expander(t.get('file_uploader1', "Documento 1"), expanded=True):
            if 'graph1' in result:
                st.pyplot(result['graph1'])
            else:
                st.warning(t.get('graph_not_available', "El gráfico no está disponible."))
            st.subheader(t.get('key_concepts', "Conceptos Clave"))
            if 'key_concepts1' in result:
                df1 = process_key_concepts(result['key_concepts1'])
                st.table(df1)
            else:
                st.warning(t.get('concepts_not_available', "Los conceptos clave no están disponibles."))

    with col2:
        with st.expander(t.get('file_uploader2', "Documento 2"), expanded=True):
            if 'graph2' in result:
                st.pyplot(result['graph2'])
            else:
                st.warning(t.get('graph_not_available', "El gráfico no está disponible."))
            st.subheader(t.get('key_concepts', "Conceptos Clave"))
            if 'key_concepts2' in result:
                df2 = process_key_concepts(result['key_concepts2'])
                st.table(df2)
            else:
                st.warning(t.get('concepts_not_available', "Los conceptos clave no están disponibles."))

    # Comparación de conceptos clave
    st.subheader(t.get('comparison', "Comparación de conceptos entre ambos documentos"))
    if 'key_concepts1' in result and 'key_concepts2' in result:
        df1 = process_key_concepts(result['key_concepts1']).set_index('Concepto')
        df2 = process_key_concepts(result['key_concepts2']).set_index('Concepto')

        df_comparison = pd.concat([df1, df2], axis=1, keys=[t.get('file_uploader1', "Documento 1"), t.get('file_uploader2', "Documento 2")])
        df_comparison = df_comparison.fillna(0.0)

        # Asegurarse de que todas las columnas sean float
        for col in df_comparison.columns:
            df_comparison[col] = df_comparison[col].astype(float)

        # Mostrar la tabla de comparación
        try:
            st.dataframe(df_comparison.style.format("{:.2f}"), width=1000)
        except Exception as e:
            st.error(f"Error al mostrar el DataFrame: {str(e)}")
            st.write("DataFrame sin formato:")
            st.write(df_comparison)
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
def display_chatbot_interface(lang_code):
    translations = {
        'es': {
            'title': "Expertos en Vacaciones",
            'input_placeholder': "Escribe tu mensaje aquí...",
            'initial_message': "¡Hola! ¿Cómo podemos ayudarte?"
        },
        'en': {
            'title': "Vacation Experts",
            'input_placeholder': "Type your message here...",
            'initial_message': "Hi! How can we help you?"
        },
        'fr': {
            'title': "Experts en Vacances",
            'input_placeholder': "Écrivez votre message ici...",
            'initial_message': "Bonjour! Comment pouvons-nous vous aider?"
        }
    }
    t = translations[lang_code]
    st.title(t['title'])

    if 'chatbot' not in st.session_state:
        st.session_state.chatbot = initialize_chatbot()
    if 'messages' not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": t['initial_message']}]

    # Contenedor principal para el chat
    chat_container = st.container()

    # Mostrar mensajes existentes
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Área de entrada del usuario
    user_input = st.chat_input(t['input_placeholder'])

    if user_input:
        # Agregar mensaje del usuario
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Mostrar mensaje del usuario
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_input)

        # Generar respuesta del chatbot
        with chat_container:
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                for chunk in get_chatbot_response(st.session_state.chatbot, user_input, lang_code):
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")
                message_placeholder.markdown(full_response)

        # Agregar respuesta del asistente a los mensajes
        st.session_state.messages.append({"role": "assistant", "content": full_response})

        # Guardar la conversación en la base de datos
        try:
            store_chat_history(st.session_state.username, st.session_state.messages)
            st.success("Conversación guardada exitosamente")
        except Exception as e:
            st.error(f"Error al guardar la conversación: {str(e)}")
            logger.error(f"Error al guardar el historial de chat para {st.session_state.username}: {str(e)}")

    # Scroll al final del chat
    st.markdown('<script>window.scrollTo(0,document.body.scrollHeight);</script>', unsafe_allow_html=True)

######################################################
if __name__ == "__main__":
    main()