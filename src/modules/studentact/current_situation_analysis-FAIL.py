#v3/modules/studentact/current_situation_analysis.py

import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
from collections import Counter
from itertools import combinations
import numpy as np
import matplotlib.patches as patches
import logging

# 2. Configuración básica del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

# 3. Obtener el logger específico para este módulo
logger = logging.getLogger(__name__)

#########################################################################

def correlate_metrics(scores):
    """
    Ajusta los scores para mantener correlaciones lógicas entre métricas.
    
    Args:
        scores: dict con scores iniciales de vocabulario, estructura, cohesión y claridad
        
    Returns:
        dict con scores ajustados
    """
    try:
        # 1. Correlación estructura-cohesión
        # La cohesión no puede ser menor que estructura * 0.7
        min_cohesion = scores['structure']['normalized_score'] * 0.7
        if scores['cohesion']['normalized_score'] < min_cohesion:
            scores['cohesion']['normalized_score'] = min_cohesion

        # 2. Correlación vocabulario-cohesión
        # La cohesión léxica depende del vocabulario
        vocab_influence = scores['vocabulary']['normalized_score'] * 0.6
        scores['cohesion']['normalized_score'] = max(
            scores['cohesion']['normalized_score'],
            vocab_influence
        )

        # 3. Correlación cohesión-claridad
        # La claridad no puede superar cohesión * 1.2
        max_clarity = scores['cohesion']['normalized_score'] * 1.2
        if scores['clarity']['normalized_score'] > max_clarity:
            scores['clarity']['normalized_score'] = max_clarity

        # 4. Correlación estructura-claridad
        # La claridad no puede superar estructura * 1.1
        struct_max_clarity = scores['structure']['normalized_score'] * 1.1
        scores['clarity']['normalized_score'] = min(
            scores['clarity']['normalized_score'],
            struct_max_clarity
        )

        # Normalizar todos los scores entre 0 y 1
        for metric in scores:
            scores[metric]['normalized_score'] = max(0.0, min(1.0, scores[metric]['normalized_score']))

        return scores

    except Exception as e:
        logger.error(f"Error en correlate_metrics: {str(e)}")
        return scores

##########################################################################

def analyze_text_dimensions(doc):
    """
    Analiza las dimensiones principales del texto manteniendo correlaciones lógicas.
    """
    try:
        # Obtener scores iniciales
        vocab_score, vocab_details = analyze_vocabulary_diversity(doc)
        struct_score = analyze_structure(doc)
        cohesion_score = analyze_cohesion(doc)
        clarity_score, clarity_details = analyze_clarity(doc)

        # Crear diccionario de scores inicial
        scores = {
            'vocabulary': {
                'normalized_score': vocab_score,
                'details': vocab_details
            },
            'structure': {
                'normalized_score': struct_score,
                'details': None
            },
            'cohesion': {
                'normalized_score': cohesion_score,
                'details': None
            },
            'clarity': {
                'normalized_score': clarity_score,
                'details': clarity_details
            }
        }

        # Ajustar correlaciones entre métricas
        adjusted_scores = correlate_metrics(scores)

        # Logging para diagnóstico
        logger.info(f"""
            Scores originales vs ajustados:
            Vocabulario: {vocab_score:.2f} -> {adjusted_scores['vocabulary']['normalized_score']:.2f}
            Estructura: {struct_score:.2f} -> {adjusted_scores['structure']['normalized_score']:.2f}
            Cohesión: {cohesion_score:.2f} -> {adjusted_scores['cohesion']['normalized_score']:.2f}
            Claridad: {clarity_score:.2f} -> {adjusted_scores['clarity']['normalized_score']:.2f}
        """)

        return adjusted_scores

    except Exception as e:
        logger.error(f"Error en analyze_text_dimensions: {str(e)}")
        return {
            'vocabulary': {'normalized_score': 0.0, 'details': {}},
            'structure': {'normalized_score': 0.0, 'details': {}},
            'cohesion': {'normalized_score': 0.0, 'details': {}},
            'clarity': {'normalized_score': 0.0, 'details': {}}
        }



#############################################################################################

