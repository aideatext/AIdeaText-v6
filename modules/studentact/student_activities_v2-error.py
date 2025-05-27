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
from ..database.morphosintax_mongo_db import get_student_morphosyntax_analysis
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

###################################################################################
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

###################################################################################
def display_semantic_activities(username: str, t: dict):
    """Muestra actividades de análisis semántico"""
    try:
        analyses = get_student_semantic_analysis(username)
        if not analyses:
            st.info(t.get('no_semantic_analyses', 'No hay análisis semánticos registrados'))
            return

        for analysis in analyses:
            with st.expander(
                f"{t.get('analysis_date', 'Fecha')}: {analysis['timestamp']}", 
                expanded=False
            ):
                
                # Mostrar conceptos clave
                if 'key_concepts' in analysis:
                    st.subheader(t.get('key_concepts', 'Conceptos clave'))
                    df = pd.DataFrame(
                        analysis['key_concepts'],
                        columns=['Concepto', 'Frecuencia']
                    )
                    st.dataframe(df)

                # Mostrar gráfico de conceptos
                if 'concept_graph' in analysis and analysis['concept_graph']:
                    st.subheader(t.get('concept_graph', 'Grafo de conceptos'))
                    image_bytes = base64.b64decode(analysis['concept_graph'])
                    st.image(image_bytes)

    except Exception as e:
        logger.error(f"Error mostrando análisis semántico: {str(e)}")
        st.error(t.get('error_semantic', 'Error al mostrar análisis semántico'))

###################################################################################

def display_discourse_activities(username: str, t: dict):
    """Muestra actividades de análisis del discurso"""
    try:
        analyses = get_student_discourse_analysis(username)
        if not analyses:
            st.info(t.get('no_discourse_analyses', 'No hay análisis del discurso registrados'))
            return

        for analysis in analyses:
            with st.expander(
                f"{t.get('analysis_date', 'Fecha')}: {analysis['timestamp']}", 
                expanded=False
            ):

                # Mostrar conceptos clave
                if 'key_concepts1' in analysis and 'key_concepts2' in analysis:
                    st.subheader(t.get('comparison_results', 'Resultados de la comparación'))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**{t.get('concepts_text_1', 'Conceptos Texto 1')}**")
                        df1 = pd.DataFrame(
                            analysis['key_concepts1'],
                            columns=['Concepto', 'Frecuencia']
                        )
                        st.dataframe(df1)
                    
                    with col2:
                        st.markdown(f"**{t.get('concepts_text_2', 'Conceptos Texto 2')}**")
                        df2 = pd.DataFrame(
                            analysis['key_concepts2'],
                            columns=['Concepto', 'Frecuencia']
                        )
                        st.dataframe(df2)

                # Mostrar gráficos
                if all(key in analysis for key in ['graph1', 'graph2']):
                    st.subheader(t.get('visualizations', 'Visualizaciones'))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**{t.get('graph_text_1', 'Grafo Texto 1')}**")
                        if analysis['graph1']:
                            image_bytes = base64.b64decode(analysis['graph1'])
                            st.image(image_bytes)
                    
                    with col2:
                        st.markdown(f"**{t.get('graph_text_2', 'Grafo Texto 2')}**")
                        if analysis['graph2']:
                            image_bytes = base64.b64decode(analysis['graph2'])
                            st.image(image_bytes)

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