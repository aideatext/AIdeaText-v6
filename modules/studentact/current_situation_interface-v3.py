# modules/studentact/current_situation_interface.py

import streamlit as st
import logging
from ..utils.widget_utils import generate_unique_key
import matplotlib.pyplot as plt
import numpy as np
from ..database.backUp.current_situation_mongo_db import store_current_situation_result

from .current_situation_analysis import (
    analyze_text_dimensions, 
    analyze_clarity,
    analyze_reference_clarity,
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
)

# Configuración del estilo de matplotlib para el gráfico de radar
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.grid'] = True
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False

logger = logging.getLogger(__name__)
####################################

def display_current_situation_interface(lang_code, nlp_models, t):
    """
    Interfaz simplificada con gráfico de radar para visualizar métricas.
    """
    try:
        # Inicializar estados si no existen
        if 'text_input' not in st.session_state:
            st.session_state.text_input = ""
        if 'show_results' not in st.session_state:
            st.session_state.show_results = False
        if 'current_doc' not in st.session_state:
            st.session_state.current_doc = None
        if 'current_metrics' not in st.session_state:
            st.session_state.current_metrics = None

        st.markdown("## Análisis Inicial de Escritura")
        
        # Container principal con dos columnas
        with st.container():
            input_col, results_col = st.columns([1,2])
            
            with input_col:
                #st.markdown("### Ingresa tu texto")
                
                # Función para manejar cambios en el texto
                def on_text_change():
                    st.session_state.text_input = st.session_state.text_area
                    st.session_state.show_results = False
                
                # Text area con manejo de estado
                text_input = st.text_area(
                    t.get('input_prompt', "Escribe o pega tu texto aquí:"),
                    height=400,
                    key="text_area",
                    value=st.session_state.text_input,
                    on_change=on_text_change,
                    help="Este texto será analizado para darte recomendaciones personalizadas"
                )
                
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
                            
                            # Guardar en MongoDB
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
                            st.session_state.text_input = text_input
                            
                    except Exception as e:
                        logger.error(f"Error en análisis: {str(e)}")
                        st.error(t.get('analysis_error', "Error al analizar el texto"))
            
            # Mostrar resultados en la columna derecha
            with results_col:
                if st.session_state.show_results and st.session_state.current_metrics is not None:
                    display_radar_chart(st.session_state.current_metrics)

    except Exception as e:
        logger.error(f"Error en interfaz: {str(e)}")
        st.error("Ocurrió un error. Por favor, intente de nuevo.")

def display_radar_chart(metrics):
    """
    Muestra un gráfico de radar con las métricas del usuario y el patrón ideal.
    """
    try:
        # Container con proporción reducida
        with st.container():
            # Métricas en la parte superior
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Vocabulario", f"{metrics['vocabulary']['normalized_score']:.2f}", "1.00")
            with col2:
                st.metric("Estructura", f"{metrics['structure']['normalized_score']:.2f}", "1.00")
            with col3:
                st.metric("Cohesión", f"{metrics['cohesion']['normalized_score']:.2f}", "1.00")
            with col4:
                st.metric("Claridad", f"{metrics['clarity']['normalized_score']:.2f}", "1.00")

            # Contenedor para el gráfico con ancho controlado
            _, graph_col, _ = st.columns([1,2,1])
            
            with graph_col:
                # Preparar datos
                categories = ['Vocabulario', 'Estructura', 'Cohesión', 'Claridad']
                values_user = [
                    metrics['vocabulary']['normalized_score'],
                    metrics['structure']['normalized_score'],
                    metrics['cohesion']['normalized_score'],
                    metrics['clarity']['normalized_score']
                ]
                values_pattern = [1.0, 1.0, 1.0, 1.0]  # Patrón ideal

                # Crear figura más compacta
                fig = plt.figure(figsize=(6, 6))
                ax = fig.add_subplot(111, projection='polar')

                # Número de variables
                num_vars = len(categories)

                # Calcular ángulos
                angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
                angles += angles[:1]

                # Extender valores para cerrar polígonos
                values_user += values_user[:1]
                values_pattern += values_pattern[:1]

                # Configurar ejes y etiquetas
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(categories, fontsize=8)

                # Círculos concéntricos y etiquetas
                circle_ticks = np.arange(0, 1.1, 0.2)  # Reducido a 5 niveles
                ax.set_yticks(circle_ticks)
                ax.set_yticklabels([f'{tick:.1f}' for tick in circle_ticks], fontsize=8)
                ax.set_ylim(0, 1)

                # Dibujar patrón ideal
                ax.plot(angles, values_pattern, 'g--', linewidth=1, label='Patrón', alpha=0.5)
                ax.fill(angles, values_pattern, 'g', alpha=0.1)

                # Dibujar valores del usuario
                ax.plot(angles, values_user, 'b-', linewidth=2, label='Tu escritura')
                ax.fill(angles, values_user, 'b', alpha=0.2)

                # Leyenda
                ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1), fontsize=8)

                # Ajustes finales
                plt.tight_layout()
                st.pyplot(fig)
                plt.close()

    except Exception as e:
        logger.error(f"Error generando gráfico de radar: {str(e)}")
        st.error("Error al generar la visualización")