def analyze_clarity(doc):
    """
    Analiza la claridad del texto considerando múltiples factores.
    """
    try:
        sentences = list(doc.sents)
        if not sentences:
            return 0.0, {}
            
        # 1. Longitud de oraciones
        sentence_lengths = [len(sent) for sent in sentences]
        avg_length = sum(sentence_lengths) / len(sentences)
        
        # Normalizar usando los umbrales definidos para clarity
        length_score = normalize_score(
            value=avg_length,
            metric_type='clarity',
            optimal_length=20,  # Una oración ideal tiene ~20 palabras
            min_threshold=0.60,  # Consistente con METRIC_THRESHOLDS
            target_threshold=0.75  # Consistente con METRIC_THRESHOLDS
        )
        
        # 2. Análisis de conectores
        connector_count = 0
        connector_weights = {
            'CCONJ': 1.0,  # Coordinantes
            'SCONJ': 1.2,  # Subordinantes
            'ADV': 0.8     # Adverbios conectivos
        }
        
        for token in doc:
            if token.pos_ in connector_weights and token.dep_ in ['cc', 'mark', 'advmod']:
                connector_count += connector_weights[token.pos_]
                
        # Normalizar conectores por oración
        connectors_per_sentence = connector_count / len(sentences) if sentences else 0
        connector_score = normalize_score(
            value=connectors_per_sentence,
            metric_type='clarity',
            optimal_connections=1.5,  # ~1.5 conectores por oración es óptimo
            min_threshold=0.60,
            target_threshold=0.75
        )
        
        # 3. Complejidad estructural
        clause_count = 0
        for sent in sentences:
            verbs = [token for token in sent if token.pos_ == 'VERB']
            clause_count += len(verbs)
            
        complexity_raw = clause_count / len(sentences) if sentences else 0
        complexity_score = normalize_score(
            value=complexity_raw,
            metric_type='clarity',
            optimal_depth=2.0,  # ~2 cláusulas por oración es óptimo
            min_threshold=0.60,
            target_threshold=0.75
        )
        
        # 4. Densidad léxica
        content_words = len([token for token in doc if token.pos_ in ['NOUN', 'VERB', 'ADJ', 'ADV']])
        total_words = len([token for token in doc if token.is_alpha])
        density = content_words / total_words if total_words > 0 else 0
        
        density_score = normalize_score(
            value=density,
            metric_type='clarity',
            optimal_connections=0.6,  # 60% de palabras de contenido es óptimo
            min_threshold=0.60,
            target_threshold=0.75
        )
        
        # Score final ponderado
        weights = {
            'length': 0.3,
            'connectors': 0.3,
            'complexity': 0.2,
            'density': 0.2
        }
        
        clarity_score = (
            weights['length'] * length_score +
            weights['connectors'] * connector_score +
            weights['complexity'] * complexity_score +
            weights['density'] * density_score
        )

        details = {
            'length_score': length_score,
            'connector_score': connector_score,
            'complexity_score': complexity_score,
            'density_score': density_score,
            'avg_sentence_length': avg_length,
            'connectors_per_sentence': connectors_per_sentence,
            'density': density
        }
        
        # Agregar logging para diagnóstico
        logger.info(f"""
            Scores de Claridad:
            - Longitud: {length_score:.2f} (avg={avg_length:.1f} palabras)
            - Conectores: {connector_score:.2f} (avg={connectors_per_sentence:.1f} por oración)
            - Complejidad: {complexity_score:.2f} (avg={complexity_raw:.1f} cláusulas)
            - Densidad: {density_score:.2f} ({density*100:.1f}% palabras de contenido)
            - Score Final: {clarity_score:.2f}
        """)
        
        return clarity_score, details

    except Exception as e:
        logger.error(f"Error en analyze_clarity: {str(e)}")
        return 0.0, {}


