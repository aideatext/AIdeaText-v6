##############
###modules/studentact/student_activities_v2.py

import streamlit as st
import re
import io
from io import BytesIO
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from spacy import displacy
import random
import base64
import seaborn as sns
import logging

# Importaciones de la base de datos
from ..database.morphosintax_mongo_db import get_student_morphosyntax_analysis
from ..database.semantic_mongo_db import get_student_semantic_analysis
from ..database.discourse_mongo_db import get_student_discourse_analysis
from ..database.chat_mongo_db import get_chat_history
from ..database.current_situation_mongo_db import get_current_situation_analysis
from ..database.claude_recommendations_mongo_db import get_claude_recommendations

# Importar la función generate_unique_key
from ..utils.widget_utils import generate_unique_key

logger = logging.getLogger(__name__)

###################################################################################

def display_student_activities(username: str, lang_code: str, t: dict):
    """
    Muestra todas las actividades del estudiante
    Args:
        username: Nombre del estudiante
        lang_code: Código del idioma
        t: Diccionario de traducciones
    """
    try:
        # Cambiado de "Mis Actividades" a "Registro de mis actividades"
        #st.header(t.get('activities_title', 'Registro de mis actividades'))

        # Tabs para diferentes tipos de análisis
        # Cambiado "Análisis del Discurso" a "Análisis comparado de textos"
        tabs = st.tabs([
            t.get('current_situation_activities', 'Registros de la función: Mi Situación Actual'),
            t.get('morpho_activities', 'Registros de mis análisis morfosintácticos'),
            t.get('semantic_activities', 'Registros de mis análisis semánticos'),
            t.get('discourse_activities', 'Registros de mis análisis comparado de textos'),
            t.get('chat_activities', 'Registros de mis conversaciones con el tutor virtual')
        ])

        # Tab de Situación Actual
        with tabs[0]:
            display_current_situation_activities(username, t)
        
        # Tab de Análisis Morfosintáctico
        with tabs[1]:
            display_morphosyntax_activities(username, t)

        # Tab de Análisis Semántico
        with tabs[2]:
            display_semantic_activities(username, t)

        # Tab de Análisis del Discurso (mantiene nombre interno pero UI muestra "Análisis comparado de textos")
        with tabs[3]:
            display_discourse_activities(username, t)
            
        # Tab de Conversaciones del Chat
        with tabs[4]:
            display_chat_activities(username, t)

    except Exception as e:
        logger.error(f"Error mostrando actividades: {str(e)}")
        st.error(t.get('error_loading_activities', 'Error al cargar las actividades'))


###############################################################################################

