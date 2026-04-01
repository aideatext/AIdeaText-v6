import pandas as pd
import numpy as np
from datetime import datetime, timezone
import re

def process_semantic_data(raw_data):
    if not raw_data:
        return pd.DataFrame()

    processed = []
    for entry in raw_data:
        res = entry.get('analysis_result', {})
        full_username = entry.get('username', '') 
        
        # --- LÓGICA DE UNIFICACIÓN AGRESIVA ---
        # 1. Limpiamos el username de los sufijos de estudiante (-t1, -t2, etc)
        # Esto asegura que "MG-G1-2025-1-t1" y "MG-G1-2025-1-t2" resulten en el mismo ID de grupo
        id_grupo_limpio = re.sub(r'-t\d+.*$', '', full_username)
        
        # 2. Identificamos al estudiante (lo que quitamos arriba)
        match_estudiante = re.search(r'(t\d+)$', full_username)
        id_estudiante = match_estudiante.group(1) if match_estudiante else "S/N"
        
        # 3. Construimos un nombre visual limpio para Martha
        # Si el ID limpio es MG-G1-2025-1, queremos que diga "Grupo G1 (2025-1)"
        parts = id_grupo_limpio.split('-')
        if len(parts) >= 4:
            display_grupo = f"Grupo {parts[1]} ({parts[2]}-{parts[3]})"
        else:
            display_grupo = id_grupo_limpio

        # --- EXTRACCIÓN DE MÉTRICAS ---
        m1 = float(res.get('m1_score', 0.0))
        m2 = 0.0
        if isinstance(res, dict):
            m2 = res.get('m2_score') or res.get('concept_graph', {}).get('M2_density', 0.0)

        processed.append({
            'Estudiante_ID': id_estudiante,      # "t1"
            'Username_Completo': full_username,  # "MG-G1-2025-1-t1"
            'Grupo_ID': id_grupo_limpio,         # "MG-G1-2025-1" (IGUAL PARA TODOS)
            'Grupo_Display': display_grupo,      # "Grupo G1 (2025-1)"
            'Fuente': entry.get('source_collection', 'student_semantic_analysis'),
            'Fecha': entry.get('timestamp') or datetime.now(timezone.utc),
            'M1': float(m1),
            'M2': float(m2 or 0.0),
            'Texto': entry.get('text', '')
        })
    
    df = pd.DataFrame(processed)
    
    if not df.empty:
        # IMPORTANTE: Esto es lo que permite que Martha vea a todos en una sola gráfica
        df['M1_D'] = df.groupby('Username_Completo')['M1'].transform('mean')
    
    return df.sort_values('Fecha')update 