def analyze_vocabulary_diversity(doc):
    """Análisis mejorado de la diversidad y calidad del vocabulario"""
    try:
        # 1. Análisis básico de diversidad
        unique_lemmas = {token.lemma_ for token in doc if token.is_alpha}
        total_words = len([token for token in doc if token.is_alpha])
        basic_diversity = len(unique_lemmas) / total_words if total_words > 0 else 0
        
        # 2. Análisis de registro
        academic_words = 0
        narrative_words = 0
        technical_terms = 0
        
        # Clasificar palabras por registro
        for token in doc:
            if token.is_alpha:
                # Detectar términos académicos/técnicos
                if token.pos_ in ['NOUN', 'VERB', 'ADJ']:
                    if any(parent.pos_ == 'NOUN' for parent in token.ancestors):
                        technical_terms += 1
                # Detectar palabras narrativas
                if token.pos_ in ['VERB', 'ADV'] and token.dep_ in ['ROOT', 'advcl']:
                    narrative_words += 1
                    
        # 3. Análisis de complejidad sintáctica
        avg_sentence_length = sum(len(sent) for sent in doc.sents) / len(list(doc.sents))
        
        # 4. Calcular score ponderado
        weights = {
            'diversity': 0.3,
            'technical': 0.3,
            'narrative': 0.2,
            'complexity': 0.2
        }
        
        scores = {
            'diversity': basic_diversity,
            'technical': technical_terms / total_words if total_words > 0 else 0,
            'narrative': narrative_words / total_words if total_words > 0 else 0,
            'complexity': min(1.0, avg_sentence_length / 20)  # Normalizado a 20 palabras
        }
        
        # Score final ponderado
        final_score = sum(weights[key] * scores[key] for key in weights)
        
        # Información adicional para diagnóstico
        details = {
            'text_type': 'narrative' if scores['narrative'] > scores['technical'] else 'academic',
            'scores': scores
        }
        
        return final_score, details
        
    except Exception as e:
        logger.error(f"Error en analyze_vocabulary_diversity: {str(e)}")
        return 0.0, {}

def analyze_cohesion(doc):
    """Analiza la cohesión textual"""
    try:
        sentences = list(doc.sents)
        if len(sentences) < 2:
            logger.warning("Texto demasiado corto para análisis de cohesión")
            return 0.0
            
        # 1. Análisis de conexiones léxicas
        lexical_connections = 0
        total_possible_connections = 0
        
        for i in range(len(sentences)-1):
            # Obtener lemmas significativos (no stopwords)
            sent1_words = {token.lemma_ for token in sentences[i] 
                         if token.is_alpha and not token.is_stop}
            sent2_words = {token.lemma_ for token in sentences[i+1] 
                         if token.is_alpha and not token.is_stop}
            
            if sent1_words and sent2_words:  # Verificar que ambos conjuntos no estén vacíos
                intersection = len(sent1_words.intersection(sent2_words))
                total_possible = min(len(sent1_words), len(sent2_words))
                
                if total_possible > 0:
                    lexical_score = intersection / total_possible
                    lexical_connections += lexical_score
                    total_possible_connections += 1
        
        # 2. Análisis de conectores
        connector_count = 0
        connector_types = {
            'CCONJ': 1.0,  # Coordinantes
            'SCONJ': 1.2,  # Subordinantes
            'ADV': 0.8     # Adverbios conectivos
        }
        
        for token in doc:
            if (token.pos_ in connector_types and 
                token.dep_ in ['cc', 'mark', 'advmod'] and 
                not token.is_stop):
                connector_count += connector_types[token.pos_]
        
        # 3. Cálculo de scores normalizados
        if total_possible_connections > 0:
            lexical_cohesion = lexical_connections / total_possible_connections
        else:
            lexical_cohesion = 0
            
        if len(sentences) > 1:
            connector_cohesion = min(1.0, connector_count / (len(sentences) - 1))
        else:
            connector_cohesion = 0
        
        # 4. Score final ponderado
        weights = {
            'lexical': 0.7,
            'connectors': 0.3
        }
        
        cohesion_score = (
            weights['lexical'] * lexical_cohesion + 
            weights['connectors'] * connector_cohesion
        )
        
        # 5. Logging para diagnóstico
        logger.info(f"""
            Análisis de Cohesión:
            - Conexiones léxicas encontradas: {lexical_connections}
            - Conexiones posibles: {total_possible_connections}
            - Lexical cohesion score: {lexical_cohesion}
            - Conectores encontrados: {connector_count}
            - Connector cohesion score: {connector_cohesion}
            - Score final: {cohesion_score}
        """)
        
        return cohesion_score

    except Exception as e:
        logger.error(f"Error en analyze_cohesion: {str(e)}")
        return 0.0

def analyze_structure(doc):
    try:
        if len(doc) == 0:
            return 0.0
            
        structure_scores = []
        for token in doc:
            if token.dep_ == 'ROOT':
                result = get_dependency_depths(token)
                structure_scores.append(result['final_score'])
                
        if not structure_scores:
            return 0.0
            
        return min(1.0, sum(structure_scores) / len(structure_scores))
        
    except Exception as e:
        logger.error(f"Error en analyze_structure: {str(e)}")
        return 0.0