def display_current_situation_activities(username: str, t: dict):
    """
    Muestra análisis de situación actual junto con las recomendaciones de Claude
    unificando la información de ambas colecciones y emparejándolas por cercanía temporal.
    """
    try:
        # Recuperar datos de ambas colecciones
        logger.info(f"Recuperando análisis de situación actual para {username}")
        situation_analyses = get_current_situation_analysis(username, limit=10)
        
        # Verificar si hay datos
        if situation_analyses:
            logger.info(f"Recuperados {len(situation_analyses)} análisis de situación")
            # Depurar para ver la estructura de datos
            for i, analysis in enumerate(situation_analyses):
                logger.info(f"Análisis #{i+1}: Claves disponibles: {list(analysis.keys())}")
                if 'metrics' in analysis:
                    logger.info(f"Métricas disponibles: {list(analysis['metrics'].keys())}")
        else:
            logger.warning("No se encontraron análisis de situación actual")
        
        logger.info(f"Recuperando recomendaciones de Claude para {username}")
        claude_recommendations = get_claude_recommendations(username)
        
        if claude_recommendations:
            logger.info(f"Recuperadas {len(claude_recommendations)} recomendaciones de Claude")
        else:
            logger.warning("No se encontraron recomendaciones de Claude")
        
        # Verificar si hay algún tipo de análisis disponible
        if not situation_analyses and not claude_recommendations:
            logger.info("No se encontraron análisis de situación actual ni recomendaciones")
            st.info(t.get('no_current_situation', 'No hay análisis de situación actual registrados'))
            return
        
        # Crear pares combinados emparejando diagnósticos y recomendaciones cercanos en tiempo
        logger.info("Creando emparejamientos temporales de análisis")
        
        # Convertir timestamps a objetos datetime para comparación
        situation_times = []
        for analysis in situation_analyses:
            if 'timestamp' in analysis:
                try:
                    timestamp_str = analysis['timestamp']
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    situation_times.append((dt, analysis))
                except Exception as e:
                    logger.error(f"Error parseando timestamp de situación: {str(e)}")
        
        recommendation_times = []
        for recommendation in claude_recommendations:
            if 'timestamp' in recommendation:
                try:
                    timestamp_str = recommendation['timestamp']
                    dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    recommendation_times.append((dt, recommendation))
                except Exception as e:
                    logger.error(f"Error parseando timestamp de recomendación: {str(e)}")
        
        # Ordenar por tiempo
        situation_times.sort(key=lambda x: x[0], reverse=True)
        recommendation_times.sort(key=lambda x: x[0], reverse=True)
        
        # Crear pares combinados
        combined_items = []
        
        # Primero, procesar todas las situaciones encontrando la recomendación más cercana
        for sit_time, situation in situation_times:
            # Buscar la recomendación más cercana en tiempo
            best_match = None
            min_diff = timedelta(minutes=30)  # Máxima diferencia de tiempo aceptable (30 minutos)
            best_rec_time = None
            
            for rec_time, recommendation in recommendation_times:
                time_diff = abs(sit_time - rec_time)
                if time_diff < min_diff:
                    min_diff = time_diff
                    best_match = recommendation
                    best_rec_time = rec_time
            
            # Crear un elemento combinado
            if best_match:
                timestamp_key = sit_time.isoformat()
                combined_items.append((timestamp_key, {
                    'situation': situation,
                    'recommendation': best_match,
                    'time_diff': min_diff.total_seconds()
                }))
                # Eliminar la recomendación usada para no reutilizarla
                recommendation_times = [(t, r) for t, r in recommendation_times if t != best_rec_time]
                logger.info(f"Emparejado: Diagnóstico {sit_time} con Recomendación {best_rec_time} (diferencia: {min_diff})")
            else:
                # Si no hay recomendación cercana, solo incluir la situación
                timestamp_key = sit_time.isoformat()
                combined_items.append((timestamp_key, {
                    'situation': situation
                }))
                logger.info(f"Sin emparejar: Diagnóstico {sit_time} sin recomendación cercana")
        
        # Agregar recomendaciones restantes sin situación
        for rec_time, recommendation in recommendation_times:
            timestamp_key = rec_time.isoformat()
            combined_items.append((timestamp_key, {
                'recommendation': recommendation
            }))
            logger.info(f"Sin emparejar: Recomendación {rec_time} sin diagnóstico cercano")
        
        # Ordenar por tiempo (más reciente primero)
        combined_items.sort(key=lambda x: x[0], reverse=True)
        
        logger.info(f"Procesando {len(combined_items)} elementos combinados")
        
        # Mostrar cada par combinado
        for i, (timestamp_key, analysis_pair) in enumerate(combined_items):
            try:
                # Obtener datos de situación y recomendación
                situation_data = analysis_pair.get('situation', {})
                recommendation_data = analysis_pair.get('recommendation', {})
                time_diff = analysis_pair.get('time_diff')
                
                # Si no hay ningún dato, continuar al siguiente
                if not situation_data and not recommendation_data:
                    continue
                
                # Determinar qué texto mostrar (priorizar el de la situación)
                text_to_show = situation_data.get('text', recommendation_data.get('text', ''))
                text_type = situation_data.get('text_type', recommendation_data.get('text_type', ''))
                
                # Formatear fecha para mostrar
                try:
                    # Usar timestamp del key que ya es un formato ISO
                    dt = datetime.fromisoformat(timestamp_key)
                    formatted_date = dt.strftime("%d/%m/%Y %H:%M:%S")
                except Exception as date_error:
                    logger.error(f"Error formateando fecha: {str(date_error)}")
                    formatted_date = timestamp_key
                
                # Determinar el título del expander
                title = f"{t.get('analysis_date', 'Fecha')}: {formatted_date}"
                if text_type:
                    text_type_display = {
                        'academic_article': t.get('academic_article', 'Artículo académico'),
                        'student_essay': t.get('student_essay', 'Trabajo universitario'),
                        'general_communication': t.get('general_communication', 'Comunicación general')
                    }.get(text_type, text_type)
                    title += f" - {text_type_display}"
                
                # Añadir indicador de emparejamiento si existe
                if time_diff is not None:
                    if time_diff < 60:  # menos de un minuto
                        title += f" 🔄 (emparejados)"
                    else:
                        title += f" 🔄 (emparejados, diferencia: {int(time_diff//60)} min)"
                
                # Usar un ID único para cada expander
                expander_id = f"analysis_{i}_{timestamp_key.replace(':', '_')}"
                
                # Mostrar el análisis en un expander
                with st.expander(title, expanded=False):
                    # Mostrar texto analizado con key único
                    st.subheader(t.get('analyzed_text', 'Texto analizado'))
                    st.text_area(
                        "Text Content", 
                        value=text_to_show, 
                        height=100,
                        disabled=True,
                        label_visibility="collapsed",
                        key=f"text_area_{expander_id}"
                    )
                    
                    # Crear tabs para separar diagnóstico y recomendaciones
                    diagnosis_tab, recommendations_tab = st.tabs([
                        t.get('diagnosis_tab', 'Diagnóstico'),
                        t.get('recommendations_tab', 'Recomendaciones')
                    ])
                    
                    # Tab de diagnóstico
                    with diagnosis_tab:
                        if situation_data and 'metrics' in situation_data:
                            metrics = situation_data['metrics']
                            
                            # Dividir en dos columnas
                            col1, col2 = st.columns(2)
                            
                            # Principales métricas en formato de tarjetas
                            with col1:
                                st.subheader(t.get('key_metrics', 'Métricas clave'))
                                
                                # Mostrar cada métrica principal
                                for metric_name, metric_data in metrics.items():
                                    try:
                                        # Determinar la puntuación
                                        score = None
                                        if isinstance(metric_data, dict):
                                            # Intentar diferentes nombres de campo
                                            if 'normalized_score' in metric_data:
                                                score = metric_data['normalized_score']
                                            elif 'score' in metric_data:
                                                score = metric_data['score']
                                            elif 'value' in metric_data:
                                                score = metric_data['value']
                                        elif isinstance(metric_data, (int, float)):
                                            score = metric_data
                                        
                                        if score is not None:
                                            # Asegurarse de que score es numérico
                                            if isinstance(score, (int, float)):
                                                # Determinar color y emoji basado en la puntuación
                                                if score < 0.5:
                                                    emoji = "🔴"
                                                    color = "#ffcccc"  # light red
                                                elif score < 0.75:
                                                    emoji = "🟡"
                                                    color = "#ffffcc"  # light yellow
                                                else:
                                                    emoji = "🟢"
                                                    color = "#ccffcc"  # light green
                                                
                                                # Mostrar la métrica con estilo
                                                st.markdown(f"""
                                                <div style="background-color:{color}; padding:10px; border-radius:5px; margin-bottom:10px;">
                                                    <b>{emoji} {metric_name.capitalize()}:</b> {score:.2f}
                                                </div>
                                                """, unsafe_allow_html=True)
                                            else:
                                                # Si no es numérico, mostrar como texto
                                                st.markdown(f"""
                                                <div style="background-color:#f0f0f0; padding:10px; border-radius:5px; margin-bottom:10px;">
                                                    <b>ℹ️ {metric_name.capitalize()}:</b> {str(score)}
                                                </div>
                                                """, unsafe_allow_html=True)
                                    except Exception as e:
                                        logger.error(f"Error procesando métrica {metric_name}: {str(e)}")
                            
                            # Mostrar detalles adicionales si están disponibles
                            with col2:
                                st.subheader(t.get('details', 'Detalles'))
                                
                                # Para cada métrica, mostrar sus detalles si existen
                                for metric_name, metric_data in metrics.items():
                                    try:
                                        if isinstance(metric_data, dict):
                                            # Mostrar detalles directamente o buscar en subcampos
                                            details = None
                                            if 'details' in metric_data and metric_data['details']:
                                                details = metric_data['details']
                                            else:
                                                # Crear un diccionario con los detalles excluyendo 'normalized_score' y similares
                                                details = {k: v for k, v in metric_data.items() 
                                                          if k not in ['normalized_score', 'score', 'value']}
                                            
                                            if details:
                                                st.write(f"**{metric_name.capitalize()}**")
                                                st.json(details, expanded=False)
                                    except Exception as e:
                                        logger.error(f"Error mostrando detalles de {metric_name}: {str(e)}")
                        else:
                            st.info(t.get('no_diagnosis', 'No hay datos de diagnóstico disponibles'))
                    
                    # Tab de recomendaciones
                    with recommendations_tab:
                        if recommendation_data and 'recommendations' in recommendation_data:
                            st.markdown(f"""
                            <div style="padding: 20px; border-radius: 10px; 
                                background-color: #f8f9fa; margin-bottom: 20px;">
                                {recommendation_data['recommendations']}
                            </div>
                            """, unsafe_allow_html=True)
                        elif recommendation_data and 'feedback' in recommendation_data:
                            st.markdown(f"""
                            <div style="padding: 20px; border-radius: 10px; 
                                background-color: #f8f9fa; margin-bottom: 20px;">
                                {recommendation_data['feedback']}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info(t.get('no_recommendations', 'No hay recomendaciones disponibles'))
            
            except Exception as e:
                logger.error(f"Error procesando par de análisis: {str(e)}")
                continue
        
    except Exception as e:
        logger.error(f"Error mostrando actividades de situación actual: {str(e)}")
        st.error(t.get('error_current_situation', 'Error al mostrar análisis de situación actual'))

###############################################################################################

def display_morphosyntax_activities(username: str, t: dict):
    """
    Muestra actividades de análisis morfosintáctico, incluyendo base e iteraciones
    desde las nuevas colecciones: student_morphosyntax_analysis_base y student_morphosyntax_iterations
    """
    try:
        # Importación inline para evitar problemas de circularidad
        # Utilizamos la función de la nueva estructura de DB iterativa
        from ..database.morphosyntax_iterative_mongo_db import get_student_morphosyntax_analysis
        
        logger.info(f"Recuperando análisis morfosintáctico para {username}")
        
        # Esta función ahora trae tanto las bases como sus iteraciones
        base_analyses = get_student_morphosyntax_analysis(username)
        
        if not base_analyses:
            logger.info("No se encontraron análisis morfosintácticos")
            st.info(t.get('no_morpho_analyses', 'No hay análisis morfosintácticos registrados'))
            return

        logger.info(f"Procesando {len(base_analyses)} análisis morfosintácticos base")
        
        # Procesar cada análisis base con sus iteraciones
        for base_analysis in base_analyses:
            try:
                # Formatear fecha
                timestamp = datetime.fromisoformat(base_analysis['timestamp'].replace('Z', '+00:00'))
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                # Título del expander: incluir información de si tiene iteraciones
                expander_title = f"{t.get('analysis_date', 'Fecha')}: {formatted_date}"
                if base_analysis.get('has_iterations', False):
                    expander_title += f" ({t.get('has_iterations', 'Con iteraciones')})"
                
                with st.expander(expander_title, expanded=False):
                    # Mostrar texto base
                    st.subheader(t.get('base_text', 'Texto original'))
                    st.text_area(
                        "Base Text Content", 
                        value=base_analysis.get('text', ''), 
                        height=100,
                        disabled=True,
                        label_visibility="collapsed",
                        key=f"base_text_{str(base_analysis['_id'])}"
                    )
                    
                    # Mostrar diagrama de arco base si existe
                    if 'arc_diagrams' in base_analysis and base_analysis['arc_diagrams']:
                        st.subheader(t.get('syntactic_diagrams', 'Diagrama sintáctico (original)'))
                        # Mostrar cada diagrama (normalmente solo uno por oración)
                        for diagram in base_analysis['arc_diagrams']:
                            st.write(diagram, unsafe_allow_html=True)
                    
                    # Procesar iteraciones si existen
                    if 'iterations' in base_analysis and base_analysis['iterations']:
                        st.markdown("---")  # Línea divisoria
                        st.subheader(t.get('iterations', 'Versiones mejoradas'))
                        
                        # Crear tabs para cada iteración
                        iteration_tabs = st.tabs([
                            f"{t.get('iteration', 'Versión')} {i+1}" 
                            for i in range(len(base_analysis['iterations']))
                        ])
                        
                        # Mostrar cada iteración en su propia pestaña
                        for i, (tab, iteration) in enumerate(zip(iteration_tabs, base_analysis['iterations'])):
                            with tab:
                                # Timestamp de la iteración
                                iter_timestamp = datetime.fromisoformat(
                                    iteration['timestamp'].replace('Z', '+00:00'))
                                iter_formatted_date = iter_timestamp.strftime("%d/%m/%Y %H:%M:%S")
                                st.caption(f"{t.get('iteration_date', 'Fecha de versión')}: {iter_formatted_date}")
                                
                                # Texto de la iteración
                                st.text_area(
                                    f"Iteration Text {i+1}", 
                                    value=iteration.get('iteration_text', ''), 
                                    height=100,
                                    disabled=True,
                                    label_visibility="collapsed",
                                    key=f"iter_text_{str(iteration['_id'])}"
                                )
                                
                                # Diagrama de arco de la iteración
                                if 'arc_diagrams' in iteration and iteration['arc_diagrams']:
                                    st.subheader(t.get('iteration_diagram', 'Diagrama sintáctico (mejorado)'))
                                    for diagram in iteration['arc_diagrams']:
                                        st.write(diagram, unsafe_allow_html=True)
                
            except Exception as e:
                logger.error(f"Error procesando análisis morfosintáctico: {str(e)}")
                st.error(t.get('error_processing_analysis', 'Error procesando este análisis'))
                continue

    except Exception as e:
        logger.error(f"Error mostrando análisis morfosintáctico: {str(e)}")
        st.error(t.get('error_morpho', 'Error al mostrar análisis morfosintáctico'))


###############################################################################################

def display_semantic_activities(username: str, t: dict):
    """Muestra actividades de análisis semántico"""
    try:
        logger.info(f"Recuperando análisis semántico para {username}")
        analyses = get_student_semantic_analysis(username)
        
        if not analyses:
            logger.info("No se encontraron análisis semánticos")
            st.info(t.get('no_semantic_analyses', 'No hay análisis semánticos registrados'))
            return

        logger.info(f"Procesando {len(analyses)} análisis semánticos")
        
        for analysis in analyses:
            try:
                # Verificar campos necesarios
                if not all(key in analysis for key in ['timestamp', 'concept_graph']):
                    logger.warning(f"Análisis incompleto: {analysis.keys()}")
                    continue
                
                # Formatear fecha
                timestamp = datetime.fromisoformat(analysis['timestamp'].replace('Z', '+00:00'))
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                # Crear expander
                with st.expander(f"{t.get('analysis_date', 'Fecha')}: {formatted_date}", expanded=False):
                    # Procesar y mostrar gráfico
                    if analysis.get('concept_graph'):
                        try:
                            # Convertir de base64 a bytes
                            logger.debug("Decodificando gráfico de conceptos")
                            image_data = analysis['concept_graph']
                            
                            # Si el gráfico ya es bytes, usarlo directamente
                            if isinstance(image_data, bytes):
                                image_bytes = image_data
                            else:
                                # Si es string base64, decodificar
                                image_bytes = base64.b64decode(image_data)
                            
                            logger.debug(f"Longitud de bytes de imagen: {len(image_bytes)}")
                            
                            # Mostrar imagen
                            st.image(
                                image_bytes,
                                caption=t.get('concept_network', 'Red de Conceptos'),
                                use_container_width=True
                            )
                            logger.debug("Gráfico mostrado exitosamente")
                            
                        except Exception as img_error:
                            logger.error(f"Error procesando gráfico: {str(img_error)}")
                            st.error(t.get('error_loading_graph', 'Error al cargar el gráfico'))
                    else:
                        st.info(t.get('no_graph', 'No hay visualización disponible'))

            except Exception as e:
                logger.error(f"Error procesando análisis individual: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error mostrando análisis semántico: {str(e)}")
        st.error(t.get('error_semantic', 'Error al mostrar análisis semántico'))


###################################################################################################

def display_discourse_activities(username: str, t: dict):
    """Muestra actividades de análisis del discurso (mostrado como 'Análisis comparado de textos' en la UI)"""
    try:
        logger.info(f"Recuperando análisis del discurso para {username}")
        analyses = get_student_discourse_analysis(username)
        
        if not analyses:
            logger.info("No se encontraron análisis del discurso")
            # Usamos el término "análisis comparado de textos" en la UI
            st.info(t.get('no_discourse_analyses', 'No hay análisis comparados de textos registrados'))
            return

        logger.info(f"Procesando {len(analyses)} análisis del discurso")
        for analysis in analyses:
            try:
                # Verificar campos mínimos necesarios
                if not all(key in analysis for key in ['timestamp']):
                    logger.warning(f"Análisis incompleto: {analysis.keys()}")
                    continue

                # Formatear fecha
                timestamp = datetime.fromisoformat(analysis['timestamp'].replace('Z', '+00:00'))
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                with st.expander(f"{t.get('analysis_date', 'Fecha')}: {formatted_date}", expanded=False):
                    # Crear dos columnas para mostrar los documentos lado a lado
                    col1, col2 = st.columns(2)
                    
                    # Documento 1 - Columna izquierda
                    with col1:
                        st.subheader(t.get('doc1_title', 'Documento 1'))
                        st.markdown(t.get('key_concepts', 'Conceptos Clave'))
                        
                        # Mostrar conceptos clave en formato de etiquetas
                        if 'key_concepts1' in analysis and analysis['key_concepts1']:
                            concepts_html = f"""
                                <div style="display: flex; flex-wrap: nowrap; gap: 8px; padding: 12px; 
                                    background-color: #f8f9fa; border-radius: 8px; overflow-x: auto; 
                                    margin-bottom: 15px; white-space: nowrap;">
                                    {''.join([
                                        f'<div style="background-color: white; border-radius: 4px; padding: 6px 10px; display: inline-flex; align-items: center; gap: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); flex-shrink: 0;">'
                                        f'<span style="font-weight: 500; color: #1f2937; font-size: 0.85em;">{concept}</span>'
                                        f'<span style="color: #6b7280; font-size: 0.75em;">({freq:.2f})</span></div>'
                                        for concept, freq in analysis['key_concepts1']
                                    ])}
                                </div>
                            """
                            st.markdown(concepts_html, unsafe_allow_html=True)
                        else:
                            st.info(t.get('no_concepts', 'No hay conceptos disponibles'))
                        
                        # Mostrar grafo 1
                        if 'graph1' in analysis:
                            try:
                                if isinstance(analysis['graph1'], bytes):
                                    st.image(
                                        analysis['graph1'],
                                        use_container_width=True
                                    )
                                else:
                                    logger.warning(f"graph1 no es bytes: {type(analysis['graph1'])}")
                                    st.warning(t.get('graph_not_available', 'Gráfico no disponible'))
                            except Exception as e:
                                logger.error(f"Error mostrando graph1: {str(e)}")
                                st.error(t.get('error_loading_graph', 'Error al cargar el gráfico'))
                        else:
                            st.info(t.get('no_visualization', 'No hay visualización disponible'))
                        
                        # Interpretación del grafo
                        st.markdown("**📊 Interpretación del grafo:**")
                        st.markdown("""
                            - 🔀 Las flechas indican la dirección de la relación entre conceptos
                            - 🎨 Los colores más intensos indican conceptos más centrales en el texto
                            - ⭕ El tamaño de los nodos representa la frecuencia del concepto
                            - ↔️ El grosor de las líneas indica la fuerza de la conexión
                        """)
                    
                    # Documento 2 - Columna derecha
                    with col2:
                        st.subheader(t.get('doc2_title', 'Documento 2'))
                        st.markdown(t.get('key_concepts', 'Conceptos Clave'))
                        
                        # Mostrar conceptos clave en formato de etiquetas
                        if 'key_concepts2' in analysis and analysis['key_concepts2']:
                            concepts_html = f"""
                                <div style="display: flex; flex-wrap: nowrap; gap: 8px; padding: 12px; 
                                    background-color: #f8f9fa; border-radius: 8px; overflow-x: auto; 
                                    margin-bottom: 15px; white-space: nowrap;">
                                    {''.join([
                                        f'<div style="background-color: white; border-radius: 4px; padding: 6px 10px; display: inline-flex; align-items: center; gap: 4px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); flex-shrink: 0;">'
                                        f'<span style="font-weight: 500; color: #1f2937; font-size: 0.85em;">{concept}</span>'
                                        f'<span style="color: #6b7280; font-size: 0.75em;">({freq:.2f})</span></div>'
                                        for concept, freq in analysis['key_concepts2']
                                    ])}
                                </div>
                            """
                            st.markdown(concepts_html, unsafe_allow_html=True)
                        else:
                            st.info(t.get('no_concepts', 'No hay conceptos disponibles'))
                        
                        # Mostrar grafo 2
                        if 'graph2' in analysis:
                            try:
                                if isinstance(analysis['graph2'], bytes):
                                    st.image(
                                        analysis['graph2'],
                                        use_container_width=True
                                    )
                                else:
                                    logger.warning(f"graph2 no es bytes: {type(analysis['graph2'])}")
                                    st.warning(t.get('graph_not_available', 'Gráfico no disponible'))
                            except Exception as e:
                                logger.error(f"Error mostrando graph2: {str(e)}")
                                st.error(t.get('error_loading_graph', 'Error al cargar el gráfico'))
                        else:
                            st.info(t.get('no_visualization', 'No hay visualización disponible'))
                        
                        # Interpretación del grafo
                        st.markdown("**📊 Interpretación del grafo:**")
                        st.markdown("""
                            - 🔀 Las flechas indican la dirección de la relación entre conceptos
                            - 🎨 Los colores más intensos indican conceptos más centrales en el texto
                            - ⭕ El tamaño de los nodos representa la frecuencia del concepto
                            - ↔️ El grosor de las líneas indica la fuerza de la conexión
                        """)

            except Exception as e:
                logger.error(f"Error procesando análisis individual: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error mostrando análisis del discurso: {str(e)}")
        # Usamos el término "análisis comparado de textos" en la UI
        st.error(t.get('error_discourse', 'Error al mostrar análisis comparado de textos'))



#################################################################################   

def display_discourse_comparison(analysis: dict, t: dict):
    """
    Muestra la comparación de conceptos clave en análisis del discurso.
    Formato horizontal simplificado.
    """
    st.subheader(t.get('comparison_results', 'Resultados de la comparación'))
    
    # Verificar si tenemos los conceptos necesarios
    if not ('key_concepts1' in analysis and analysis['key_concepts1']):
        st.info(t.get('no_concepts', 'No hay conceptos disponibles para comparar'))
        return
    
    # Conceptos del Texto 1 - Formato horizontal
    st.markdown(f"**{t.get('concepts_text_1', 'Conceptos Texto 1')}:**")
    try:
        # Comprobar formato y mostrar horizontalmente
        if isinstance(analysis['key_concepts1'], list) and len(analysis['key_concepts1']) > 0:
            if isinstance(analysis['key_concepts1'][0], list) and len(analysis['key_concepts1'][0]) == 2:
                # Formatear como "concepto (valor), concepto2 (valor2), ..."
                concepts_text = ", ".join([f"{c[0]} ({c[1]})" for c in analysis['key_concepts1'][:10]])
                st.markdown(f"*{concepts_text}*")
            else:
                # Si no tiene el formato esperado, mostrar como lista simple
                st.markdown(", ".join(str(c) for c in analysis['key_concepts1'][:10]))
        else:
            st.write(str(analysis['key_concepts1']))
    except Exception as e:
        logger.error(f"Error mostrando key_concepts1: {str(e)}")
        st.error(t.get('error_concepts1', 'Error mostrando conceptos del Texto 1'))
    
    # Conceptos del Texto 2 - Formato horizontal
    st.markdown(f"**{t.get('concepts_text_2', 'Conceptos Texto 2')}:**")
    if 'key_concepts2' in analysis and analysis['key_concepts2']:
        try:
            # Comprobar formato y mostrar horizontalmente
            if isinstance(analysis['key_concepts2'], list) and len(analysis['key_concepts2']) > 0:
                if isinstance(analysis['key_concepts2'][0], list) and len(analysis['key_concepts2'][0]) == 2:
                    # Formatear como "concepto (valor), concepto2 (valor2), ..."
                    concepts_text = ", ".join([f"{c[0]} ({c[1]})" for c in analysis['key_concepts2'][:10]])
                    st.markdown(f"*{concepts_text}*")
                else:
                    # Si no tiene el formato esperado, mostrar como lista simple
                    st.markdown(", ".join(str(c) for c in analysis['key_concepts2'][:10]))
            else:
                st.write(str(analysis['key_concepts2']))
        except Exception as e:
            logger.error(f"Error mostrando key_concepts2: {str(e)}")
            st.error(t.get('error_concepts2', 'Error mostrando conceptos del Texto 2'))
    else:
        st.info(t.get('no_concepts2', 'No hay conceptos disponibles para el Texto 2'))


#################################################################################   
def display_chat_activities(username: str, t: dict):
    """
    Muestra historial de conversaciones del chat
    """
    try:
        # Obtener historial del chat
        chat_history = get_chat_history(
            username=username,
            analysis_type='sidebar',
            limit=50
        )
        
        if not chat_history:
            st.info(t.get('no_chat_history', 'No hay conversaciones registradas'))
            return

        for chat in reversed(chat_history):  # Mostrar las más recientes primero
            try:
                # Convertir timestamp a datetime para formato
                timestamp = datetime.fromisoformat(chat['timestamp'].replace('Z', '+00:00'))
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                with st.expander(
                    f"{t.get('chat_date', 'Fecha de conversación')}: {formatted_date}",
                    expanded=False
                ):
                    if 'messages' in chat and chat['messages']:
                        # Mostrar cada mensaje en la conversación
                        for message in chat['messages']:
                            role = message.get('role', 'unknown')
                            content = message.get('content', '')
                            
                            # Usar el componente de chat de Streamlit
                            with st.chat_message(role):
                                st.markdown(content)
                                
                            # Agregar separador entre mensajes
                            st.divider()
                    else:
                        st.warning(t.get('invalid_chat_format', 'Formato de chat no válido'))
                        
            except Exception as e:
                logger.error(f"Error mostrando conversación: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error mostrando historial del chat: {str(e)}")
        st.error(t.get('error_chat', 'Error al mostrar historial del chat'))
        
#################################################################################        
