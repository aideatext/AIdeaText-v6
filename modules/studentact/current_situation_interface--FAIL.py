# modules/studentact/current_situation_interface.py

import streamlit as st
import logging
from ..utils.widget_utils import generate_unique_key
import matplotlib.pyplot as plt
import numpy as np

from ..database.backUp.current_situation_mongo_db import store_current_situation_result

from ..database.writing_progress_mongo_db import (
    store_writing_baseline,
    store_writing_progress,
    get_writing_baseline,
    get_writing_progress,
    get_latest_writing_metrics
)

from .current_situation_analysis import (
    analyze_text_dimensions, 
    analyze_clarity,
    analyze_vocabulary_diversity, 
    analyze_cohesion,
    analyze_structure,
    get_dependency_depths, 
    normalize_score, 
    generate_sentence_graphs, 
    generate_word_connections, 
    generate_connection_paths,
    create_vocabulary_network, 
    create_syntax_complexity_graph, 
    create_cohesion_heatmap     
)

# Configuración del estilo de matplotlib para el gráfico de radar
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.grid'] = True
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False

logger = logging.getLogger(__name__)
####################################

TEXT_TYPES = {
    'academic_article': {
        'name': 'Artículo Académico',
        'thresholds': {
            'vocabulary': {'min': 0.70, 'target': 0.85},
            'structure': {'min': 0.75, 'target': 0.90},
            'cohesion': {'min': 0.65, 'target': 0.80},
            'clarity': {'min': 0.70, 'target': 0.85}
        }
    },
    'student_essay': {
        'name': 'Trabajo Universitario',
        'thresholds': {
            'vocabulary': {'min': 0.60, 'target': 0.75},
            'structure': {'min': 0.65, 'target': 0.80},
            'cohesion': {'min': 0.55, 'target': 0.70},
            'clarity': {'min': 0.60, 'target': 0.75}
        }
    },
    'general_communication': {
        'name': 'Comunicación General',
        'thresholds': {
            'vocabulary': {'min': 0.50, 'target': 0.65},
            'structure': {'min': 0.55, 'target': 0.70},
            'cohesion': {'min': 0.45, 'target': 0.60},
            'clarity': {'min': 0.50, 'target': 0.65}
        }
    }
}
####################################

ANALYSIS_DIMENSION_MAPPING = {
    'morphosyntactic': {
        'primary': ['vocabulary', 'clarity'],
        'secondary': ['structure'],
        'tools': ['arc_diagrams', 'word_repetition']
    },
    'semantic': {
        'primary': ['cohesion', 'structure'],
        'secondary': ['vocabulary'],
        'tools': ['concept_graphs', 'semantic_networks']
    },
    'discourse': {
        'primary': ['cohesion', 'structure'],
        'secondary': ['clarity'],
        'tools': ['comparative_analysis']
    }
}