# Funciones auxiliares de análisis

def get_dependency_depths(token, depth=0, analyzed_tokens=None):
    """
    Analiza la profundidad y calidad de las relaciones de dependencia.
    
    Args:
        token: Token a analizar
        depth: Profundidad actual en el árbol
        analyzed_tokens: Set para evitar ciclos en el análisis
    
    Returns:
        dict: Información detallada sobre las dependencias
            - depths: Lista de profundidades
            - relations: Diccionario con tipos de relaciones encontradas
            - complexity_score: Puntuación de complejidad
    """
    if analyzed_tokens is None:
        analyzed_tokens = set()
        
    # Evitar ciclos
    if token.i in analyzed_tokens:
        return {
            'depths': [],
            'relations': {},
            'complexity_score': 0
        }
    
    analyzed_tokens.add(token.i)
    
    # Pesos para diferentes tipos de dependencias
    dependency_weights = {
        # Dependencias principales
        'nsubj': 1.2,    # Sujeto nominal
        'obj': 1.1,      # Objeto directo
        'iobj': 1.1,     # Objeto indirecto
        'ROOT': 1.3,     # Raíz
        
        # Modificadores
        'amod': 0.8,     # Modificador adjetival
        'advmod': 0.8,   # Modificador adverbial
        'nmod': 0.9,     # Modificador nominal
        
        # Estructuras complejas
        'csubj': 1.4,    # Cláusula como sujeto
        'ccomp': 1.3,    # Complemento clausal
        'xcomp': 1.2,    # Complemento clausal abierto
        'advcl': 1.2,    # Cláusula adverbial
        
        # Coordinación y subordinación
        'conj': 1.1,     # Conjunción
        'cc': 0.7,       # Coordinación
        'mark': 0.8,     # Marcador
        
        # Otros
        'det': 0.5,      # Determinante
        'case': 0.5,     # Caso
        'punct': 0.1     # Puntuación
    }
    
    # Inicializar resultados
    current_result = {
        'depths': [depth],
        'relations': {token.dep_: 1},
        'complexity_score': dependency_weights.get(token.dep_, 0.5) * (depth + 1)
    }
    
    # Analizar hijos recursivamente
    for child in token.children:
        child_result = get_dependency_depths(child, depth + 1, analyzed_tokens)
        
        # Combinar profundidades
        current_result['depths'].extend(child_result['depths'])
        
        # Combinar relaciones
        for rel, count in child_result['relations'].items():
            current_result['relations'][rel] = current_result['relations'].get(rel, 0) + count
            
        # Acumular score de complejidad
        current_result['complexity_score'] += child_result['complexity_score']
        
    # Calcular métricas adicionales
    current_result['max_depth'] = max(current_result['depths'])
    current_result['avg_depth'] = sum(current_result['depths']) / len(current_result['depths'])
    current_result['relation_diversity'] = len(current_result['relations'])
    
    # Calcular score ponderado por tipo de estructura
    structure_bonus = 0
    
    # Bonus por estructuras complejas
    if 'csubj' in current_result['relations'] or 'ccomp' in current_result['relations']:
        structure_bonus += 0.3
    
    # Bonus por coordinación balanceada
    if 'conj' in current_result['relations'] and 'cc' in current_result['relations']:
        structure_bonus += 0.2
    
    # Bonus por modificación rica
    if len(set(['amod', 'advmod', 'nmod']) & set(current_result['relations'])) >= 2:
        structure_bonus += 0.2
        
    current_result['final_score'] = (
        current_result['complexity_score'] * (1 + structure_bonus)
    )
    
    return current_result

