# modules/metrics/metrics_processor.py
import pandas as pd
from datetime import datetime

def process_semantic_data(raw_data):
    """Limpia y normaliza los datos de Mongo para la interfaz."""
    if not raw_data:
        return pd.DataFrame()

    processed = []
    for entry in raw_data:
        res = entry.get('analysis_result', {})
        graph = res.get('concept_graph', {})
        
        # Corrección de Timestamps
        ts = entry.get('timestamp')
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except:
                ts = datetime.now() # Fallback
                
        processed.append({
            'Estudiante': entry.get('username'),
            'Grupo': entry.get('group_id'),
            'Fecha': ts,
            'M1': res.get('m1_score', 0.0),
            'M2': graph.get('M2_density', 0.0) if isinstance(graph, dict) else 0.0,
            'Texto': entry.get('text', ''),
            'img_raw': res.get('graph_image') or entry.get('concept_graph')
        })
    
    return pd.DataFrame(processed).sort_values('Fecha')