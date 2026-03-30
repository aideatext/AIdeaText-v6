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
from datetime import datetime
from spacy import displacy
import random
import base64
import seaborn as sns
import logging

# Importaciones de la base de datos
from ..database.backUp.morphosintax_mongo_db import get_student_morphosyntax_analysis
from ..database.semantic_mongo_db import get_student_semantic_analysis
from ..database.discourse_mongo_db import get_student_discourse_analysis
from ..database.chat_mongo_db import get_chat_history

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
        st.header(t.get('activities_title', 'Mis Actividades'))

        # Tabs para diferentes tipos de análisis
        tabs = st.tabs([
            t.get('morpho_activities', 'Análisis Morfosintáctico'),
            t.get('semantic_activities', 'Análisis Semántico'),
            t.get('discourse_activities', 'Análisis del Discurso'),
            t.get('chat_activities', 'Conversaciones con el Asistente')
        ])

        # Tab de Análisis Morfosintáctico
        with tabs[0]:
            display_morphosyntax_activities(username, t)

        # Tab de Análisis Semántico
        with tabs[1]:
            display_semantic_activities(username, t)

        # Tab de Análisis del Discurso
        with tabs[2]:
            display_discourse_activities(username, t)

        # Tab de Conversaciones del Chat
        with tabs[3]:
            display_chat_activities(username, t)

    except Exception as e:
        logger.error(f"Error mostrando actividades: {str(e)}")
        st.error(t.get('error_loading_activities', 'Error al cargar las actividades'))


###############################################################################################
def display_morphosyntax_activities(username: str, t: dict):
    """Muestra actividades de análisis morfosintáctico"""
    try:
        analyses = get_student_morphosyntax_analysis(username)
        if not analyses:
            st.info(t.get('no_morpho_analyses', 'No hay análisis morfosintácticos registrados'))
            return

        for analysis in analyses:
            with st.expander(
                f"{t.get('analysis_date', 'Fecha')}: {analysis['timestamp']}", 
                expanded=False
            ):
                st.text(f"{t.get('analyzed_text', 'Texto analizado')}:")
                st.write(analysis['text'])
                
                if 'arc_diagrams' in analysis:
                    st.subheader(t.get('syntactic_diagrams', 'Diagramas sintácticos'))
                    for diagram in analysis['arc_diagrams']:
                        st.write(diagram, unsafe_allow_html=True)

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
                # Verificar campos mínimos necesarios
                if not all(key in analysis for key in ['timestamp', 'concept_graph']):
                    logger.warning(f"Análisis incompleto: {analysis.keys()}")
                    continue

                # Formatear fecha
                timestamp = datetime.fromisoformat(analysis['timestamp'].replace('Z', '+00:00'))
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                with st.expander(f"{t.get('analysis_date', 'Fecha')}: {formatted_date}", expanded=False):
                    if analysis['concept_graph']:
                        logger.debug("Decodificando gráfico de conceptos")
                        try:
                            image_bytes = base64.b64decode(analysis['concept_graph'])
                            st.image(image_bytes, use_column_width=True)
                            logger.debug("Gráfico mostrado exitosamente")
                        except Exception as img_error:
                            logger.error(f"Error decodificando imagen: {str(img_error)}")
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
    """Muestra actividades de análisis del discurso"""
    try:
        logger.info(f"Recuperando análisis del discurso para {username}")
        analyses = get_student_discourse_analysis(username)
        
        if not analyses:
            logger.info("No se encontraron análisis del discurso")
            st.info(t.get('no_discourse_analyses', 'No hay análisis del discurso registrados'))
            return

        logger.info(f"Procesando {len(analyses)} análisis del discurso")
        for analysis in analyses:
            try:
                # Verificar campos mínimos necesarios
                if not all(key in analysis for key in ['timestamp', 'combined_graph']):
                    logger.warning(f"Análisis incompleto: {analysis.keys()}")
                    continue

                # Formatear fecha
                timestamp = datetime.fromisoformat(analysis['timestamp'].replace('Z', '+00:00'))
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                with st.expander(f"{t.get('analysis_date', 'Fecha')}: {formatted_date}", expanded=False):
                    if analysis['combined_graph']:
                        logger.debug("Decodificando gráfico combinado")
                        try:
                            image_bytes = base64.b64decode(analysis['combined_graph'])
                            st.image(image_bytes, use_column_width=True)
                            logger.debug("Gráfico mostrado exitosamente")
                        except Exception as img_error:
                            logger.error(f"Error decodificando imagen: {str(img_error)}")
                            st.error(t.get('error_loading_graph', 'Error al cargar el gráfico'))
                    else:
                        st.info(t.get('no_visualization', 'No hay visualización comparativa disponible'))

            except Exception as e:
                logger.error(f"Error procesando análisis individual: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error mostrando análisis del discurso: {str(e)}")
        st.error(t.get('error_discourse', 'Error al mostrar análisis del discurso'))

