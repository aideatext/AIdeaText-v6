# modules/utils/helpers.py
def decode_professor_id(prof_id):
    """
    Descompone el ID tipo MG-EDU-UNIFE-LIM
    Retorna un diccionario con la información formateada.
    """
    if not prof_id or not isinstance(prof_id, str):
        return {"iniciales": "N/A", "facultad": "General", "institucion": "Global", "ciudad": "N/A"}

    parts = prof_id.split('-')
    
    # Mapeo de siglas (Extensible)
    FACULTADES = {
        "EDU": "Educación", 
        "PSI": "Psicología", 
        "DER": "Derecho", 
        "ING": "Ingeniería",
        "MED": "Medicina"
    }
    
    INSTITUCIONES = {
        "UNIFE": "Universidad Femenina del Sagrado Corazón",
        "ULIMA": "Universidad de Lima",
        "PUCP": "Pontificia Universidad Católica del Perú"
    }

    # Si el formato es correcto (4 partes), mapeamos. Si no, devolvemos lo que haya.
    return {
        "iniciales": parts[0] if len(parts) > 0 else "N/A",
        "facultad": FACULTADES.get(parts[1], parts[1]) if len(parts) > 1 else "General",
        "institucion": INSTITUCIONES.get(parts[2], parts[2]) if len(parts) > 2 else "Global",
        "ciudad": parts[3] if len(parts) > 3 else "N/A"
    }