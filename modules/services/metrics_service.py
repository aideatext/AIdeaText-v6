# modules/services/metrics_service.py
"""
MetricsService — Calcula M1, M2 y M1_D cross-cubeta.

ShortTerm: llamado desde professor_ui y metrics_processor.
LongTerm:  será un endpoint POST /metrics/coherence.

Sin imports de streamlit ni pandas obligatorios — portable a FastAPI.
"""

import logging
import numpy as np
from typing import Optional

import networkx as nx

logger = logging.getLogger(__name__)


class MetricsService:
    """
    Calcula y agrega métricas de coherencia para estudiantes y grupos.
    Stateless.
    """

    # ─── M1: COHERENCIA TRANSMODAL ────────────────────────────────────────────

    def calculate_m1(
        self,
        graph_written: Optional[nx.Graph],
        graph_chat: Optional[nx.Graph],
        nlp,
    ) -> float:
        """
        M1 = similitud coseno entre el grafo de escritura y el grafo del chat.
        Retorna 0.0 si falta alguno de los dos grafos.
        """
        if graph_written is None or graph_chat is None:
            return 0.0
        try:
            from modules.metrics.m1_m2 import calculate_M1
            result = calculate_M1(graph_written, graph_chat, nlp)
            return float(result) if result is not None else 0.0
        except Exception as exc:
            logger.warning(f"[MetricsService.calculate_m1] {exc}")
            return 0.0

    # ─── M2: ROBUSTEZ ESTRUCTURAL ─────────────────────────────────────────────

    def calculate_m2(self, graph: Optional[nx.Graph]) -> dict:
        """
        M2 = densidad + grado promedio del grafo de conceptos.
        """
        if graph is None:
            return {'M2_density': 0.0, 'M2_average_degree': 0.0, 'M2_node_count': 0}
        try:
            from modules.metrics.m1_m2 import calculate_M2
            return calculate_M2(graph)
        except Exception as exc:
            logger.warning(f"[MetricsService.calculate_m2] {exc}")
            return {'M2_density': 0.0, 'M2_average_degree': 0.0, 'M2_node_count': 0}

    # ─── M1_D: COHERENCIA DIALÓGICA CROSS-CUBETA ─────────────────────────────

    def calculate_m1d(self, m1_scores: list[float]) -> float:
        """
        M1_D = mean(M1 scores) * (1 - 0.15 * std(M1 scores))

        La penalización de 0.15 reduce el score si el estudiante es
        inconsistente entre modalidades (escritura vs. chat vs. oral).

        Args:
            m1_scores: lista de M1 por cubeta [M1_live, M1_doc, M1_chat, ...]
                       Se filtran los 0.0 que corresponden a cubetas sin datos.
        Returns:
            M1_D en [0.0, 1.0]
        """
        active = [s for s in m1_scores if s > 0.0]
        if not active:
            return 0.0
        mean_val = float(np.mean(active))
        std_val = float(np.std(active)) if len(active) > 1 else 0.0
        return round(float(np.clip(mean_val * (1 - 0.15 * std_val), 0.0, 1.0)), 4)

    def compute_student_m1d(
        self,
        username: str,
        group_id: str,
        nlp_models: Optional[dict] = None,
    ) -> dict:
        """
        Calcula M1_D completo para un estudiante consultando las 4 cubetas.

        Returns:
            {
                'username': str,
                'M1_live': float,
                'M1_doc': float,
                'M1_chat': float,
                'M2_doc': float,
                'M1_D': float,
                'interpretation': str
            }
        """
        try:
            from modules.database.semantic_mongo_db import get_student_semantic_analysis
            from modules.database.semantic_mongo_live_db import get_student_semantic_live_analysis
            from modules.database.chat_mongo_db import get_chat_history

            # ─ Cubeta 1: Doc (escritura formal)
            docs = get_student_semantic_analysis(username=username, group_id=group_id, limit=5) or []
            m1_doc = self._avg_m1_from_docs(docs, field='analysis_result')
            m2_doc = self._avg_m2_from_docs(docs)

            # ─ Cubeta 2: Live (pizarrón)
            lives = get_student_semantic_live_analysis(username=username, group_id=group_id) or []
            m1_live = self._avg_m1_from_docs(lives, field='analysis_result')

            # ─ Cubeta 3: Chat (tutor virtual)
            chats = get_chat_history(username=username, group_id=group_id) or []
            m1_chat = self._avg_m1_from_chat(chats)

            m1d = self.calculate_m1d([m1_doc, m1_live, m1_chat])

            return {
                'username': username,
                'group_id': group_id,
                'M1_doc': round(m1_doc, 4),
                'M1_live': round(m1_live, 4),
                'M1_chat': round(m1_chat, 4),
                'M2_doc': round(m2_doc, 4),
                'M1_D': m1d,
                'interpretation': self._interpret_m1d(m1d),
            }

        except Exception as exc:
            logger.error(f"[MetricsService.compute_student_m1d] {exc}", exc_info=True)
            return {
                'username': username,
                'group_id': group_id,
                'M1_doc': 0.0,
                'M1_live': 0.0,
                'M1_chat': 0.0,
                'M2_doc': 0.0,
                'M1_D': 0.0,
                'interpretation': 'Sin datos',
            }

    # ─── HELPERS ──────────────────────────────────────────────────────────────

    @staticmethod
    def _avg_m1_from_docs(docs: list, field: str = 'analysis_result') -> float:
        scores = []
        for doc in docs:
            res = doc.get(field) or {}
            if isinstance(res, dict):
                val = res.get('m1_score', 0.0)
                if val and val > 0:
                    scores.append(float(val))
            # Fallback: campo directo
            elif doc.get('m1_score', 0.0) > 0:
                scores.append(float(doc['m1_score']))
        return float(np.mean(scores)) if scores else 0.0

    @staticmethod
    def _avg_m2_from_docs(docs: list) -> float:
        scores = []
        for doc in docs:
            res = doc.get('analysis_result') or {}
            val = (
                res.get('m2_score')
                or (res.get('concept_graph') or {}).get('M2_density')
                or doc.get('m2_score', 0.0)
            )
            if val and float(val) > 0:
                scores.append(float(val))
        return float(np.mean(scores)) if scores else 0.0

    @staticmethod
    def _avg_m1_from_chat(chats: list) -> float:
        scores = []
        for chat in chats:
            meta = chat.get('metadata') or {}
            val = meta.get('m1_score', 0.0)
            if val and float(val) > 0:
                scores.append(float(val))
        return float(np.mean(scores)) if scores else 0.0

    @staticmethod
    def _interpret_m1d(m1d: float) -> str:
        if m1d >= 0.80:
            return "Alta coherencia dialógica — el tesista integra escritura y diálogo."
        elif m1d >= 0.60:
            return "Coherencia moderada — revisar consistencia entre modalidades."
        elif m1d > 0.0:
            return "Coherencia baja — riesgo reproductivo. Atención inmediata."
        else:
            return "Sin datos suficientes para calcular M1_D."
