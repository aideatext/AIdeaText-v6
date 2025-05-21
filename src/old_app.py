#old.app.py

import logging
import datetime
import io
import base64
import os
import streamlit as st
import spacy
from spacy import displacy
import re
import numpy as np
import certifi
#from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
from azure.cosmos import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from bson.objectid import ObjectId
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

from modules.auth import (
    clean_and_validate_key,
    register_user,
    authenticate_user,
    get_user_role
)

from modules.morpho_analysis import get_repeated_words_colors, highlight_repeated_words, POS_COLORS, POS_TRANSLATIONS
from modules.syntax_analysis import visualize_syntax

# Azure Cosmos DB configuration
cosmos_endpoint = os.environ.get("COSMOS_ENDPOINT")
cosmos_key = os.environ.get("COSMOS_KEY")

if not cosmos_endpoint or not cosmos_key:
    raise ValueError("Las variables de entorno COSMOS_ENDPOINT y COSMOS_KEY deben estar configuradas")

try:
    cosmos_key = clean_and_validate_key(cosmos_key)
    cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)

    # SQL API database for user management
    user_database = cosmos_client.get_database_client("user_database")
    user_container = user_database.get_container_client("users")

    print("Conexión a Cosmos DB SQL API exitosa")
except Exception as e:
    print(f"Error al conectar con Cosmos DB SQL API: {str(e)}")
    raise

# MongoDB API configuration for text analysis results
#mongo_connection_string = os.environ.get("MONGODB_CONNECTION_STRING")
cosmos_mongodb_connection_string = os.getenv("MONGODB_CONNECTION_STRING")
if not cosmos_mongodb_connection_string:
    logger.error("La variable de entorno MONGODB_CONNECTION_STRING no está configurada")
else:
    logger.info("La variable de entorno MONGODB_CONNECTION_STRING está configurada")

# Variable global para el cliente de MongoDB
mongo_client = None
db = None
analysis_collection = None
####################################################################################################################
def initialize_mongodb_connection():
    global mongo_client, db, analysis_collection
    try:
        # Crear el cliente de MongoDB con configuración TLS
        mongo_client = MongoClient(cosmos_mongodb_connection_string,
                                   tls=True,
                                   tlsCAFile=certifi.where(),
                                   retryWrites=False,
                                   serverSelectionTimeoutMS=5000,
                                   connectTimeoutMS=10000,
                                   socketTimeoutMS=10000)

        # Forzar una conexión para verificar
        mongo_client.admin.command('ping')

        # Seleccionar la base de datos y la colección
        db = mongo_client['aideatext_db']
        analysis_collection = db['text_analysis']

        logger.info("Conexión a Cosmos DB MongoDB API exitosa")
        return True
    except Exception as e:
        logger.error(f"Error al conectar con Cosmos DB MongoDB API: {str(e)}", exc_info=True)
        return False

##################################################################################################################3
def get_student_data(username):
    if analysis_collection is None:
        logger.error("La conexión a MongoDB no está inicializada")
        return None

    try:
        # Buscar los datos del estudiante
        student_data = analysis_collection.find({"username": username}).sort("timestamp", -1)

        if not student_data:
            return None

        # Formatear los datos
        formatted_data = {
            "username": username,
            "entries": [],
            "entries_count": 0,
            "word_count": {},
            "arc_diagrams": [],
            "network_diagrams": []
        }

        for entry in student_data:
            formatted_data["entries"].append({
                "timestamp": entry["timestamp"].isoformat(),
                "text": entry["text"]
            })
            formatted_data["entries_count"] += 1

            # Agregar conteo de palabras
            for category, count in entry.get("word_count", {}).items():
                if category in formatted_data["word_count"]:
                    formatted_data["word_count"][category] += count
                else:
                    formatted_data["word_count"][category] = count

            # Agregar diagramas
            formatted_data["arc_diagrams"].extend(entry.get("arc_diagrams", []))
            formatted_data["network_diagrams"].append(entry.get("network_diagram", ""))

        return formatted_data
    except Exception as e:
        logger.error(f"Error al obtener datos del estudiante {username}: {str(e)}")
        return None


