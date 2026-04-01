# test_archive_sync.py
from modules.database.semantic_mongo_db import store_student_semantic_result
from modules.database.mongo_db import get_collection

# Datos de simulación
USER = "manuel_tester"
GROUP = "UNIFE_TEAM_A"
ANALISIS_MOCK = {"key_concepts": ["educación", "IA"], "concept_graph": b"fake_graph_bytes"}

def run_test():
    print(f"--- Iniciando Prueba de Archivos para el grupo: {GROUP} ---")
    
    # Paso 1: Subir el primer archivo
    print("1. Subiendo primer archivo...")
    store_student_semantic_result(USER, GROUP, "Texto del primer archivo", ANALISIS_MOCK)
    
    # Paso 2: Subir un segundo archivo (el más reciente)
    print("2. Subiendo segundo archivo (actualización)...")
    store_student_semantic_result(USER, GROUP, "Texto del segundo archivo corregido", ANALISIS_MOCK)
    
    # Paso 3: Verificar en la base de datos
    collection = get_collection('student_semantic_analysis')
    archivos = list(collection.find({'group_id': GROUP}))
    
    print(f"\nResultados en MongoDB para {GROUP}:")
    for doc in archivos:
        status = "🟢 ACTIVO (is_latest: True)" if doc.get('is_latest') else "⚪ HISTORIAL (is_latest: False)"
        print(f" - Documento ID: {doc['_id']} | {status} | Contenido: {doc['text'][:30]}...")

    # Validación lógica
    activos = [d for d in archivos if d.get('is_latest')]
    if len(activos) == 1 and activos[0]['text'] == "Texto del segundo archivo corregido":
        print("\n✅ PRUEBA EXITOSA: El Tutor solo verá el último archivo como activo.")
    else:
        print("\n❌ ERROR: La lógica de 'is_latest' no funcionó como se esperaba.")

if __name__ == "__main__":
    run_test()
