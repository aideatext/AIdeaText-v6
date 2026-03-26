# Importaciones generales
import sys
import streamlit as st
from translations import get_translations
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
        create_admin_user,
        create_student_user,
        get_user,
        get_student_data,
        store_file_contents, #gestión archivos
        retrieve_file_contents, #gestión archivos
        get_user_files, #gestión archivos
        delete_file, # #gestión archivos
        store_application_request, # form
        store_user_feedback, # form
        store_morphosyntax_result,
        store_semantic_result,
        store_discourse_analysis_result,
        store_chat_history,
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
    process_morphosyntactic_input,
    process_semantic_input,
    process_discourse_input,
    process_chat_input,
    get_connectors,
    handle_semantic_commands,
    generate_topics_visualization,
    extract_topics,
    get_semantic_chatbot_response
)

#####################-- Funciones de inicialización y configuración--- ##############################################################################
def initialize_session_state():
    if 'initialized' not in st.session_state:
        st.session_state.clear()
        st.session_state.initialized = True
        st.session_state.logged_in = False
        st.session_state.page = 'login'
        st.session_state.username = None
        st.session_state.role = None

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

#############################--- # Funciones de autenticación y registro --- #####################################################################
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
            st.experimental_rerun()
        else:
            st.error("Credenciales incorrectas")

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

def is_institutional_email(email):
    forbidden_domains = ['gmail.com', 'hotmail.com', 'yahoo.com', 'outlook.com']
    return not any(domain in email.lower() for domain in forbidden_domains)

###########################################--- Funciones de interfaz general --- ######################################################

def user_page():
    # Asumimos que el idioma seleccionado está almacenado en st.session_state.lang_code
    # Si no está definido, usamos 'es' como valor predeterminado
    t = get_translations(lang_code)

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

#####################--- Funciones de manejo de archivos --- #############################################################################

def handle_file_upload(username, lang_code, nlp_models, t, analysis_type):
    st.subheader(t['get_text']('file_upload_section', analysis_type.upper(), 'File Upload'))

    uploaded_file = st.file_uploader(
        t['get_text']('file_uploader', analysis_type.upper(), 'Upload a file'),
        type=['txt', 'pdf', 'docx', 'doc', 'odt']
    )

    if uploaded_file is not None:
        file_contents = read_file_contents(uploaded_file)

        if store_file_contents(username, uploaded_file.name, file_contents, analysis_type):
            st.success(t['get_text']('file_upload_success', analysis_type.upper(), 'File uploaded successfully'))
            return file_contents, uploaded_file.name
        else:
            st.error(t['get_text']('file_upload_error', analysis_type.upper(), 'Error uploading file'))

    return None, None

def read_file_contents(uploaded_file):
    # Implementar la lógica para leer diferentes tipos de archivos
    # Por ahora, asumimos que es un archivo de texto
    return uploaded_file.getvalue().decode('utf-8')

######################--- Funciones generales de análisis ---########################################################
def display_analysis_results(analysis, lang_code, t):
    if analysis is None:
        st.warning(t.get('no_analysis', "No hay análisis disponible."))
        return

    if not isinstance(analysis, dict):
        st.error(f"Error: El resultado del análisis no es un diccionario. Tipo actual: {type(analysis)}")
        return

    if 'type' not in analysis:
        st.error("Error: El resultado del análisis no contiene la clave 'type'")
        st.write("Claves presentes en el resultado:", list(analysis.keys()))
        return

    if analysis['type'] == 'morphosyntactic':
        st.subheader(t.get('morphosyntactic_title', "Análisis Morfosintáctico"))
        display_morphosyntax_results(analysis['result'], lang_code, t)
    elif analysis['type'] == 'semantic':
        st.subheader(t.get('semantic_title', "Análisis Semántico"))
        display_semantic_results(analysis['result'], lang_code, t)
    elif analysis['type'] == 'discourse':
        st.subheader(t.get('discourse_title', "Análisis del Discurso"))
        display_discourse_results(analysis['result'], lang_code, t)
    else:
        st.warning(t.get('no_analysis', "No hay análisis disponible."))

    # Mostrar el contenido completo del análisis para depuración
    st.write("Contenido completo del análisis:", analysis)

def handle_user_input(user_input, lang_code, nlp_models, analysis_type, file_contents=None):
    response = process_chat_input(user_input, lang_code, nlp_models, analysis_type, file_contents, t)
    # Procesa la respuesta y actualiza la interfaz de usuario


###################################--- Funciones específicas de análisis morfosintáctico ---################################################################

