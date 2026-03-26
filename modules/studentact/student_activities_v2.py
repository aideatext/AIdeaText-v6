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

from ..database.semantic_mongo_live_db import get_student_semantic_live_analysis
from ..database.semantic_mongo_db import get_student_semantic_analysis
from ..database.discourse_mongo_db import get_student_discourse_analysis

from ..database.chat_mongo_db import get_chat_history
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
            t.get('semantic_live_activities', 'Registros de análisis en vivo'),
            t.get('semantic_activities', 'Registros de mis análisis semánticos'),
            t.get('discourse_activities', 'Registros de mis análisis comparado de textos'),
            t.get('chat_activities', 'Registros de mis conversaciones con el tutor virtual')
        ])

        # Tab de Análisis Semántico
        with tabs[0]:
            display_semantic_live_activities(username, t)
        
        with tabs[1]:
            display_semantic_activities(username, t)

        # Tab de Análisis del Discurso (mantiene nombre interno pero UI muestra "Análisis comparado de textos")
        with tabs[2]:
            display_discourse_activities(username, t)
            
        # Tab de Conversaciones del Chat
        with tabs[3]:
            display_chat_activities(username, t)

    except Exception as e:
        logger.error(f"Error mostrando actividades: {str(e)}")
        st.error(t.get('error_loading_activities', 'Error al cargar las actividades'))


