# database_export.py

import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
#importaciones locales
from .morphosintax_mongo_db import get_student_morphosyntax_analysis
from .chat_db import get_chat_history


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

#def export_user_interactions(username, analysis_type):
    # Obtener análisis morfosintáctico
    #morphosyntax_data = get_student_morphosyntax_analysis(username)

    # Obtener historial de chat
    #chat_history = get_chat_history(username, analysis_type)

    # Crear un DataFrame con los datos
    #df = pd.DataFrame({
    #    'Timestamp': [entry['timestamp'] for entry in chat_history],
    #    'Role': [msg['role'] for entry in chat_history for msg in entry['messages']],
    #    'Content': [msg['content'] for entry in chat_history for msg in entry['messages']]
    #})

    # Crear un PDF
    #buffer = BytesIO()
    #plt.figure(figsize=(12, 6))
    #plt.axis('off')
    #plt.text(0.5, 0.98, f"Interacciones de {username} - Análisis {analysis_type}", ha='center', va='top', fontsize=16)
    #plt.text(0.5, 0.95, f"Total de interacciones: {len(df)}", ha='center', va='top', fontsize=12)

    # Añadir tabla con las interacciones
    #plt.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')

    # Añadir diagramas de arco si es análisis morfosintáctico
    #if analysis_type == 'morphosyntax' and morphosyntax_data:
    #    for i, analysis in enumerate(morphosyntax_data):
    #        plt.figure(figsize=(12, 6))
    #        plt.axis('off')
    #        plt.text(0.5, 0.98, f"Diagrama de Arco {i+1}", ha='center', va='top', fontsize=16)
    #        plt.imshow(analysis['arc_diagrams'][0])  # Asumiendo que arc_diagrams es una lista de imágenes

    #plt.savefig(buffer, format='pdf', bbox_inches='tight')
    #buffer.seek(0)
    #return buffer

# Uso:
# pdf_buffer = export_user_interactions(username, 'morphosyntax')
# st.download_button(label="Descargar PDF", data=pdf_buffer, file_name="interacciones.pdf", mime="application/pdf")