##############################################################################
#                           FUNCIÓN PRINCIPAL
##############################################################################
def display_current_situation_interface(lang_code, nlp_models, t):
    """
    TAB:
      - Expander con radio para tipo de texto
    Contenedor-1 con expanders:
       - Expander "Métricas de la línea base"
       - Expander "Métricas de la iteración"
    Contenedor-2 (2 columnas):
       - Col1: Texto base
       - Col2: Texto iteración
    Al final, Recomendaciones en un expander (una sola “fila”).
    """

    # --- Inicializar session_state ---
    if 'base_text' not in st.session_state:
        st.session_state.base_text = ""
    if 'iter_text' not in st.session_state:
        st.session_state.iter_text = ""
    if 'base_metrics' not in st.session_state:
        st.session_state.base_metrics = {}
    if 'iter_metrics' not in st.session_state:
        st.session_state.iter_metrics = {}
    if 'show_base' not in st.session_state:
        st.session_state.show_base = False
    if 'show_iter' not in st.session_state:
        st.session_state.show_iter = False

    # Creamos un tab
    tabs = st.tabs(["Análisis de Texto"])
    with tabs[0]:
        # [1] Expander con radio para seleccionar tipo de texto
        with st.expander("Selecciona el tipo de texto", expanded=True):
            text_type = st.radio(
                "¿Qué tipo de texto quieres analizar?",
                options=list(TEXT_TYPES.keys()),
                format_func=lambda x: TEXT_TYPES[x]['name'],
                index=0
            )
            st.session_state.current_text_type = text_type

        st.markdown("---")

        # ---------------------------------------------------------------------
        # CONTENEDOR-1: Expanders para métricas base e iteración
        # ---------------------------------------------------------------------
        with st.container():
            # --- Expander para la línea base ---
            with st.expander("Métricas de la línea base", expanded=False):
                if st.session_state.show_base and st.session_state.base_metrics:
                    # Mostramos los valores reales
                    display_metrics_in_one_row(st.session_state.base_metrics, text_type)
                else:
                    # Mostramos la maqueta vacía
                    display_empty_metrics_row()

            # --- Expander para la iteración ---
            with st.expander("Métricas de la iteración", expanded=False):
                if st.session_state.show_iter and st.session_state.iter_metrics:
                    display_metrics_in_one_row(st.session_state.iter_metrics, text_type)
                else:
                    display_empty_metrics_row()

        st.markdown("---")

        # ---------------------------------------------------------------------
        # CONTENEDOR-2: 2 columnas (texto base | texto iteración)
        # ---------------------------------------------------------------------
        with st.container():
            col_left, col_right = st.columns(2)

            # Columna izquierda: Texto base
            with col_left:
                st.markdown("**Texto base**")
                text_base = st.text_area(
                    label="",
                    value=st.session_state.base_text,
                    key="text_base_area",
                    placeholder="Pega aquí tu texto base",
                )
                if st.button("Analizar Base"):
                    with st.spinner("Analizando texto base..."):
                        doc = nlp_models[lang_code](text_base)
                        metrics = analyze_text_dimensions(doc)

                        st.session_state.base_text = text_base
                        st.session_state.base_metrics = metrics
                        st.session_state.show_base = True
                        # Al analizar base, reiniciamos la iteración
                        st.session_state.show_iter = False

            # Columna derecha: Texto iteración
            with col_right:
                st.markdown("**Texto de iteración**")
                text_iter = st.text_area(
                    label="",
                    value=st.session_state.iter_text,
                    key="text_iter_area",
                    placeholder="Edita y mejora tu texto...",
                    disabled=not st.session_state.show_base
                )
                if st.button("Analizar Iteración", disabled=not st.session_state.show_base):
                    with st.spinner("Analizando iteración..."):
                        doc = nlp_models[lang_code](text_iter)
                        metrics = analyze_text_dimensions(doc)

                        st.session_state.iter_text = text_iter
                        st.session_state.iter_metrics = metrics
                        st.session_state.show_iter = True

        # ---------------------------------------------------------------------
        # Recomendaciones al final en un expander (una sola “fila”)
        # ---------------------------------------------------------------------
        if st.session_state.show_iter:
            with st.expander("Recomendaciones", expanded=False):
                reco_list = []
                for dimension, values in st.session_state.iter_metrics.items():
                    score = values['normalized_score']
                    target = TEXT_TYPES[text_type]['thresholds'][dimension]['target']
                    if score < target:
                        # Aquí, en lugar de get_dimension_suggestions, unificamos con:
                        suggestions = suggest_improvement_tools_list(dimension)
                        reco_list.extend(suggestions)

                if reco_list:
                    # Todas en una sola línea
                    st.write(" | ".join(reco_list))
                else:
                    st.info("¡No hay recomendaciones! Todas las métricas superan la meta.")







#Funciones de visualización ##################################
############################################################
# Funciones de visualización para las métricas
############################################################

