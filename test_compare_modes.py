# test_discourse_modes.py
from modules.database.discourse_mongo_db import store_student_discourse_result

USER = "manuel_vargas"
GROUP = "UNIFE_PILOTO"
MOCK_RESULT = {
    'success': True, 
    'key_concepts1': ['A'], 'key_concepts2': ['B'],
    'graph1': b"data1", 'graph2': b"data2", 'combined_graph': b"datacombined"
}

print("--- Test de Modos de Discurso ---")
# Simulación 1: Mejora de un borrador
store_student_discourse_result(USER, GROUP, "Borrador 1", "Borrador 2", MOCK_RESULT, mode="evolution")

# Simulación 2: Comparación de autores
store_student_discourse_result(USER, GROUP, "Autor 1", "Autor 2", MOCK_RESULT, mode="contrast")

print("✅ Ambas pruebas enviadas. Verifica en Compass los valores de 'mode'.")
