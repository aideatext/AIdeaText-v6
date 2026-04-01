# modules/metrics/metrics_processor.py
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import re

def process_semantic_data(raw_data):
    """
    Procesador de métricas con jerarquía estándar:
    Grupo: MG-G1-2025-1
    Estudiante: MG-G1-2025-1-t1
    """
    if not raw_data:
        return pd.DataFrame()

    processed = []
    for entry in raw_data:
        source = entry.get('source_collection', 'student_semantic_analysis')
        res = entry.get('analysis_result', {})
        full_username = entry.get('username', '') 
        
        # --- NUEVA LÓGICA DE JERARQUÍA ESTÁNDAR ---
        # Separamos por guiones: ['MG', 'G1', '2025', '1', 't1']
        parts = full_username.split('-')
        
        if len(parts) >= 5:
            # El estudiante es SIEMPRE el último bloque (ej: t1)
            id_estudiante = parts[-1]
            # El grupo es la unión de todos los bloques anteriores (ej: MG-G1-2025-1)
            id_grupo = "-".join(parts[:-1])
            # Nombre amigable basado en posiciones fijas del nuevo estándar
            # MG (0), G1 (1), 2025 (2), 1 (3)
            display_grupo = f"Grupo {parts[1]} ({parts[2]}-{parts[3]})"
        else:
            # Fallback para IDs que no cumplan el estándar de 5 partes
            id_estudiante = full_username
            id_grupo = entry.get('group_id', 'Sin Grupo')
            display_grupo = id_grupo

        # --- NORMALIZACIÓN DE TIEMPO ---
        ts = entry.get('timestamp') or datetime.now(timezone.utc)
        if isinstance(ts, str):
            try:
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except:
                ts = datetime.now(timezone.utc)

        # --- EXTRACCIÓN DE MÉTRICAS (M1 y M2) ---
        m1 = float(res.get('m1_score', 0.0))
        if source == 'chat_history-v3':
            m1 = float(entry.get('metadata', {}).get('chat_coherence', m1))

        # Manejo robusto de M2 para evitar errores de tipo 'dict' o 'bytes'
        m2 = 0.0
        if isinstance(res, dict):
            m2 = res.get('m2_score')
            if m2 is None:
                cg = res.get('concept_graph', {})
                m2 = cg.get('M2_density', 0.0) if isinstance(cg, dict) else 0.0
        
        processed.append({
            'Estudiante_ID': id_estudiante,      # Muestra: t1
            'Username_Completo': full_username,  # Muestra: MG-G1-2025-1-t1
            'Grupo_ID': id_grupo,                # Muestra: MG-G1-2025-1
            'Grupo_Display': display_grupo,      # Muestra: Grupo G1 (2025-1)
            'Fuente': source,
            'Fecha': ts,
            'M1': float(m1),
            'M2': float(m2 or 0.0),
            'Texto': entry.get('text', ''),
            'img_raw': res.get('graph_image') or res.get('concept_graph')
        })
    
    df = pd.DataFrame(processed)
    
    # --- CÁLCULO DE COHERENCIA DIALÓGICA (M1-D) ---
    if not df.empty:
        # Promedio de M1 por tesista a través de todas sus participaciones
        df['M1_D'] = df.groupby('Username_Completo')['M1'].transform('mean')
        
        # Penalización por varianza: premia la consistencia entre chat y escritos
        varianza = df.groupby('Username_Completo')['M1'].transform('std').fillna(0)
        df['M1_D'] = df['M1_D'] * (1 - (varianza * 0.15))
    
    return df.sort_values('Fecha')