def display_metrics_in_one_row(metrics, text_type):
    """
    Muestra las cuatro dimensiones (Vocabulario, Estructura, Cohesión, Claridad)
    en una sola línea, usando 4 columnas con ancho uniforme.
    """
    thresholds = TEXT_TYPES[text_type]['thresholds']
    dimensions = ["vocabulary", "structure", "cohesion", "clarity"]

    col1, col2, col3, col4 = st.columns([1,1,1,1])
    cols = [col1, col2, col3, col4]

    for dim, col in zip(dimensions, cols):
        score = metrics[dim]['normalized_score']
        target = thresholds[dim]['target']
        min_val = thresholds[dim]['min']

        if score < min_val:
            status = "⚠️ Por mejorar"
            color = "inverse"
        elif score < target:
            status = "📈 Aceptable"
            color = "off"
        else:
            status = "✅ Óptimo"
            color = "normal"

        with col:
            col.metric(
                label=dim.capitalize(),
                value=f"{score:.2f}",
                delta=f"{status} (Meta: {target:.2f})",
                delta_color=color,
                border=True
            )


# -------------------------------------------------------------------------
# Función que muestra una fila de 4 columnas “vacías”
# -------------------------------------------------------------------------
def display_empty_metrics_row():
    """
    Muestra una fila de 4 columnas vacías (Vocabulario, Estructura, Cohesión, Claridad).
    Cada columna se dibuja con st.metric en blanco (“-”).
    """
    empty_cols = st.columns([1,1,1,1])
    labels = ["Vocabulario", "Estructura", "Cohesión", "Claridad"]

    for col, lbl in zip(empty_cols, labels):
        with col:
            col.metric(
                label=lbl,
                value="-",
                delta="",
                border=True
            )



####################################################################

def display_metrics_analysis(metrics, text_type=None):
    """
    Muestra los resultados del análisis: métricas verticalmente y gráfico radar.
    """
    try:
        # Usar valor por defecto si no se especifica tipo
        text_type = text_type or 'student_essay'
        
        # Obtener umbrales según el tipo de texto
        thresholds = TEXT_TYPES[text_type]['thresholds']

        # Crear dos columnas para las métricas y el gráfico
        metrics_col, graph_col = st.columns([1, 1.5])
        
        # Columna de métricas
        with metrics_col:
            metrics_config = [
                {
                    'label': "Vocabulario",
                    'key': 'vocabulary',
                    'value': metrics['vocabulary']['normalized_score'],
                    'help': "Riqueza y variedad del vocabulario",
                    'thresholds': thresholds['vocabulary']
                },
                {
                    'label': "Estructura",
                    'key': 'structure',
                    'value': metrics['structure']['normalized_score'],
                    'help': "Organización y complejidad de oraciones",
                    'thresholds': thresholds['structure']
                },
                {
                    'label': "Cohesión",
                    'key': 'cohesion',
                    'value': metrics['cohesion']['normalized_score'],
                    'help': "Conexión y fluidez entre ideas",
                    'thresholds': thresholds['cohesion']
                },
                {
                    'label': "Claridad",
                    'key': 'clarity',
                    'value': metrics['clarity']['normalized_score'],
                    'help': "Facilidad de comprensión del texto",
                    'thresholds': thresholds['clarity']
                }
            ]

            # Mostrar métricas
            for metric in metrics_config:
                value = metric['value']
                if value < metric['thresholds']['min']:
                    status = "⚠️ Por mejorar"
                    color = "inverse"
                elif value < metric['thresholds']['target']:
                    status = "📈 Aceptable"
                    color = "off"
                else:
                    status = "✅ Óptimo"
                    color = "normal"
                
                st.metric(
                    metric['label'],
                    f"{value:.2f}",
                    f"{status} (Meta: {metric['thresholds']['target']:.2f})",
                    delta_color=color,
                    help=metric['help']
                )
                st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

    except Exception as e:
        logger.error(f"Error mostrando resultados: {str(e)}")
        st.error("Error al mostrar los resultados")

