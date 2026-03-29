from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import spacy
import networkx as nx
# Importaciones de tus módulos de métricas y limpieza
from modules.text_analysis.semantic_analysis import create_concept_graph
from modules.text_analysis.stopwords import process_text
from modules.metrics.m1_m2 import calculate_M2, graph_to_dict

app = FastAPI(title="AIdeaText NLP Engine - UNIFE 2026 Edition")

models = {}

def get_model(lang: str):
    model_name = "es_core_news_md" if lang == "es" else "en_core_web_md"
    if model_name not in models:
        try:
            models[model_name] = spacy.load(model_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error cargando modelo {lang}: {str(e)}")
    return models[model_name]

class AnalysisRequest(BaseModel):
    text: str
    student_id: str
    modality: str  # 'writing' o 'oral' (Tutor Virtual)
    lang: str = "es"

@app.post("/analyze")
async def analyze_text(request: AnalysisRequest):
    nlp = get_model(request.lang)
    
    # 1. Limpieza académica (Stopwords + Reglas locales)
    # Esto asegura que el texto del Tutor Virtual y la Tesis pasen por el mismo filtro
    cleaned_text = process_text(request.text, request.lang)
    
    # 2. Procesamiento spaCy
    # doc_TutorVirtual o doc_Escrito según la modalidad
    doc = nlp(cleaned_text)
    
    # 3. Generación de Grafo (Filtro POS: Solo Sustantivos)
    # La función create_concept_graph ya debe tener el filtro allowed_pos=['NOUN', 'PROPN']
    G = create_concept_graph(doc, lang_code=request.lang)
    
    # 4. Cálculo de Métricas M2 (Robustez Estructural)
    m2_results = calculate_M2(G)
    
    return {
        "student_id": request.student_id,
        "modality": request.modality,
        "analysis": {
            "graph_data": graph_to_dict(G), # Incluye nodos, aristas y M2
            "m2_metrics": m2_results,
            "text_summary": f"Procesado bajo modalidad {request.modality}"
        }
    }