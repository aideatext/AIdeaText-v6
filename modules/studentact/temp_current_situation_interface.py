# modules/studentact/current_situation_interface.py

import streamlit as st
import logging
from ..utils.widget_utils import generate_unique_key
from .current_situation_analysis import (
    analyze_text_dimensions,
    create_vocabulary_network,
    create_syntax_complexity_graph, 
    create_cohesion_heatmap
)

logger = logging.getLogger(__name__)

def display_current_situation_interface(lang_code, nlp_models, t):
    """
    Interfaz modular para el análisis de la situación actual del estudiante.
    Esta función maneja la presentación y la interacción con el usuario.
    
    Args:
        lang_code: Código del idioma actual
        nlp_models: Diccionario de modelos de spaCy cargados
        t: Diccionario de traducciones
    """
    st.markdown("## Mi Situación Actual de Escritura")
    
    # Container principal para mejor organización visual
    with st.container():
        # Columnas para entrada y visualización
        text_col, visual_col = st.columns([1,2])
        
        with text_col:
            # Área de entrada de texto
            text_input = st.text_area(
                t.get('current_situation_input', "Ingresa tu texto para analizar:"),
                height=400,
                key=generate_unique_key("current_situation", "input")
            )
            
            # Botón de análisis
            if st.button(
                t.get('analyze_button', "Explorar mi escritura"),
                type="primary",
                disabled=not text_input,
                key=generate_unique_key("current_situation", "analyze")
            ):
                try:
                    with st.spinner(t.get('processing', "Analizando texto...")):
                        # 1. Procesar el texto
                        doc = nlp_models[lang_code](text_input)
                        metrics = analyze_text_dimensions(doc)
                        
                        # 2. Mostrar visualizaciones en la columna derecha
                        with visual_col:
                            display_current_situation_visual(doc, metrics)
                        
                        # 3. Obtener retroalimentación de Claude
                        feedback = get_claude_feedback(metrics, text_input)
                        
                        # 4. Guardar los resultados
                        from ..database.backUp.current_situation_mongo_db import store_current_situation_result
                        
                    if st.button(t.get('analyze_button', "Explorar mi escritura")):
                        with st.spinner(t.get('processing', "Analizando texto...")):
                            # Procesar y analizar
                            doc = nlp_models[lang_code](text_input)
                            
                            # Obtener métricas con manejo de errores
                            try:
                                metrics = analyze_text_dimensions(doc)
                            except Exception as e:
                                logger.error(f"Error en análisis: {str(e)}")
                                st.error("Error en el análisis de dimensiones")
                                return
                            
                            # Obtener feedback
                            try:
                                feedback = get_claude_feedback(metrics, text_input)
                            except Exception as e:
                                logger.error(f"Error obteniendo feedback: {str(e)}")
                                st.error("Error obteniendo retroalimentación")
                                return
                            
                            # Guardar resultados con verificación
                            if store_current_situation_result(
                                st.session_state.username,
                                text_input,
                                metrics,
                                feedback
                            ):
                                st.success(t.get('save_success', "Análisis guardado"))
                                
                                # Mostrar visualizaciones y recomendaciones
                                display_current_situation_visual(doc, metrics)
                                show_recommendations(feedback, t)
                            else:
                                st.error("Error al guardar el análisis")
                                
                except Exception as e:
                    logger.error(f"Error en interfaz: {str(e)}")
                    st.error("Error general en la interfaz")

