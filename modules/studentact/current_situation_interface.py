# modules/studentact/current_situation_interface.py

import streamlit as st
import logging
from ..utils.widget_utils import generate_unique_key
import matplotlib.pyplot as plt
import numpy as np
from ..database.backUp.current_situation_mongo_db import store_current_situation_result

# Importaciones locales
from translations import get_translations 

# Importamos la función de recomendaciones personalizadas si existe
try:
    from .claude_recommendations import display_personalized_recommendations
except ImportError:
    # Si no existe el módulo, definimos una función placeholder
    def display_personalized_recommendations(text, metrics, text_type, lang_code, t):
        # Obtener el mensaje de advertencia traducido si está disponible
        warning = t.get('module_not_available', "Módulo de recomendaciones personalizadas no disponible. Por favor, contacte al administrador.")
        st.warning(warning)

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

# Definición de tipos de texto con umbrales
TEXT_TYPES = {
    'academic_article': {
        # Los nombres se obtendrán de las traducciones
        'thresholds': {
            'vocabulary': {'min': 0.70, 'target': 0.85},
            'structure': {'min': 0.75, 'target': 0.90},
            'cohesion': {'min': 0.65, 'target': 0.80},
            'clarity': {'min': 0.70, 'target': 0.85}
        }
    },
    'student_essay': {
        'thresholds': {
            'vocabulary': {'min': 0.60, 'target': 0.75},
            'structure': {'min': 0.65, 'target': 0.80},
            'cohesion': {'min': 0.55, 'target': 0.70},
            'clarity': {'min': 0.60, 'target': 0.75}
        }
    },
    'general_communication': {
        'thresholds': {
            'vocabulary': {'min': 0.50, 'target': 0.65},
            'structure': {'min': 0.55, 'target': 0.70},
            'cohesion': {'min': 0.45, 'target': 0.60},
            'clarity': {'min': 0.50, 'target': 0.65}
        }
    }
}

####################################################
####################################################
def display_current_situation_interface(lang_code, nlp_models, t):
    """
    Interfaz simplificada con gráfico de radar para visualizar métricas.
    """
    # Agregar logs para depuración
    logger.info(f"Idioma: {lang_code}")
    logger.info(f"Claves en t: {list(t.keys())}")
    
    # Inicializar estados si no existen
    if 'text_input' not in st.session_state:
        st.session_state.text_input = ""
    if 'text_area' not in st.session_state:
        st.session_state.text_area = ""
    if 'show_results' not in st.session_state:
        st.session_state.show_results = False
    if 'current_doc' not in st.session_state:
        st.session_state.current_doc = None
    if 'current_metrics' not in st.session_state:
        st.session_state.current_metrics = None
    if 'current_recommendations' not in st.session_state:
        st.session_state.current_recommendations = None
        
    try:
        # Container principal con dos columnas
        with st.container():
            input_col, results_col = st.columns([1,2])

