##modules/text_analysis/morpho_analysis.py

import spacy
from collections import Counter
from spacy import displacy
import re
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
        'ADJ': 'Adjetivo', 'ADP': 'Preposición', 'ADV': 'Adverbio', 'AUX': 'Auxiliar',
        'CCONJ': 'Conjunción Coordinante', 'DET': 'Determinante', 'INTJ': 'Interjección',
        'NOUN': 'Sustantivo', 'NUM': 'Número', 'PART': 'Partícula', 'PRON': 'Pronombre',
        'PROPN': 'Nombre Propio', 'SCONJ': 'Conjunción Subordinante', 'SYM': 'Símbolo',
        'VERB': 'Verbo', 'X': 'Otro',
    },
    'en': {
        'ADJ': 'Adjective', 'ADP': 'Preposition', 'ADV': 'Adverb', 'AUX': 'Auxiliary',
        'CCONJ': 'Coordinating Conjunction', 'DET': 'Determiner', 'INTJ': 'Interjection',
        'NOUN': 'Noun', 'NUM': 'Number', 'PART': 'Particle', 'PRON': 'Pronoun',
        'PROPN': 'Proper Noun', 'SCONJ': 'Subordinating Conjunction', 'SYM': 'Symbol',
        'VERB': 'Verb', 'X': 'Other',
    },
    'fr': {
        'ADJ': 'Adjectif', 'ADP': 'Préposition', 'ADV': 'Adverbe', 'AUX': 'Auxiliaire',
        'CCONJ': 'Conjonction de Coordination', 'DET': 'Déterminant', 'INTJ': 'Interjection',
        'NOUN': 'Nom', 'NUM': 'Nombre', 'PART': 'Particule', 'PRON': 'Pronom',
        'PROPN': 'Nom Propre', 'SCONJ': 'Conjonction de Subordination', 'SYM': 'Symbole',
        'VERB': 'Verbe', 'X': 'Autre',
    },
    'pt': {
        'ADJ': 'Adjetivo', 'ADP': 'Preposição', 'ADV': 'Advérbio', 'AUX': 'Auxiliar',
        'CCONJ': 'Conjunção Coordenativa', 'DET': 'Determinante', 'INTJ': 'Interjeição',
        'NOUN': 'Substantivo', 'NUM': 'Número', 'PART': 'Partícula', 'PRON': 'Pronome',
        'PROPN': 'Nome Próprio', 'SCONJ': 'Conjunção Subordinativa', 'SYM': 'Símbolo',
        'VERB': 'Verbo', 'X': 'Outro',
    }
}

#############################################################################################
def get_repeated_words_colors(doc):
    word_counts = Counter(token.text.lower() for token in doc if token.pos_ != 'PUNCT')
    repeated_words = {word: count for word, count in word_counts.items() if count > 1}

    word_colors = {}
    for token in doc:
        if token.text.lower() in repeated_words:
            word_colors[token.text.lower()] = POS_COLORS.get(token.pos_, '#FFFFFF')

    return word_colors
    
######################################################################################################
def highlight_repeated_words(doc, word_colors):
    highlighted_text = []
    for token in doc:
        if token.text.lower() in word_colors:
            color = word_colors[token.text.lower()]
            highlighted_text.append(f'<span style="background-color: {color};">{token.text}</span>')
        else:
            highlighted_text.append(token.text)
    return ' '.join(highlighted_text)
    
#################################################################################################

def generate_arc_diagram(doc):
    """
    Genera diagramas de arco para cada oración en el documento usando spacy-streamlit.
    
    Args:
        doc: Documento procesado por spaCy
    Returns:
        list: Lista de diagramas en formato HTML
    """
    arc_diagrams = []
    try:
        options = {
            "compact": False,
            "color": "#ffffff",
            "bg": "#0d6efd",
            "font": "Arial",
            "offset_x": 50,
            "distance": 100,
            "arrow_spacing": 12,
            "arrow_width": 2,
            "arrow_stroke": 2,
            "word_spacing": 25,
            "maxZoom": 2
        }

        for sent in doc.sents:
            try:
                # Usar el método render de displacy directamente con las opciones
                html = displacy.render(sent, style="dep", options=options)
                arc_diagrams.append(html)
            except Exception as e:
                logger.error(f"Error al renderizar oración: {str(e)}")
                continue

        return arc_diagrams
    except Exception as e:
        logger.error(f"Error general en generate_arc_diagram: {str(e)}")
        return None

    
#################################################################################################
def get_detailed_pos_analysis(doc):
    """
    Realiza un análisis detallado de las categorías gramaticales (POS) en el texto.
    """
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

#################################################################################################
def get_morphological_analysis(doc):
    """
    Realiza un análisis morfológico detallado de las palabras en el texto.
    """
    morphology_analysis = []
    for token in doc:
        if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']:  # Enfocarse en categorías principales
            morphology_analysis.append({
                'text': token.text,
                'lemma': token.lemma_,
                'pos': token.pos_,
                'tag': token.tag_,
                'dep': token.dep_,
                'shape': token.shape_,
                'is_alpha': token.is_alpha,
                'is_stop': token.is_stop,
                'morph': str(token.morph)
            })
    return morphology_analysis

#################################################################################################
def get_sentence_structure_analysis(doc):
    """
    Analiza la estructura de las oraciones en el texto.
    """
    sentence_analysis = []
    for sent in doc.sents:
        sentence_analysis.append({
            'text': sent.text,
            'root': sent.root.text,
            'root_pos': sent.root.pos_,
            'num_tokens': len(sent),
            'num_words': len([token for token in sent if token.is_alpha]),
            'subjects': [token.text for token in sent if "subj" in token.dep_],
            'objects': [token.text for token in sent if "obj" in token.dep_],
            'verbs': [token.text for token in sent if token.pos_ == "VERB"]
        })
    return sentence_analysis
    
#################################################################################################
def perform_advanced_morphosyntactic_analysis(text, nlp):
    """
    Realiza un análisis morfosintáctico avanzado del texto.
    """
    try:
        # Verificar el idioma del modelo
        model_lang = nlp.lang
        logger.info(f"Realizando análisis con modelo de idioma: {model_lang}")
        
        # Procesar el texto con el modelo específico del idioma
        doc = nlp(text)
        
        # Realizar análisis específico según el idioma
        return {
            'doc': doc,
            'pos_analysis': get_detailed_pos_analysis(doc),
            'morphological_analysis': get_morphological_analysis(doc),
            'sentence_structure': get_sentence_structure_analysis(doc),
            'arc_diagrams': generate_arc_diagram(doc),  # Quitamos nlp.lang
            'repeated_words': get_repeated_words_colors(doc),
            'highlighted_text': highlight_repeated_words(doc, get_repeated_words_colors(doc))
        }
    except Exception as e:
        logger.error(f"Error en análisis morfosintáctico: {str(e)}")
        return None

# Al final del archivo morph_analysis.py
__all__ = [
    'perform_advanced_morphosyntactic_analysis',
    'get_repeated_words_colors',
    'highlight_repeated_words',
    'generate_arc_diagram',
    'get_detailed_pos_analysis',
    'get_morphological_analysis',
    'get_sentence_structure_analysis',
    'POS_COLORS',
    'POS_TRANSLATIONS'
]