################################################################
def display_current_situation_visual(doc, metrics):
    """Visualización mejorada de resultados con interpretaciones"""
    try:
        with st.container():
            # Estilos CSS mejorados para los contenedores
            st.markdown("""
                <style>
                .graph-container {
                    background-color: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin: 15px 0;
                }
                .interpretation-box {
                    background-color: #f8f9fa;
                    border-left: 4px solid #0d6efd;
                    padding: 15px;
                    margin: 10px 0;
                }
                .metric-indicator {
                    font-size: 1.2em;
                    font-weight: 500;
                    color: #1f2937;
                }
                </style>
            """, unsafe_allow_html=True)

            # 1. Riqueza de Vocabulario
            with st.expander("📚 Riqueza de Vocabulario", expanded=True):
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                vocabulary_graph = create_vocabulary_network(doc)
                if vocabulary_graph:
                    # Mostrar gráfico
                    st.pyplot(vocabulary_graph)
                    plt.close(vocabulary_graph)
                    
                    # Interpretación
                    st.markdown('<div class="interpretation-box">', unsafe_allow_html=True)
                    st.markdown("**¿Qué significa este gráfico?**")
                    st.markdown("""
                        - 🔵 Los nodos azules representan palabras clave en tu texto
                        - 📏 El tamaño de cada nodo indica su frecuencia de uso
                        - 🔗 Las líneas conectan palabras que aparecen juntas frecuentemente
                        - 🎨 Los colores más intensos indican palabras más centrales
                    """)
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # 2. Estructura de Oraciones
            with st.expander("🏗️ Complejidad Estructural", expanded=True):
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                syntax_graph = create_syntax_complexity_graph(doc)
                if syntax_graph:
                    st.pyplot(syntax_graph)
                    plt.close(syntax_graph)
                    
                    st.markdown('<div class="interpretation-box">', unsafe_allow_html=True)
                    st.markdown("**Análisis de la estructura:**")
                    st.markdown("""
                        - 📊 Las barras muestran la complejidad de cada oración
                        - 📈 Mayor altura indica estructuras más elaboradas
                        - 🎯 La línea punteada indica el nivel óptimo de complejidad
                        - 🔄 Variación en las alturas sugiere dinamismo en la escritura
                    """)
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # 3. Cohesión Textual
            with st.expander("🔄 Cohesión del Texto", expanded=True):
                st.markdown('<div class="graph-container">', unsafe_allow_html=True)
                cohesion_map = create_cohesion_heatmap(doc)
                if cohesion_map:
                    st.pyplot(cohesion_map)
                    plt.close(cohesion_map)
                    
                    st.markdown('<div class="interpretation-box">', unsafe_allow_html=True)
                    st.markdown("**¿Cómo leer el mapa de calor?**")
                    st.markdown("""
                        - 🌈 Colores más intensos indican mayor conexión entre oraciones
                        - 📝 La diagonal muestra la coherencia interna de cada oración
                        - 🔗 Las zonas claras sugieren oportunidades de mejorar conexiones
                        - 🎯 Un buen texto muestra patrones de color consistentes
                    """)
                    st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # 4. Métricas Generales
            with st.expander("📊 Resumen de Métricas", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Diversidad Léxica",
                        f"{metrics['vocabulary_richness']:.2f}/1.0",
                        help="Mide la variedad de palabras diferentes utilizadas"
                    )
                
                with col2:
                    st.metric(
                        "Complejidad Estructural",
                        f"{metrics['structural_complexity']:.2f}/1.0",
                        help="Indica qué tan elaboradas son las estructuras de las oraciones"
                    )
                
                with col3:
                    st.metric(
                        "Cohesión Textual",
                        f"{metrics['cohesion_score']:.2f}/1.0",
                        help="Evalúa qué tan bien conectadas están las ideas entre sí"
                    )

    except Exception as e:
        logger.error(f"Error en visualización: {str(e)}")
        st.error("Error al generar las visualizaciones")

################################################################
def show_recommendations(feedback, t):
    """
    Muestra las recomendaciones y ejercicios personalizados para el estudiante,
    permitiendo el seguimiento de su progreso.
    
    Args:
        feedback: Diccionario con retroalimentación y ejercicios recomendados
        t: Diccionario de traducciones
    """
    st.markdown("### " + t.get('recommendations_title', "Recomendaciones para mejorar"))
    
    for area, exercises in feedback['recommendations'].items():
        with st.expander(f"💡 {area}"):
            try:
                # Descripción del área de mejora
                st.markdown(exercises['description'])
                
                # Obtener el historial de ejercicios del estudiante
                from ..database.backUp.current_situation_mongo_db import get_student_exercises_history
                exercises_history = get_student_exercises_history(st.session_state.username)
                
                # Separar ejercicios en completados y pendientes
                completed = exercises_history.get(area, [])
                
                # Mostrar estado actual
                progress_col1, progress_col2 = st.columns([3,1])
                with progress_col1:
                    st.markdown("**Ejercicio sugerido:**")
                    st.markdown(exercises['activity'])
                
                with progress_col2:
                    # Verificar si el ejercicio ya está completado
                    exercise_key = f"{area}_{exercises['activity']}"
                    is_completed = exercise_key in completed
                    
                    if is_completed:
                        st.success("✅ Completado")
                    else:
                        # Botón para marcar ejercicio como completado
                        if st.button(
                            t.get('mark_complete', "Marcar como completado"),
                            key=generate_unique_key("exercise", area),
                            type="primary"
                        ):
                            try:
                                from ..database.backUp.current_situation_mongo_db import update_exercise_status
                                
                                # Actualizar estado del ejercicio
                                success = update_exercise_status(
                                    username=st.session_state.username,
                                    area=area,
                                    exercise=exercises['activity'],
                                    completed=True
                                )
                                
                                if success:
                                    st.success(t.get(
                                        'exercise_completed', 
                                        "¡Ejercicio marcado como completado!"
                                    ))
                                    st.rerun()
                                else:
                                    st.error(t.get(
                                        'exercise_error',
                                        "Error al actualizar el estado del ejercicio"
                                    ))
                            except Exception as e:
                                logger.error(f"Error actualizando estado del ejercicio: {str(e)}")
                                st.error(t.get('update_error', "Error al actualizar el ejercicio"))
                
                # Mostrar recursos adicionales si existen
                if 'resources' in exercises:
                    st.markdown("**Recursos adicionales:**")
                    for resource in exercises['resources']:
                        st.markdown(f"- {resource}")
                
                # Mostrar fecha de finalización si está completado
                if is_completed:
                    completion_date = exercises_history[exercise_key].get('completion_date')
                    if completion_date:
                        st.caption(
                            t.get('completed_on', "Completado el") + 
                            f": {completion_date.strftime('%d/%m/%Y %H:%M')}"
                        )
                        
            except Exception as e:
                logger.error(f"Error mostrando recomendaciones para {area}: {str(e)}")
                st.error(t.get(
                    'recommendations_error',
                    f"Error al mostrar las recomendaciones para {area}"
                ))