###############################################################################################
            # CSS personalizado para que el formulario ocupe todo el alto disponible
            st.markdown("""
            <style>
                /* Hacer que la columna tenga una altura definida */
                [data-testid="column"] {
                    min-height: 900px;
                    height: 100vh; /* 100% del alto visible de la ventana */
                }
                
                /* Hacer que el formulario ocupe el espacio disponible en la columna */
                .stForm {
                    height: calc(100% - 40px); /* Ajuste por márgenes y paddings */
                    display: flex;
                    flex-direction: column;
                }
                
                /* Hacer que el área de texto se expanda dentro del formulario */
                .stForm .stTextArea {
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }
                
                /* El textarea en sí debe expandirse */
                .stForm .stTextArea textarea {
                    flex: 1;
                    min-height: 750px !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
###############################################################################################
            with input_col:
                with st.form(key=f"text_input_form_{lang_code}"):
                    text_input = st.text_area(
                        t.get('input_prompt', "Escribe o pega tu texto aquí:"),
                        height=800,
                        key=f"text_area_{lang_code}",
                        value=st.session_state.text_input,
                        help=t.get('help', "Este texto será analizado para darte recomendaciones personalizadas")
                    )
                    
                    submit_button = st.form_submit_button(
                        t.get('analyze_button', "Analizar mi escritura"),
                        type="primary",
                        use_container_width=True
                    )
                    
                    if submit_button:
                        if text_input.strip():
                            st.session_state.text_input = text_input

#######################################################################
                # Código para análisis...
                    try:
                        with st.spinner(t.get('processing', "Analizando...")):  # Usando t.get directamente
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
                        st.error(t.get('analysis_error', "Error al analizar el texto"))  # Usando t.get directamente
            
            # Mostrar resultados en la columna derecha
            with results_col:
                if st.session_state.show_results and st.session_state.current_metrics is not None:
                    # Primero los radio buttons para tipo de texto - usando t.get directamente
                    st.markdown(f"### {t.get('text_type_header', 'Tipo de texto')}")
                    
                    # Preparar opciones de tipos de texto con nombres traducidos
                    text_type_options = {}
                    for text_type_key in TEXT_TYPES.keys():
                        # Fallback a nombres genéricos si no hay traducción
                        default_names = {
                            'academic_article': 'Academic Article' if lang_code == 'en' else 'Article Académique' if lang_code == 'fr' else 'Artigo Acadêmico' if lang_code == 'pt' else 'Artículo Académico',
                            'student_essay': 'Student Essay' if lang_code == 'en' else 'Devoir Universitaire' if lang_code == 'fr' else 'Trabalho Universitário' if lang_code == 'pt' else 'Trabajo Universitario',
                            'general_communication': 'General Communication' if lang_code == 'en' else 'Communication Générale' if lang_code == 'fr' else 'Comunicação Geral' if lang_code == 'pt' else 'Comunicación General'
                        }
                        text_type_options[text_type_key] = default_names.get(text_type_key, text_type_key)
                    
                    text_type = st.radio(
                        label=t.get('text_type_header', "Tipo de texto"),  # Usando t.get directamente
                        options=list(TEXT_TYPES.keys()),
                        format_func=lambda x: text_type_options.get(x, x),
                        horizontal=True,
                        key="text_type_radio",
                        label_visibility="collapsed",
                        help=t.get('text_type_help', "Selecciona el tipo de texto para ajustar los criterios de evaluación")  # Usando t.get directamente
                    )
                    
                    st.session_state.current_text_type = text_type
                    
                    # Crear subtabs con nombres traducidos
                    diagnosis_tab = "Diagnosis" if lang_code == 'en' else "Diagnostic" if lang_code == 'fr' else "Diagnóstico" if lang_code == 'pt' else "Diagnóstico"
                    recommendations_tab = "Recommendations" if lang_code == 'en' else "Recommandations" if lang_code == 'fr' else "Recomendações" if lang_code == 'pt' else "Recomendaciones"
                    
                    subtab1, subtab2 = st.tabs([diagnosis_tab, recommendations_tab])
                    
                    # Mostrar resultados en el primer subtab
                    with subtab1:
                        display_diagnosis(
                            metrics=st.session_state.current_metrics,
                            text_type=text_type,
                            lang_code=lang_code,
                            t=t  # Pasar t directamente, no current_situation_t
                        )
                    
                    # Mostrar recomendaciones en el segundo subtab
                    with subtab2:
                        # Llamar directamente a la función de recomendaciones personalizadas
                        display_personalized_recommendations(
                            text=text_input,
                            metrics=st.session_state.current_metrics,
                            text_type=text_type,
                            lang_code=lang_code,
                            t=t
                        )

    except Exception as e:
        logger.error(f"Error en interfaz principal: {str(e)}")
        st.error(t.get('error_interface', "Ocurrió un error al cargar la interfaz"))  # Usando t.get directamente

#################################################################
#################################################################
def display_diagnosis(metrics, text_type=None, lang_code='es', t=None):
    """
    Muestra los resultados del análisis: métricas verticalmente y gráfico radar.
    """
    try:
        # Asegurar que tenemos traducciones
        if t is None:
            t = {}

        # Traducciones para títulos y etiquetas
        dimension_labels = {
            'es': {
                'title': "Tipo de texto",
                'vocabulary': "Vocabulario",
                'structure': "Estructura",
                'cohesion': "Cohesión",
                'clarity': "Claridad",
                'improvement': "⚠️ Por mejorar",
                'acceptable': "📈 Aceptable",
                'optimal': "✅ Óptimo",
                'target': "Meta: {:.2f}"
            },
            'en': {
                'title': "Text Type",
                'vocabulary': "Vocabulary",
                'structure': "Structure",
                'cohesion': "Cohesion",
                'clarity': "Clarity",
                'improvement': "⚠️ Needs improvement",
                'acceptable': "📈 Acceptable", 
                'optimal': "✅ Optimal",
                'target': "Target: {:.2f}"
            },
            'fr': {
                'title': "Type de texte",
                'vocabulary': "Vocabulaire",
                'structure': "Structure",
                'cohesion': "Cohésion",
                'clarity': "Clarté",
                'improvement': "⚠️ À améliorer",
                'acceptable': "📈 Acceptable",
                'optimal': "✅ Optimal",
                'target': "Objectif: {:.2f}"
            },
            'pt': {
                'title': "Tipo de texto",
                'vocabulary': "Vocabulário",
                'structure': "Estrutura",
                'cohesion': "Coesão",
                'clarity': "Clareza",
                'improvement': "⚠️ Precisa melhorar",
                'acceptable': "📈 Aceitável",
                'optimal': "✅ Ótimo",
                'target': "Meta: {:.2f}"
            }
        }
        
        # Obtener traducciones para el idioma actual, con fallback a español
        labels = dimension_labels.get(lang_code, dimension_labels['es'])
        
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
                    'label': labels['vocabulary'],
                    'key': 'vocabulary',
                    'value': metrics['vocabulary']['normalized_score'],
                    'help': t.get('vocabulary_help', "Riqueza y variedad del vocabulario"),
                    'thresholds': thresholds['vocabulary']
                },
                {
                    'label': labels['structure'],
                    'key': 'structure',
                    'value': metrics['structure']['normalized_score'],
                    'help': t.get('structure_help', "Organización y complejidad de oraciones"),
                    'thresholds': thresholds['structure']
                },
                {
                    'label': labels['cohesion'],
                    'key': 'cohesion',
                    'value': metrics['cohesion']['normalized_score'],
                    'help': t.get('cohesion_help', "Conexión y fluidez entre ideas"),
                    'thresholds': thresholds['cohesion']
                },
                {
                    'label': labels['clarity'],
                    'key': 'clarity',
                    'value': metrics['clarity']['normalized_score'],
                    'help': t.get('clarity_help', "Facilidad de comprensión del texto"),
                    'thresholds': thresholds['clarity']
                }
            ]

            # Mostrar métricas con textos traducidos
            for metric in metrics_config:
                value = metric['value']
                if value < metric['thresholds']['min']:
                    status = labels['improvement']
                    color = "inverse"
                elif value < metric['thresholds']['target']:
                    status = labels['acceptable']
                    color = "off"
                else:
                    status = labels['optimal']
                    color = "normal"
                
                target_text = labels['target'].format(metric['thresholds']['target'])
                
                st.metric(
                    metric['label'],
                    f"{value:.2f}",
                    f"{status} ({target_text})",
                    delta_color=color,
                    help=metric['help']
                )
                st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

        # Gráfico radar en la columna derecha
        with graph_col:
            display_radar_chart(metrics_config, thresholds, lang_code)  # Pasar el parámetro lang_code

    except Exception as e:
        logger.error(f"Error mostrando resultados: {str(e)}")
        st.error(t.get('error_results', "Error al mostrar los resultados"))

##################################################################
##################################################################
def display_radar_chart(metrics_config, thresholds, lang_code='es'):
    """
    Muestra el gráfico radar con los resultados.
    """
    try:
        # Traducción de las etiquetas de leyenda según el idioma
        legend_translations = {
            'es': {'min': 'Mínimo', 'target': 'Meta', 'user': 'Tu escritura'},
            'en': {'min': 'Minimum', 'target': 'Target', 'user': 'Your writing'},
            'fr': {'min': 'Minimum', 'target': 'Objectif', 'user': 'Votre écriture'},
            'pt': {'min': 'Mínimo', 'target': 'Meta', 'user': 'Sua escrita'}
        }
        
        # Usar español por defecto si el idioma no está soportado
        translations = legend_translations.get(lang_code, legend_translations['es'])
        
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

        # Dibujar áreas de umbrales con etiquetas traducidas
        ax.plot(angles, min_values, '#e74c3c', linestyle='--', linewidth=1, label=translations['min'], alpha=0.5)
        ax.plot(angles, target_values, '#2ecc71', linestyle='--', linewidth=1, label=translations['target'], alpha=0.5)
        ax.fill_between(angles, target_values, [1]*len(angles), color='#2ecc71', alpha=0.1)
        ax.fill_between(angles, [0]*len(angles), min_values, color='#e74c3c', alpha=0.1)

        # Dibujar valores del usuario con etiqueta traducida
        ax.plot(angles, values_user, '#3498db', linewidth=2, label=translations['user'])
        ax.fill(angles, values_user, '#3498db', alpha=0.2)

        # Ajustar leyenda
        ax.legend(
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