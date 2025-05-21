# modules/text_analysis/semantic_analysis.py
# [Mantener todas las importaciones y constantes existentes...]

import streamlit as st
import spacy
import networkx as nx
import matplotlib.pyplot as plt
import io
import base64
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)


# Define colors for grammatical categories
POS_COLORS = {
    'ADJ': '#FFA07A', 'ADP': '#98FB98', 'ADV': '#87CEFA', 'AUX': '#DDA0DD',
    'CCONJ': '#F0E68C', 'DET': '#FFB6C1', 'INTJ': '#FF6347', 'NOUN': '#90EE90',
    'NUM': '#FAFAD2', 'PART': '#D3D3D3', 'PRON': '#FFA500', 'PROPN': '#20B2AA',
    'SCONJ': '#DEB887', 'SYM': '#7B68EE', 'VERB': '#FF69B4', 'X': '#A9A9A9',
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
    }
}

ENTITY_LABELS = {
    'es': {
        "Personas": "lightblue",
        "Lugares": "lightcoral",
        "Inventos": "lightgreen",
        "Fechas": "lightyellow",
        "Conceptos": "lightpink"
    },
    'en': {
        "People": "lightblue",
        "Places": "lightcoral",
        "Inventions": "lightgreen",
        "Dates": "lightyellow",
        "Concepts": "lightpink"
    },
    'fr': {
        "Personnes": "lightblue",
        "Lieux": "lightcoral",
        "Inventions": "lightgreen",
        "Dates": "lightyellow",
        "Concepts": "lightpink"
    }
}

CUSTOM_STOPWORDS = {
    'es': {
        # Artículos
        'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
        # Preposiciones comunes
        'a', 'ante', 'bajo', 'con', 'contra', 'de', 'desde', 'en',
        'entre', 'hacia', 'hasta', 'para', 'por', 'según', 'sin',
        'sobre', 'tras', 'durante', 'mediante',
        # Conjunciones
        'y', 'e', 'ni', 'o', 'u', 'pero', 'sino', 'porque',
        # Pronombres
        'yo', 'tú', 'él', 'ella', 'nosotros', 'vosotros', 'ellos',
        'ellas', 'este', 'esta', 'ese', 'esa', 'aquel', 'aquella',
        # Verbos auxiliares comunes
        'ser', 'estar', 'haber', 'tener',
        # Palabras comunes en textos académicos
        'además', 'también', 'asimismo', 'sin embargo', 'no obstante',
        'por lo tanto', 'entonces', 'así', 'luego', 'pues',
        # Números escritos
        'uno', 'dos', 'tres', 'primer', 'primera', 'segundo', 'segunda',
        # Otras palabras comunes
        'cada', 'todo', 'toda', 'todos', 'todas', 'otro', 'otra',
        'donde', 'cuando', 'como', 'que', 'cual', 'quien',
        'cuyo', 'cuya', 'hay', 'solo', 'ver', 'si', 'no',
        # Símbolos y caracteres especiales
        '#', '@', '/', '*', '+', '-', '=', '$', '%'
    },
    'en': {
        # Articles
        'the', 'a', 'an',
        # Common prepositions
        'in', 'on', 'at', 'by', 'for', 'with', 'about', 'against',
        'between', 'into', 'through', 'during', 'before', 'after',
        'above', 'below', 'to', 'from', 'up', 'down', 'of',
        # Conjunctions
        'and', 'or', 'but', 'nor', 'so', 'for', 'yet',
        # Pronouns
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this',
        'that', 'these', 'those', 'my', 'your', 'his', 'her',
        # Auxiliary verbs
        'be', 'am', 'is', 'are', 'was', 'were', 'been', 'have',
        'has', 'had', 'do', 'does', 'did',
        # Common academic words
        'therefore', 'however', 'thus', 'hence', 'moreover',
        'furthermore', 'nevertheless',
        # Numbers written
        'one', 'two', 'three', 'first', 'second', 'third',
        # Other common words
        'where', 'when', 'how', 'what', 'which', 'who',
        'whom', 'whose', 'there', 'here', 'just', 'only',
        # Symbols and special characters
        '#', '@', '/', '*', '+', '-', '=', '$', '%'
    },
    'fr': {
        # Articles
        'le', 'la', 'les', 'un', 'une', 'des',
        # Prepositions
        'à', 'de', 'dans', 'sur', 'en', 'par', 'pour', 'avec',
        'sans', 'sous', 'entre', 'derrière', 'chez', 'avant',
        # Conjunctions
        'et', 'ou', 'mais', 'donc', 'car', 'ni', 'or',
        # Pronouns
        'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils',
        'elles', 'ce', 'cette', 'ces', 'celui', 'celle',
        # Auxiliary verbs
        'être', 'avoir', 'faire',
        # Academic words
        'donc', 'cependant', 'néanmoins', 'ainsi', 'toutefois',
        'pourtant', 'alors',
        # Numbers
        'un', 'deux', 'trois', 'premier', 'première', 'second',
        # Other common words
        'où', 'quand', 'comment', 'que', 'qui', 'quoi',
        'quel', 'quelle', 'plus', 'moins',
        # Symbols
        '#', '@', '/', '*', '+', '-', '=', '$', '%'
    }
}

