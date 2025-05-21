#modules/studentact/student_activities.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import base64
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx import Document
from odf.opendocument import OpenDocumentText
from odf.text import P
from datetime import datetime, timedelta
import pytz
import logging

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Importaciones locales
try:
    from ..database.morphosintax_mongo_db import get_student_morphosyntax_data
    from ..database.semantic_mongo_db import get_student_semantic_data
    from ..database.discourse_mongo_db import get_student_discourse_data
    
    from ..database.chat_mongo_db import get_chat_history
    
    logger.info("Importaciones locales exitosas")
except ImportError as e:
    logger.error(f"Error en las importaciones locales: {e}")

def display_student_progress(username, lang_code, t):
    logger.debug(f"Iniciando display_student_progress para {username}")

    st.title(f"{t.get('progress_of', 'Progreso de')} {username}")

    # Obtener los datos del estudiante
    student_data = get_student_morphosyntax_data(username)

    if not student_data or len(student_data.get('entries', [])) == 0:
        logger.warning(f"No se encontraron datos para el estudiante {username}")
        st.warning(t.get("no_data_warning", "No se encontraron datos para este estudiante."))
        st.info(t.get("try_analysis", "Intenta realizar algunos análisis de texto primero."))
        return

    logger.debug(f"Datos del estudiante obtenidos: {len(student_data['entries'])} entradas")

    # Resumen de actividades
    with st.expander(t.get("activities_summary", "Resumen de Actividades"), expanded=True):
        total_entries = len(student_data['entries'])
        st.write(f"{t.get('total_analyses', 'Total de análisis realizados')}: {total_entries}")

        # Gráfico de tipos de análisis
        try:
            analysis_types = [entry.get('analysis_type', 'unknown') for entry in student_data['entries']]
            analysis_counts = pd.Series(analysis_types).value_counts()
            fig, ax = plt.subplots()
            sns.barplot(x=analysis_counts.index, y=analysis_counts.values, ax=ax)
            ax.set_title(t.get("analysis_types_chart", "Tipos de análisis realizados"))
            ax.set_xlabel(t.get("analysis_type", "Tipo de análisis"))
            ax.set_ylabel(t.get("count", "Cantidad"))
            st.pyplot(fig)
        except Exception as e:
            logger.error(f"Error al crear el gráfico: {e}")
            st.error("No se pudo crear el gráfico de tipos de análisis.")

    # Función para generar el contenido del archivo de actividades de las últimas 48 horas
    def generate_activity_content_48h():
        content = f"Actividades de {username} en las últimas 48 horas\n\n"

        two_days_ago = datetime.now(pytz.utc) - timedelta(days=2)

        try:
            morphosyntax_analyses = get_student_morphosyntax_data(username)
            recent_morphosyntax = [a for a in morphosyntax_analyses if datetime.fromisoformat(a['timestamp']) > two_days_ago]

            content += f"Análisis morfosintácticos: {len(recent_morphosyntax)}\n"
            for analysis in recent_morphosyntax:
                content += f"- Análisis del {analysis['timestamp']}: {analysis['text'][:50]}...\n"

            chat_history = get_chat_history(username, None)
            recent_chats = [c for c in chat_history if datetime.fromisoformat(c['timestamp']) > two_days_ago]

            content += f"\nConversaciones de chat: {len(recent_chats)}\n"
            for chat in recent_chats:
                content += f"- Chat del {chat['timestamp']}: {len(chat['messages'])} mensajes\n"
        except Exception as e:
            logger.error(f"Error al generar el contenido de actividades: {e}")
            content += "Error al recuperar los datos de actividades.\n"

        return content

    # Botones para descargar el histórico de actividades de las últimas 48 horas
    st.subheader(t.get("download_history_48h", "Descargar Histórico de Actividades (Últimas 48 horas)"))
    if st.button("Generar reporte de 48 horas"):
        try:
            report_content = generate_activity_content_48h()
            st.text_area("Reporte de 48 horas", report_content, height=300)
            st.download_button(
                label="Descargar TXT (48h)",
                data=report_content,
                file_name="actividades_48h.txt",
                mime="text/plain"
            )
        except Exception as e:
            logger.error(f"Error al generar el reporte: {e}")
            st.error("No se pudo generar el reporte. Por favor, verifica los logs para más detalles.")

    logger.debug("Finalizando display_student_progress")