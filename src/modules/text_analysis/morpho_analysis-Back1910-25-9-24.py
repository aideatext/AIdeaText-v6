import spacy
from spacy import displacy
from streamlit.components.v1 import html
import base64

from collections import Counter
import re
from ..utils.widget_utils import generate_unique_key

import logging
logger = logging.getLogger(__name__)


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
        'ADP': 'Preposición',
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
        'ADP': 'Preposition',
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
        'ADP': 'Préposition',
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

def generate_arc_diagram(doc):
    arc_diagrams = []
    for sent in doc.sents:
        words = [token.text for token in sent]
        # Calculamos el ancho del SVG basado en la longitud de la oración
        svg_width = max(100, len(words) * 120)
        # Altura fija para cada oración
        svg_height = 300 # Controla la altura del SVG

        # Renderizamos el diagrama de dependencias
        html = displacy.render(sent, style="dep", options={
            "add_lemma":False, # Introduced in version 2.2.4, this argument prints the lemma’s in a separate row below the token texts.
            "arrow_spacing": 12, #This argument is used for adjusting the spacing between arrows in px to avoid overlaps.
            "arrow_width": 2, #This argument is used for adjusting the width of arrow head in px.
            "arrow_stroke": 2, #This argument is used for adjusting the width of arrow path in px.
            "collapse_punct": True, #It attaches punctuation to the tokens.
            "collapse_phrases": False, # This argument merges the noun phrases into one token.
            "compact":False, # If you will take this argument as true, you will get the “Compact mode” with square arrows that takes up less space.
            "color": "#ffffff", 
            "bg": "#0d6efd", 
            "compact": False, #Put the value of this argument True, if you want to use fine-grained part-of-speech tags (Token.tag_), instead of coarse-grained tags (Token.pos_).
            "distance": 100,  # Aumentamos la distancia entre palabras
            "fine_grained": False, #Put the value of this argument True, if you want to use fine-grained part-of-speech tags (Token.tag_), instead of coarse-grained tags (Token.pos_).
            "offset_x": 0, #	This argument is used for spacing on left side of the SVG in px.
            "word_spacing": 25, #This argument is used for adjusting the vertical spacing between words and arcs in px.
        })

        # Ajustamos el tamaño del SVG y el viewBox
        html = re.sub(r'width="(\d+)"', f'width="{svg_width}"', html)
        html = re.sub(r'height="(\d+)"', f'height="{svg_height}"', html)
        html = re.sub(r'<svg', f'<svg viewBox="0 0 {svg_width} {svg_height}"', html)

        #html = re.sub(r'<svg[^>]*>', lambda m: m.group(0).replace('height="450"', 'height="300"'), html)
        #html = re.sub(r'<g [^>]*transform="translate\((\d+),(\d+)\)"', lambda m: f'<g transform="translate({m.group(1)},50)"', html)

        # Movemos todo el contenido hacia abajo
        #html = html.replace('<g', f'<g transform="translate(50, {svg_height - 200})"')

         # Movemos todo el contenido hacia arriba para eliminar el espacio vacío en la parte superior
        html = re.sub(r'<g transform="translate\((\d+),(\d+)\)"', 
                      lambda m: f'<g transform="translate({m.group(1)},10)"', html)


        # Ajustamos la posición de las etiquetas de las palabras
        html = html.replace('dy="1em"', 'dy="-1em"')

        # Ajustamos la posición de las etiquetas POS
        html = html.replace('dy="0.25em"', 'dy="-3em"')

        # Aumentamos el tamaño de la fuente para las etiquetas POS
        html = html.replace('.displacy-tag {', '.displacy-tag { font-size: 14px;')

        # Rotamos las etiquetas de las palabras para mejorar la legibilidad
        #html = html.replace('class="displacy-label"', 'class="displacy-label" transform="rotate(30)"')

        arc_diagrams.append(html)
    return arc_diagrams