##############################################################################################################
def get_stopwords(lang_code):
    """
    Obtiene el conjunto de stopwords para un idioma específico.
    Combina las stopwords de spaCy con las personalizadas.
    """
    try:
        nlp = spacy.load(f'{lang_code}_core_news_sm')
        spacy_stopwords = nlp.Defaults.stop_words
        custom_stopwords = CUSTOM_STOPWORDS.get(lang_code, set())
        return spacy_stopwords.union(custom_stopwords)
    except:
        return CUSTOM_STOPWORDS.get(lang_code, set())


def perform_semantic_analysis(text, nlp, lang_code):
    """
    Realiza el análisis semántico completo del texto.
    Args:
        text: Texto a analizar
        nlp: Modelo de spaCy
        lang_code: Código del idioma
    Returns:
        dict: Resultados del análisis
    """
    
    logger.info(f"Starting semantic analysis for language: {lang_code}")
    try:
        doc = nlp(text)
        key_concepts = identify_key_concepts(doc)
        concept_graph = create_concept_graph(doc, key_concepts)
        concept_graph_fig = visualize_concept_graph(concept_graph, lang_code)
        entities = extract_entities(doc, lang_code)
        entity_graph = create_entity_graph(entities)
        entity_graph_fig = visualize_entity_graph(entity_graph, lang_code)

        # Convertir figuras a bytes
        concept_graph_bytes = fig_to_bytes(concept_graph_fig)
        entity_graph_bytes = fig_to_bytes(entity_graph_fig)

        logger.info("Semantic analysis completed successfully")
        return {
            'key_concepts': key_concepts,
            'concept_graph': concept_graph_bytes,
            'entities': entities,
            'entity_graph': entity_graph_bytes
        }
    except Exception as e:
        logger.error(f"Error in perform_semantic_analysis: {str(e)}")
        raise


def fig_to_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    return buf.getvalue()


