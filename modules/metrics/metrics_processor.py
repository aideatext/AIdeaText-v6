#modules/metrics/metrics_processor.py
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def process_semantic_data(raw_data):
    if not raw_data:
        return pd.DataFrame()

    processed = []
    for entry in raw_data:
        source = entry.get('source_collection', 'semantic_analysis')
        res = entry.get('analysis_result', {})
        full_username = entry.get('username', '')
        
        # --- NUEVA LÓGICA DE JERARQUÍA ROBUSTA ---
        # Ejemplo: MG-G1-2025-1-t1
        parts = full_username.split('-')
        
        if len(parts) >= 5:
            # El tesista es SIEMPRE el último elemento (t1)
            id_estudiante = parts[-1] 
            # El grupo es todo lo anterior unido de nuevo (MG-G1-2025-1)
            id_grupo = "-".join(parts[:-1]) 
            
            # Formato para Martha: "Grupo G1 (2025-1)"
            # parts[1] es G1, parts[2] es 2025, parts[3] es 1
            display_grupo = f"Grupo {parts[1]} ({parts[2]}-{parts[3]})"
        else:
            id_grupo = entry.get('group_id', 'Sin Grupo')
            id_estudiante = full_username
            display_grupo = id_grupo

        # --- NORMALIZACIÓN DE MÉTRICAS Y FECHAS ---
        ts = entry.get('timestamp') or datetime.now(timezone.utc)
        if isinstance(ts, str):
            try: ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except: ts = datetime.now(timezone.utc)

        m1 = float(res.get('m1_score', 0.0))
        if source == 'chat_history-v3':
            m1 = float(entry.get('metadata', {}).get('chat_coherence', m1))

        # Extraer M2 (Robustez) con fallback
        m2 = 0.0
        if isinstance(res, dict):
            m2 = res.get('m2_score') or res.get('concept_graph', {}).get('M2_density', 0.0)
        
        processed.append({
            'Estudiante_ID': id_estudiante,      # Muestra: t1
            'Username_Completo': full_username,  # Muestra: MG-G1-2025-1-t1
            'Grupo_ID': id_grupo,                # Muestra: MG-G1-2025-1
            'Grupo_Display': display_grupo,      # Muestra: Grupo G1 (2025-1)
            'Fuente': source,
            'Fecha': ts,
            'M1': m1,
            'M2': float(m2 or 0.0),
            'Texto': entry.get('text', '')
        })
    
    df = pd.DataFrame(processed)
    
    # Cálculo de Coherencia Dialógica M1-D
    if not df.empty:
        df['M1_D'] = df.groupby('Username_Completo')['M1'].transform('mean')
        varianza = df.groupby('Username_Completo')['M1'].transform('std').fillna(0)
        df['M1_D'] = df['M1_D'] * (1 - (varianza * 0.15))
    
    return df.sort_values('Fecha')