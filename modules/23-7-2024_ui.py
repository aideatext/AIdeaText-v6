# modules/ui.py
# Importaciones estandar de python
import io
import streamlit as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import squarify
import pandas as pd
from datetime import datetime
import base64
from spacy import displacy
import re
from .morpho_analysis import POS_COLORS, POS_TRANSLATIONS  # Asegúrate de que esta importación esté presente
print("POS_COLORS:", POS_COLORS)
print("POS_TRANSLATIONS:", POS_TRANSLATIONS)

# Importaciones locales
from .auth import authenticate_user, register_user, get_user_role
from .database import get_student_data, store_analysis_result
from .morpho_analysis import get_repeated_words_colors, highlight_repeated_words, POS_COLORS, POS_TRANSLATIONS
from .syntax_analysis import visualize_syntax

#########################################################################
# Define colors for grammatical categories
POS_COLORS = {
    'ADJ': '#FFA07A',    # Light Salmon
    'ADP': '#98FB98',    # Pale Green
    'ADV': '#87CEFA',    # Light Sky Blue
    'AUX': '#DDA0DD',    # Plum
    'CCONJ': '#F0E68C',  # Khaki
    'DET': '#FFB6C1',    # Light Pink
    'INTJ': '#FF6347',   # Tomato
    'NOUN': '#90EE90',   # Light Green
    'NUM': '#FAFAD2',    # Light Goldenrod Yellow
    'PART': '#D3D3D3',   # Light Gray
    'PRON': '#FFA500',   # Orange
    'PROPN': '#20B2AA',  # Light Sea Green
    'SCONJ': '#DEB887',  # Burlywood
    'SYM': '#7B68EE',    # Medium Slate Blue
    'VERB': '#FF69B4',   # Hot Pink
    'X': '#A9A9A9',      # Dark Gray
}

POS_TRANSLATIONS = {
    'es': {
        'ADJ': 'Adjetivo',
        'ADP': 'Adposición',
        'ADV': 'Adverbio',
        'AUX': 'Auxiliar',
        'CCONJ': 'Conjunción Coordinante',
        'DET': 'Determinante',
        'INTJ': 'Interjección',
        'NOUN': 'Sustantivo',
        'NUM': 'Número',
        'PART': 'Partícula',
        'PRON': 'Pronombre',
        'PROPN': 'Nombre Propio',
        'SCONJ': 'Conjunción Subordinante',
        'SYM': 'Símbolo',
        'VERB': 'Verbo',
        'X': 'Otro',
    },
    'en': {
        'ADJ': 'Adjective',
        'ADP': 'Adposition',
        'ADV': 'Adverb',
        'AUX': 'Auxiliary',
        'CCONJ': 'Coordinating Conjunction',
        'DET': 'Determiner',
        'INTJ': 'Interjection',
        'NOUN': 'Noun',
        'NUM': 'Number',
        'PART': 'Particle',
        'PRON': 'Pronoun',
        'PROPN': 'Proper Noun',
        'SCONJ': 'Subordinating Conjunction',
        'SYM': 'Symbol',
        'VERB': 'Verb',
        'X': 'Other',
    },
    'fr': {
        'ADJ': 'Adjectif',
        'ADP': 'Adposition',
        'ADV': 'Adverbe',
        'AUX': 'Auxiliaire',
        'CCONJ': 'Conjonction de Coordination',
        'DET': 'Déterminant',
        'INTJ': 'Interjection',
        'NOUN': 'Nom',
        'NUM': 'Nombre',
        'PART': 'Particule',
        'PRON': 'Pronom',
        'PROPN': 'Nom Propre',
        'SCONJ': 'Conjonction de Subordination',
        'SYM': 'Symbole',
        'VERB': 'Verbe',
        'X': 'Autre',
    }
}

##########################################################################
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

##########################################################################
def register_page():
    st.title("Registrarse")
    new_username = st.text_input("Nuevo Usuario")
    new_password = st.text_input("Nueva Contraseña", type='password')
    
    additional_info = {}
    additional_info['carrera'] = st.text_input("Carrera")

    if st.button("Registrarse"):
        if register_user(new_username, new_password, additional_info):
            st.success("Registro exitoso. Por favor, inicia sesión.")
        else:
            st.error("El usuario ya existe o ocurrió un error durante el registro")

##########################################################################
def get_chatbot_response(input_text):
    # Esta función debe ser implementada o importada de otro módulo
    # Por ahora, retornamos un mensaje genérico
    return "Lo siento, el chatbot no está disponible en este momento."

##########################################################################
def display_chat_interface():
    st.markdown("### Chat con AIdeaText")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    for i, (role, text) in enumerate(st.session_state.chat_history):
        if role == "user":
            st.text_area(f"Tú:", value=text, height=50, key=f"user_message_{i}", disabled=True)
        else:
            st.text_area(f"AIdeaText:", value=text, height=50, key=f"bot_message_{i}", disabled=True)

    user_input = st.text_input("Escribe tu mensaje aquí:")

    if st.button("Enviar"):
        if user_input:
            st.session_state.chat_history.append(("user", user_input))
            response = get_chatbot_response(user_input)
            st.session_state.chat_history.append(("bot", response))
            st.experimental_rerun()

##########################################################################