def display_comparison_results(baseline_metrics, current_metrics):
    """Muestra comparación entre línea base y métricas actuales"""
    
    # Crear columnas para métricas y gráfico
    metrics_col, graph_col = st.columns([1, 1.5])
    
    with metrics_col:
        for dimension in ['vocabulary', 'structure', 'cohesion', 'clarity']:
            baseline = baseline_metrics[dimension]['normalized_score']
            current = current_metrics[dimension]['normalized_score']
            delta = current - baseline
            
            st.metric(
                dimension.title(),
                f"{current:.2f}",
                f"{delta:+.2f}",
                delta_color="normal" if delta >= 0 else "inverse"
            )
            
            # Sugerir herramientas de mejora
            if delta < 0:
                suggest_improvement_tools(dimension)
                
    with graph_col:
        display_radar_chart_comparison(
            baseline_metrics,
            current_metrics
        )

def display_metrics_and_suggestions(metrics, text_type, title, show_suggestions=False):
    """
    Muestra métricas y opcionalmente sugerencias de mejora.
    Args:
        metrics: Diccionario con las métricas analizadas
        text_type: Tipo de texto seleccionado
        title: Título para las métricas ("Base" o "Iteración")
        show_suggestions: Booleano para mostrar sugerencias
    """
    try:
        thresholds = TEXT_TYPES[text_type]['thresholds']
        
        st.markdown(f"### Métricas {title}")
        
        for dimension, values in metrics.items():
            score = values['normalized_score']
            target = thresholds[dimension]['target']
            min_val = thresholds[dimension]['min']
            
            # Determinar estado y color
            if score < min_val:
                status = "⚠️ Por mejorar"
                color = "inverse"
            elif score < target:
                status = "📈 Aceptable"
                color = "off"
            else:
                status = "✅ Óptimo"
                color = "normal"
            
            # Mostrar métrica
            st.metric(
                dimension.title(),
                f"{score:.2f}",
                f"{status} (Meta: {target:.2f})",
                delta_color=color,
                help=f"Meta: {target:.2f}, Mínimo: {min_val:.2f}"
            )
            
            # Mostrar sugerencias si es necesario
            if show_suggestions and score < target:
                suggest_improvement_tools(dimension)
            
            # Agregar espacio entre métricas
            st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
            
    except Exception as e:
        logger.error(f"Error mostrando métricas: {str(e)}")
        st.error("Error al mostrar métricas")