def display_morphosyntax_analysis_interface(user_input, nlp_models, lang_code, t):
    logging.info(f"Displaying morphosyntax analysis interface. Language code: {lang_code}")

    # Inicializar el historial del chat si no existe
    if 'morphosyntax_chat_history' not in st.session_state:
        initial_message = t['get_text']('initial_message', 'MORPHOSYNTACTIC',
            "Este es un chatbot para análisis morfosintáctico. Para generar un diagrama de arco, "
            "use el comando /analisis_morfosintactico seguido del texto entre corchetes.")
        st.session_state.morphosyntax_chat_history = [{"role": "assistant", "content": initial_message}]

    # Contenedor para el chat
    chat_container = st.container()

    # Mostrar el historial del chat
    with chat_container:
        for message in st.session_state.morphosyntax_chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "visualization" in message:
                    st.components.v1.html(message["visualization"], height=450, scrolling=True)

    # Input del usuario
    user_input = st.chat_input(t['get_text']('chat_placeholder', 'MORPHOSYNTACTIC',
        "Ingrese su mensaje o use /analisis_morfosintactico [texto] para analizar"))

    if user_input:
        # Añadir el mensaje del usuario al historial
        st.session_state.morphosyntax_chat_history.append({"role": "user", "content": user_input})

        # Procesar el input del usuario
        if user_input.startswith('/analisis_morfosintactico'):
            text_to_analyze = user_input.split('[', 1)[1].rsplit(']', 1)[0]
            try:
                result = perform_advanced_morphosyntactic_analysis(text_to_analyze, nlp_models[lang_code])

                # Guardar el resultado en el estado de la sesión
                st.session_state.current_analysis = {
                    'type': 'morphosyntactic',
                    'result': result
                }

                # Añadir el resultado al historial del chat
                response = t['get_text']('analysis_completed', 'MORPHOSYNTACTIC', 'Análisis morfosintáctico completado.')
                st.session_state.morphosyntax_chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "visualization": result['arc_diagram'][0] if result['arc_diagram'] else None
                })

                # Guardar resultados en la base de datos
                if store_morphosyntax_result(
                    st.session_state.username,
                    text_to_analyze,
                    get_repeated_words_colors(nlp_models[lang_code](text_to_analyze)),
                    result['arc_diagram'],
                    result['pos_analysis'],
                    result['morphological_analysis'],
                    result['sentence_structure']
                ):
                    st.success(t['get_text']('success_message', 'MORPHOSYNTACTIC', 'Análisis guardado correctamente.'))
                else:
                    st.error(t['get_text']('error_message', 'MORPHOSYNTACTIC', 'Hubo un problema al guardar el análisis.'))

            except Exception as e:
                error_message = t['get_text']('analysis_error', 'MORPHOSYNTACTIC', f'Ocurrió un error durante el análisis: {str(e)}')
                st.session_state.morphosyntax_chat_history.append({"role": "assistant", "content": error_message})
                logging.error(f"Error in morphosyntactic analysis: {str(e)}")
        else:
            # Aquí puedes procesar otros tipos de inputs del usuario si es necesario
            response = t['get_text']('command_not_recognized', 'MORPHOSYNTACTIC',
                "Comando no reconocido. Use /analisis_morfosintactico [texto] para realizar un análisis.")
            st.session_state.morphosyntax_chat_history.append({"role": "assistant", "content": response})

        # Forzar la actualización de la interfaz
        st.experimental_rerun()

    logging.info("Morphosyntax analysis interface displayed successfully")


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

#####################--- Funciones específicas de análisis semántico --- ##############
#display_chatbot_interface(lang_code, nlp_models, t, analysis_type='semantic')

