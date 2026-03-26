from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import spacy

app = FastAPI(title="AIdeaText NLP Engine - Multi-Language")

# Diccionario para gestionar los modelos cargados en RAM
models = {}

def get_model(lang: str):
    """Carga el modelo bajo demanda para ahorrar RAM si no se usa un idioma"""
    model_name = "es_core_news_md" if lang == "es" else "en_core_web_md"
    
    if model_name not in models:
        try:
            print(f"Cargando modelo: {model_name}...")
            models[model_name] = spacy.load(model_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error cargando modelo {lang}: {str(e)}")
    
    return models[model_name]

class AnalysisRequest(BaseModel):
    text: str
    student_id: str
    modality: str  # 'writing' o 'voice'
    lang: str = "es" # Por defecto español

@app.get("/")
def health_check():
    return {"status": "online", "models_loaded": list(models.keys())}

@app.post("/analyze")
async def analyze_text(request: AnalysisRequest):
    # 1. Obtener el modelo correcto (ES o EN)
    nlp = get_model(request.lang)
    
    # 2. Procesamiento base
    doc = nlp(request.text)
    
    # 3. Respuesta estructurada
    return {
        "student_id": request.student_id,
        "language_used": request.lang,
        "metrics": {
            "tokens": len(doc),
            "entities": len(doc.ents)
        },
        "status": "processed"
    }

if __name__ == "__main__":
    import uvicorn
    # Importante: host 0.0.0.0 para que AWS lo deje pasar
    uvicorn.run(app, host="0.0.0.0", port=8080)