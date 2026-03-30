import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import pytz
import logging
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from docx import Document
from odf.opendocument import OpenDocumentText
from odf.text import P

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Asumimos que estas funciones están disponibles a través de las importaciones en load_database_functions
from .database.backUp.morphosintax_mongo_db import get_student_morphosyntax_analysis, get_student_morphosyntax_data
from .database.chat_db import get_chat_history

def display_student_progress(username, lang_code, t):
    logger.debug(f"Iniciando display_student_progress para {username}")

    st.title(f"{t.get('progress_of', 'Progreso de')} {username}")

    # Obtener datos de análisis morfosintáctico
    morphosyntax_data = get_student_morphosyntax_data(username)
    # Obtener historial de chat
    chat_history = get_chat_history(username, None)

    if not morphosyntax_data and not chat_history:
        logger.warning(f"No se encontraron datos para el estudiante {username}")
        st.warning(t.get("no_data_warning", "No se encontraron datos para este estudiante."))
        st.info(t.get("try_analysis", "Intenta realizar algunos análisis de texto primero."))
        return

    # Resumen de actividades
    with st.expander(t.get("activities_summary", "Resumen de Actividades"), expanded=True):
        total_morphosyntax = len(morphosyntax_data)
        total_chats = len(chat_history)
        st.write(f"{t.get('total_morphosyntax_analyses', 'Total de análisis morfosintácticos')}: {total_morphosyntax}")
        st.write(f"{t.get('total_chats', 'Total de conversaciones de chat')}: {total_chats}")

        # Gráfico de tipos de actividades
        try:
            activity_counts = pd.Series({
                'Análisis Morfosintáctico': total_morphosyntax,
                'Conversaciones de Chat': total_chats
            })
            fig, ax = plt.subplots()
            sns.barplot(x=activity_counts.index, y=activity_counts.values, ax=ax)
            ax.set_title(t.get("activity_types_chart", "Tipos de actividades realizadas"))
            ax.set_ylabel(t.get("count", "Cantidad"))
            st.pyplot(fig)
        except Exception as e:
            logger.error(f"Error al crear el gráfico: {e}")
            st.error("No se pudo crear el gráfico de tipos de actividades.")

    # Función para generar el contenido del archivo de actividades de las últimas 48 horas
    def generate_activity_content_48h():
        content = f"Actividades de {username} en las últimas 48 horas\n\n"

        two_days_ago = datetime.now(pytz.utc) - timedelta(days=2)

        try:
            recent_morphosyntax = [a for a in morphosyntax_data if datetime.fromisoformat(a['timestamp']) > two_days_ago]

            content += f"Análisis morfosintácticos: {len(recent_morphosyntax)}\n"
            for analysis in recent_morphosyntax:
                content += f"- Análisis del {analysis['timestamp']}: {analysis['text'][:50]}...\n"

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

# Funciones auxiliares para generar diferentes formatos de archivo (PDF, DOCX, ODT) se mantienen igual
# ...