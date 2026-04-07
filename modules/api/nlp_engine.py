"""
modules/api/nlp_engine.py
==========================
FastAPI endpoint para el motor NLP de AIdeaText.

ShortTerm: coexiste con Streamlit (mismo proceso o separado).
LongTerm:  será el único punto de entrada — Streamlit queda como UI thin.

Todos los pipelines NLP pasan por AnalysisService para garantizar
que la lógica de negocio sea idéntica en Streamlit y en la API.
"""

from contextlib import asynccontextmanager
from typing import Optional

import spacy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from modules.services.analysis_service import AnalysisService

# ─── Modelos spaCy — cargados una sola vez al arrancar ───────────────────────

_NLP_MODELS: dict = {}

SPACY_MAP = {
    "es": ["es_core_news_lg", "es_core_news_md"],
    "en": ["en_core_web_lg", "en_core_web_md"],
    "fr": ["fr_core_news_lg", "fr_core_news_md"],
    "pt": ["pt_core_news_lg", "pt_core_news_md"],
}


def _load_model(lang: str) -> Optional[object]:
    """Intenta cargar el modelo grande, cae al medium si no está instalado."""
    for model_name in SPACY_MAP.get(lang, []):
        try:
            return spacy.load(model_name)
        except OSError:
            continue
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga modelos spaCy en el arranque — startup/shutdown lifecycle."""
    for lang in SPACY_MAP:
        model = _load_model(lang)
        if model:
            _NLP_MODELS[lang] = model
    yield
    _NLP_MODELS.clear()


app = FastAPI(
    title="AIdeaText NLP Engine — UNIFE 2026",
    description="Motor NLP + métricas M1/M2. Todos los pipelines pasan por AnalysisService.",
    version="2.0.0",
    lifespan=lifespan,
)


def _get_service() -> AnalysisService:
    """Factory de AnalysisService con los modelos cargados."""
    if not _NLP_MODELS:
        raise HTTPException(status_code=503, detail="Modelos NLP no disponibles — espera al arranque.")
    return AnalysisService(nlp_models=_NLP_MODELS)


# ─── Schemas ─────────────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    text: str
    student_id: str                     # username completo (ej. MG-G1-2025-1-t1)
    group_id: str                       # ej. MG-G1-2025-1
    modality: str = "writing"           # 'writing' | 'live' | 'chat'
    lang: str = "es"
    file_name: Optional[str] = None


class AnalysisResponse(BaseModel):
    student_id: str
    group_id: str
    modality: str
    success: bool
    m1_score: float
    m2_score: float
    m2_metrics: dict
    key_concepts: list
    error: Optional[str] = None


# ─── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check — devuelve los idiomas con modelos cargados."""
    return {
        "status": "ok",
        "models_loaded": list(_NLP_MODELS.keys()),
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(req: AnalysisRequest):
    """
    Pipeline completo: texto → grafo semántico → métricas M2 → guardado en MongoDB.

    - modality='writing' → student_semantic_analysis (documento Word/PDF)
    - modality='live'    → student_semantic_live_analysis (pizarrón en vivo)
    """
    if not req.text or len(req.text.strip()) < 10:
        raise HTTPException(status_code=422, detail="Texto demasiado corto para analizar.")

    svc = _get_service()

    if req.modality == "live":
        result = svc.run_live_analysis(
            text=req.text,
            lang_code=req.lang,
            username=req.student_id,
            group_id=req.group_id,
        )
    else:
        result = svc.run_semantic_analysis(
            text=req.text,
            lang_code=req.lang,
            username=req.student_id,
            group_id=req.group_id,
            file_name=req.file_name or "api_upload",
        )

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Error en el pipeline NLP"))

    return AnalysisResponse(
        student_id=req.student_id,
        group_id=req.group_id,
        modality=req.modality,
        success=result["success"],
        m1_score=result.get("m1_score", 0.0),
        m2_score=result.get("m2_score", 0.0),
        m2_metrics=result.get("m2_metrics", {}),
        key_concepts=[
            {"concept": c, "frequency": f}
            for c, f in (result.get("key_concepts") or [])
        ],
        error=result.get("error"),
    )
