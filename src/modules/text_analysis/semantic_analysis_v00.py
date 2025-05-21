#semantic_analysis.py
import streamlit as st
import spacy
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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

def identify_and_contextualize_entities(doc, lang):
    entities = []
    for ent in doc.ents:
        # Obtener el contexto (3 palabras antes y después de la entidad)
        start = max(0, ent.start - 3)
        end = min(len(doc), ent.end + 3)
        context = doc[start:end].text
        
        # Mapear las etiquetas de spaCy a nuestras categorías
        if ent.label_ in ['PERSON', 'ORG']:
            category = "Personas" if lang == 'es' else "People" if lang == 'en' else "Personnes"
        elif ent.label_ in ['LOC', 'GPE']:
            category = "Lugares" if lang == 'es' else "Places" if lang == 'en' else "Lieux"
        elif ent.label_ in ['PRODUCT']:
            category = "Inventos" if lang == 'es' else "Inventions" if lang == 'en' else "Inventions"
        elif ent.label_ in ['DATE', 'TIME']:
            category = "Fechas" if lang == 'es' else "Dates" if lang == 'en' else "Dates"
        else:
            category = "Conceptos" if lang == 'es' else "Concepts" if lang == 'en' else "Concepts"
        
        entities.append({
            'text': ent.text,
            'label': category,
            'start': ent.start,
            'end': ent.end,
            'context': context
        })
    
    # Identificar conceptos clave (usando sustantivos y verbos más frecuentes)
    word_freq = Counter([token.lemma_.lower() for token in doc if token.pos_ in ['NOUN', 'VERB'] and not token.is_stop])
    key_concepts = word_freq.most_common(10)  # Top 10 conceptos clave
    
    return entities, key_concepts

def create_concept_graph(text, concepts):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([text])
    concept_vectors = vectorizer.transform(concepts)
    similarity_matrix = cosine_similarity(concept_vectors, concept_vectors)

    G = nx.Graph()
    for i, concept in enumerate(concepts):
        G.add_node(concept)
        for j in range(i+1, len(concepts)):
            if similarity_matrix[i][j] > 0.1:
                G.add_edge(concept, concepts[j], weight=similarity_matrix[i][j])

    return G

def visualize_concept_graph(G, lang):
    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(G)
    
    nx.draw_networkx_nodes(G, pos, node_size=3000, node_color='lightblue', ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold", ax=ax)
    nx.draw_networkx_edges(G, pos, width=1, ax=ax)
    
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8, ax=ax)

    title = {
        'es': "Relaciones Conceptuales",
        'en': "Conceptual Relations",
        'fr': "Relations Conceptuelles"
    }
    ax.set_title(title[lang], fontsize=16)
    ax.axis('off')

    return fig

def perform_semantic_analysis(text, nlp, lang):
    doc = nlp(text)

    # Identificar entidades y conceptos clave
    entities, key_concepts = identify_and_contextualize_entities(doc, lang)

    # Crear y visualizar grafo de conceptos
    concepts = [concept for concept, _ in key_concepts]
    concept_graph = create_concept_graph(text, concepts)
    relations_graph = visualize_concept_graph(concept_graph, lang)
    
    return {
        'entities': entities,
        'key_concepts': key_concepts,
        'relations_graph': relations_graph
    }

__all__ = ['perform_semantic_analysis', 'ENTITY_LABELS', 'POS_TRANSLATIONS']