def display_semantic_analysis_interface(lang_code, nlp_models, t):
    print("Iniciando display_semantic_analysis_interface")
    st.write("Debug: Iniciando interfaz de análisis semántico")

    st.header(t['get_text']('semantic_analysis_title', 'SEMANTIC', 'Semantic Analysis'))

    # Sección para gestionar archivos
    with st.expander("Gestión de Archivos", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            # Cargar nuevo archivo
            uploaded_file = st.file_uploader(t['file_uploader'], type=['txt', 'pdf', 'docx', 'doc', 'odt'])
            if uploaded_file:
                file_contents = read_file_contents(uploaded_file)
                if store_file_contents(st.session_state.username, uploaded_file.name, file_contents, "semantic"):
                    st.success(t['file_upload_success'])
                    st.session_state.file_contents = file_contents
                    st.session_state.file_name = uploaded_file.name
                else:
                    st.error(t['file_upload_error'])

        with col2:
            # Lista desplegable de archivos guardados
            saved_files = get_user_files(st.session_state.username, "semantic")
            if saved_files:
                selected_file = st.selectbox(
                    t['select_saved_file'],
                    options=[file['file_name'] for file in saved_files],
                    format_func=lambda x: f"{x} ({next(file['timestamp'] for file in saved_files if file['file_name'] == x)})"
                )
                col2_1, col2_2 = st.columns(2)
                with col2_1:
                    if st.button(t['load_selected_file']):
                        file_contents = retrieve_file_contents(st.session_state.username, selected_file, "semantic")
                        if file_contents:
                            st.session_state.file_contents = file_contents
                            st.session_state.file_name = selected_file
                            st.success(t['file_loaded_success'])
                        else:
                            st.error(t['file_load_error'])
                with col2_2:
                    if st.button(t['delete_selected_file']):
                        if 'file_name' in st.session_state and delete_file(st.session_state.username, st.session_state.file_name, "semantic"):
                            st.success(t['file_deleted_success'])
                            st.session_state.pop('file_contents', None)
                            st.session_state.pop('file_name', None)
                        else:
                            st.error(t['file_delete_error'])

        # Botón para analizar documento
        if st.button(t['analyze_document']):
            if 'file_contents' in st.session_state:
                result = perform_semantic_analysis(st.session_state.file_contents, nlp_models[lang_code], lang_code)
                st.session_state.semantic_result = result
                if store_semantic_result(st.session_state.username, st.session_state.file_contents, result):
                    st.success(t['analysis_saved_success'])
                else:
                    st.error(t['analysis_save_error'])
            else:
                st.warning(t['no_file_selected'])

    # Interfaz principal de chat y grafo
    chat_col, graph_col = st.columns([1, 1])

    with chat_col:
        st.subheader(t['chat_title'])
        # Mostrar la interfaz de chat
        display_semantic_chatbot_interface(nlp_models, lang_code, st.session_state.get('file_contents'), t)

    with graph_col:
        st.subheader(t['graph_title'])
        if 'semantic_result' in st.session_state:
            display_semantic_results(st.session_state.semantic_result, lang_code, t)
        else:
            st.info(t['no_analysis'])

    # Mostrar el chatbot general para análisis semántico
    st.subheader("Chatbot de Análisis Semántico")
    display_chatbot_interface(lang_code, nlp_models, t, analysis_type='semantic')

############################
def display_semantic_chatbot_interface(nlp_models, lang_code, file_contents, t):
    # Generar una clave única para esta sesión si aún no existe
    if 'semantic_chat_input_key' not in st.session_state:
        st.session_state.semantic_chat_input_key = f"semantic_chat_input_{id(st.session_state)}"

    # Inicializar el historial del chat si no existe
    if 'semantic_chat_history' not in st.session_state:
        st.session_state.semantic_chat_history = [{"role": "assistant", "content": t['initial_message']}]

    # Crear un contenedor con altura fija para el chat
    chat_container = st.container()

    # Mostrar el historial del chat en el contenedor
    with chat_container:
        # Crear un área de desplazamiento para el historial del chat
        with st.empty():
            chat_history = "".join([f"{'You' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}\n\n" for msg in st.session_state.semantic_chat_history])
            st.text_area("Chat History", value=chat_history, height=300, key="chat_history", disabled=True)

    # Usa la clave única para el chat_input
    user_input = st.chat_input(t['chat_placeholder'], key=st.session_state.semantic_chat_input_key)

    if user_input:
        st.session_state.semantic_chat_history.append({"role": "user", "content": user_input})

        try:
            response, graph = handle_semantic_commands(user_input, lang_code, file_contents, nlp_models)
            st.session_state.semantic_chat_history.append({"role": "assistant", "content": response})

            if graph is not None:
                st.session_state.semantic_graph = graph
        except Exception as e:
            error_message = f"Error al procesar la solicitud: {str(e)}"
            st.session_state.semantic_chat_history.append({"role": "assistant", "content": error_message})
            st.error(error_message)

    # Botón para limpiar el historial del chat
    if st.button(t['clear_chat'], key=f"clear_chat_{st.session_state.semantic_chat_input_key}"):
        st.session_state.semantic_chat_history = [{"role": "assistant", "content": t['initial_message']}]

############################
def display_semantic_results(result, lang_code, t):
    if result is None:
        st.warning(t.get('no_results', "No hay resultados disponibles."))
        return

    # Mostrar conceptos clave
    st.subheader(t.get('key_concepts', "Conceptos Clave"))
    if 'key_concepts' in result:
        for concept, frequency in result['key_concepts']:
            st.write(f"{concept}: {frequency}")
    else:
        st.warning(t.get('no_key_concepts', "No se encontraron conceptos clave."))

    # Mostrar el gráfico de relaciones conceptuales
    st.subheader(t.get('conceptual_relations', "Relaciones Conceptuales"))
    if 'relations_graph' in result:
        st.pyplot(result['relations_graph'])
    else:
        st.warning(t.get('no_graph', "No se pudo generar el gráfico de relaciones."))

    # Mostrar el contenido completo del resultado para depuración
    st.write("Contenido completo del resultado:", result)

############################





##################################### --- Funciones específicas de análisis del discurso --- ##############################################################

def display_discourse_analysis_interface(nlp_models, lang_code, t):
    st.header(t['get_text']('discourse_analysis_title', 'DISCOURSE', 'Discourse Analysis'))

    # Mostrar la interfaz de chat
    display_chatbot_interface(lang_code, nlp_models, t, analysis_type='discourse')

    # Subir archivos
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file1 = st.file_uploader(t['get_text']('file_uploader1', 'DISCOURSE', 'Upload first file'), type=['txt'])
    with col2:
        uploaded_file2 = st.file_uploader(t['get_text']('file_uploader2', 'DISCOURSE', 'Upload second file'), type=['txt'])

    if uploaded_file1 is not None and uploaded_file2 is not None:
        if st.button(t['get_text']('analyze_button', 'DISCOURSE', 'Analyze')):
            text_content1 = uploaded_file1.getvalue().decode('utf-8')
            text_content2 = uploaded_file2.getvalue().decode('utf-8')

            # Realizar el análisis
            analysis_result = perform_discourse_analysis(text_content1, text_content2, nlp_models[lang_code], lang_code)

            # Guardar el resultado en el estado de la sesión
            st.session_state.discourse_result = analysis_result

            # Mostrar los resultados del análisis
            display_discourse_results(analysis_result, lang_code, t)

            # Guardar el resultado del análisis
            if store_discourse_analysis_result(st.session_state.username, text_content1, text_content2, analysis_result):
                st.success(t['get_text']('success_message', 'DISCOURSE', 'Analysis result saved successfully'))
            else:
                st.error(t['get_text']('error_message', 'DISCOURSE', 'Failed to save analysis result'))
    elif 'discourse_result' in st.session_state and st.session_state.discourse_result is not None:
        # Si hay un resultado guardado, mostrarlo
        display_discourse_results(st.session_state.discourse_result, lang_code, t)
    else:
        st.info(t['get_text']('DISCOURSE_initial_message', 'DISCOURSE', 'Upload two files and click "Analyze" to start the discourse analysis.'))

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

#################################### --- Función general de interfaz de chatbot --- ###############################################################

def display_chatbot_interface(lang_code, nlp_models, t, analysis_type='morphosyntactic'):
    # Verificar que todos los argumentos necesarios estén presentes
    if not all([lang_code, nlp_models, t]):
        st.error("Missing required arguments in display_chatbot_interface")
        return

    valid_types = ['morphosyntactic', 'semantic', 'discourse']
    if analysis_type not in valid_types:
        raise ValueError(f"Invalid analysis_type. Must be one of {valid_types}")

    logger.debug(f"Displaying chatbot interface for {analysis_type} analysis")

    # Obtener el mensaje inicial del diccionario de traducciones
    initial_message = t['get_text'](f'initial_message', analysis_type.upper(), "Mensaje inicial no encontrado")

    chat_key = f'{analysis_type}_messages'
    if chat_key not in st.session_state or not st.session_state[chat_key]:
        st.session_state[chat_key] = [{"role": "assistant", "content": initial_message, "visualizations": []}]
    elif st.session_state[chat_key][0]['content'] != initial_message:
        st.session_state[chat_key][0] = {"role": "assistant", "content": initial_message, "visualizations": []}

    # Contenedor para el chat
    chat_container = st.container()

    # Mostrar el historial del chat
    with chat_container:
        for message in st.session_state[chat_key]:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                for i, visualization in enumerate(message.get("visualizations", [])):
                    if visualization:
                        if analysis_type == 'morphosyntactic':
                            st.subheader(f"{t['get_text']('sentence', 'COMMON', 'Oración')} {i+1}")
                            st.components.v1.html(visualization, height=450, scrolling=True)
                        elif analysis_type in ['semantic', 'discourse']:
                            st.pyplot(visualization)

    # Input del usuario
    chat_input_key = f"chat_input_{analysis_type}_{lang_code}"
    user_input = st.chat_input(
        t['get_text']('input_placeholder', analysis_type.upper(), 'Ingrese su mensaje aquí...'),
        key=chat_input_key
    )

    if user_input:
        st.session_state[chat_key].append({"role": "user", "content": user_input, "visualizations": []})

        try:
            # Procesar la entrada del usuario
            response, visualizations = process_chat_input(user_input, lang_code, nlp_models, analysis_type, t)

            st.session_state[chat_key].append({"role": "assistant", "content": response, "visualizations": visualizations})
            st.experimental_rerun()

        except Exception as e:
            error_message = t['get_text']('error_message', 'COMMON', f"Lo siento, ocurrió un error: {str(e)}")
            st.error(error_message)
            st.session_state[chat_key].append({"role": "assistant", "content": error_message, "visualizations": []})

    # Lógica específica para cada tipo de análisis
    uploaded_file = None  # Inicializar uploaded_file a None

    if analysis_type in ['semantic', 'discourse']:
        file_key = f"{analysis_type}_file_uploader_{lang_code}"

        if analysis_type == 'discourse':
            # Para el análisis del discurso, necesitamos dos archivos
            uploaded_file1 = st.file_uploader(
                t['get_text']('file_uploader1', 'DISCOURSE', 'Upload first file'),
                type=['txt', 'pdf', 'docx', 'doc', 'odt'],
                key=f"{file_key}_1"
            )
            uploaded_file2 = st.file_uploader(
                t['get_text']('file_uploader2', 'DISCOURSE', 'Upload second file'),
                type=['txt', 'pdf', 'docx', 'doc', 'odt'],
                key=f"{file_key}_2"
            )
            uploaded_file = (uploaded_file1, uploaded_file2)
        else:
            uploaded_file = st.file_uploader(
                t['get_text']('file_uploader', analysis_type.upper(), 'Upload a file'),
                type=['txt', 'pdf', 'docx', 'doc', 'odt'],
                key=file_key
            )

        if uploaded_file:
            if analysis_type == 'discourse':
                if uploaded_file[0] and uploaded_file[1]:
                    file_contents1 = read_file_contents(uploaded_file[0])
                    file_contents2 = read_file_contents(uploaded_file[1])
                    if st.button(t['get_text']('analyze_button', 'DISCOURSE', 'Analyze')):
                        result = perform_discourse_analysis(file_contents1, file_contents2, nlp_models[lang_code], lang_code)
                        result = {'type': 'discourse', 'result': result}
                        st.session_state['discourse_result'] = result
                        display_analysis_results(result, lang_code, t)
            else:
                file_contents = read_file_contents(uploaded_file)
                if st.button(t['get_text']('analyze_button', analysis_type.upper(), 'Analyze')):
                    if analysis_type == 'semantic':
                        result = perform_semantic_analysis(file_contents, nlp_models[lang_code], lang_code)
                        result = {'type': 'semantic', 'result': result}
                    st.session_state[f'{analysis_type}_result'] = result
                    display_analysis_results(result, lang_code, t)


def process_chat_input(user_input, lang_code, nlp_models, analysis_type, t, file_contents=None):
    chatbot_key = f'{analysis_type}_chatbot'
    if chatbot_key not in st.session_state:
        st.session_state[chatbot_key] = initialize_chatbot(analysis_type)

    chatbot = st.session_state[chatbot_key]

    if analysis_type == 'morphosyntactic':
        response = chatbot.process_input(user_input, lang_code, nlp_models, t)
        visualizations = []
        if user_input.startswith('/analisis_morfosintactico') or user_input.startswith('/morphosyntactic_analysis') or user_input.startswith('/analyse_morphosyntaxique'):
            result = perform_advanced_morphosyntactic_analysis(user_input.split(' ', 1)[1].strip('[]'), nlp_models[lang_code])
            visualizations = result.get('arc_diagram', [])
        return response, visualizations
    elif analysis_type == 'semantic':
        response, graph = chatbot.process_input(user_input, lang_code, nlp_models[lang_code], file_contents, t)
        return response, [graph] if graph else []
    elif analysis_type == 'discourse':
        response = chatbot.process_input(user_input, lang_code, nlp_models, t)
        visualizations = []
        if user_input.startswith('/analisis_discurso') or user_input.startswith('/discourse_analysis') or user_input.startswith('/analyse_discours'):
            texts = user_input.split(' ', 1)[1].split('|')
            if len(texts) == 2:
                result = perform_discourse_analysis(texts[0].strip(), texts[1].strip(), nlp_models[lang_code], lang_code)
                visualizations = [result.get('graph1'), result.get('graph2'), result.get('combined_graph')]
        return response, visualizations
    else:
        raise ValueError(f"Invalid analysis_type: {analysis_type}")

######################################################
if __name__ == "__main__":
    main()