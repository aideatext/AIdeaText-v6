# modules/metrics/metrics_processor.py
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

def process_semantic_data(raw_data):
    """
    Procesa y unifica las 4 cubetas (Live, Analysis, Discourse, Chat).
    Calcula el Índice de Coherencia Dialógica (M1-D).
    """
    if not raw_data:
        return pd.DataFrame()

    processed = []
    for entry in raw_data:
        # 1. Identificación de la Fuente
        source = entry.get('source_collection', 'semantic_analysis')
        res = entry.get('analysis_result', {})
        full_username = entry.get('username', '')
        parts = full_username.split('-')
        
        # 2. Lógica de Jerarquía Institucional (5 partes: MG-G1-2025-1-t1)
        if len(parts) >= 5:
            id_grupo = "-".join(parts[0:4]) 
            id_estudiante = parts[4]
            display_grupo = f"Grupo {parts[1]} ({parts[2]}-{parts[3]})"
        else:
            id_grupo = entry.get('group_id', 'Sin Grupo')
            id_estudiante = full_username
            display_grupo = id_grupo

        # 3. Normalización de Fecha
        ts = entry.get('timestamp') or datetime.now(timezone.utc)
        if isinstance(ts, str):
            try: 
                ts = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            except: 
                ts = datetime.now(timezone.utc)

        # 4. Extracción de Métricas Base (M1 y M2)
        # Intentamos obtener M1 de varias fuentes posibles
        m1 = float(res.get('m1_score', 0.0))
        if source == 'chat_history-v3':
            m1 = float(entry.get('metadata', {}).get('chat_coherence', m1))

        # Intentamos obtener M2 (Densidad del grafo o robustez)
        m2 = 0.0
        if isinstance(res, dict):
            # Prioridad 1: m2_score directo
            m2 = res.get('m2_score')
            # Prioridad 2: Densidad del grafo si m2_score no existe
            if m2 is None:
                cg = res.get('concept_graph', {})
                m2 = cg.get('M2_density') if isinstance(cg, dict) else 0.0
        
        m2 = float(m2 or 0.0)

        # 5. Manejo de Texto (Soporta strings o listas de chat)
        texto_raw = entry.get('text', '')
        if not texto_raw and 'messages' in entry:
            # Si es un chat, unimos los mensajes para que Martha pueda leer la conversación
            msgs = entry.get('messages', [])
            texto_raw = " | ".join([f"{m.get('role')}: {m.get('content')}" for m in msgs if isinstance(m, dict)])

        processed.append({
            'Estudiante_ID': id_estudiante,
            'Username_Completo': full_username,
            'Grupo_ID': id_grupo,
            'Grupo_Display': display_grupo,
            'Fuente': source,
            'Fecha': ts,
            'M1': m1,
            'M2': m2,
            'Texto': texto_raw,
            'img_raw': res.get('graph_image') or entry.get('concept_graph')
        })
    
    df = pd.DataFrame(processed)
    
    # --- 6. CÁLCULO DE COHERENCIA DIALÓGICA (M1-D) ---
    if not df.empty:
        # Promedio simple por estudiante
        df['M1_D'] = df.groupby('Username_Completo')['M1'].transform('mean')
        
        # Penalización por Varianza (Inconsistencia Dialógica)
        # Si el estudiante fluctúa mucho entre chat y escritos, su M1_D baja.
        varianza = df.groupby('Username_Completo')['M1'].transform('std').fillna(0)
        df['M1_D'] = df['M1_D'] * (1 - (varianza * 0.15)) 
    
    return df.sort_values('Fecha')