###############################################################################################
def display_semantic_live_activities(username: str, t: dict):
    """Muestra actividades de análisis semántico en vivo (CORREGIDO)"""
    try:
        analyses = get_student_semantic_live_analysis(username)
        
        if not analyses:
            st.info(t.get('no_semantic_live_analyses', 'No hay análisis semánticos en vivo registrados'))
            return

        for i, analysis in enumerate(analyses):
            try:
                # 1. Manejar formato de fecha (Optimizado para objetos datetime nativos)
                # Usamos el objeto directamente si ya es datetime, si es string lo convertimos
                ts_raw = analysis.get('timestamp')
                if isinstance(ts_raw, datetime):
                    timestamp = ts_raw
                elif isinstance(ts_raw, str):
                    timestamp = datetime.fromisoformat(ts_raw.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.now() # Fallback por seguridad
                    
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                # Usamos el ID de MongoDB o el índice como sufijo para asegurar unicidad absoluta
                unique_id = str(analysis.get('_id', i))
                
                with st.expander(f"{t.get('analysis_date', 'Fecha')}: {formatted_date}", expanded=False):
                    # 2. SOLUCIÓN AL ERROR DE KEY DUPLICADO
                    # Agregamos 'key' usando generate_unique_key con un sufijo único
                    st.text_area(
                        t.get('analyzed_text', 'Texto analizado'),
                        value=analysis.get('text', '')[:500], # Aumentado un poco para mejor lectura
                        height=150,
                        disabled=True,
                        key=generate_unique_key("sem_live", "text", username, suffix=unique_id)
                    )
                    
                    # 3. Mostrar gráfico si existe
                    if analysis.get('concept_graph'):
                        try:
                            # Manejar diferentes formatos de imagen
                            graph_data = analysis['concept_graph']
                            if isinstance(graph_data, bytes):
                                image_to_show = graph_data
                            elif isinstance(graph_data, str):
                                # Decodificar si está en base64
                                image_to_show = base64.b64decode(graph_data)
                            
                            st.image(
                                image_to_show,
                                caption=t.get('concept_network', 'Red de Conceptos'),
                                use_container_width=True # Ajustado según tus logs de advertencia
                            )
                        except Exception as img_error:
                            logger.error(f"Error procesando gráfico: {str(img_error)}")
                            st.error(t.get('error_loading_graph', 'Error al cargar el gráfico'))

            except Exception as e:
                logger.error(f"Error procesando análisis individual: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error mostrando análisis semántico en vivo: {str(e)}")
        st.error(t.get('error_semantic_live', 'Error al mostrar análisis semántico en vivo'))


###############################################################################################

def display_semantic_activities(username: str, t: dict):
    """Muestra actividades de análisis semántico (ACTUALIZADO)"""
    try:
        logger.info(f"Recuperando análisis semántico para {username}")
        analyses = get_student_semantic_analysis(username)
        
        if not analyses:
            logger.info("No se encontraron análisis semánticos")
            st.info(t.get('no_semantic_analyses', 'No hay análisis semánticos registrados'))
            return

        logger.info(f"Procesando {len(analyses)} análisis semánticos")
        
        # Usamos enumerate para tener un índice de respaldo
        for i, analysis in enumerate(analyses):
            try:
                # 1. Validación de campos críticos
                if not all(key in analysis for key in ['timestamp', 'concept_graph']):
                    logger.warning(f"Análisis incompleto: {analysis.keys()}")
                    continue
                
                # 2. Manejo de Fecha (Híbrido: Objeto Date o String ISO)
                ts_raw = analysis['timestamp']
                if isinstance(ts_raw, datetime):
                    timestamp = ts_raw
                else:
                    # Por si hay registros antiguos en formato texto
                    timestamp = datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00'))
                
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                # 3. Generar ID único para los widgets internos
                unique_id = str(analysis.get('_id', i))
                
                # Crear expander con el ID único en el key por seguridad
                with st.expander(
                    f"{t.get('analysis_date', 'Fecha')}: {formatted_date}", 
                    expanded=False
                ):
                    # 4. Procesar y mostrar gráfico
                    if analysis.get('concept_graph'):
                        try:
                            image_data = analysis['concept_graph']
                            
                            # Decodificación robusta
                            if isinstance(image_data, bytes):
                                image_bytes = image_data
                            else:
                                image_bytes = base64.b64decode(image_data)
                            
                            # 5. Corrección de 'use_container_width' según tus logs (BugOne.txt)
                            # El log sugiere usar width='stretch' para versiones nuevas
                            st.image(
                                image_bytes,
                                caption=t.get('concept_network', 'Red de Conceptos'),
                                width='stretch' 
                            )
                            
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
    """Muestra actividades de análisis del discurso (Análisis comparado)"""
    try:
        logger.info(f"Recuperando análisis del discurso para {username}")
        analyses = get_student_discourse_analysis(username)
        
        if not analyses:
            logger.info("No se encontraron análisis del discurso")
            st.info(t.get('no_discourse_analyses', 'No hay análisis comparados de textos registrados'))
            return

        logger.info(f"Procesando {len(analyses)} análisis del discurso")
        for i, analysis in enumerate(analyses):
            try:
                if not all(key in analysis for key in ['timestamp']):
                    logger.warning(f"Análisis incompleto: {analysis.keys()}")
                    continue

                # 1. Manejo Híbrido de Fechas
                ts_raw = analysis['timestamp']
                if isinstance(ts_raw, datetime):
                    timestamp = ts_raw
                else:
                    timestamp = datetime.fromisoformat(str(ts_raw).replace('Z', '+00:00'))
                
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                # 2. ID único para los componentes de este bloque
                unique_id = str(analysis.get('_id', i))
                
                with st.expander(f"{t.get('analysis_date', 'Fecha')}: {formatted_date}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    # --- Documento 1 ---
                    with col1:
                        st.subheader(t.get('doc1_title', 'Documento 1'))
                        st.markdown(f"**{t.get('key_concepts', 'Conceptos Clave')}**")
                        
                        if 'key_concepts1' in analysis and analysis['key_concepts1']:
                            # El HTML no requiere Key de Streamlit, pero es bueno que el contenedor sea único
                            concepts_html = f"""
                                <div id="concepts1_{unique_id}" style="display: flex; flex-wrap: nowrap; gap: 8px; padding: 12px; 
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
                        
                        #if 'graph1' in analysis:
                        if analysis.get('graph1'): # Esto verifica que exista y que NO sea None
                            try:
                                # 3. Ajuste de imagen y ancho
                                img1 = analysis['graph1']
                                st.image(img1, width='stretch') 
                            except Exception as e:
                                logger.error(f"Error mostrando graph1: {str(e)}")
                                st.error(t.get('error_loading_graph', 'Error al cargar el gráfico'))

                    # --- Documento 2 ---
                    with col2:
                        st.subheader(t.get('doc2_title', 'Documento 2'))
                        st.markdown(f"**{t.get('key_concepts', 'Conceptos Clave')}**")
                        
                        if 'key_concepts2' in analysis and analysis['key_concepts2']:
                            concepts_html2 = f"""
                                <div id="concepts2_{unique_id}" style="display: flex; flex-wrap: nowrap; gap: 8px; padding: 12px; 
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
                            st.markdown(concepts_html2, unsafe_allow_html=True)
                        
                        #if 'graph2' in analysis:
                        if analysis.get('graph2'): # Esto verifica que exista y que NO sea None
                            try:
                                img2 = analysis['graph2']
                                st.image(img2, width='stretch')
                            except Exception as e:
                                logger.error(f"Error mostrando graph2: {str(e)}")
                                st.error(t.get('error_loading_graph', 'Error al cargar el gráfico'))

                    # Interpretación común para ambos
                    st.info("💡 **Interpretación:** Los nodos más grandes representan mayor frecuencia. El grosor de las líneas indica la fuerza de la relación semántica entre términos.")

            except Exception as e:
                logger.error(f"Error procesando análisis individual: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error mostrando análisis del discurso: {str(e)}")
        st.error(t.get('error_discourse', 'Error al mostrar análisis comparado de textos'))

#################################################################################   

def display_discourse_comparison(analysis: dict, t: dict):
    """
    Muestra la comparación de conceptos clave en análisis del discurso.
    Formato horizontal simplificado con validación robusta de tipos.
    """
    st.subheader(t.get('comparison_results', 'Resultados de la comparación'))
    
    # Verificar si tenemos los conceptos necesarios
    if not analysis.get('key_concepts1'):
        st.info(t.get('no_concepts', 'No hay conceptos disponibles para comparar'))
        return
    
    # Función auxiliar interna para renderizar conceptos de forma segura
    def render_concepts_horizontal(concepts_list):
        if not isinstance(concepts_list, list) or len(concepts_list) == 0:
            return str(concepts_list)
        
        formatted_items = []
        for item in concepts_list[:10]: # Limitamos a los 10 principales
            try:
                # Caso 1: [concepto, valor]
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    val = f"{item[1]:.2f}" if isinstance(item[1], (int, float)) else str(item[1])
                    formatted_items.append(f"**{item[0]}** ({val})")
                # Caso 2: Solo el concepto
                else:
                    formatted_items.append(f"**{str(item)}**")
            except Exception:
                formatted_items.append(str(item))
        
        return " • ".join(formatted_items)

    # --- Renderizado de Conceptos Texto 1 ---
    st.markdown(f"🔹 **{t.get('concepts_text_1', 'Conceptos Texto 1')}:**")
    try:
        concepts1_html = render_concepts_horizontal(analysis['key_concepts1'])
        st.markdown(concepts1_html)
    except Exception as e:
        logger.error(f"Error mostrando key_concepts1: {str(e)}")
        st.error(t.get('error_concepts1', 'Error mostrando conceptos del Texto 1'))
    
    st.divider() # Separador visual sutil

    # --- Renderizado de Conceptos Texto 2 ---
    st.markdown(f"🔸 **{t.get('concepts_text_2', 'Conceptos Texto 2')}:**")
    if analysis.get('key_concepts2'):
        try:
            concepts2_html = render_concepts_horizontal(analysis['key_concepts2'])
            st.markdown(concepts2_html)
        except Exception as e:
            logger.error(f"Error mostrando key_concepts2: {str(e)}")
            st.error(t.get('error_concepts2', 'Error mostrando conceptos del Texto 2'))
    else:
        st.info(t.get('no_concepts2', 'No hay conceptos disponibles para el Texto 2'))


#################################################################################
def clean_chat_content(content: str) -> str:
    """Limpia caracteres especiales del contenido del chat"""
    if not content:
        return content
        
    # Eliminar caracteres de bloque y otros especiales
    special_chars = ["▌", "\u2588", "\u2580", "\u2584", "\u258C", "\u2590"]
    for char in special_chars:
        content = content.replace(char, "")
    
    # Normalizar espacios y saltos de línea
    content = re.sub(r'\s+', ' ', content).strip()
    return content

#################################################################################   
def display_chat_activities(username: str, t: dict):
    """
    Muestra historial de conversaciones del chat con manejo robusto de fechas
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

        # Invertir para mostrar las más recientes primero
        for i, chat in enumerate(reversed(chat_history)):
            try:
                # 1. Manejo Híbrido de Fechas (Objeto vs String)
                ts_raw = chat.get('timestamp')
                if isinstance(ts_raw, datetime):
                    timestamp = ts_raw
                elif isinstance(ts_raw, str):
                    timestamp = datetime.fromisoformat(ts_raw.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.now() # Fallback
                
                formatted_date = timestamp.strftime("%d/%m/%Y %H:%M:%S")
                
                # 2. ID único para el expander (previene cierres inesperados al recargar)
                unique_id = str(chat.get('_id', i))
                
                with st.expander(
                    f"💬 {t.get('chat_date', 'Conversación')}: {formatted_date}",
                    expanded=False
                ):
                    if 'messages' in chat and chat['messages']:
                        # 3. Mostrar mensajes de forma limpia
                        for msg_idx, message in enumerate(chat['messages']):
                            role = message.get('role', 'unknown')
                            # Aseguramos que el contenido sea string y esté limpio
                            content = str(message.get('content', ''))
                            
                            # Intentar usar clean_chat_content si está disponible en el scope
                            try:
                                content = clean_chat_content(content)
                            except NameError:
                                pass 
                            
                            with st.chat_message(role):
                                st.markdown(content)
                            
                            # Solo poner divisor si no es el último mensaje
                            if msg_idx < len(chat['messages']) - 1:
                                st.divider()
                    else:
                        st.warning(t.get('invalid_chat_format', 'Formato de chat no válido'))
                        
            except Exception as e:
                logger.error(f"Error mostrando conversación individual: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error mostrando historial del chat: {str(e)}")
        st.error(t.get('error_chat', 'Error al mostrar historial del chat'))

#################################################################################    



