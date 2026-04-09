# modules/services/analysis_service.py
"""
AnalysisService — Orquesta el pipeline NLP completo.

ShortTerm: llamado directamente desde Streamlit (semantic_process.py).
LongTerm:  será llamado desde un FastAPI endpoint POST /analyze.

Principio: este módulo NO importa streamlit. Todo lo que necesita
viene como parámetros. Esto garantiza que en FastAPI solo se cambia
el handler, no la lógica.
"""

import logging
from typing import Optional

import networkx as nx

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Orquesta el análisis semántico desde texto crudo hasta métricas M1/M2.
    Sin estado (stateless) — instanciar una vez y reutilizar.
    """

    def __init__(self, nlp_models: dict):
        """
        Args:
            nlp_models: dict {lang_code: spacy_model} — cargado una sola vez
                        por la app (st.cache_resource o startup de FastAPI).
        """
        self._nlp = nlp_models
        self._m2_calculator = None  # lazy import

    # ─── API PÚBLICA ──────────────────────────────────────────────────────────

    def run_semantic_analysis(
        self,
        text: str,
        lang_code: str,
        username: str,
        group_id: str,
        file_name: str = "sin_nombre",
    ) -> dict:
        """
        Pipeline completo: texto → grafo → M2 → guardado en MongoDB.

        Returns:
            {
                'success': bool,
                'm1_score': float,   # 0.0 hasta que haya chat comparison
                'm2_score': float,   # M2_density del grafo generado
                'm2_metrics': dict,
                'key_concepts': list,
                'concept_graph': bytes,  # imagen PNG/JPEG
                'concept_graph_nx': nx.Graph | None,
                'error': str | None
            }
        """
        try:
            nlp = self._get_nlp(lang_code)
            if nlp is None:
                return self._error(f"Modelo spaCy no disponible para '{lang_code}'")

            # 1. NLP + grafo
            from modules.text_analysis.semantic_analysis import perform_semantic_analysis
            raw = perform_semantic_analysis(text, nlp, lang_code)

            if not raw.get('success'):
                return self._error(raw.get('error', 'Error en NLP pipeline'))

            # 2. M2 — robustez estructural del grafo
            m2_metrics, m2_score = self._compute_m2(raw.get('concept_graph_nx'))

            # 3. Enriquecer resultado
            result = {
                'success': True,
                'error': None,
                'm1_score': 0.0,          # requiere chat — se actualiza vía ChatService
                'm2_score': m2_score,
                'm2_metrics': m2_metrics,
                'key_concepts': raw.get('key_concepts', []),
                'concept_graph': raw.get('concept_graph'),
                'concept_graph_nx': raw.get('concept_graph_nx'),
            }

            # 4. Persistir
            self._store(username, group_id, text, result, lang_code, file_name)

            logger.info(
                f"[AnalysisService] usuario={username} grupo={group_id} "
                f"M2={m2_score:.4f} lang={lang_code}"
            )
            return result

        except Exception as exc:
            logger.error(f"[AnalysisService] error inesperado: {exc}", exc_info=True)
            return self._error(str(exc))

    def run_live_analysis(
        self,
        text: str,
        lang_code: str,
        username: str,
        group_id: str,
    ) -> dict:
        """
        Pipeline para el pizarrón en vivo (upsert — siempre la última versión).
        Similar a run_semantic_analysis pero sin file_name y usando la cubeta live.
        """
        try:
            nlp = self._get_nlp(lang_code)
            if nlp is None:
                return self._error(f"Modelo spaCy no disponible para '{lang_code}'")

            from modules.text_analysis.semantic_analysis import perform_semantic_analysis
            raw = perform_semantic_analysis(text, nlp, lang_code)

            if not raw.get('success'):
                return self._error(raw.get('error', 'Error en NLP pipeline'))

            m2_metrics, m2_score = self._compute_m2(raw.get('concept_graph_nx'))
            raw['m2_score'] = m2_score
            raw['m2_metrics'] = m2_metrics
            raw['m1_score'] = 0.0

            from modules.database.semantic_mongo_live_db import store_student_semantic_live_result
            store_student_semantic_live_result(
                username=username,
                group_id=group_id,
                text=text,
                analysis_result=raw.get('analysis', raw),
                lang_code=lang_code,
            )

            return {
                'success': True,
                'error': None,
                'm1_score': 0.0,
                'm2_score': m2_score,
                'm2_metrics': m2_metrics,
                'key_concepts': raw.get('key_concepts', []),
                'concept_graph': raw.get('concept_graph'),
                'concept_graph_nx': raw.get('concept_graph_nx'),
            }

        except Exception as exc:
            logger.error(f"[AnalysisService.live] {exc}", exc_info=True)
            return self._error(str(exc))

    def analyze_text_only(self, text: str, lang_code: str) -> dict:
        """
        Ejecuta el pipeline NLP completo (identical a run_semantic_analysis)
        pero NO persiste en MongoDB.

        Uso: análisis intermedios que no deben crear documentos propios —
        grafo híbrido del chat, comparaciones en tiempo real, validaciones.

        Garantiza que TODOS los textos del sistema (tesis, live, chat) pasen
        por el mismo proceso: spaCy → identify_key_concepts → create_concept_graph
        → calculate_M2. Esto es un requisito de la investigación UNIFE.

        Returns:
            {
                'success': bool,
                'concept_graph_nx': nx.Graph | None,
                'concept_graph': bytes | None,   # imagen PNG
                'key_concepts': list,
                'm2_score': float,
                'm2_metrics': dict,
                'error': str | None,
            }
        """
        try:
            nlp = self._get_nlp(lang_code)
            if nlp is None:
                return self._error(f"Modelo spaCy no disponible para '{lang_code}'")

            from modules.text_analysis.semantic_analysis import perform_semantic_analysis
            raw = perform_semantic_analysis(text, nlp, lang_code)

            if not raw.get('success'):
                return self._error(raw.get('error', 'Error en NLP pipeline'))

            m2_metrics, m2_score = self._compute_m2(raw.get('concept_graph_nx'))

            return {
                'success': True,
                'error': None,
                'concept_graph_nx': raw.get('concept_graph_nx'),
                'concept_graph': raw.get('concept_graph'),
                'key_concepts': raw.get('key_concepts', []),
                'm2_score': m2_score,
                'm2_metrics': m2_metrics,
            }

        except Exception as exc:
            logger.error(f"[AnalysisService.analyze_text_only] {exc}", exc_info=True)
            return self._error(str(exc))

    # ─── HELPERS PRIVADOS ─────────────────────────────────────────────────────

    def _get_nlp(self, lang_code: str):
        model = self._nlp.get(lang_code) or self._nlp.get('es')
        if model is None:
            logger.error(f"No hay modelo para '{lang_code}' ni fallback 'es'")
        return model

    def _compute_m2(self, G: Optional[nx.Graph]) -> tuple[dict, float]:
        """Calcula M2 si hay grafo. Retorna (m2_metrics_dict, m2_density_float)."""
        if G is None or G.number_of_nodes() == 0:
            return {}, 0.0
        try:
            from modules.metrics.m1_m2 import calculate_M2
            m2 = calculate_M2(G)
            return m2, float(m2.get('density', 0.0))
        except Exception as exc:
            logger.warning(f"[AnalysisService._compute_m2] {exc}")
            return {}, 0.0

    def _store(self, username, group_id, text, result, lang_code, file_name):
        """Delega persistencia al módulo CRUD — sin lógica de negocio aquí."""
        try:
            from modules.database.semantic_mongo_db import store_student_semantic_result
            store_student_semantic_result(
                username=username,
                group_id=group_id,
                text=text,
                analysis_result=result,
                lang_code=lang_code,
                file_name=file_name,
            )
        except Exception as exc:
            logger.error(f"[AnalysisService._store] {exc}")

    @staticmethod
    def _error(msg: str) -> dict:
        return {
            'success': False,
            'error': msg,
            'm1_score': 0.0,
            'm2_score': 0.0,
            'm2_metrics': {},
            'key_concepts': [],
            'concept_graph': None,
            'concept_graph_nx': None,
        }