##################################################################################################################################
def perform_advanced_morphosyntactic_analysis(text, nlp):
    logger.info(f"Performing advanced morphosyntactic analysis on text: {text[:50]}...")
    try:
        doc = nlp(text)
        arc_diagram = generate_arc_diagram(doc)
        logger.info(f"Arc diagram generated: {arc_diagram is not None}")
        logger.debug(f"Arc diagram content: {arc_diagram[:500] if arc_diagram else 'None'}")

        # Asegurar que arc_diagram sea una lista
        if not isinstance(arc_diagram, list):
            logger.warning("Warning: arc_diagram is not a list. Type: %s", type(arc_diagram))
            arc_diagram = [arc_diagram] if arc_diagram else []

        result = {
            'arc_diagram': arc_diagram,
            'pos_analysis': perform_pos_analysis(doc),
            'morphological_analysis': perform_morphological_analysis(doc),
            'sentence_structure': analyze_sentence_structure(doc),
            'repeated_words': highlight_repeated_words(doc)
        }

        logger.info(f"Analysis result keys: {result.keys()}")
        logger.info(f"Arc diagram in result: {result['arc_diagram'] is not None}")
        return result
    except Exception as e:
        logger.error(f"Error in perform_advanced_morphosyntactic_analysis: {str(e)}", exc_info=True)
        return None
    

###########################################################
def perform_pos_analysis(doc):
    pos_counts = Counter(token.pos_ for token in doc)
    total_tokens = len(doc)
    pos_analysis = []
    for pos, count in pos_counts.items():
        percentage = (count / total_tokens) * 100
        pos_analysis.append({
            'pos': pos,
            'count': count,
            'percentage': round(percentage, 2),
            'examples': [token.text for token in doc if token.pos_ == pos][:5]  # Primeros 5 ejemplos
        })
    return sorted(pos_analysis, key=lambda x: x['count'], reverse=True)

def perform_morphological_analysis(doc):
    return [{
        'text': token.text,
        'lemma': token.lemma_,
        'pos': token.pos_,
        'tag': token.tag_,
        'dep': token.dep_,
        'shape': token.shape_,
        'is_alpha': token.is_alpha,
        'is_stop': token.is_stop,
        'morph': str(token.morph)
    } for token in doc if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']]

def analyze_sentence_structure(doc):
    return [{
        'text': sent.text,
        'root': sent.root.text,
        'root_pos': sent.root.pos_,
        'num_tokens': len(sent),
        'num_words': len([token for token in sent if token.is_alpha]),
        'subjects': [token.text for token in sent if "subj" in token.dep_],
        'objects': [token.text for token in sent if "obj" in token.dep_],
        'verbs': [token.text for token in sent if token.pos_ == "VERB"]
    } for sent in doc.sents]


def get_repeated_words_colors(doc):
    word_counts = Counter(token.text.lower() for token in doc if token.pos_ != 'PUNCT')
    repeated_words = {word: count for word, count in word_counts.items() if count > 1}

    word_colors = {}
    for token in doc:
        if token.text.lower() in repeated_words:
            word_colors[token.text.lower()] = POS_COLORS.get(token.pos_, '#FFFFFF')

    return word_colors

def highlight_repeated_words(doc):
    word_colors = get_repeated_words_colors(doc)
    highlighted_text = []
    for token in doc:
        if token.text.lower() in word_colors:
            color = word_colors[token.text.lower()]
            highlighted_text.append(f'<span style="background-color: {color};">{token.text}</span>')
        else:
            highlighted_text.append(token.text)
    return ' '.join(highlighted_text)


# Exportar todas las funciones y variables necesarias
__all__ = [
    'get_repeated_words_colors',
    'highlight_repeated_words',
    'generate_arc_diagram',
    'perform_pos_analysis',
    'perform_morphological_analysis',
    'analyze_sentence_structure',
    'perform_advanced_morphosyntactic_analysis',
    'POS_COLORS',
    'POS_TRANSLATIONS'
]