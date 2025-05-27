#semantic_analysis.py
import streamlit as st
import spacy
import networkx as nx
import matplotlib.pyplot as plt
from collections import Counter
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

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
########################################################################################################################################

# Definimos las etiquetas y colores para cada idioma
ENTITY_LABELS = {
    'es': {
        "Personas": "lightblue",
        "Conceptos": "lightgreen",
        "Lugares": "lightcoral",
        "Fechas": "lightyellow"
    },
    'en': {
        "People": "lightblue",
        "Concepts": "lightgreen",
        "Places": "lightcoral",
        "Dates": "lightyellow"
    },
    'fr': {
        "Personnes": "lightblue",
        "Concepts": "lightgreen",
        "Lieux": "lightcoral",
        "Dates": "lightyellow"
    }
}

#########################################################################################################
def count_pos(doc):
    return Counter(token.pos_ for token in doc if token.pos_ != 'PUNCT')

#####################################################################################################################

def create_semantic_graph(doc, lang):
    G = nx.Graph()
    word_freq = defaultdict(int)
    lemma_to_word = {}
    lemma_to_pos = {}

    # Count frequencies of lemmas and map lemmas to their most common word form and POS
    for token in doc:
        if token.pos_ in ['NOUN', 'VERB']:
            lemma = token.lemma_.lower()
            word_freq[lemma] += 1
            if lemma not in lemma_to_word or token.text.lower() == lemma:
                lemma_to_word[lemma] = token.text
            lemma_to_pos[lemma] = token.pos_

    # Get top 20 most frequent lemmas
    top_lemmas = [lemma for lemma, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]]

    # Add nodes
    for lemma in top_lemmas:
        word = lemma_to_word[lemma]
        G.add_node(word, pos=lemma_to_pos[lemma])

    # Add edges
    for token in doc:
        if token.lemma_.lower() in top_lemmas:
            if token.head.lemma_.lower() in top_lemmas:
                source = lemma_to_word[token.lemma_.lower()]
                target = lemma_to_word[token.head.lemma_.lower()]
                if source != target:  # Avoid self-loops
                    G.add_edge(source, target, label=token.dep_)

    return G, word_freq

############################################################################################################################################

def visualize_semantic_relations(doc, lang):
    G = nx.Graph()
    word_freq = defaultdict(int)
    lemma_to_word = {}
    lemma_to_pos = {}

    # Count frequencies of lemmas and map lemmas to their most common word form and POS
    for token in doc:
        if token.pos_ in ['NOUN', 'VERB']:
            lemma = token.lemma_.lower()
            word_freq[lemma] += 1
            if lemma not in lemma_to_word or token.text.lower() == lemma:
                lemma_to_word[lemma] = token.text
            lemma_to_pos[lemma] = token.pos_

    # Get top 20 most frequent lemmas
    top_lemmas = [lemma for lemma, _ in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]]

    # Add nodes
    for lemma in top_lemmas:
        word = lemma_to_word[lemma]
        G.add_node(word, pos=lemma_to_pos[lemma])

    # Add edges
    for token in doc:
        if token.lemma_.lower() in top_lemmas:
            if token.head.lemma_.lower() in top_lemmas:
                source = lemma_to_word[token.lemma_.lower()]
                target = lemma_to_word[token.head.lemma_.lower()]
                if source != target:  # Avoid self-loops
                    G.add_edge(source, target, label=token.dep_)

    fig, ax = plt.subplots(figsize=(36, 27))
    pos = nx.spring_layout(G, k=0.7, iterations=50)

    node_colors = [POS_COLORS.get(G.nodes[node]['pos'], '#CCCCCC') for node in G.nodes()]

    nx.draw(G, pos, node_color=node_colors, with_labels=True, 
            node_size=10000, 
            font_size=16, 
            font_weight='bold', 
            arrows=True, 
            arrowsize=30, 
            width=3, 
            edge_color='gray',
            ax=ax)

    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=14, ax=ax)

    title = {
        'es': "Relaciones Semánticas Relevantes",
        'en': "Relevant Semantic Relations",
        'fr': "Relations Sémantiques Pertinentes"
    }
    ax.set_title(title[lang], fontsize=24, fontweight='bold')
    ax.axis('off')

    legend_elements = [plt.Rectangle((0,0),1,1,fc=POS_COLORS.get(pos, '#CCCCCC'), edgecolor='none', 
                       label=f"{POS_TRANSLATIONS[lang].get(pos, pos)}")
                       for pos in ['NOUN', 'VERB']]
    ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=16)

    return fig

############################################################################################################################################
def identify_and_contextualize_entities(doc, lang):
    entities = []
    for ent in doc.ents:
        # Obtener el contexto (3 palabras antes y después de la entidad)
        start = max(0, ent.start - 3)
        end = min(len(doc), ent.end + 3)
        context = doc[start:end].text
        
        entities.append({
            'text': ent.text,
            'label': ent.label_,
            'start': ent.start,
            'end': ent.end,
            'context': context
        })
    
    # Identificar conceptos clave (usando sustantivos y verbos más frecuentes)
    word_freq = Counter([token.lemma_.lower() for token in doc if token.pos_ in ['NOUN', 'VERB'] and not token.is_stop])
    key_concepts = word_freq.most_common(10)  # Top 10 conceptos clave
    
    return entities, key_concepts


############################################################################################################################################
def perform_semantic_analysis(text, nlp, lang):
    doc = nlp(text)

    # Identificar entidades y conceptos clave
    entities, key_concepts = identify_and_contextualize_entities(doc, lang)

    # Visualizar relaciones semánticas
    relations_graph = visualize_semantic_relations(doc, lang)
    
    # Imprimir entidades para depuración
    print(f"Entidades encontradas ({lang}):")
    for ent in doc.ents:
        print(f"{ent.text} - {ent.label_}")
    
    relations_graph = visualize_semantic_relations(doc, lang)
    return {
        'entities': entities,
        'key_concepts': key_concepts,
        'relations_graph': relations_graph
    }

__all__ = ['visualize_semantic_relations', 'create_semantic_graph', 'POS_COLORS', 'POS_TRANSLATIONS', 'identify_and_contextualize_entities']    