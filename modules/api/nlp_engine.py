from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import spacy
# Aquí importaremos tus funciones de grafos actuales
# from modules.nlp.graph_generator import generate_semantic_graph 

app = FastAPI(title="AIdeaText NLP Engine - UNIFE 2026")

# Cargar el modelo de spaCy una sola vez al arrancar (Ahorra mucha RAM)
try:
    nlp = spacy.load("es_core_news_lg")
except:
    nlp = spacy.load("es_core_news_sm")

class AnalysisRequest(BaseModel):
    text: str
    student_id: str
    modality: str  # 'writing' o 'voice'

@app.get("/")
def read_root():
    return {"status": "NLP Engine Online", "version": "v6.0-aws"}

@app.post("/analyze")
async def analyze_text(request: AnalysisRequest):
    if not request.text:
        raise HTTPException(status_code=400, detail="No text provided")
    
    # 1. Procesamiento con spaCy
    doc = nlp(request.text)
    
    # 2. Aquí calcularemos M2 (Densidad Proposicional / Grafos)
    # Por ahora simulamos la respuesta para probar la conexión
    entities = [ent.text for ent in doc.ents]
    num_tokens = len(doc)
    
    # 3. Estructura de respuesta para DocumentDB
    analysis_results = {
        "student_id": request.student_id,
        "metrics": {
            "word_count": num_tokens,
            "entities_found": len(entities),
            "M2_graph_density": 0.0, # Placeholder para tu función de grafos
        },
        "entities": entities,
        "status": "success"
    }
    
    return analysis_results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)