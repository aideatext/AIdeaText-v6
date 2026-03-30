from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
import base64
import cairosvg
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader

#importaciones locales
from .morphosintax_mongo_db import get_student_morphosyntax_data
from .chat_db import get_chat_history

# Placeholder para el logo
LOGO_PATH = "assets\img\logo_92x92.png" # Reemplaza esto con la ruta real de tu logo

# Definir el tamaño de página carta manualmente (612 x 792 puntos)
LETTER_SIZE = (612, 792)

def add_logo(canvas, doc):
    logo = Image(LOGO_PATH, width=2*cm, height=2*cm)
    logo.drawOn(canvas, doc.leftMargin, doc.height + doc.topMargin - 0.5*cm)

def export_user_interactions(username, analysis_type):
    # Obtener historial de chat (que ahora incluye los análisis morfosintácticos)
    chat_history = get_chat_history(username, analysis_type)

    # Crear un PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    story = []
    styles = getSampleStyleSheet()

    # Título
    story.append(Paragraph(f"Interacciones de {username} - Análisis {analysis_type}", styles['Title']))
    story.append(Spacer(1, 0.5*cm))

    # Historial del chat y análisis
    for entry in chat_history:
        for message in entry['messages']:
            role = message['role']
            content = message['content']
            story.append(Paragraph(f"<b>{role.capitalize()}:</b> {content}", styles['BodyText']))
            story.append(Spacer(1, 0.25*cm))

            # Si hay visualizaciones (diagramas SVG), convertirlas a imagen y añadirlas
            if 'visualizations' in message and message['visualizations']:
                for svg in message['visualizations']:
                    drawing = svg2rlg(BytesIO(svg.encode('utf-8')))
                    img_data = BytesIO()
                    renderPM.drawToFile(drawing, img_data, fmt="PNG")
                    img_data.seek(0)
                    img = Image(img_data, width=15*cm, height=7.5*cm)
                    story.append(img)
                    story.append(Spacer(1, 0.5*cm))

        story.append(PageBreak())

    # Construir el PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Uso en Streamlit:
# pdf_buffer = export_user_interactions(username, 'morphosyntax')
# st.download_button(label="Descargar PDF", data=pdf_buffer, file_name="interacciones.pdf", mime="application/pdf")