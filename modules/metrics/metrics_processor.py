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
        # Priorizamos 'username' pero buscamos en otros campos si no está
        full_id = entry.get('username') or entry.get('student_id') or "Desconocido-t0"
        
        # --- EXTRACCIÓN DE TESISTA (t1, t2, etc.) ---
        # Buscamos 't' seguido de números de forma insensible a mayúsculas
        match_estudiante = re.search(r'[tT](\d+)', full_id)
        if match_estudiante:
            id_estudiante = f"t{match_estudiante.group(1)}"
        else:
            id_estudiante = "S/N"

        # --- EXTRACCIÓN DE GRUPO ---
        # El grupo es todo lo que está antes de la marca de tesista (-t1)
        # O si no hay marca, usamos el campo group_id del registro
        id_grupo_base = re.split(r'-[tT]\d+', full_id)[0]
        id_grupo_db = entry.get('group_id', id_grupo_base)
        
        # Limpieza visual para Martha: MG-G1-2025-1 -> "Grupo G1 (2025-1)"
        parts = id_grupo_db.split('-')
        if len(parts) >= 4:
            display_grupo = f"Grupo {parts[1]} ({parts[2]}-{parts[3]})"
        else:
            display_grupo = id_grupo_db

        # --- MÉTRICAS ---
        m1 = float(res.get('m1_score', 0.0))
        m2 = 0.0
        if isinstance(res, dict):
            # Compatibilidad: nuevas claves (density) y legacy (M2_density, m2_score)
            m2 = (
                res.get('m2_score')
                or res.get('concept_graph', {}).get('density')
                or res.get('concept_graph', {}).get('M2_density', 0.0)
            )

        processed.append({
            'Estudiante_ID': id_estudiante,      # "t1"
            'Username_Completo': full_id,        # "MG-G1-2025-1-t1"
            'Grupo_ID': id_grupo_db,             # "MG-G1-2025-1"
            'Grupo_Display': display_grupo,
            'M1': float(m1),
            'M2': float(m2 or 0.0),
            'Fecha': entry.get('timestamp') or datetime.now(timezone.utc),
            'Texto': entry.get('text', '')
        })
    
    df = pd.DataFrame(processed)
    
    if not df.empty:
        # M1_D intra-escritura: fórmula canónica con penalización por std
        # mean(M1) × (1 - 0.15 × std(M1)) — misma fórmula que MetricsService.calculate_m1d
        def _m1d_writing(series):
            active = series[series > 0.0]
            if active.empty:
                return 0.0
            mean_val = float(np.mean(active))
            std_val = float(np.std(active)) if len(active) > 1 else 0.0
            return round(float(np.clip(mean_val * (1 - 0.15 * std_val), 0.0, 1.0)), 4)

        df['M1_D'] = df.groupby('Username_Completo')['M1'].transform(_m1d_writing)

    return df.sort_values('Fecha')