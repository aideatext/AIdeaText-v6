# modules/studentact/current_situation_interface.py

import streamlit as st
import logging
from ..utils.widget_utils import generate_unique_key

from ..database.current_situation_mongo_db import store_current_situation_result

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

logger = logging.getLogger(__name__)
####################################

def display_current_situation_interface(lang_code, nlp_models, t):
    """
    Interfaz simplificada para el análisis inicial, enfocada en recomendaciones directas.
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
                st.markdown("### Ingresa tu texto")
                
                # Función para manejar cambios en el texto
                def on_text_change():
                    st.session_state.text_input = st.session_state.text_area
                    st.session_state.show_results = False  # Resetear resultados cuando el texto cambia
                
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
                            # Procesar texto y obtener métricas
                            doc = nlp_models[lang_code](text_input)
                            metrics = analyze_text_dimensions(doc)
                            
                            # Guardar en MongoDB
                            storage_success = store_current_situation_result(
                                username=st.session_state.username,
                                text=text_input,
                                metrics=metrics,
                                feedback=None  # Por ahora sin feedback
                            )
                            
                            if not storage_success:
                                logger.warning("No se pudo guardar el análisis en la base de datos")
                            
                            # Actualizar estado
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
                    display_recommendations(st.session_state.current_metrics, t)
                    
                    # Opción para ver detalles
                    with st.expander("🔍 Ver análisis detallado", expanded=False):
                        display_current_situation_visual(
                            st.session_state.current_doc,
                            st.session_state.current_metrics
                        )
                        
    except Exception as e:
        logger.error(f"Error en interfaz: {str(e)}")
        st.error("Ocurrió un error. Por favor, intente de nuevo.")



def display_current_situation_visual(doc, metrics):
    """
    Muestra visualizaciones detalladas del análisis.
    """
    try:
        st.markdown("### 📊 Visualizaciones Detalladas")
        
        # 1. Visualización de vocabulario
        with st.expander("Análisis de Vocabulario", expanded=True):
            vocab_graph = create_vocabulary_network(doc)
            if vocab_graph:
                st.pyplot(vocab_graph)
                plt.close(vocab_graph)
        
        # 2. Visualización de estructura
        with st.expander("Análisis de Estructura", expanded=True):
            syntax_graph = create_syntax_complexity_graph(doc)
            if syntax_graph:
                st.pyplot(syntax_graph)
                plt.close(syntax_graph)
        
        # 3. Visualización de cohesión
        with st.expander("Análisis de Cohesión", expanded=True):
            cohesion_graph = create_cohesion_heatmap(doc)
            if cohesion_graph:
                st.pyplot(cohesion_graph)
                plt.close(cohesion_graph)

    except Exception as e:
        logger.error(f"Error en visualización: {str(e)}")
        st.error("Error al generar las visualizaciones")


####################################
def display_recommendations(metrics, t):
    """
    Muestra recomendaciones basadas en las métricas del texto.
    """
    # 1. Resumen Visual con Explicación
    st.markdown("### 📊 Resumen de tu Análisis")
    
    # Explicación del sistema de medición
    st.markdown("""
        **¿Cómo interpretar los resultados?**
        
        Cada métrica se mide en una escala de 0.0 a 1.0, donde:
        - 0.0 - 0.4: Necesita atención prioritaria
        - 0.4 - 0.6: En desarrollo
        - 0.6 - 0.8: Buen nivel
        - 0.8 - 1.0: Nivel avanzado
    """)

    # Métricas con explicaciones detalladas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Vocabulario",
            f"{metrics['vocabulary']['normalized_score']:.2f}",
            help="Mide la variedad y riqueza de tu vocabulario. Un valor alto indica un uso diverso de palabras sin repeticiones excesivas."
        )
        with st.expander("ℹ️ Detalles"):
            st.write("""
                **Vocabulario**
                - Evalúa la diversidad léxica
                - Considera palabras únicas vs. totales
                - Detecta repeticiones innecesarias
                - Valor óptimo: > 0.7
            """)
    
    with col2:
        st.metric(
            "Estructura",
            f"{metrics['structure']['normalized_score']:.2f}",
            help="Evalúa la complejidad y variedad de las estructuras sintácticas en tus oraciones."
        )
        with st.expander("ℹ️ Detalles"):
            st.write("""
                **Estructura**
                - Analiza la complejidad sintáctica
                - Mide variación en construcciones
                - Evalúa longitud de oraciones
                - Valor óptimo: > 0.6
            """)
    
    with col3:
        st.metric(
            "Cohesión",
            f"{metrics['cohesion']['normalized_score']:.2f}",
            help="Indica qué tan bien conectadas están tus ideas y párrafos entre sí."
        )
        with st.expander("ℹ️ Detalles"):
            st.write("""
                **Cohesión**
                - Mide conexiones entre ideas
                - Evalúa uso de conectores
                - Analiza progresión temática
                - Valor óptimo: > 0.65
            """)
    
    with col4:
        st.metric(
            "Claridad",
            f"{metrics['clarity']['normalized_score']:.2f}",
            help="Evalúa la facilidad de comprensión general de tu texto."
        )
        with st.expander("ℹ️ Detalles"):
            st.write("""
                **Claridad**
                - Evalúa comprensibilidad
                - Considera estructura lógica
                - Mide precisión expresiva
                - Valor óptimo: > 0.7
            """)

    st.markdown("---")

    # 2. Recomendaciones basadas en puntuaciones
    st.markdown("### 💡 Recomendaciones Personalizadas")
    
    # Recomendaciones morfosintácticas
    if metrics['structure']['normalized_score'] < 0.6:
        st.warning("""
        #### 📝 Análisis Morfosintáctico Recomendado
        
        **Tu nivel actual sugiere que sería beneficioso:**
        1. Realizar el análisis morfosintáctico de 3 párrafos diferentes
        2. Practicar la combinación de oraciones simples en compuestas
        3. Identificar y clasificar tipos de oraciones en textos académicos
        4. Ejercitar la variación sintáctica
        
        *Hacer clic en "Comenzar ejercicios" para acceder al módulo morfosintáctico*
        """)
        
    # Recomendaciones semánticas
    if metrics['vocabulary']['normalized_score'] < 0.7:
        st.warning("""
        #### 📚 Análisis Semántico Recomendado
        
        **Para mejorar tu vocabulario y expresión:**
        A. Realiza el análisis semántico de un texto académico
        B. Identifica y agrupa campos semánticos relacionados
        C. Practica la sustitución léxica en tus párrafos
        D. Construye redes de conceptos sobre tu tema
        E. Analiza las relaciones entre ideas principales
        
        *Hacer clic en "Comenzar ejercicios" para acceder al módulo semántico*
        """)
    
    # Recomendaciones de cohesión
    if metrics['cohesion']['normalized_score'] < 0.65:
        st.warning("""
        #### 🔄 Análisis del Discurso Recomendado
        
        **Para mejorar la conexión entre ideas:**
        1. Realizar el análisis del discurso de un texto modelo
        2. Practicar el uso de diferentes conectores textuales
        3. Identificar cadenas de referencia en textos académicos
        4. Ejercitar la progresión temática en tus escritos
        
        *Hacer clic en "Comenzar ejercicios" para acceder al módulo de análisis del discurso*
        """)
    
    # Botón de acción
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.button(
            "🎯 Comenzar ejercicios recomendados",
            type="primary",
            use_container_width=True,
            key="start_exercises"
        )
