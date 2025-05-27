import io
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from pymongo import MongoClient
import base64

# Asume que tienes una función para obtener la conexión a MongoDB
from ..database.mongo_db import get_mongodb

def convert_svg_to_png(svg_string):
    """Convierte una cadena SVG a una imagen PNG."""
    drawing = svg2rlg(io.BytesIO(svg_string.encode('utf-8')))
    png_bio = io.BytesIO()
    renderPM.drawToFile(drawing, png_bio, fmt="PNG")
    return png_bio.getvalue()

def save_png_to_database(username, analysis_id, png_data):
    """Guarda la imagen PNG en la base de datos."""
    client = get_mongodb()
    db = client['aideatext_db']  # Asegúrate de usar el nombre correcto de tu base de datos
    collection = db['png_diagrams']

    png_base64 = base64.b64encode(png_data).decode('utf-8')

    document = {
        'username': username,
        'analysis_id': analysis_id,
        'png_data': png_base64
    }

    result = collection.insert_one(document)
    return result.inserted_id

def process_and_save_svg_diagrams(username, analysis_id, svg_diagrams):
    """Procesa una lista de diagramas SVG, los convierte a PNG y los guarda en la base de datos."""
    png_ids = []
    for svg in svg_diagrams:
        png_data = convert_svg_to_png(svg)
        png_id = save_png_to_database(username, analysis_id, png_data)
        png_ids.append(png_id)
    return png_ids

# Función para recuperar PNGs de la base de datos
def get_png_diagrams(username, analysis_id):
    """Recupera los diagramas PNG de la base de datos para un análisis específico."""
    client = get_mongodb()
    db = client['aideatext_db']
    collection = db['png_diagrams']

    diagrams = collection.find({'username': username, 'analysis_id': analysis_id})
    return [base64.b64decode(doc['png_data']) for doc in diagrams]