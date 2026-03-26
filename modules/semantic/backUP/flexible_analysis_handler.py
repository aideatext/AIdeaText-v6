from typing import Dict, Any
import base64
from io import BytesIO
from matplotlib.figure import Figure

class FlexibleAnalysisHandler:
    def __init__(self, analysis_data):
        self.data = analysis_data

    def get_key_concepts(self):
        return self.data.get('key_concepts', [])

    def get_concept_graph(self):
        return self.data.get('concept_graph')

    def get_entity_graph(self):
        return self.data.get('entity_graph')

    # Método genérico para obtener cualquier tipo de grafo
    def get_graph(self, graph_type):
        return self.data.get(graph_type)

    # Agrega más métodos según sea necesario


'''
class FlexibleAnalysisHandler:
    def __init__(self, analysis_data: Dict[str, Any]):
        self.data = analysis_data

    def get_key_concepts(self):
        if 'key_concepts' in self.data:
            return self.data['key_concepts']
        elif 'word_count' in self.data:
            # Convertir word_count a un formato similar a key_concepts
            return [(word, count) for word, count in self.data['word_count'].items()]
        return []

    def get_graph(self):
        if 'graph' in self.data:
            # Decodificar la imagen base64
            image_data = base64.b64decode(self.data['graph'])
            return BytesIO(image_data)
        elif 'arc_diagrams' in self.data:
            # Devolver el primer diagrama de arco como SVG
            return self.data['arc_diagrams'][0]
        return None

    def get_pos_analysis(self):
        return self.data.get('pos_analysis', [])

    def get_morphological_analysis(self):
        return self.data.get('morphological_analysis', [])

    def get_sentence_structure(self):
        return self.data.get('sentence_structure', [])

    # Agregar más métodos según sea necesario para otros tipos de análisis
'''