def fig_to_html(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode()
    return f'<img src="data:image/png;base64,{img_str}" />'



def identify_key_concepts(doc, min_freq=2, min_length=3):
    """
    Identifica conceptos clave en el texto.
    Args:
        doc: Documento procesado por spaCy
        min_freq: Frecuencia mínima para considerar un concepto
        min_length: Longitud mínima de palabra para considerar
    Returns:
        list: Lista de tuplas (concepto, frecuencia)
    """
    try:
        # Obtener stopwords para el idioma
        stopwords = get_stopwords(doc.lang_)
        
        # Contar frecuencias de palabras
        word_freq = Counter()
        
        for token in doc:
            if (token.lemma_.lower() not in stopwords and
                len(token.lemma_) >= min_length and
                token.is_alpha and
                not token.is_punct and
                not token.like_num):
                
                word_freq[token.lemma_.lower()] += 1
        
        # Filtrar por frecuencia mínima
        concepts = [(word, freq) for word, freq in word_freq.items() 
                   if freq >= min_freq]
        
        # Ordenar por frecuencia
        concepts.sort(key=lambda x: x[1], reverse=True)
        
        return concepts[:10]  # Retornar los 10 conceptos más frecuentes
        
    except Exception as e:
        logger.error(f"Error en identify_key_concepts: {str(e)}")
        return []  # Retornar lista vacía en caso de error


def create_concept_graph(doc, key_concepts):
    """
    Crea un grafo de relaciones entre conceptos.
    Args:
        doc: Documento procesado por spaCy
        key_concepts: Lista de tuplas (concepto, frecuencia)
    Returns:
        nx.Graph: Grafo de conceptos
    """
    try:
        G = nx.Graph()
        
        # Crear un conjunto de conceptos clave para búsqueda rápida
        concept_words = {concept[0].lower() for concept in key_concepts}
        
        # Añadir nodos al grafo
        for concept, freq in key_concepts:
            G.add_node(concept.lower(), weight=freq)
        
        # Analizar cada oración
        for sent in doc.sents:
            # Obtener conceptos en la oración actual
            current_concepts = []
            for token in sent:
                if token.lemma_.lower() in concept_words:
                    current_concepts.append(token.lemma_.lower())
            
            # Crear conexiones entre conceptos en la misma oración
            for i, concept1 in enumerate(current_concepts):
                for concept2 in current_concepts[i+1:]:
                    if concept1 != concept2:
                        # Si ya existe la arista, incrementar el peso
                        if G.has_edge(concept1, concept2):
                            G[concept1][concept2]['weight'] += 1
                        # Si no existe, crear nueva arista con peso 1
                        else:
                            G.add_edge(concept1, concept2, weight=1)
        
        return G
        
    except Exception as e:
        logger.error(f"Error en create_concept_graph: {str(e)}")
        # Retornar un grafo vacío en caso de error
        return nx.Graph()

def visualize_concept_graph(G, lang_code):
    """
    Visualiza el grafo de conceptos.
    Args:
        G: Grafo de networkx
        lang_code: Código del idioma
    Returns:
        matplotlib.figure.Figure: Figura con el grafo visualizado
    """
    try:
        plt.figure(figsize=(12, 8))
        
        # Calcular el layout del grafo
        pos = nx.spring_layout(G)
        
        # Obtener pesos de nodos y aristas
        node_weights = [G.nodes[node].get('weight', 1) * 500 for node in G.nodes()]
        edge_weights = [G[u][v].get('weight', 1) for u, v in G.edges()]
        
        # Dibujar el grafo
        nx.draw_networkx_nodes(G, pos, 
                             node_size=node_weights,
                             node_color='lightblue',
                             alpha=0.6)
        
        nx.draw_networkx_edges(G, pos,
                             width=edge_weights,
                             alpha=0.5,
                             edge_color='gray')
        
        nx.draw_networkx_labels(G, pos,
                              font_size=10,
                              font_weight='bold')
        
        plt.title("Red de conceptos relacionados")
        plt.axis('off')
        
        return plt.gcf()
        
    except Exception as e:
        logger.error(f"Error en visualize_concept_graph: {str(e)}")
        # Retornar una figura vacía en caso de error
        return plt.figure()

def create_entity_graph(entities):
    G = nx.Graph()
    for entity_type, entity_list in entities.items():
        for entity in entity_list:
            G.add_node(entity, type=entity_type)
        for i, entity1 in enumerate(entity_list):
            for entity2 in entity_list[i+1:]:
                G.add_edge(entity1, entity2)
    return G

def visualize_entity_graph(G, lang_code):
    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(G)
    for entity_type, color in ENTITY_LABELS[lang_code].items():
        node_list = [node for node, data in G.nodes(data=True) if data['type'] == entity_type]
        nx.draw_networkx_nodes(G, pos, nodelist=node_list, node_color=color, node_size=500, alpha=0.8, ax=ax)
    nx.draw_networkx_edges(G, pos, width=1, alpha=0.5, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight="bold", ax=ax)
    ax.set_title(f"Relaciones entre Entidades ({lang_code})", fontsize=16)
    ax.axis('off')
    plt.tight_layout()
    return fig


#################################################################################
def create_topic_graph(topics, doc):
    G = nx.Graph()
    for topic in topics:
        G.add_node(topic, weight=doc.text.count(topic))
    for i, topic1 in enumerate(topics):
        for topic2 in topics[i+1:]:
            weight = sum(1 for sent in doc.sents if topic1 in sent.text and topic2 in sent.text)
            if weight > 0:
                G.add_edge(topic1, topic2, weight=weight)
    return G

def visualize_topic_graph(G, lang_code):
    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(G)
    node_sizes = [G.nodes[node]['weight'] * 100 for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='lightgreen', alpha=0.8, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", ax=ax)
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5, ax=ax)
    ax.set_title(f"Relaciones entre Temas ({lang_code})", fontsize=16)
    ax.axis('off')
    plt.tight_layout()
    return fig

###########################################################################################
def generate_summary(doc, lang_code):
    sentences = list(doc.sents)
    summary = sentences[:3]  # Toma las primeras 3 oraciones como resumen
    return " ".join([sent.text for sent in summary])

def extract_entities(doc, lang_code):
    entities = defaultdict(list)
    for ent in doc.ents:
        if ent.label_ in ENTITY_LABELS[lang_code]:
            entities[ent.label_].append(ent.text)
    return dict(entities)

def analyze_sentiment(doc, lang_code):
    positive_words = sum(1 for token in doc if token.sentiment > 0)
    negative_words = sum(1 for token in doc if token.sentiment < 0)
    total_words = len(doc)
    if positive_words > negative_words:
        return "Positivo"
    elif negative_words > positive_words:
        return "Negativo"
    else:
        return "Neutral"

def extract_topics(doc, lang_code):
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5)
    tfidf_matrix = vectorizer.fit_transform([doc.text])
    feature_names = vectorizer.get_feature_names_out()
    return list(feature_names)

# Asegúrate de que todas las funciones necesarias estén exportadas
__all__ = [
    'perform_semantic_analysis',
    'identify_key_concepts',
    'create_concept_graph',
    'visualize_concept_graph',
    'create_entity_graph',
    'visualize_entity_graph',
    'generate_summary',
    'extract_entities',
    'analyze_sentiment',
    'create_topic_graph',
    'visualize_topic_graph',
    'extract_topics',
    'ENTITY_LABELS',
    'POS_COLORS',
    'POS_TRANSLATIONS'
]