def display_student_progress(username, lang_code='es'):
    print("lang_code:", lang_code)
    student_data = get_student_data(username)
    
    if student_data is None:
        st.warning("No se encontraron datos para este estudiante.")
        st.info("Intenta realizar algunos análisis de texto primero.")
        return

    st.title(f"Progreso de {username}")

    if student_data['entries_count'] > 0:
        if 'word_count' in student_data and student_data['word_count']:
            st.subheader("Total de palabras por categoría gramatical")
            
            df = pd.DataFrame(list(student_data['word_count'].items()), columns=['category', 'count'])
            df['label'] = df.apply(lambda x: f"{POS_TRANSLATIONS[lang_code].get(x['category'], x['category'])}", axis=1)
            
            # Ordenar el DataFrame por conteo de palabras, de mayor a menor
            df = df.sort_values('count', ascending=False)
            
            fig, ax = plt.subplots(figsize=(12, 6))
            bars = ax.bar(df['label'], df['count'], color=[POS_COLORS.get(cat, '#CCCCCC') for cat in df['category']])
            
            ax.set_xlabel('Categoría Gramatical')
            ax.set_ylabel('Cantidad de Palabras')
            ax.set_title('Total de palabras por categoría gramatical')
            plt.xticks(rotation=45, ha='right')
            
            # Añadir etiquetas de valor en las barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height}',
                        ha='center', va='bottom')
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            st.image(buf, use_column_width=True)
        else:
            st.info("No hay datos de conteo de palabras disponibles.")    
        
        # Diagramas de Arco (consolidados)
        st.header("Diagramas de Arco")
        with st.expander("Ver todos los Diagramas de Arco"):
            for i, entry in enumerate(student_data['entries']):
                if 'arc_diagrams' in entry and entry['arc_diagrams']:
                    st.subheader(f"Entrada {i+1} - {entry['timestamp']}")
                    st.write(entry['arc_diagrams'][0], unsafe_allow_html=True)
        
        # Diagramas de Red (consolidados)
        st.header("Diagramas de Red")
        with st.expander("Ver todos los Diagramas de Red"):
            for i, entry in enumerate(student_data['entries']):
                if 'network_diagram' in entry and entry['network_diagram']:
                    st.subheader(f"Entrada {i+1} - {entry['timestamp']}")
                    try:
                        # Decodificar la imagen base64
                        image_bytes = base64.b64decode(entry['network_diagram'])
                        st.image(image_bytes)
                    except Exception as e:
                        st.error(f"Error al mostrar el diagrama de red: {str(e)}")
    else:
        st.warning("No se encontraron entradas para este estudiante.")
        st.info("Intenta realizar algunos análisis de texto primero.")

##############################################################Mostrar entradas recientes######################################################################
        #st.header("Entradas Recientes")
        #for i, entry in enumerate(student_data['entries'][:5]):  # Mostrar las 5 entradas más recientes
            #with st.expander(f"Entrada {i+1} - {entry['timestamp']}"):
                #st.write(entry['text'])
    #else:
        #st.warning("No se encontraron entradas para este estudiante.")
        #st.info("Intenta realizar algunos análisis de texto primero.")
    
##########################################################################
def display_text_analysis_interface(nlp_models, lang_code):
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

    t = translations[lang_code]

    if 'input_text' not in st.session_state:
        st.session_state.input_text = ""

    # Añadimos una clave única basada en el idioma seleccionado
    sentence_input = st.text_area(
        t['input_label'],
        height=150,
        placeholder=t['input_placeholder'],
        value=st.session_state.input_text,
        key=f"text_input_{lang_code}"  # Clave única basada en el idioma
    )
    st.session_state.input_text = sentence_input

#    sentence_input = st.text_area(t['input_label'], height=150, placeholder=t['input_placeholder'], value=st.session_state.input_text)
#    st.session_state.input_text = sentence_input

    if st.button(t['analyze_button'], key=f"analyze_button_{lang_code}"):
        if sentence_input:
            doc = nlp_models[lang_code](sentence_input)

            with st.expander(t['repeated_words'], expanded=True):
                word_colors = get_repeated_words_colors(doc)
                highlighted_text = highlight_repeated_words(doc, word_colors)
                st.markdown(highlighted_text, unsafe_allow_html=True)

            st.markdown(f"##### {t['legend']}")
            legend_html = "<div style='display: flex; flex-wrap: wrap;'>"
            for pos, color in POS_COLORS.items():
                if pos in POS_TRANSLATIONS:
                    legend_html += f"<div style='margin-right: 10px;'><span style='background-color: {color}; padding: 2px 5px;'>{POS_TRANSLATIONS[pos]}</span></div>"
            legend_html += "</div>"
            st.markdown(legend_html, unsafe_allow_html=True)

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

            with st.expander(t['network_diagram'], expanded=True):
                fig = visualize_syntax(sentence_input, nlp_models[lang_code], lang_code)
                st.pyplot(fig)

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
                st.error(f"Falló el guardado del análisis. Username: {st.session_state.username}")

##########################################################################
def display_teacher_interface():
    st.write("Bienvenido, profesor. Aquí podrás ver el progreso de tus estudiantes.")
    # Aquí puedes agregar la lógica para mostrar el progreso de los estudiantes