# modules/studentact/current_situation_interface-vOK.py

import streamlit as st
import logging
from ..utils.widget_utils import generate_unique_key
import matplotlib.pyplot as plt
import numpy as np
from ..database.backUp.current_situation_mongo_db import store_current_situation_result

# Importaciones locales
from translations import get_translations 

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
    create_cohesion_heatmap,
    generate_recommendations
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

def display_current_situation_interface(lang_code, nlp_models, t):
    """
    Interfaz simplificada con gráfico de radar para visualizar métricas.
    """
    # Inicializar estados si no existen
    if 'text_input' not in st.session_state:
        st.session_state.text_input = ""
    if 'text_area' not in st.session_state:  # Añadir inicialización de text_area
        st.session_state.text_area = ""
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    if 'current_doc' not in st.session_state:
        st.session_state.current_doc = None
    if 'current_metrics' not in st.session_state:
        st.session_state.current_metrics = None
        
    try:
        # Container principal con dos columnas
        with st.container():
            input_col, results_col = st.columns([1,2])
            
            with input_col:
                # Text area con manejo de estado
                text_input = st.text_area(
                    t.get('input_prompt', "Escribe o pega tu texto aquí:"),
                    height=400,
                    key="text_area",
                    value=st.session_state.text_input,
                    help="Este texto será analizado para darte recomendaciones personalizadas"
                )
                
                # Función para manejar cambios de texto
                if text_input != st.session_state.text_input:
                    st.session_state.text_input = text_input
                    st.session_state.show_results = False
                
                if st.button(
                    t.get('analyze_button', "Analizar mi escritura"),
                    type="primary",
                    disabled=not text_input.strip(),
                    use_container_width=True,
                ):
                    try:
                        with st.spinner(t.get('processing', "Analizando...")):
                            doc = nlp_models[lang_code](text_input)
                            metrics = analyze_text_dimensions(doc)
                            
                            storage_success = store_current_situation_result(
                                username=st.session_state.username,
                                text=text_input,
                                metrics=metrics,
                                feedback=None
                            )
                            
                            if not storage_success:
                                logger.warning("No se pudo guardar el análisis en la base de datos")
                            
                            st.session_state.current_doc = doc
                            st.session_state.current_metrics = metrics
                            st.session_state.show_results = True
                            
                    except Exception as e:
                        logger.error(f"Error en análisis: {str(e)}")
                        st.error(t.get('analysis_error', "Error al analizar el texto"))
            
            # Mostrar resultados en la columna derecha
            with results_col:
                if st.session_state.show_results and st.session_state.current_metrics is not None:
                    # Primero los radio buttons para tipo de texto
                    st.markdown("### Tipo de texto")
                    text_type = st.radio(
                        "",
                        options=list(TEXT_TYPES.keys()),
                        format_func=lambda x: TEXT_TYPES[x]['name'],
                        horizontal=True,
                        key="text_type_radio",
                        help="Selecciona el tipo de texto para ajustar los criterios de evaluación"
                    )
                    
                    st.session_state.current_text_type = text_type
                    
                    # Luego mostrar los resultados
                    display_results(
                        metrics=st.session_state.current_metrics,
                        text_type=text_type
                    )

    except Exception as e:
        logger.error(f"Error en interfaz principal: {str(e)}")
        st.error("Ocurrió un error al cargar la interfaz")

###################################3333

'''
def display_results(metrics, text_type=None):
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

        # Gráfico radar en la columna derecha
        with graph_col:
            display_radar_chart(metrics_config, thresholds)

    except Exception as e:
        logger.error(f"Error mostrando resultados: {str(e)}")
        st.error("Error al mostrar los resultados")
'''

######################################
######################################
def display_results(metrics, text_type=None):
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

        # Gráfico radar en la columna derecha
        with graph_col:
            display_radar_chart(metrics_config, thresholds)

        recommendations = generate_recommendations(
            metrics=metrics,
            text_type=text_type,
            lang_code=st.session_state.lang_code
        )
        
        # Separador visual
        st.markdown("---")
        
        # Título para la sección de recomendaciones
        st.subheader("Recomendaciones para mejorar tu escritura")
        
        # Mostrar las recomendaciones
        display_recommendations(recommendations, get_translations(st.session_state.lang_code))

    except Exception as e:
        logger.error(f"Error mostrando resultados: {str(e)}")
        st.error("Error al mostrar los resultados")


