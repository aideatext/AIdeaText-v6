import pandas as pd
import numpy as np
from datetime import datetime, timezone
import re

def process_semantic_data(raw_data):
    if not raw_data:
        return pd.DataFrame()

    processed = []
    for entry in raw_data:
        source = entry.get('source_collection', 'semantic_analysis')
        res = entry.get('analysis_result', {})
        full_username = entry.get('username', '') # Ej: MG-G1-t1-2025-1
        
        # --- LÓGICA DE JERARQUÍA REPARADA ---
        parts = full_username.split('-')
        
        # Buscamos cuál de las partes es el tesista (t1, t2, etc.)
        id_estudiante = "SN"
        grupo_parts = []
        
        for p in parts:
            if re.match(r'^t\d+$', p.lower()): # Si la parte es t1, t2...
                id_estudiante = p
            else:
                grupo_parts.append(p)
        
        # El ID del Grupo es todo lo que NO es el tesista
        # Resultado esperado: MG-G1-2025-1
        id_grupo = "-".join(grupo_parts)
        
        # Nombre amigable para el eje X de las gráficas de Martha
        # Si parts tiene el formato esperado, extraemos G1 y el periodo
        try:
            display_grupo = f"Grupo {parts[1]} ({parts[-2]}-{parts[-1]})"
        except:
            display_grupo = id_grupo

        # --- NORMALIZACIÓN DE DATOS ---
        ts = entry.get('timestamp') or datetime.now(timezone.utc)
        if isinstance(ts, str):
            try: ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except: ts = datetime.now(timezone.utc)

        m1 = float(res.get('m1_score', 0.0))
        if source == 'chat_history-v3':
            m1 = float(entry.get('metadata', {}).get('chat_coherence', m1))

        processed.append({
            'Estudiante_ID': id_estudiante,      # Solo "t1" o "t2"
            'Username_Completo': full_username,  # El ID largo
            'Grupo_ID': id_grupo,                # MG-G1-2025-1
            'Grupo_Display': display_grupo,      # Grupo G1 (2025-1)
            'Fuente': source,
            'Fecha': ts,
            'M1': m1,
            'M2': float(res.get('m2_score') or res.get('concept_graph', {}).get('M2_density', 0.0)),
            'Texto': entry.get('text', '')
        })
    
    df = pd.DataFrame(processed)
    
    # Cálculo de M1-D (Coherencia Dialógica)
    if not df.empty:
        df['M1_D'] = df.groupby('Username_Completo')['M1'].transform('mean')
        varianza = df.groupby('Username_Completo')['M1'].transform('std').fillna(0)
        df['M1_D'] = df['M1_D'] * (1 - (varianza * 0.15))
    
    return df.sort_values('Fecha')