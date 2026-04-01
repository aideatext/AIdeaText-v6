import pandas as pd
import numpy as np
from datetime import datetime, timezone
import re

def process_semantic_data(raw_data):
    """
    Procesa la jerarquía: MG-G1-2025-1-t1
    Grupo: MG-G1-2025-1 (Partes 0 a 3)
    Estudiante: t1 (Parte 4)
    """
    if not raw_data:
        return pd.DataFrame()

    processed = []
    for entry in raw_data:
        res = entry.get('analysis_result', {})
        full_username = entry.get('username', '') 
        
        # --- LÓGICA DE SEGMENTACIÓN POR POSICIÓN ---
        parts = full_username.split('-')
        
        # Si cumple el estándar de 5 partes (MG-G1-2025-1-t1)
        if len(parts) >= 5:
            # El estudiante es el último
            id_estudiante = parts[-1] 
            # El grupo es la unión de las primeras 4 partes: MG-G1-2025-1
            id_grupo = "-".join(parts[0:4])
            # Nombre para el selector: "Grupo G1 (2025-1)"
            display_grupo = f"Grupo {parts[1]} ({parts[2]}-{parts[3]})"
        else:
            # Fallback para evitar que el sistema se rompa con IDs viejos
            id_grupo = entry.get('group_id', 'Sin Grupo')
            id_estudiante = full_username
            display_grupo = id_grupo

        # --- NORMALIZACIÓN DE MÉTRICAS ---
        # Aseguramos que M1 y M2 sean floats y no dicts
        m1 = float(res.get('m1_score', 0.0))
        
        m2 = 0.0
        if isinstance(res, dict):
            m2 = res.get('m2_score')
            if m2 is None:
                cg = res.get('concept_graph', {})
                m2 = cg.get('M2_density', 0.0) if isinstance(cg, dict) else 0.0

        processed.append({
            'Estudiante_ID': id_estudiante,      # "t1"
            'Username_Completo': full_username,  # "MG-G1-2025-1-t1"
            'Grupo_ID': id_grupo,                # "MG-G1-2025-1" -> CLAVE PARA UNIFICAR
            'Grupo_Display': display_grupo,      # "Grupo G1 (2025-1)"
            'Fuente': entry.get('source_collection', 'student_semantic_analysis'),
            'Fecha': entry.get('timestamp') or datetime.now(timezone.utc),
            'M1': float(m1),
            'M2': float(m2 or 0.0),
            'Texto': entry.get('text', '')
        })
    
    df = pd.DataFrame(processed)
    
    if not df.empty:
        # Esto unifica a t1 y t2 bajo el mismo Grupo_ID en las gráficas de grupo
        df['M1_D'] = df.groupby('Username_Completo')['M1'].transform('mean')
    
    return df.sort_values('Fecha')