######################################
######################################
def display_radar_chart(metrics_config, thresholds):
    """
    Muestra el gráfico radar con los resultados.
    """
    try:
        # Preparar datos para el gráfico
        categories = [m['label'] for m in metrics_config]
        values_user = [m['value'] for m in metrics_config]
        min_values = [m['thresholds']['min'] for m in metrics_config]
        target_values = [m['thresholds']['target'] for m in metrics_config]

        # Crear y configurar gráfico
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='polar')

        # Configurar radar
        angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
        angles += angles[:1]
        values_user += values_user[:1]
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
        ax.plot(angles, min_values, '#e74c3c', linestyle='--', linewidth=1, label='Mínimo', alpha=0.5)
        ax.plot(angles, target_values, '#2ecc71', linestyle='--', linewidth=1, label='Meta', alpha=0.5)
        ax.fill_between(angles, target_values, [1]*len(angles), color='#2ecc71', alpha=0.1)
        ax.fill_between(angles, [0]*len(angles), min_values, color='#e74c3c', alpha=0.1)

        # Dibujar valores del usuario
        ax.plot(angles, values_user, '#3498db', linewidth=2, label='Tu escritura')
        ax.fill(angles, values_user, '#3498db', alpha=0.2)

        # Ajustar leyenda
        ax.legend(
            loc='upper right',
            bbox_to_anchor=(1.3, 1.1),  # Cambiado de (0.1, 0.1) a (1.3, 1.1)
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

#####################################################
def display_recommendations(recommendations, t):
    """
    Muestra las recomendaciones con un diseño de tarjetas.
    """
    # Definir colores para cada categoría
    colors = {
        'vocabulary': '#2E86C1',  # Azul
        'structure': '#28B463',   # Verde
        'cohesion': '#F39C12',    # Naranja
        'clarity': '#9B59B6',     # Púrpura
        'priority': '#E74C3C'     # Rojo para la categoría prioritaria
    }
    
    # Iconos para cada categoría
    icons = {
        'vocabulary': '📚',
        'structure': '🏗️',
        'cohesion': '🔄',
        'clarity': '💡',
        'priority': '⭐'
    }
    
    # Obtener traducciones para cada dimensión
    dimension_names = {
        'vocabulary': t.get('SITUATION_ANALYSIS', {}).get('vocabulary', "Vocabulario"),
        'structure': t.get('SITUATION_ANALYSIS', {}).get('structure', "Estructura"),
        'cohesion': t.get('SITUATION_ANALYSIS', {}).get('cohesion', "Cohesión"),
        'clarity': t.get('SITUATION_ANALYSIS', {}).get('clarity', "Claridad"),
        'priority': t.get('SITUATION_ANALYSIS', {}).get('priority', "Prioridad")
    }
    
    # Título de la sección prioritaria
    priority_focus = t.get('SITUATION_ANALYSIS', {}).get('priority_focus', 'Área prioritaria para mejorar')
    st.markdown(f"### {icons['priority']} {priority_focus}")
    
    # Determinar área prioritaria (la que tiene menor puntuación)
    priority_area = recommendations.get('priority', 'vocabulary')
    priority_title = dimension_names.get(priority_area, "Área prioritaria")
    
    # Determinar el contenido para mostrar
    if isinstance(recommendations[priority_area], dict) and 'title' in recommendations[priority_area]:
        priority_title = recommendations[priority_area]['title']
        priority_content = recommendations[priority_area]['content']
    else:
        priority_content = recommendations[priority_area]
    
    # Mostrar la recomendación prioritaria con un estilo destacado
    with st.container():
        st.markdown(
            f"""
            <div style="border:2px solid {colors['priority']}; border-radius:5px; padding:15px; margin-bottom:20px;">
                <h4 style="color:{colors['priority']};">{priority_title}</h4>
                <p>{priority_content}</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Crear dos columnas para las tarjetas de recomendaciones restantes
    col1, col2 = st.columns(2)
    
    # Distribuir las recomendaciones en las columnas
    categories = ['vocabulary', 'structure', 'cohesion', 'clarity']
    for i, category in enumerate(categories):
        # Saltar si esta categoría ya es la prioritaria
        if category == priority_area:
            continue
            
        # Determinar título y contenido
        if isinstance(recommendations[category], dict) and 'title' in recommendations[category]:
            category_title = recommendations[category]['title']
            category_content = recommendations[category]['content']
        else:
            category_title = dimension_names.get(category, category)
            category_content = recommendations[category]
        
        # Alternar entre columnas
        with col1 if i % 2 == 0 else col2:
            # Crear tarjeta para cada recomendación
            st.markdown(
                f"""
                <div style="border:1px solid {colors[category]}; border-radius:5px; padding:10px; margin-bottom:15px;">
                    <h4 style="color:{colors[category]};">{icons[category]} {category_title}</h4>
                    <p>{category_content}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )