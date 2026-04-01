import os
import datetime
import spacy
import logging
from dotenv import load_dotenv

# Importaciones exactas de tus módulos
from modules.text_analysis.semantic_analysis import create_concept_graph
from modules.database.semantic_mongo_live_db import store_student_semantic_live_result
from modules.database.semantic_mongo_db import store_student_semantic_result
from modules.database.chat_mongo_db import store_chat_history
from modules.metrics.m1_m2 import calculate_M1, graph_to_dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

# Carga del modelo
nlp = spacy.load("es_core_news_md")

def get_demo_hitos():
    # Retornamos los 24 hitos basados en ART2.txt
    return [
        {"fase": "Iniciación", "t": "La construcción del objeto de investigación nace de una pasión.", "c": "Tutor: Larrosa dice que la pregunta es pasión. ¿Qué te apasiona?"},
        {"fase": "Iniciación", "t": "Busco entender la relación entre docente y alumno desde la mirada cualitativa.", "c": "Tutor: Taylor & Bogdan sugieren que la investigación cualitativa busca la comprensión profunda."},
        {"fase": "Problematización", "t": "El plan de estudios 2012 limita la creatividad en el aula.", "c": "Tutor: Sánchez Puentes menciona que la investigación es un campo de lucha institucional."},
        {"fase": "Problematización", "t": "Mi pregunta es: ¿Cómo influye el lenguaje en la inclusión educativa?", "c": "Tutor: Porter indica que el lenguaje nos vincula a voces anteriores."},
        {"fase": "Marco Teórico", "t": "La hermenéutica de Ricoeur permite interpretar la acción como un texto.", "c": "Tutor: Ricoeur dice que el sentido está frente al texto."},
        {"fase": "Marco Teórico", "t": "Interpretar es apropiarse de lo que inicialmente era extraño.", "c": "Tutor: Esa es la esencia de la apropiación hermenéutica."},
        {"fase": "Metodología", "t": "Usaré la narrativa biográfica para recolectar relatos de vida.", "c": "Tutor: Weiss afirma que el oficio de investigar se aprende haciendo."},
        {"fase": "Metodología", "t": "He diseñado una entrevista abierta para no sesgar las respuestas.", "c": "Tutor: La escucha activa es clave para desmarcarse de prejuicios."},
        {"fase": "Crisis/Bloqueo", "t": "Siento que mis datos son puros chismes, no tienen rigor.", "c": "Tutor: Primero (2006) advierte sobre el miedo al cientificismo."},
        {"fase": "Crisis/Bloqueo", "t": "No puedo escribir. Me quedé en blanco frente a la computadora.", "c": "Tutor: Hernández Belmonte dice que investigar es resistencia."},
        {"fase": "Crisis/Bloqueo", "t": "Quizás debería cambiar a algo cuantitativo para terminar rápido.", "c": "Tutor: González Villarreal habla de no huir de la complejidad."},
        {"fase": "Recuperación", "t": "He vuelto a leer mis transcripciones. Hay patrones ocultos.", "c": "Tutor: ¡Eso es! Estás descubriendo la trama de Ricoeur."},
        {"fase": "Trabajo de Campo", "t": "Las maestras antiguas narran una mística que ya no existe.", "c": "Tutor: Estás documentando una ruptura generacional."},
        {"fase": "Trabajo de Campo", "t": "El lenguaje de los directivos es autoritario en mis grabaciones.", "c": "Tutor: Compara eso con lo que dice Mier sobre lenguaje y poder."},
        {"fase": "Análisis", "t": "La interpretación requiere un desdoblamiento de mi identidad.", "c": "Tutor: El investigador es sujeto y objeto a la vez."},
        {"fase": "Análisis", "t": "La pasión de Larrosa se está perdiendo por la burocracia.", "c": "Tutor: Has llegado al núcleo: la burocracia contra el pensamiento."},
        {"fase": "Interpretación", "t": "Mi texto ahora dialoga con la teoría y con la realidad.", "c": "Tutor: Eso es la 'fusión de horizontes' hermenéutica."},
        {"fase": "Interpretación", "t": "La formación docente está atravesada por tensiones múltiples.", "c": "Tutor: ¿Cómo se resuelven esas tensiones en tu propuesta?"},
        {"fase": "Redacción", "t": "Estoy tejiendo los argumentos usando la voz de las informantes.", "c": "Tutor: Interpretar es dar voz a lo que estaba en silencio."},
        {"fase": "Redacción", "t": "El capítulo 3 está listo, integrando a Ricoeur y Taylor.", "c": "Tutor: Revisa la coherencia con tu marco inicial."},
        {"fase": "Revisión", "t": "He corregido las citas. El sentido del texto es sólido.", "c": "Tutor: La forma también comunica un sentido."},
        {"fase": "Revisión", "t": "Esta investigación me ha cambiado como profesora.", "c": "Tutor: Ese es el fin: la transformación del sujeto."},
        {"fase": "Finalización", "t": "Borrador final terminado. El objeto ha concluido.", "c": "Tutor: Has pasado de la pasión a la rigurosidad."},
        {"fase": "Finalización", "t": "Listo para entrega a coordinación de titulación.", "c": "Tutor: Fue un honor acompañarte en esta resistencia."}
    ]

def run_population():
    hitos = get_demo_hitos()
    # IDs con el nuevo formato estandarizado
    students = ["MG-G1-2025-1-t1", "MG-G1-2025-1-t2"]
    group_id = "MG-G1-2025-1"

    logger.info(f"Poblando DocumentDB para {len(students)} estudiantes en el grupo {group_id}...")

    for student_id in students:
        for idx, hito in enumerate(hitos):
            # 1. Procesamiento de texto
            doc_t = nlp(hito["t"])
            doc_c = nlp(hito["c"])

            # 2. Generar grafos
            G_escrito = create_concept_graph(doc_t, nlp)
            G_tutor = create_concept_graph(doc_c, nlp)

            # 3. Calcular M1
            m1_val = calculate_M1(G_escrito, G_tutor, nlp)

            # --- CORRECCIÓN EN LA LÓGICA DE CRISIS ---
            # El ID ahora es MG-G1-2025-1-t2 (no MG-G1-t2-2025-1)
            if student_id == "MG-G1-2025-1-t2" and "Crisis" in hito["fase"]:
                m1_val = 0.48 if m1_val is None else m1_val * 0.5

            # 4. Preparar payload
            analysis_payload = {
                'concept_graph': graph_to_dict(G_escrito),
                'm1_score': m1_val,
                'fase': hito["fase"],
		'entities': [] # Evita errores de campos faltantes
            }

            # 5. ALMACENAMIENTO CON FIRMAS ACTUALIZADAS

            # A. Chat History: Ahora requiere group_id como segundo argumento
            chat_messages = [
                {"role": "user", "content": hito["t"]},
                {"role": "assistant", "content": hito["c"]}
            ]
            # Pasamos (username, group_id, messages)
            store_chat_history(student_id, group_id, chat_messages)

            # B. Live Result
            store_student_semantic_live_result(student_id, group_id, hito["t"], analysis_payload)

            # C. Historical Result
            store_student_semantic_result(student_id, group_id, hito["t"], analysis_payload)

    logger.info(f"✅ Inyección completada. {len(students)} tesistas vinculados al grupo {group_id}")

if __name__ == "__main__":
    run_population()
