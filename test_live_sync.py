# test_live_sync.py
from modules.database.semantic_mongo_live_db import store_student_semantic_live_result, get_live_analysis_for_tutor

# Datos de prueba
USER = "manuel_profe"
GROUP = "UNIFE_PILOTO_1"
TEXTO_1 = "La inteligencia artificial en la educación debe ser ética."
ANALISIS_1 = {"concept_graph": "base64_grafo_1", "key_concepts": ["ética", "IA"]}

TEXTO_2 = "La IA en la educación debe ser ética y transparente." # Edición posterior
ANALISIS_2 = {"concept_graph": "base64_grafo_2", "key_concepts": ["ética", "transparencia"]}

print("--- Iniciando Prueba de Sincronización Automática ---")

# Paso A: El usuario analiza el primer texto
store_student_semantic_live_result(USER, GROUP, TEXTO_1, ANALISIS_1)
print("1. Primer análisis guardado.")

# Paso B: El usuario edita y analiza de nuevo
store_student_semantic_live_result(USER, GROUP, TEXTO_2, ANALISIS_2)
print("2. Segundo análisis guardado (sobrescribiendo el primero).")

# Paso C: Simulamos al Tutor Virtual pidiendo el texto
contexto = get_live_analysis_for_tutor(GROUP)

if contexto and contexto['text'] == TEXTO_2:
    print(f"\n✅ PRUEBA EXITOSA")
    print(f"El Tutor recibió el último texto: '{contexto['text']}'")
    print(f"Conceptos detectados: {contexto['key_concepts']}")
else:
    print("\n❌ FALLO: El Tutor no recibió la versión más reciente.")