def normalize_score(value, metric_type, 
                   min_threshold=0.0, target_threshold=1.0, 
                   range_factor=2.0, optimal_length=None, 
                   optimal_connections=None, optimal_depth=None):
    """
    Normaliza un valor considerando umbrales específicos por tipo de métrica.
    
    Args:
        value: Valor a normalizar
        metric_type: Tipo de métrica ('vocabulary', 'structure', 'cohesion', 'clarity')
        min_threshold: Valor mínimo aceptable
        target_threshold: Valor objetivo
        range_factor: Factor para ajustar el rango
        optimal_length: Longitud óptima (opcional)
        optimal_connections: Número óptimo de conexiones (opcional)
        optimal_depth: Profundidad óptima de estructura (opcional)
    
    Returns:
        float: Valor normalizado entre 0 y 1
    """
    try:
        # Definir umbrales por tipo de métrica
        METRIC_THRESHOLDS = {
            'vocabulary': {
                'min': 0.60,
                'target': 0.75,
                'range_factor': 1.5
            },
            'structure': {
                'min': 0.65,
                'target': 0.80,
                'range_factor': 1.8
            },
            'cohesion': {
                'min': 0.55,
                'target': 0.70,
                'range_factor': 1.6
            },
            'clarity': {
                'min': 0.60,
                'target': 0.75,
                'range_factor': 1.7
            }
        }

        # Validar valores negativos o cero
        if value < 0:
            logger.warning(f"Valor negativo recibido: {value}")
            return 0.0
            
        # Manejar caso donde el valor es cero
        if value == 0:
            logger.warning("Valor cero recibido")
            return 0.0

        # Obtener umbrales específicos para el tipo de métrica
        thresholds = METRIC_THRESHOLDS.get(metric_type, {
            'min': min_threshold,
            'target': target_threshold,
            'range_factor': range_factor
        })
        
        # Identificar el valor de referencia a usar
        if optimal_depth is not None:
            reference = optimal_depth
        elif optimal_connections is not None:
            reference = optimal_connections
        elif optimal_length is not None:
            reference = optimal_length
        else:
            reference = thresholds['target']

        # Validar valor de referencia
        if reference <= 0:
            logger.warning(f"Valor de referencia inválido: {reference}")
            return 0.0

        # Calcular score basado en umbrales
        if value < thresholds['min']:
            # Valor por debajo del mínimo
            score = (value / thresholds['min']) * 0.5  # Máximo 0.5 para valores bajo el mínimo
        elif value < thresholds['target']:
            # Valor entre mínimo y objetivo
            range_size = thresholds['target'] - thresholds['min']
            progress = (value - thresholds['min']) / range_size
            score = 0.5 + (progress * 0.5)  # Escala entre 0.5 y 1.0
        else:
            # Valor alcanza o supera el objetivo
            score = 1.0
            
            # Penalizar valores muy por encima del objetivo
            if value > (thresholds['target'] * thresholds['range_factor']):
                excess = (value - thresholds['target']) / (thresholds['target'] * thresholds['range_factor'])
                score = max(0.7, 1.0 - excess)  # No bajar de 0.7 para valores altos

        # Asegurar que el resultado esté entre 0 y 1
        return max(0.0, min(1.0, score))

    except Exception as e:
        logger.error(f"Error en normalize_score: {str(e)}")
        return 0.0


# Funciones de generación de gráficos
def generate_sentence_graphs(doc):
    """Genera visualizaciones de estructura de oraciones"""
    fig, ax = plt.subplots(figsize=(10, 6))
    # Implementar visualización
    plt.close()
    return fig

def generate_word_connections(doc):
    """Genera red de conexiones de palabras"""
    fig, ax = plt.subplots(figsize=(10, 6))
    # Implementar visualización
    plt.close()
    return fig

def generate_connection_paths(doc):
    """Genera patrones de conexión"""
    fig, ax = plt.subplots(figsize=(10, 6))
    # Implementar visualización
    plt.close()
    return fig

def create_vocabulary_network(doc):
    """
    Genera el grafo de red de vocabulario.
    """
    G = nx.Graph()
    
    # Crear nodos para palabras significativas
    words = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop]
    word_freq = Counter(words)
    
    # Añadir nodos con tamaño basado en frecuencia
    for word, freq in word_freq.items():
        G.add_node(word, size=freq)
    
    # Crear conexiones basadas en co-ocurrencia
    window_size = 5
    for i in range(len(words) - window_size):
        window = words[i:i+window_size]
        for w1, w2 in combinations(set(window), 2):
            if G.has_edge(w1, w2):
                G[w1][w2]['weight'] += 1
            else:
                G.add_edge(w1, w2, weight=1)
    
    # Crear visualización
    fig, ax = plt.subplots(figsize=(12, 8))
    pos = nx.spring_layout(G)
    
    # Dibujar nodos
    nx.draw_networkx_nodes(G, pos, 
                          node_size=[G.nodes[node]['size']*100 for node in G.nodes],
                          node_color='lightblue',
                          alpha=0.7)
    
    # Dibujar conexiones
    nx.draw_networkx_edges(G, pos, 
                          width=[G[u][v]['weight']*0.5 for u,v in G.edges],
                          alpha=0.5)
    
    # Añadir etiquetas
    nx.draw_networkx_labels(G, pos)
    
    plt.title("Red de Vocabulario")
    plt.axis('off')
    return fig