def display_radar_chart(metrics_config, thresholds, baseline_metrics=None):
    """
    Muestra el gráfico radar con los resultados.
    Args:
        metrics_config: Configuración actual de métricas
        thresholds: Umbrales para las métricas
        baseline_metrics: Métricas de línea base (opcional)
    """
    try:
        # Preparar datos para el gráfico
        categories = [m['label'] for m in metrics_config]
        values_current = [m['value'] for m in metrics_config]
        min_values = [m['thresholds']['min'] for m in metrics_config]
        target_values = [m['thresholds']['target'] for m in metrics_config]

        # Crear y configurar gráfico
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='polar')

        # Configurar radar
        angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
        angles += angles[:1]
        values_current += values_current[:1]
        min_values += min_values[:1]
        target_values += target_values[:1]

        # Configurar ejes
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        circle_ticks = np.arange(0, 1.1, 0.2)
        ax.set_yticks(circle_ticks)
        ax.set_yticklabels([f'{tick:.1f}' for tick in circle_ticks], fontsize=8)
        ax.set_ylim(0, 1)

        # Dibujar áreas de umbrales
        ax.plot(angles, min_values, '#e74c3c', linestyle='--', linewidth=1, 
                label='Mínimo', alpha=0.5)
        ax.plot(angles, target_values, '#2ecc71', linestyle='--', linewidth=1, 
                label='Meta', alpha=0.5)
        ax.fill_between(angles, target_values, [1]*len(angles), 
                       color='#2ecc71', alpha=0.1)
        ax.fill_between(angles, [0]*len(angles), min_values, 
                       color='#e74c3c', alpha=0.1)

        # Si hay línea base, dibujarla primero
        if baseline_metrics is not None:
            values_baseline = [baseline_metrics[m['key']]['normalized_score'] 
                             for m in metrics_config]
            values_baseline += values_baseline[:1]
            ax.plot(angles, values_baseline, '#888888', linewidth=2, 
                   label='Línea base', linestyle='--')
            ax.fill(angles, values_baseline, '#888888', alpha=0.1)

        # Dibujar valores actuales
        label = 'Actual' if baseline_metrics else 'Tu escritura'
        color = '#3498db' if baseline_metrics else '#3498db'
        
        ax.plot(angles, values_current, color, linewidth=2, label=label)
        ax.fill(angles, values_current, color, alpha=0.2)

        # Ajustar leyenda
        legend_handles = []
        if baseline_metrics:
            legend_handles.extend([
                plt.Line2D([], [], color='#888888', linestyle='--', 
                          label='Línea base'),
                plt.Line2D([], [], color='#3498db', label='Actual')
            ])
        else:
            legend_handles.extend([
                plt.Line2D([], [], color='#3498db', label='Tu escritura')
            ])
        
        legend_handles.extend([
            plt.Line2D([], [], color='#e74c3c', linestyle='--', label='Mínimo'),
            plt.Line2D([], [], color='#2ecc71', linestyle='--', label='Meta')
        ])

        ax.legend(
            handles=legend_handles,
            loc='upper right',
            bbox_to_anchor=(1.3, 1.1),
            fontsize=10,
            frameon=True,
            facecolor='white',
            edgecolor='none',
            shadow=True
        )

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    except Exception as e:
        logger.error(f"Error mostrando gráfico radar: {str(e)}")
        st.error("Error al mostrar el gráfico")

#Funciones auxiliares ##################################


############################################################
# Unificamos la lógica de sugerencias en una función
############################################################
def suggest_improvement_tools_list(dimension):
    """
    Retorna en forma de lista las herramientas sugeridas 
    basadas en 'ANALYSIS_DIMENSION_MAPPING'.
    """
    suggestions = []
    for analysis, mapping in ANALYSIS_DIMENSION_MAPPING.items():
        # Verificamos si la dimensión está en primary o secondary
        if dimension in mapping['primary'] or dimension in mapping['secondary']:
            suggestions.extend(mapping['tools'])
    # Si no hay nada, al menos retornamos un placeholder
    return suggestions if suggestions else ["Sin sugerencias específicas."]

        
def prepare_metrics_config(metrics, text_type='student_essay'):
    """
    Prepara la configuración de métricas en el mismo formato que display_results.
    Args:
        metrics: Diccionario con las métricas analizadas
        text_type: Tipo de texto para los umbrales
    Returns:
        list: Lista de configuraciones de métricas
    """
    # Obtener umbrales según el tipo de texto
    thresholds = TEXT_TYPES[text_type]['thresholds']
    
    # Usar la misma estructura que en display_results
    return [
        {
            'label': "Vocabulario",
            'key': 'vocabulary',
            'value': metrics['vocabulary']['normalized_score'],
            'help': "Riqueza y variedad del vocabulario",
            'thresholds': thresholds['vocabulary']
        },
        {
            'label': "Estructura", 
            'key': 'structure',
            'value': metrics['structure']['normalized_score'],
            'help': "Organización y complejidad de oraciones",
            'thresholds': thresholds['structure']
        },
        {
            'label': "Cohesión",
            'key': 'cohesion', 
            'value': metrics['cohesion']['normalized_score'],
            'help': "Conexión y fluidez entre ideas",
            'thresholds': thresholds['cohesion']
        },
        {
            'label': "Claridad",
            'key': 'clarity',
            'value': metrics['clarity']['normalized_score'],
            'help': "Facilidad de comprensión del texto",
            'thresholds': thresholds['clarity']
        }
    ]        