##################################################################################################################
# Función para insertar un documento
def insert_document(document):
    try:
        result = analysis_collection.insert_one(document)
        logger.info(f"Documento insertado con ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        logger.error(f"Error al insertar documento: {str(e)}", exc_info=True)
        return None

# Configure the page to use the full width
st.set_page_config(
    page_title="AIdeaText",
    layout="wide",
    page_icon="random"
)
#####################################################################################################
@st.cache_resource
def load_chatbot_model():
    try:
        from transformers import BlenderbotTokenizer, BlenderbotForConditionalGeneration
        tokenizer = BlenderbotTokenizer.from_pretrained("facebook/blenderbot-400M-distill")
        model = BlenderbotForConditionalGeneration.from_pretrained("facebook/blenderbot-400M-distill")
        return tokenizer, model
    except Exception as e:
        logger.error(f"Error al cargar el modelo del chatbot: {str(e)}")
        return None, None

# Load the chatbot model
chatbot_tokenizer, chatbot_model = load_chatbot_model()

def get_chatbot_response(input_text):
    if chatbot_tokenizer is None or chatbot_model is None:
        return "Lo siento, el chatbot no está disponible en este momento."
    try:
        inputs = chatbot_tokenizer(input_text, return_tensors="pt")
        reply_ids = chatbot_model.generate(**inputs)
        return chatbot_tokenizer.batch_decode(reply_ids, skip_special_tokens=True)[0]
    except Exception as e:
        logger.error(f"Error al generar respuesta del chatbot: {str(e)}")
        return "Lo siento, hubo un error al procesar tu mensaje."
########################################################################################################
def load_spacy_models():
    return {
        'es': spacy.load("es_core_news_lg"),
        'en': spacy.load("en_core_web_lg"),
        'fr': spacy.load("fr_core_news_lg")
    }
#########################################################################################################
def store_analysis_result(username, text, repeated_words, arc_diagrams, network_diagram):
    if analysis_collection is None:
        logging.error("La conexión a MongoDB no está inicializada")
        return False

    try:
        # Convertir el gráfico de matplotlib a base64
        buffer = io.BytesIO()
        network_diagram.savefig(buffer, format='png')
        buffer.seek(0)
        network_diagram_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Contar palabras repetidas por categoría gramatical
        word_count = {}
        for word, color in repeated_words.items():
            category = POS_TRANSLATIONS.get(color, 'Otros')
            word_count[category] = word_count.get(category, 0) + 1

        # Crear el documento para MongoDB
        analysis_document = {
            'username': username,  # Este campo se usará como sharded key
            'timestamp': datetime.datetime.utcnow(),
            'text': text,
            'word_count': word_count,
            'arc_diagrams': arc_diagrams,
            'network_diagram': network_diagram_base64
        }

        # Insertar el documento en la colección
        result = analysis_collection.insert_one(analysis_document)

        logging.info(f"Análisis guardado con ID: {result.inserted_id} para el usuario: {username}")
        return True
    except Exception as e:
        logging.error(f"Error al guardar el análisis para el usuario {username}: {str(e)}")
        return False

#############################################################################################33
def login_page():
    st.title("Iniciar Sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type='password')
    if st.button("Iniciar Sesión"):
        if authenticate_user(username, password):
            st.success(f"Bienvenido, {username}!")
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.role = get_user_role(username)
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

#####################################################################################################3
def register_page():
    st.title("Registrarse")
    new_username = st.text_input("Nuevo Usuario")
    new_password = st.text_input("Nueva Contraseña", type='password')
    role = st.selectbox("Rol", ["Estudiante", "Profesor"])

    additional_info = {}
    if role == "Estudiante":
        additional_info['carrera'] = st.text_input("Carrera")
    elif role == "Profesor":
        additional_info['departamento'] = st.text_input("Departamento")

    if st.button("Registrarse"):
        if register_user(new_username, new_password, role, additional_info):
            st.success("Registro exitoso. Por favor, inicia sesión.")
        else:
            st.error("El usuario ya existe o ocurrió un error durante el registro")

############################################################################################
def main_app():
    # Load spaCy models
    nlp_models = load_spacy_models()

    # Language selection
    languages = {
        'Español': 'es',
        'English': 'en',
        'Français': 'fr'
    }
    selected_lang = st.sidebar.selectbox("Select Language / Seleccione el idioma / Choisissez la langue", list(languages.keys()))
    lang_code = languages[selected_lang]

    # Translations
    translations = {
        'es': {
            'title': "AIdeaText - Análisis morfológico y sintáctico",
            'input_label': "Ingrese un texto para analizar (máx. 5,000 palabras):",
            'input_placeholder': "El objetivo de esta aplicación es que mejore sus habilidades de redacción. Para ello, después de ingresar su texto y presionar el botón obtendrá tres vistas horizontales. La primera, le indicará las palabras que se repiten por categoría gramátical; la segunda, un diagrama de arco le indicara las conexiones sintácticas en cada oración; y la tercera, es un grafo en el cual visualizara la configuración de su texto.",
            'analyze_button': "Analizar texto",
            'repeated_words': "Palabras repetidas",
            'legend': "Leyenda: Categorías gramaticales",
            'arc_diagram': "Análisis sintáctico: Diagrama de arco",
            'network_diagram': "Análisis sintáctico: Diagrama de red",
            'sentence': "Oración"
        },
        'en': {
            'title': "AIdeaText - Morphological and Syntactic Analysis",
            'input_label': "Enter a text to analyze (max 5,000 words):",
            'input_placeholder': "The goal of this app is for you to improve your writing skills. To do this, after entering your text and pressing the button you will get three horizontal views. The first will indicate the words that are repeated by grammatical category; second, an arc diagram will indicate the syntactic connections in each sentence; and the third is a graph in which you will visualize the configuration of your text.",
            'analyze_button': "Analyze text",
            'repeated_words': "Repeated words",
            'legend': "Legend: Grammatical categories",
            'arc_diagram': "Syntactic analysis: Arc diagram",
            'network_diagram': "Syntactic analysis: Network diagram",
            'sentence': "Sentence"
        },
        'fr': {
            'title': "AIdeaText - Analyse morphologique et syntaxique",
            'input_label': "Entrez un texte à analyser (max 5 000 mots) :",
            'input_placeholder': "Le but de cette application est d'améliorer vos compétences en rédaction. Pour ce faire, après avoir saisi votre texte et appuyé sur le bouton vous obtiendrez trois vues horizontales. Le premier indiquera les mots répétés par catégorie grammaticale; deuxièmement, un diagramme en arcs indiquera les connexions syntaxiques dans chaque phrase; et le troisième est un graphique dans lequel vous visualiserez la configuration de votre texte.",
            'analyze_button': "Analyser le texte",
            'repeated_words': "Mots répétés",
            'legend': "Légende : Catégories grammaticales",
            'arc_diagram': "Analyse syntaxique : Diagramme en arc",
            'network_diagram': "Analyse syntaxique : Diagramme de réseau",
            'sentence': "Phrase"
        }
    }

    # Use translations
    t = translations[lang_code]

    # Create two columns: one for chat and one for analysis
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"### Chat con AIdeaText")

        # Initialize chat history if it doesn't exist
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []

        # Display chat history
        for i, (role, text) in enumerate(st.session_state.chat_history):
            if role == "user":
                st.text_area(f"Tú:", value=text, height=50, key=f"user_message_{i}", disabled=True)
            else:
                st.text_area(f"AIdeaText:", value=text, height=50, key=f"bot_message_{i}", disabled=True)

        # User input field
        user_input = st.text_input("Escribe tu mensaje aquí:")

        if st.button("Enviar"):
            if user_input:
                # Add user message to history
                st.session_state.chat_history.append(("user", user_input))

                # Get chatbot response
                response = get_chatbot_response(user_input)

                # Add chatbot response to history
                st.session_state.chat_history.append(("bot", response))

                # Clear input field
                st.experimental_rerun()

    with col2:
        st.markdown(f"### {t['title']}")

        if st.session_state.role == "Estudiante":
            # Agregar un botón para ver el progreso del estudiante
            if st.button("Ver mi progreso"):
                student_data = get_student_data(st.session_state.username)
                if student_data:
                    st.success("Datos obtenidos exitosamente")

                    # Mostrar estadísticas generales
                    st.subheader("Estadísticas generales")
                    st.write(f"Total de entradas: {student_data['entries_count']}")

                    # Mostrar gráfico de conteo de palabras
                    st.subheader("Conteo de palabras por categoría")
                    st.bar_chart(student_data['word_count'])

                    # Mostrar entradas recientes
                    st.subheader("Entradas recientes")
                    for entry in student_data['entries'][:5]:  # Mostrar las 5 entradas más recientes
                        st.text_area(f"Entrada del {entry['timestamp']}", entry['text'], height=100)

                    # Aquí puedes agregar más visualizaciones según necesites
                else:
                    st.warning("No se encontraron datos para este estudiante")

        if st.session_state.role == "Estudiante":
            # Student interface code
            if 'input_text' not in st.session_state:
                st.session_state.input_text = ""

            sentence_input = st.text_area(t['input_label'], height=150, placeholder=t['input_placeholder'], value=st.session_state.input_text)
            st.session_state.input_text = sentence_input

            if st.button(t['analyze_button']):
                if sentence_input:
                    doc = nlp_models[lang_code](sentence_input)

                    # Highlighted Repeated Words
                    with st.expander(t['repeated_words'], expanded=True):
                        word_colors = get_repeated_words_colors(doc)
                        highlighted_text = highlight_repeated_words(doc, word_colors)
                        st.markdown(highlighted_text, unsafe_allow_html=True)

                    # Legend for grammatical categories
                    st.markdown(f"##### {t['legend']}")
                    legend_html = "<div style='display: flex; flex-wrap: wrap;'>"
                    for pos, color in POS_COLORS.items():
                        if pos in POS_TRANSLATIONS:
                            legend_html += f"<div style='margin-right: 10px;'><span style='background-color: {color}; padding: 2px 5px;'>{POS_TRANSLATIONS[pos]}</span></div>"
                    legend_html += "</div>"
                    st.markdown(legend_html, unsafe_allow_html=True)

                    # Arc Diagram
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

                    # Network graph
                    with st.expander(t['network_diagram'], expanded=True):
                        fig = visualize_syntax(sentence_input, nlp_models[lang_code], lang_code)
                        st.pyplot(fig)

                    # Store analysis results
                    if store_analysis_result(
                        st.session_state.username,
                        sentence_input,
                        word_colors,
                        arc_diagrams,
                        fig
                    ):
                        st.success("Análisis guardado correctamente.")
                    else:
                        st.error("Hubo un problema al guardar el análisis. Por favor, inténtelo de nuevo.")
                        logger.error(f"Falló el guardado del análisis. Username: {st.session_state.username}")

        elif st.session_state.role == "Profesor":
            # Teacher interface code
            st.write("Bienvenido, profesor. Aquí podrás ver el progreso de tus estudiantes.")
            # Add logic to display student progress

#####################################################################################################
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
            st.experimental_rerun()
        main_app()

if __name__ == "__main__":
    main()