def create_syntax_complexity_graph(doc):
    """
    Genera el diagrama de arco de complejidad sintáctica.
    Muestra la estructura de dependencias con colores basados en la complejidad.
    """
    try:
        # Preparar datos para la visualización
        sentences = list(doc.sents)
        if not sentences:
            return None
            
        # Crear figura para el gráfico
        fig, ax = plt.subplots(figsize=(12, len(sentences) * 2))
        
        # Colores para diferentes niveles de profundidad
        depth_colors = plt.cm.viridis(np.linspace(0, 1, 6))
        
        y_offset = 0
        max_x = 0
        
        for sent in sentences:
            words = [token.text for token in sent]
            x_positions = range(len(words))
            max_x = max(max_x, len(words))
            
            # Dibujar palabras
            plt.plot(x_positions, [y_offset] * len(words), 'k-', alpha=0.2)
            plt.scatter(x_positions, [y_offset] * len(words), alpha=0)
            
            # Añadir texto
            for i, word in enumerate(words):
                plt.annotate(word, (i, y_offset), xytext=(0, -10), 
                           textcoords='offset points', ha='center')
            
            # Dibujar arcos de dependencia
            for token in sent:
                if token.dep_ != "ROOT":
                    # Calcular profundidad de dependencia
                    depth = 0
                    current = token
                    while current.head != current:
                        depth += 1
                        current = current.head
                    
                    # Determinar posiciones para el arco
                    start = token.i - sent[0].i
                    end = token.head.i - sent[0].i
                    
                    # Altura del arco basada en la distancia entre palabras
                    height = 0.5 * abs(end - start)
                    
                    # Color basado en la profundidad
                    color = depth_colors[min(depth, len(depth_colors)-1)]
                    
                    # Crear arco
                    arc = patches.Arc((min(start, end) + abs(end - start)/2, y_offset),
                                    width=abs(end - start),
                                    height=height,
                                    angle=0,
                                    theta1=0,
                                    theta2=180,
                                    color=color,
                                    alpha=0.6)
                    ax.add_patch(arc)
            
            y_offset -= 2
        
        # Configurar el gráfico
        plt.xlim(-1, max_x)
        plt.ylim(y_offset - 1, 1)
        plt.axis('off')
        plt.title("Complejidad Sintáctica")
        
        return fig
        
    except Exception as e:
        logger.error(f"Error en create_syntax_complexity_graph: {str(e)}")
        return None


def create_cohesion_heatmap(doc):
    """Genera un mapa de calor que muestra la cohesión entre párrafos/oraciones."""
    try:
        sentences = list(doc.sents)
        n_sentences = len(sentences)
        
        if n_sentences < 2:
            return None
            
        similarity_matrix = np.zeros((n_sentences, n_sentences))
        
        for i in range(n_sentences):
            for j in range(n_sentences):
                sent1_lemmas = {token.lemma_ for token in sentences[i] 
                              if token.is_alpha and not token.is_stop}
                sent2_lemmas = {token.lemma_ for token in sentences[j] 
                              if token.is_alpha and not token.is_stop}
                
                if sent1_lemmas and sent2_lemmas:
                    intersection = len(sent1_lemmas & sent2_lemmas)  # Corregido aquí
                    union = len(sent1_lemmas | sent2_lemmas)  # Y aquí
                    similarity_matrix[i, j] = intersection / union if union > 0 else 0
        
        # Crear visualización
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sns.heatmap(similarity_matrix,
                   cmap='YlOrRd',
                   square=True,
                   xticklabels=False,
                   yticklabels=False,
                   cbar_kws={'label': 'Cohesión'},
                   ax=ax)
        
        plt.title("Mapa de Cohesión Textual")
        plt.xlabel("Oraciones")
        plt.ylabel("Oraciones")
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        logger.error(f"Error en create_cohesion_heatmap: {str(e)}")
        return None
