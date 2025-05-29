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
# from ..database.morphosintax_mongo_db import get_student_morphosyntax_analysis
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
            #t.get('current_situation_activities', 'Registros de la función: Mi Situación Actual'),
            #t.get('morpho_activities', 'Registros de mis análisis morfosintácticos'),
            t.get('semantic_activities', 'Registros de mis análisis semánticos'),
            t.get('discourse_activities', 'Registros de mis análisis comparado de textos'),
            t.get('chat_activities', 'Registros de mis conversaciones con el tutor virtual')
        ])

        # Tab de Situación Actual
        #with tabs[0]:
        #    display_current_situation_activities(username, t)
        
        # Tab de Análisis Morfosintáctico
        #with tabs[1]:
        #    display_morphosyntax_activities(username, t)

        # Tab de Análisis Semántico
        with tabs[0]:
            display_semantic_activities(username, t)

        # Tab de Análisis del Discurso (mantiene nombre interno pero UI muestra "Análisis comparado de textos")
        with tabs[1]:
            display_discourse_activities(username, t)
            
        # Tab de Conversaciones del Chat
        with tabs[2]:
            display_chat_activities(username, t)

    except Exception as e:
        logger.error(f"Error mostrando actividades: {str(e)}")
        st.error(t.get('error_loading_activities', 'Error al cargar las actividades'))


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
