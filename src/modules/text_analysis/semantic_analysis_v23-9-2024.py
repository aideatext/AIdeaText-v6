#semantic_analysis.py
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

##############################################################################################################
def perform_semantic_analysis(text, nlp, lang_code):
    logger.info(f"Starting semantic analysis for language: {lang_code}")
    try:
        doc = nlp(text)

        # Conceptos clave y grafo de conceptos
        key_concepts = identify_key_concepts(doc)
        concept_graph = create_concept_graph(doc, key_concepts)
        concept_graph_fig = visualize_concept_graph(concept_graph, lang_code)
        #concept_graph_html = fig_to_html(concept_graph_fig)

        # Entidades y grafo de entidades
        entities = extract_entities(doc, lang_code)
        entity_graph = create_entity_graph(entities)
        entity_graph_fig = visualize_entity_graph(entity_graph, lang_code)
        #entity_graph_html = fig_to_html(entity_graph_fig)

        logger.info("Semantic analysis completed successfully")
        return {
            'doc': doc,
            'key_concepts': key_concepts,
            'concept_graph': concept_graph_fig,
            'entities': entities,
            'entity_graph': entity_graph_fig
        }
    except Exception as e:
        logger.error(f"Error in perform_semantic_analysis: {str(e)}")
        raise

'''
def fig_to_html(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    img_str = base64.b64encode(buf.getvalue()).decode()
    return f'<img src="data:image/png;base64,{img_str}" />'
'''


def identify_key_concepts(doc):
    logger.info("Identifying key concepts")
    word_freq = Counter([token.lemma_.lower() for token in doc if token.pos_ in ['NOUN', 'VERB'] and not token.is_stop])
    key_concepts = word_freq.most_common(10)
    return [(concept, float(freq)) for concept, freq in key_concepts]


def create_concept_graph(doc, key_concepts):
    G = nx.Graph()
    for concept, freq in key_concepts:
        G.add_node(concept, weight=freq)
    for sent in doc.sents:
        sent_concepts = [token.lemma_.lower() for token in sent if token.lemma_.lower() in dict(key_concepts)]
        for i, concept1 in enumerate(sent_concepts):
            for concept2 in sent_concepts[i+1:]:
                if G.has_edge(concept1, concept2):
                    G[concept1][concept2]['weight'] += 1
                else:
                    G.add_edge(concept1, concept2, weight=1)
    return G

def visualize_concept_graph(G, lang_code):
    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    node_sizes = [G.nodes[node]['weight'] * 100 for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color='lightblue', alpha=0.8, ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", ax=ax)
    edge_weights = [G[u][v]['weight'] for u, v in G.edges()]
    nx.draw_networkx_edges(G, pos, width=edge_weights, alpha=0.5, ax=ax)
    title = {
        'es': "Relaciones entre Conceptos Clave",
        'en': "Key Concept Relations",
        'fr': "Relations entre Concepts Clés"
    }
    ax.set_title(title[lang_code], fontsize=16)
    ax.axis('off')
    plt.tight_layout()
    return fig

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