#################################################################################        
def display_discourse_comparison(analysis: dict, t: dict):
    """Muestra la comparación de análisis del discurso"""
    st.subheader(t.get('comparison_results', 'Resultados de la comparación'))
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**{t.get('concepts_text_1', 'Conceptos Texto 1')}**")
        df1 = pd.DataFrame(analysis['key_concepts1'])
        st.dataframe(df1)
    
    with col2:
        st.markdown(f"**{t.get('concepts_text_2', 'Conceptos Texto 2')}**")
        df2 = pd.DataFrame(analysis['key_concepts2'])
        st.dataframe(df2)

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









'''
##########versión 25-9-2024---02:30 ################ OK (username)####################

def display_student_progress(username, lang_code, t, student_data):
    st.title(f"{t.get('progress_of', 'Progreso de')} {username}")

    if not student_data or len(student_data.get('entries', [])) == 0:
        st.warning(t.get("no_data_warning", "No se encontraron datos para este estudiante."))
        st.info(t.get("try_analysis", "Intenta realizar algunos análisis de texto primero."))
        return

    with st.expander(t.get("activities_summary", "Resumen de Actividades"), expanded=True):
        total_entries = len(student_data['entries'])
        st.write(f"{t.get('total_analyses', 'Total de análisis realizados')}: {total_entries}")

        # Gráfico de tipos de análisis
        analysis_types = [entry['analysis_type'] for entry in student_data['entries']]
        analysis_counts = pd.Series(analysis_types).value_counts()
        fig, ax = plt.subplots()
        analysis_counts.plot(kind='bar', ax=ax)
        ax.set_title(t.get("analysis_types_chart", "Tipos de análisis realizados"))
        ax.set_xlabel(t.get("analysis_type", "Tipo de análisis"))
        ax.set_ylabel(t.get("count", "Cantidad"))
        st.pyplot(fig)

    # Mostrar los últimos análisis morfosintácticos
    with st.expander(t.get("morphosyntax_history", "Histórico de Análisis Morfosintácticos")):
        morphosyntax_entries = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'morphosyntax']
        for entry in morphosyntax_entries[:5]:  # Mostrar los últimos 5
            st.subheader(f"{t.get('analysis_of', 'Análisis del')} {entry['timestamp']}")
            if 'arc_diagrams' in entry and entry['arc_diagrams']:
                st.components.v1.html(entry['arc_diagrams'][0], height=300, scrolling=True)

    # Añadir secciones similares para análisis semánticos y discursivos si es necesario

    # Mostrar el historial de chat
    with st.expander(t.get("chat_history", "Historial de Chat")):
        if 'chat_history' in student_data:
            for chat in student_data['chat_history'][:5]:  # Mostrar las últimas 5 conversaciones
                st.subheader(f"{t.get('chat_from', 'Chat del')} {chat['timestamp']}")
                for message in chat['messages']:
                    st.write(f"{message['role'].capitalize()}: {message['content']}")
                st.write("---")
        else:
            st.write(t.get("no_chat_history", "No hay historial de chat disponible."))


##########versión 24-9-2024---17:30 ################ OK FROM--V2 de def get_student_data(username)####################

def display_student_progress(username, lang_code, t, student_data):
    if not student_data or len(student_data['entries']) == 0:
        st.warning(t.get("no_data_warning", "No se encontraron datos para este estudiante."))
        st.info(t.get("try_analysis", "Intenta realizar algunos análisis de texto primero."))
        return

    st.title(f"{t.get('progress_of', 'Progreso de')} {username}")

    with st.expander(t.get("activities_summary", "Resumen de Actividades y Progreso"), expanded=True):
        total_entries = len(student_data['entries'])
        st.write(f"{t.get('total_analyses', 'Total de análisis realizados')}: {total_entries}")

        # Gráfico de tipos de análisis
        analysis_types = [entry['analysis_type'] for entry in student_data['entries']]
        analysis_counts = pd.Series(analysis_types).value_counts()

        fig, ax = plt.subplots(figsize=(8, 4))
        analysis_counts.plot(kind='bar', ax=ax)
        ax.set_title(t.get("analysis_types_chart", "Tipos de análisis realizados"))
        ax.set_xlabel(t.get("analysis_type", "Tipo de análisis"))
        ax.set_ylabel(t.get("count", "Cantidad"))
        st.pyplot(fig)

    # Histórico de Análisis Morfosintácticos
    with st.expander(t.get("morphosyntax_history", "Histórico de Análisis Morfosintácticos")):
        morphosyntax_entries = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'morphosyntax']
        if not morphosyntax_entries:
            st.warning("No se encontraron análisis morfosintácticos.")
        for entry in morphosyntax_entries:
            st.subheader(f"{t.get('analysis_of', 'Análisis del')} {entry['timestamp']}")
            if 'arc_diagrams' in entry and entry['arc_diagrams']:
                try:
                    st.write(entry['arc_diagrams'][0], unsafe_allow_html=True)
                except Exception as e:
                    logger.error(f"Error al mostrar diagrama de arco: {str(e)}")
                    st.error("Error al mostrar el diagrama de arco.")
            else:
                st.write(t.get("no_arc_diagram", "No se encontró diagrama de arco para este análisis."))

    # Histórico de Análisis Semánticos
    with st.expander(t.get("semantic_history", "Histórico de Análisis Semánticos")):
        semantic_entries = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'semantic']
        if not semantic_entries:
            st.warning("No se encontraron análisis semánticos.")
        for entry in semantic_entries:
            st.subheader(f"{t.get('analysis_of', 'Análisis del')} {entry['timestamp']}")
            if 'key_concepts' in entry:
                st.write(t.get("key_concepts", "Conceptos clave:"))
                concepts_str = " | ".join([f"{concept} ({frequency:.2f})" for concept, frequency in entry['key_concepts']])
                st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{concepts_str}</div>", unsafe_allow_html=True)
            if 'graph' in entry:
                try:
                    img_bytes = base64.b64decode(entry['graph'])
                    st.image(img_bytes, caption=t.get("conceptual_relations_graph", "Gráfico de relaciones conceptuales"))
                except Exception as e:
                    logger.error(f"Error al mostrar gráfico semántico: {str(e)}")
                    st.error(t.get("graph_display_error", f"No se pudo mostrar el gráfico: {str(e)}"))

    # Histórico de Análisis Discursivos
    with st.expander(t.get("discourse_history", "Histórico de Análisis Discursivos")):
        discourse_entries = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'discourse']
        for entry in discourse_entries:
            st.subheader(f"{t.get('analysis_of', 'Análisis del')} {entry['timestamp']}")
            for i in [1, 2]:
                if f'key_concepts{i}' in entry:
                    st.write(f"{t.get('key_concepts', 'Conceptos clave')} {t.get('document', 'documento')} {i}:")
                    concepts_str = " | ".join([f"{concept} ({frequency:.2f})" for concept, frequency in entry[f'key_concepts{i}']])
                    st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{concepts_str}</div>", unsafe_allow_html=True)
            try:
                if 'combined_graph' in entry and entry['combined_graph']:
                    img_bytes = base64.b64decode(entry['combined_graph'])
                    st.image(img_bytes, caption=t.get("combined_graph", "Gráfico combinado"))
                elif 'graph1' in entry and 'graph2' in entry:
                    col1, col2 = st.columns(2)
                    with col1:
                        if entry['graph1']:
                            img_bytes1 = base64.b64decode(entry['graph1'])
                            st.image(img_bytes1, caption=t.get("graph_doc1", "Gráfico documento 1"))
                    with col2:
                        if entry['graph2']:
                            img_bytes2 = base64.b64decode(entry['graph2'])
                            st.image(img_bytes2, caption=t.get("graph_doc2", "Gráfico documento 2"))
            except Exception as e:
                st.error(t.get("graph_display_error", f"No se pudieron mostrar los gráficos: {str(e)}"))

    # Histórico de Conversaciones con el ChatBot
    with st.expander(t.get("chatbot_history", "Histórico de Conversaciones con el ChatBot")):
        if 'chat_history' in student_data and student_data['chat_history']:
            for i, chat in enumerate(student_data['chat_history']):
                st.subheader(f"{t.get('conversation', 'Conversación')} {i+1} - {chat['timestamp']}")
                for message in chat['messages']:
                    if message['role'] == 'user':
                        st.write(f"{t.get('user', 'Usuario')}: {message['content']}")
                    else:
                        st.write(f"{t.get('assistant', 'Asistente')}: {message['content']}")
                st.write("---")
        else:
            st.write(t.get("no_chat_history", "No se encontraron conversaciones con el ChatBot."))

    # Añadir logs para depuración
    if st.checkbox(t.get("show_debug_data", "Mostrar datos de depuración")):
        st.write(t.get("student_debug_data", "Datos del estudiante (para depuración):"))
        st.json(student_data)

        # Mostrar conteo de tipos de análisis
        analysis_types = [entry['analysis_type'] for entry in student_data['entries']]
        type_counts = {t: analysis_types.count(t) for t in set(analysis_types)}
        st.write("Conteo de tipos de análisis:")
        st.write(type_counts)


#############################--- Update 16:00 24-9 #########################################
def display_student_progress(username, lang_code, t, student_data):
    try:
        st.subheader(t.get('student_activities', 'Student Activitie'))

        if not student_data or all(len(student_data.get(key, [])) == 0 for key in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses']):
            st.warning(t.get('no_data_warning', 'No analysis data found for this student.'))
            return

        # Resumen de actividades
        total_analyses = sum(len(student_data.get(key, [])) for key in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses'])
        st.write(f"{t.get('total_analyses', 'Total analyses performed')}: {total_analyses}")

        # Gráfico de tipos de análisis
        analysis_counts = {
            t.get('morpho_analyses', 'Morphosyntactic Analyses'): len(student_data.get('morphosyntax_analyses', [])),
            t.get('semantic_analyses', 'Semantic Analyses'): len(student_data.get('semantic_analyses', [])),
            t.get('discourse_analyses', 'Discourse Analyses'): len(student_data.get('discourse_analyses', []))
        }
        # Configurar el estilo de seaborn para un aspecto más atractivo
        sns.set_style("whitegrid")

        # Crear una figura más pequeña
        fig, ax = plt.subplots(figsize=(6, 4))

        # Usar colores más atractivos
        colors = ['#ff9999', '#66b3ff', '#99ff99']

        # Crear el gráfico de barras
        bars = ax.bar(analysis_counts.keys(), analysis_counts.values(), color=colors)

        # Añadir etiquetas de valor encima de cada barra
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height}',
                    ha='center', va='bottom')

        # Configurar el título y las etiquetas
        ax.set_title(t.get('analysis_types_chart', 'Types of analyses performed'), fontsize=12)
        ax.set_ylabel(t.get('count', 'Count'), fontsize=10)

        # Rotar las etiquetas del eje x para mejor legibilidad
        plt.xticks(rotation=45, ha='right')

        # Ajustar el diseño para que todo quepa
        plt.tight_layout()

        # Mostrar el gráfico en Streamlit
        st.pyplot(fig)

        # Mostrar los últimos análisis
        for analysis_type in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses']:
            with st.expander(t.get(f'{analysis_type}_expander', f'{analysis_type.capitalize()} History')):
                for analysis in student_data.get(analysis_type, [])[:5]:  # Mostrar los últimos 5
                    st.subheader(f"{t.get('analysis_from', 'Analysis from')} {analysis.get('timestamp', 'N/A')}")
                    if analysis_type == 'morphosyntax_analyses':
                        if 'arc_diagrams' in analysis:
                            st.write(analysis['arc_diagrams'][0], unsafe_allow_html=True)
                    elif analysis_type == 'semantic_analyses':
                        if 'key_concepts' in analysis:
                            st.write(t.get('key_concepts', 'Key concepts'))
                            st.write(", ".join([f"{concept} ({freq:.2f})" for concept, freq in analysis['key_concepts']]))
                        if 'graph' in analysis:
                            st.image(base64.b64decode(analysis['graph']))
                    elif analysis_type == 'discourse_analyses':
                        for i in [1, 2]:
                            if f'key_concepts{i}' in analysis:
                                st.write(f"{t.get('key_concepts', 'Key concepts')} {t.get('document', 'Document')} {i}")
                                st.write(", ".join([f"{concept} ({freq:.2f})" for concept, freq in analysis[f'key_concepts{i}']]))
                        if 'combined_graph' in analysis:
                            st.image(base64.b64decode(analysis['combined_graph']))

        # Mostrar el historial de chat
        with st.expander(t.get('chat_history_expander', 'Chat History')):
            for chat in student_data.get('chat_history', [])[:5]:  # Mostrar las últimas 5 conversaciones
                st.subheader(f"{t.get('chat_from', 'Chat from')} {chat.get('timestamp', 'N/A')}")
                for message in chat.get('messages', []):
                    st.write(f"{message.get('role', 'Unknown').capitalize()}: {message.get('content', 'No content')}")
                st.write("---")

    except Exception as e:
        logger.error(f"Error in display_student_progress: {str(e)}", exc_info=True)
        st.error(t.get('error_loading_progress', 'Error loading student progress. Please try again later.'))



























#####################################################################
def display_student_progress(username, lang_code, t, student_data):
    st.subheader(t['student_progress'])

    if not student_data or all(len(student_data[key]) == 0 for key in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses']):
        st.warning(t['no_data_warning'])
        return

    # Resumen de actividades
    total_analyses = sum(len(student_data[key]) for key in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses'])
    st.write(f"{t['total_analyses']}: {total_analyses}")

    # Gráfico de tipos de análisis
    analysis_counts = {
        t['morpho_analyses']: len(student_data['morphosyntax_analyses']),
        t['semantic_analyses']: len(student_data['semantic_analyses']),
        t['discourse_analyses']: len(student_data['discourse_analyses'])
    }
    fig, ax = plt.subplots()
    ax.bar(analysis_counts.keys(), analysis_counts.values())
    ax.set_title(t['analysis_types_chart'])
    st.pyplot(fig)

    # Mostrar los últimos análisis
    for analysis_type in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses']:
        with st.expander(t[f'{analysis_type}_expander']):
            for analysis in student_data[analysis_type][:5]:  # Mostrar los últimos 5
                st.subheader(f"{t['analysis_from']} {analysis['timestamp']}")
                if analysis_type == 'morphosyntax_analyses':
                    if 'arc_diagrams' in analysis:
                        st.write(analysis['arc_diagrams'][0], unsafe_allow_html=True)
                elif analysis_type == 'semantic_analyses':
                    if 'key_concepts' in analysis:
                        st.write(t['key_concepts'])
                        st.write(", ".join([f"{concept} ({freq:.2f})" for concept, freq in analysis['key_concepts']]))
                    if 'graph' in analysis:
                        st.image(base64.b64decode(analysis['graph']))
                elif analysis_type == 'discourse_analyses':
                    for i in [1, 2]:
                        if f'key_concepts{i}' in analysis:
                            st.write(f"{t['key_concepts']} {t['document']} {i}")
                            st.write(", ".join([f"{concept} ({freq:.2f})" for concept, freq in analysis[f'key_concepts{i}']]))
                    if 'combined_graph' in analysis:
                        st.image(base64.b64decode(analysis['combined_graph']))

    # Mostrar el historial de chat
    with st.expander(t['chat_history_expander']):
        for chat in student_data['chat_history'][:5]:  # Mostrar las últimas 5 conversaciones
            st.subheader(f"{t['chat_from']} {chat['timestamp']}")
            for message in chat['messages']:
                st.write(f"{message['role'].capitalize()}: {message['content']}")
            st.write("---")



def display_student_progress(username, lang_code, t, student_data):
    st.subheader(t['student_activities'])

    if not student_data or all(len(student_data[key]) == 0 for key in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses']):
        st.warning(t['no_data_warning'])
        return

    # Resumen de actividades
    total_analyses = sum(len(student_data[key]) for key in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses'])
    st.write(f"{t['total_analyses']}: {total_analyses}")

    # Gráfico de tipos de análisis
    analysis_counts = {
        t['morphological_analysis']: len(student_data['morphosyntax_analyses']),
        t['semantic_analyses']: len(student_data['semantic_analyses']),
        t['discourse_analyses']: len(student_data['discourse_analyses'])
    }
    fig, ax = plt.subplots()
    ax.bar(analysis_counts.keys(), analysis_counts.values())
    ax.set_title(t['analysis_types_chart'])
    st.pyplot(fig)

    # Mostrar los últimos análisis
    for analysis_type in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses']:
        with st.expander(t[f'{analysis_type}_expander']):
            for analysis in student_data[analysis_type][:5]:  # Mostrar los últimos 5
                st.subheader(f"{t['analysis_from']} {analysis['timestamp']}")
                if analysis_type == 'morphosyntax_analyses':
                    if 'arc_diagrams' in analysis:
                        st.write(analysis['arc_diagrams'][0], unsafe_allow_html=True)
                elif analysis_type == 'semantic_analyses':
                    if 'key_concepts' in analysis:
                        st.write(t['key_concepts'])
                        st.write(", ".join([f"{concept} ({freq:.2f})" for concept, freq in analysis['key_concepts']]))
                    if 'graph' in analysis:
                        st.image(base64.b64decode(analysis['graph']))
                elif analysis_type == 'discourse_analyses':
                    for i in [1, 2]:
                        if f'key_concepts{i}' in analysis:
                            st.write(f"{t['key_concepts']} {t['document']} {i}")
                            st.write(", ".join([f"{concept} ({freq:.2f})" for concept, freq in analysis[f'key_concepts{i}']]))
                    if 'combined_graph' in analysis:
                        st.image(base64.b64decode(analysis['combined_graph']))

    # Mostrar el historial de chat
    with st.expander(t['chat_history_expander']):
        for chat in student_data['chat_history'][:5]:  # Mostrar las últimas 5 conversaciones
            st.subheader(f"{t['chat_from']} {chat['timestamp']}")
            for message in chat['messages']:
                st.write(f"{message['role'].capitalize()}: {message['content']}")
            st.write("---")




def display_student_progress(username, lang_code, t, student_data):
    st.subheader(t['student_activities'])

    if not student_data or all(len(student_data[key]) == 0 for key in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses']):
        st.warning(t['no_data_warning'])
        return

    # Resumen de actividades
    total_analyses = sum(len(student_data[key]) for key in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses'])
    st.write(f"{t['total_analyses']}: {total_analyses}")

    # Gráfico de tipos de análisis
    analysis_counts = {
        t['morphological_analysis']: len(student_data['morphosyntax_analyses']),
        t['semantic_analyses']: len(student_data['semantic_analyses']),
        t['discourse_analyses']: len(student_data['discourse_analyses'])
    }
    fig, ax = plt.subplots()
    ax.bar(analysis_counts.keys(), analysis_counts.values())
    ax.set_title(t['analysis_types_chart'])
    st.pyplot(fig)

    # Mostrar los últimos análisis
    for analysis_type in ['morphosyntax_analyses', 'semantic_analyses', 'discourse_analyses']:
        with st.expander(t[f'{analysis_type}_expander']):
            for analysis in student_data[analysis_type][:5]:  # Mostrar los últimos 5
                st.subheader(f"{t['analysis_from']} {analysis['timestamp']}")
                if analysis_type == 'morphosyntax_analyses':
                    if 'arc_diagrams' in analysis:
                        st.write(analysis['arc_diagrams'][0], unsafe_allow_html=True)
                elif analysis_type == 'semantic_analyses':
                    if 'key_concepts' in analysis:
                        st.write(t['key_concepts'])
                        st.write(", ".join([f"{concept} ({freq:.2f})" for concept, freq in analysis['key_concepts']]))
                    if 'graph' in analysis:
                        st.image(base64.b64decode(analysis['graph']))
                elif analysis_type == 'discourse_analyses':
                    for i in [1, 2]:
                        if f'key_concepts{i}' in analysis:
                            st.write(f"{t['key_concepts']} {t['document']} {i}")
                            st.write(", ".join([f"{concept} ({freq:.2f})" for concept, freq in analysis[f'key_concepts{i}']]))
                    if 'combined_graph' in analysis:
                        st.image(base64.b64decode(analysis['combined_graph']))

    # Mostrar el historial de chat
    with st.expander(t['chat_history_expander']):
        for chat in student_data['chat_history'][:5]:  # Mostrar las últimas 5 conversaciones
            st.subheader(f"{t['chat_from']} {chat['timestamp']}")
            for message in chat['messages']:
                st.write(f"{message['role'].capitalize()}: {message['content']}")
            st.write("---")




def display_student_progress(username, lang_code, t):
    st.subheader(t['student_activities'])
    st.write(f"{t['activities_message']} {username}")

    # Aquí puedes agregar más contenido estático o placeholder
    st.info(t['activities_placeholder'])

    # Si necesitas mostrar algún dato, puedes usar datos de ejemplo o placeholders
    col1, col2, col3 = st.columns(3)
    col1.metric(t['morpho_analyses'], "5")  # Ejemplo de dato
    col2.metric(t['semantic_analyses'], "3")  # Ejemplo de dato
    col3.metric(t['discourse_analyses'], "2")  # Ejemplo de dato



def display_student_progress(username, lang_code, t):
    st.title(f"Actividades de {username}")

    # Obtener todos los datos del estudiante
    student_data = get_student_data(username)

    if not student_data or len(student_data.get('entries', [])) == 0:
        st.warning("No se encontraron datos de análisis para este estudiante.")
        st.info("Intenta realizar algunos análisis de texto primero.")
        return

    # Resumen de actividades
    with st.expander("Resumen de Actividades", expanded=True):
        total_entries = len(student_data['entries'])
        st.write(f"Total de análisis realizados: {total_entries}")

        # Gráfico de tipos de análisis
        analysis_types = [entry['analysis_type'] for entry in student_data['entries']]
        analysis_counts = pd.Series(analysis_types).value_counts()
        fig, ax = plt.subplots()
        analysis_counts.plot(kind='bar', ax=ax)
        ax.set_title("Tipos de análisis realizados")
        ax.set_xlabel("Tipo de análisis")
        ax.set_ylabel("Cantidad")
        st.pyplot(fig)

    # Histórico de Análisis Morfosintácticos
    with st.expander("Histórico de Análisis Morfosintácticos"):
        morpho_analyses = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'morphosyntax']
        for analysis in morpho_analyses[:5]:  # Mostrar los últimos 5
            st.subheader(f"Análisis del {analysis['timestamp']}")
            if 'arc_diagrams' in analysis:
                st.write(analysis['arc_diagrams'][0], unsafe_allow_html=True)

    # Histórico de Análisis Semánticos
    with st.expander("Histórico de Análisis Semánticos"):
        semantic_analyses = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'semantic']
        for analysis in semantic_analyses[:5]:  # Mostrar los últimos 5
            st.subheader(f"Análisis del {analysis['timestamp']}")
            if 'key_concepts' in analysis:
                concepts_str = " | ".join([f"{concept} ({frequency:.2f})" for concept, frequency in analysis['key_concepts']])
                st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{concepts_str}</div>", unsafe_allow_html=True)
            if 'graph' in analysis:
                try:
                    img_bytes = base64.b64decode(analysis['graph'])
                    st.image(img_bytes, caption="Gráfico de relaciones conceptuales")
                except Exception as e:
                    st.error(f"No se pudo mostrar el gráfico: {str(e)}")

    # Histórico de Análisis Discursivos
    with st.expander("Histórico de Análisis Discursivos"):
        discourse_analyses = [entry for entry in student_data['entries'] if entry['analysis_type'] == 'discourse']
        for analysis in discourse_analyses[:5]:  # Mostrar los últimos 5
            st.subheader(f"Análisis del {analysis['timestamp']}")
            for i in [1, 2]:
                if f'key_concepts{i}' in analysis:
                    concepts_str = " | ".join([f"{concept} ({frequency:.2f})" for concept, frequency in analysis[f'key_concepts{i}']])
                    st.write(f"Conceptos clave del documento {i}:")
                    st.markdown(f"<div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px;'>{concepts_str}</div>", unsafe_allow_html=True)
            if 'combined_graph' in analysis:
                try:
                    img_bytes = base64.b64decode(analysis['combined_graph'])
                    st.image(img_bytes)
                except Exception as e:
                    st.error(f"No se pudo mostrar el gráfico combinado: {str(e)}")

    # Histórico de Conversaciones con el ChatBot
    with st.expander("Histórico de Conversaciones con el ChatBot"):
        if 'chat_history' in student_data:
            for i, chat in enumerate(student_data['chat_history'][:5]):  # Mostrar las últimas 5 conversaciones
                st.subheader(f"Conversación {i+1} - {chat['timestamp']}")
                for message in chat['messages']:
                    st.write(f"{message['role'].capitalize()}: {message['content']}")
                st.write("---")
        else:
            st.write("No se encontraron conversaciones con el ChatBot.")

    # Opción para mostrar datos de depuración
    if st.checkbox("Mostrar datos de depuración"):
        st.write("Datos del estudiante (para depuración):")
        st.json(student_data)

'''