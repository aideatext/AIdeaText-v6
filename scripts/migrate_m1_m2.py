"""
scripts/migrate_m1_m2.py
=========================
Backfill de métricas M2 en documentos existentes de `student_semantic_analysis`.

Contexto:
  Los ~48 documentos guardados antes del fix del 2026-04-03 no tienen el campo
  `analysis_result` (o lo tienen vacío), por lo que `metrics_processor.py` los
  lee como M1=0, M2=0 en el dashboard de Martha.

Estrategia:
  Fase 1 — Backfill estructural (siempre seguro, no requiere NLP):
    • Añade `analysis_result: {m1_score: 0.0, m2_score: 0.0, ...}` a docs sin él.
    • Asegura que `group_id` exista en todos los docs (usa `username` como fallback).

  Fase 2 — Recálculo con NLP (opcional, requiere --nlp):
    • Carga spaCy y recalcula M2 a partir del texto guardado.
    • Solo actualiza docs donde el texto esté disponible y M2 sea 0.

Uso:
  # Solo backfill estructural (sin NLP, rápido):
  python scripts/migrate_m1_m2.py

  # Backfill + recálculo NLP (más lento, más preciso):
  python scripts/migrate_m1_m2.py --nlp --lang es

  # Solo ver qué haría (sin modificar nada):
  python scripts/migrate_m1_m2.py --dry-run
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Añadir la raíz del proyecto al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

COLLECTION = "student_semantic_analysis"


# ─── Conexión DocumentDB ──────────────────────────────────────────────────────

def get_mongo_collection(name: str):
    """Retorna la colección MongoDB usando la misma lógica que database_init.py"""
    from pymongo import MongoClient
    uri = os.getenv("MONGO_URI")
    ca_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "global-bundle.pem")
    client = MongoClient(uri, tlsCAFile=ca_path if os.path.exists(ca_path) else None)
    db_name = os.getenv("MONGO_DB_NAME", "aideatext")
    return client[db_name][name]


# ─── Fase 1: Backfill estructural ────────────────────────────────────────────

def phase1_structural_backfill(col, dry_run: bool) -> int:
    """
    Añade `analysis_result` mínimo a documentos que no lo tienen.
    Retorna número de docs actualizados.
    """
    logger.info("=== FASE 1: Backfill estructural ===")

    # Docs sin analysis_result O con analysis_result sin m2_score
    query = {
        "$or": [
            {"analysis_result": {"$exists": False}},
            {"analysis_result": None},
            {"analysis_result.m2_score": {"$exists": False}},
        ]
    }
    docs = list(col.find(query, {"_id": 1, "username": 1, "group_id": 1, "m2_score": 1}))
    logger.info(f"  Docs sin analysis_result completo: {len(docs)}")

    updated = 0
    for doc in docs:
        doc_id = doc["_id"]
        # Intentar recuperar m2_score del campo raíz si existe
        m2_root = float(doc.get("m2_score") or 0.0)
        m1_root = float(doc.get("m1_score") or 0.0)

        # Reparar group_id si falta
        group_id = doc.get("group_id")
        username = doc.get("username", "")
        update_fields = {
            "analysis_result": {
                "m1_score": m1_root,
                "m2_score": m2_root,
                "concept_graph": {
                    "M2_density": m2_root,
                },
            },
            "migration_ts": datetime.now(timezone.utc),
        }
        if not group_id and username:
            # Intentar derivar group_id del username (formato MG-G1-2025-1-t1)
            parts = username.rsplit("-", 1)
            if len(parts) == 2 and parts[1].startswith("t"):
                update_fields["group_id"] = parts[0]
                logger.info(f"    Reparando group_id: {username} → {parts[0]}")

        if dry_run:
            logger.info(f"  [DRY-RUN] _id={doc_id}  m2={m2_root:.4f}")
        else:
            col.update_one({"_id": doc_id}, {"$set": update_fields})
            updated += 1

    action = "Se actualizarían" if dry_run else "Actualizados"
    logger.info(f"  {action}: {len(docs) if dry_run else updated} docs")
    return updated


# ─── Fase 2: Recálculo NLP ───────────────────────────────────────────────────

def phase2_nlp_recalculate(col, lang_code: str, dry_run: bool) -> int:
    """
    Para docs con texto guardado y M2=0, recalcula M2 usando spaCy.
    Requiere el modelo spaCy instalado.
    """
    logger.info(f"=== FASE 2: Recálculo NLP (lang={lang_code}) ===")

    try:
        import spacy
        from modules.text_analysis.semantic_analysis import perform_semantic_analysis
        from modules.metrics.m1_m2 import calculate_M2
    except ImportError as e:
        logger.error(f"  No se pudieron importar módulos NLP: {e}")
        logger.error("  Asegúrate de ejecutar desde el virtualenv del proyecto.")
        return 0

    model_names = {
        "es": "es_core_news_lg",
        "en": "en_core_web_lg",
        "fr": "fr_core_news_lg",
        "pt": "pt_core_news_lg",
    }
    model_name = model_names.get(lang_code, "es_core_news_lg")
    logger.info(f"  Cargando spaCy model: {model_name}...")
    try:
        nlp = spacy.load(model_name)
    except OSError:
        # Fallback a versión md
        try:
            nlp = spacy.load(model_name.replace("_lg", "_md"))
        except OSError as e:
            logger.error(f"  Modelo no encontrado: {e}")
            return 0
    logger.info("  Modelo cargado.")

    # Solo docs con texto guardado y M2=0 (o cercano)
    query = {
        "text": {"$exists": True, "$ne": "", "$ne": None},
        "$or": [
            {"analysis_result.m2_score": 0.0},
            {"analysis_result.m2_score": {"$exists": False}},
            {"m2_score": 0.0},
        ],
    }
    docs = list(col.find(query, {"_id": 1, "username": 1, "text": 1, "language": 1}))
    logger.info(f"  Docs candidatos para recálculo: {len(docs)}")

    updated = 0
    for i, doc in enumerate(docs, 1):
        doc_lang = doc.get("language", lang_code)
        text = doc.get("text", "")
        if not text or len(text) < 50:
            continue

        try:
            raw = perform_semantic_analysis(text, nlp, doc_lang)
            if not raw.get("success"):
                logger.warning(f"  [{i}/{len(docs)}] NLP falló para {doc['_id']}")
                continue

            G = raw.get("concept_graph_nx")
            if G is None or G.number_of_nodes() == 0:
                continue

            m2 = calculate_M2(G)
            m2_score = float(m2.get("M2_density", 0.0))

            if dry_run:
                logger.info(f"  [DRY-RUN] [{i}/{len(docs)}] {doc.get('username')} M2={m2_score:.4f}")
            else:
                col.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {
                        "m2_score": m2_score,
                        "analysis_result.m2_score": m2_score,
                        "analysis_result.concept_graph.M2_density": m2_score,
                        "migration_nlp_ts": datetime.now(timezone.utc),
                    }},
                )
                logger.info(f"  [{i}/{len(docs)}] {doc.get('username')} → M2={m2_score:.4f}")
                updated += 1

        except Exception as e:
            logger.error(f"  Error procesando {doc['_id']}: {e}")
            continue

    action = "Se actualizarían" if dry_run else "Actualizados"
    logger.info(f"  {action}: {len(docs) if dry_run else updated} docs con M2 recalculado")
    return updated


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Backfill M2 en student_semantic_analysis")
    parser.add_argument("--dry-run", action="store_true", help="Sin modificar la DB")
    parser.add_argument("--nlp", action="store_true", help="Activa recálculo NLP (Fase 2)")
    parser.add_argument("--lang", default="es", help="Idioma para el modelo spaCy (es/en/fr/pt)")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("=== MODO DRY-RUN — ningún cambio será guardado ===\n")

    col = get_mongo_collection(COLLECTION)
    total_docs = col.count_documents({})
    logger.info(f"Colección `{COLLECTION}` — total docs: {total_docs}\n")

    n1 = phase1_structural_backfill(col, dry_run=args.dry_run)
    logger.info("")

    n2 = 0
    if args.nlp:
        n2 = phase2_nlp_recalculate(col, lang_code=args.lang, dry_run=args.dry_run)

    logger.info("")
    logger.info(f"Migración completa — Fase1: {n1} | Fase2 NLP: {n2}")


if __name__ == "__main__":
    main()
