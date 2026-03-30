# modules/text_analysis/discourse_analysis.py
# Configuración de matplotlib

import streamlit as st
import spacy
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import logging
import io
import base64
from collections import Counter, defaultdict
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from .semantic_analysis import (
    create_concept_graph,
    visualize_concept_graph,
    identify_key_concepts
)


from .stopwords import (
    get_custom_stopwords,
    process_text,
    get_stopwords_for_spacy
)


#####################
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
    },
    'pt': {
        "Pessoas": "lightblue",
        "Lugares": "lightcoral",
        "Invenções": "lightgreen",
        "Datas": "lightyellow",
        "Conceitos": "lightpink"
    }
}

#################

def fig_to_bytes(fig, dpi=100):
    """Convierte una figura de matplotlib a bytes."""
    try:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')  # Sin compression
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        logger.error(f"Error en fig_to_bytes: {str(e)}")
        return None
        
################################################################################################

def compare_semantic_analysis(text1, text2, nlp, lang):
    """
    Realiza el análisis semántico comparativo sincronizado con semantic_analysis.
    Optimizado para archivos grandes (UNIFE 2026).
    """
    try:
        COMPARE_GRAPH_TITLES = {
            'es': {
                'doc1_network': 'Estructura Semántica: Documento 1',
                'doc2_network': 'Estructura Semántica: Documento 2'
            },
            'en': {
                'doc1_network': 'Semantic Structure: Document 1',
                'doc2_network': 'Semantic Structure: Document 2'
            }
        }
        titles = COMPARE_GRAPH_TITLES.get(lang, COMPARE_GRAPH_TITLES['en'])
        stopwords = get_custom_stopwords(lang)
        
        # 1. Procesamiento de spaCy
        doc1 = nlp(text1)
        doc2 = nlp(text2)
        
        # 2. Identificación de conceptos (Sincronizado y Reforzado)
        # Aumentamos min_freq a 4 para comparativos de archivos pesados (>0.5MB)
        key_concepts1 = identify_key_concepts(doc1, stopwords=stopwords, min_freq=4, min_length=3)
        key_concepts2 = identify_key_concepts(doc2, stopwords=stopwords, min_freq=4, min_length=3)

        if not key_concepts1 or not key_concepts2:
            raise ValueError("Conceptos insuficientes para generar la comparación")

        # 3. Creación de Grafos (CRA)
        G1 = create_concept_graph(doc1, lang_code=lang)
        G2 = create_concept_graph(doc2, lang_code=lang)
        
        # 4. Poda de Grafos (Mantener solo Top Conceptos para legibilidad)
        for G, concepts in [(G1, key_concepts1), (G2, key_concepts2)]:
            nodes_to_keep = [c[0] for c in concepts]
            nodes_to_remove = [n for n in G.nodes if n not in nodes_to_keep]
            G.remove_nodes_from(nodes_to_remove)

        # 5. Visualización Optimizada (Llama a la función con escala Logarítmica Min-Max)
        # Importante: visualize_concept_graph ya tiene el parche de 600 a 4000
        fig1 = visualize_concept_graph(G1, lang)
        fig1.suptitle(titles['doc1_network'], fontsize=14, fontweight='bold')
        
        fig2 = visualize_concept_graph(G2, lang)
        fig2.suptitle(titles['doc2_network'], fontsize=14, fontweight='bold')

        return fig1, fig2, key_concepts1, key_concepts2

    except Exception as e:
        logger.error(f"Error en comparación de discurso: {str(e)}")
        plt.close('all')
        raise

############################################
def create_concept_table(key_concepts):
    """
    Crea una tabla de conceptos clave con sus frecuencias
    Args:
        key_concepts: Lista de tuplas (concepto, frecuencia)
    Returns:
        pandas.DataFrame: Tabla formateada de conceptos
    """
    try:
        if not key_concepts:
            logger.warning("Lista de conceptos vacía")
            return pd.DataFrame(columns=['Concepto', 'Frecuencia'])
            
        df = pd.DataFrame(key_concepts, columns=['Concepto', 'Frecuencia'])
        df['Frecuencia'] = df['Frecuencia'].round(2)
        return df
    except Exception as e:
        logger.error(f"Error en create_concept_table: {str(e)}")
        return pd.DataFrame(columns=['Concepto', 'Frecuencia'])


##########################################################        

def perform_discourse_analysis(text1, text2, nlp, lang):
    """
    Realiza el análisis completo del discurso
    Args:
        text1: Primer texto a analizar
        text2: Segundo texto a analizar
        nlp: Modelo de spaCy cargado
        lang: Código de idioma
    Returns:
        dict: Resultados del análisis con gráficos convertidos a bytes
    """
    try:
        logger.info("Iniciando análisis del discurso...")
        
        # Verificar inputs
        if not text1 or not text2:
            raise ValueError("Los textos de entrada no pueden estar vacíos")
            
        if not nlp:
            raise ValueError("Modelo de lenguaje no inicializado")
        
        # Realizar análisis comparativo
        fig1, fig2, key_concepts1, key_concepts2 = compare_semantic_analysis(
            text1, text2, nlp, lang
        )
        
        logger.info("Análisis comparativo completado, convirtiendo figuras a bytes...")

        # Convertir figuras a bytes para almacenamiento
        graph1_bytes = fig_to_bytes(fig1)
        graph2_bytes = fig_to_bytes(fig2)
        
        logger.info(f"Figura 1 convertida a {len(graph1_bytes) if graph1_bytes else 0} bytes")
        logger.info(f"Figura 2 convertida a {len(graph2_bytes) if graph2_bytes else 0} bytes")

        # Verificar que las conversiones fueron exitosas antes de continuar
        if not graph1_bytes or not graph2_bytes:
            logger.error("Error al convertir figuras a bytes - obteniendo 0 bytes")
            # Opción 1: Devolver error
            raise ValueError("No se pudieron convertir las figuras a bytes")

        # Crear tablas de resultados
        table1 = create_concept_table(key_concepts1)
        table2 = create_concept_table(key_concepts2)

        # Cerrar figuras para liberar memoria
        plt.close(fig1)
        plt.close(fig2)

        result = {
            'graph1': graph1_bytes,  # Bytes en lugar de figura
            'graph2': graph2_bytes,  # Bytes en lugar de figura
            'combined_graph': None,  # No hay gráfico combinado por ahora
            'key_concepts1': key_concepts1,
            'key_concepts2': key_concepts2,
            'table1': table1,
            'table2': table2,
            'success': True
        }
        
        logger.info("Análisis del discurso completado y listo para almacenamiento")
        return result

    except Exception as e:
        logger.error(f"Error en perform_discourse_analysis: {str(e)}")
        # Asegurar limpieza de recursos
        plt.close('all')
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        # Asegurar limpieza en todos los casos
        plt.close('all')

#################################################################