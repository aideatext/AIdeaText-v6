# modules/text_analysis/semantic_analysis.py
#Prueba_mundial

# 1. Importaciones estándar del sistema
import logging
import io
import base64
from collections import Counter, defaultdict

# 2. Importaciones de terceros
import numpy as np
import streamlit as st
import spacy
import networkx as nx
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 3. Solo configurar si no hay handlers ya configurados
logger = logging.getLogger(__name__)

# 4. Importaciones locales
from .stopwords import (
    process_text,
    clean_text,
    get_custom_stopwords,
    get_stopwords_for_spacy
)

try:
    from modules.metrics.m1_m2 import calculate_M2, graph_to_dict
    _METRICS_AVAILABLE = True
except ImportError:
    _METRICS_AVAILABLE = False
    logger.warning("modules.metrics.m1_m2 no disponible en semantic_analysis.")

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

###########################################################
def fig_to_bytes(fig):
    """Convierte una figura de matplotlib a bytes."""
    try:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Error en fig_to_bytes: {str(e)}")
        return None
        
###########################################################
def perform_semantic_analysis(text: str, nlp, lang_code: str) -> dict:
    """
    Analizador Adaptativo Piloto UNIFE 2026.
    Ajusta la densidad del grafo según la extensión del documento.
    """
    if not text or not nlp or not lang_code:
        return {"success": False, "error": "Parámetros inválidos"}

    try:
        # 1. ESCALA DE EXTENSIÓN (Estrategia sugerida por Manuel)
        word_count = len(text.split())
        
        if word_count < 1000:
            # Nivel 1: Inicial (Resumen/Avance)
            max_nodes = 40
            min_edge_weight = 1
            node_scale = 600  # Nodos grandes y detallados
        elif word_count <= 3000:
            # Nivel 2: Consolidación (Paper)
            max_nodes = 30
            min_edge_weight = 2
            node_scale = 400
        elif word_count <= 5000:
            # Nivel 3: Extenso (Capítulo)
            max_nodes = 25
            min_edge_weight = 3
            node_scale = 250
        else:
            # Nivel 4: Macro (Tesis completa > 5000 palabras)
            max_nodes = 20
            min_edge_weight = 4
            node_scale = 150  # Nodos pequeños para evitar colapso

        logger.info(f"Nivel de análisis detectado: {word_count} palabras. Max nodos: {max_nodes}")

        # 2. Procesamiento y Extracción de Conceptos
        doc = nlp(text)
        stopwords = get_custom_stopwords(lang_code)
        
        # Limitamos los conceptos según la escala para mantener legibilidad
        key_concepts = identify_key_concepts(doc, stopwords=stopwords)[:max_nodes]

        if not key_concepts:
            return {"success": False, "error": "No se identificaron conceptos clave"}

        # 3. Generación y Poda del Grafo (CRA)
        concept_graph_nx = create_concept_graph(doc, lang_code=lang_code)
        
        # Poda de Nodos: Solo dejamos los Top N
        nodes_to_keep = [c[0] for c in key_concepts]
        nodes_to_remove = [n for n in concept_graph_nx.nodes if n not in nodes_to_keep]
        concept_graph_nx.remove_nodes_from(nodes_to_remove)

        # Poda de Aristas: Eliminamos conexiones débiles según la escala
        weak_edges = [(u, v) for u, v, d in concept_graph_nx.edges(data=True) if d.get('weight', 1) < min_edge_weight]
        concept_graph_nx.remove_edges_from(weak_edges)

        # 4. Métricas y Serialización
        if _METRICS_AVAILABLE:
            m2_metrics = calculate_M2(concept_graph_nx)
            gdict = graph_to_dict(concept_graph_nx)
        else:
            m2_metrics, gdict = {}, {}

        # 5. Visualización con ESCALA LOGARÍTMICA
        plt.clf()
        # Pasamos node_scale a la función de dibujo
        fig = visualize_concept_graph(concept_graph_nx, lang_code, node_scale=node_scale)
        graph_bytes = fig_to_bytes(fig)
        plt.close(fig)

        # 6. Retorno (Estructura fija para conexión con Sidebar/Tutor)
        return {
            "success": True,
            "text": text,
            "key_concepts": key_concepts,
            "concept_graph": graph_bytes,
            "concept_graph_nx": concept_graph_nx,
            "graph_dict": gdict,
            "metrics": {
                "key_concepts": key_concepts,
                "M2": m2_metrics,
                "word_count": word_count
            }
        }

    except Exception as e:
        logger.error(f"Error en perform_semantic_analysis: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

############################################################ 

def identify_key_concepts(doc, stopwords, min_freq=2, min_length=3):
    """
    Identifica conceptos clave en el texto, excluyendo entidades nombradas.
    Args:
        doc: Documento procesado por spaCy
        stopwords: Lista de stopwords
        min_freq: Frecuencia mínima para considerar un concepto
        min_length: Longitud mínima del concepto
    Returns:
        List[Tuple[str, int]]: Lista de tuplas (concepto, frecuencia)
    """
    try:
        word_freq = Counter()
        
        # Crear conjunto de tokens que son parte de entidades
        entity_tokens = set()
        for ent in doc.ents:
            entity_tokens.update(token.i for token in ent)
        
        # Procesar tokens
        for token in doc:
            # Verificar si el token no es parte de una entidad nombrada
            if (token.i not in entity_tokens and  # No es parte de una entidad
                token.lemma_.lower() not in stopwords and  # No es stopword
                len(token.lemma_) >= min_length and  # Longitud mínima
                token.is_alpha and  # Es alfabético
                not token.is_punct and  # No es puntuación
                not token.like_num and  # No es número
                not token.is_space and  # No es espacio
                not token.is_stop and  # No es stopword de spaCy
                not token.pos_ == 'PROPN' and  # No es nombre propio
                not token.pos_ == 'SYM' and  # No es símbolo
                not token.pos_ == 'NUM' and  # No es número
                not token.pos_ == 'X'):  # No es otro
                
                # Convertir a minúsculas y añadir al contador
                word_freq[token.lemma_.lower()] += 1
        
        # Filtrar conceptos por frecuencia mínima y ordenar por frecuencia
        concepts = [(word, freq) for word, freq in word_freq.items() 
                   if freq >= min_freq]
        concepts.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Identified {len(concepts)} key concepts after excluding entities")
        return concepts[:10]
        
    except Exception as e:
        logger.error(f"Error en identify_key_concepts: {str(e)}")
        return []

########################################################################

def create_concept_graph(doc, lang_code='es'):
    """
    Crea un grafo de red semántica basado en la co-ocurrencia de conceptos.
    Ajuste UNIFE 2026: Filtra estrictamente SUSTANTIVOS (NOUN/PROPN) para CRA.
    """
    try:
        G = nx.Graph()
        
        # 1. Extraer solo Sustantivos y Nombres Propios (Filtrado POS)
        allowed_pos = ['NOUN', 'PROPN']
        
        # Obtenemos la lista de conceptos limpios
        concepts = [
            token.lemma_.lower() 
            for token in doc 
            if token.pos_ in allowed_pos 
            and not token.is_stop 
            and len(token.text) > 2 
        ]

        if not concepts:
            return G

        # 2. Contar frecuencia para el tamaño de los nodos
        counts = Counter(concepts)
        for concept, count in counts.items():
            G.add_node(concept, weight=count)

        # 3. Crear aristas por co-ocurrencia (ventana de contexto)
        window_size = 5
        for i in range(len(concepts)):
            for j in range(i + 1, min(i + window_size, len(concepts))):
                u, v = concepts[i], concepts[j]
                if u != v:
                    if G.has_edge(u, v):
                        G[u][v]['weight'] += 1
                    else:
                        G.add_edge(u, v, weight=1)

        # El return exitoso debe ir dentro del bloque try
        return G

    except Exception as e:
        # Ahora el except sí tiene un try al cual referirse
        logger.error(f"Error en create_concept_graph: {str(e)}")
        # Devolvemos un grafo vacío para que la app no se rompa
        return nx.Graph()
    
###############################################################################

def visualize_concept_graph(G, lang_code, node_scale=None):
    import numpy as np
    import networkx as nx
    import matplotlib.pyplot as plt

    GRAPH_LABELS = {
        'es': {'concept_network': 'Relaciones entre conceptos clave', 'concept_centrality': 'Centralidad'},
        'en': {'concept_network': 'Key Concept Relationships', 'concept_centrality': 'Centrality'}
    }
    translations = GRAPH_LABELS.get(lang_code, GRAPH_LABELS['en'])
    
    fig, ax = plt.subplots(figsize=(15, 10))
    DG = nx.DiGraph(G)
    centrality = nx.degree_centrality(G)
    pos = nx.spring_layout(DG, k=2.5, iterations=50, seed=42)
    
    # Lógica Min-Max para evitar "bolas de pelos" en 0.9MB
    weights = [DG.nodes[n].get('weight', 1) for n in DG.nodes()]
    max_w, min_w = max(weights) if weights else 1, min(weights) if weights else 1
    
    # Normalización Logarítmica
    node_sizes = []
    for w in weights:
        norm = (np.log1p(w) - np.log1p(min_w)) / (np.log1p(max_w) - np.log1p(min_w) + 1e-9)
        node_sizes.append(600 + norm * 3400) # Rango entre 600 y 4000
    
    node_colors = [plt.cm.viridis(centrality[node]) for node in DG.nodes()]
    
    nx.draw_networkx_nodes(DG, pos, node_size=node_sizes, node_color=node_colors, alpha=0.8, ax=ax)
    nx.draw_networkx_edges(DG, pos, width=1.5, alpha=0.3, edge_color='gray', arrows=True, ax=ax)
    nx.draw_networkx_labels(DG, pos, font_size=10, font_weight='bold', ax=ax)
    
    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=0, vmax=1))
    plt.colorbar(sm, ax=ax, label=translations['concept_centrality'])
    plt.title(translations['concept_network'])
    ax.set_axis_off()
    return fig

########################################################################
def create_entity_graph(entities):
    G = nx.Graph()
    for entity_type, entity_list in entities.items():
        for entity in entity_list:
            G.add_node(entity, type=entity_type)
        for i, entity1 in enumerate(entity_list):
            for entity2 in entity_list[i+1:]:
                G.add_edge(entity1, entity2)
    return G


#############################################################
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
    'fig_to_bytes',  # Faltaba esta coma
    'ENTITY_LABELS',
    'POS_COLORS',
    'POS_TRANSLATIONS'
]