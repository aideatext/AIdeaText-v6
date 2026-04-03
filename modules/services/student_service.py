# modules/services/student_service.py
"""
StudentService — Recupera y agrega datos de un estudiante desde las 4 cubetas.

ShortTerm: llamado desde user_page.py y student_activities_v2.py.
LongTerm:  será un endpoint GET /students/{student_id}/summary.

Sin imports de streamlit — totalmente portable a FastAPI.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class StudentService:
    """
    Agrega datos de las 4 cubetas para un estudiante o grupo.
    Stateless — instanciar una vez, reutilizar.
    """

    # ─── API PÚBLICA ──────────────────────────────────────────────────────────

    def get_student_summary(self, username: str, group_id: str) -> dict:
        """
        Retorna un resumen consolidado del estudiante con datos de las 4 cubetas.

        Returns:
            {
                'username': str,
                'group_id': str,
                'semantic_analyses': list,      # student_semantic_analysis
                'live_analyses': list,          # student_semantic_live_analysis
                'discourse_analyses': list,     # student_discourse_analysis
                'chat_sessions': list,          # chat_history-v3
                'latest_m1': float,
                'latest_m2': float,
                'session_count': int,
            }
        """
        try:
            sem = self._get_semantic(username, group_id)
            live = self._get_live(username, group_id)
            discourse = self._get_discourse(username, group_id)
            chat = self._get_chat(username, group_id)

            # Métricas más recientes de escritura
            latest_m1, latest_m2 = self._extract_latest_metrics(sem)

            return {
                'username': username,
                'group_id': group_id,
                'semantic_analyses': sem,
                'live_analyses': live,
                'discourse_analyses': discourse,
                'chat_sessions': chat,
                'latest_m1': latest_m1,
                'latest_m2': latest_m2,
                'session_count': len(sem) + len(live) + len(discourse) + len(chat),
            }

        except Exception as exc:
            logger.error(f"[StudentService.get_student_summary] {exc}", exc_info=True)
            return {
                'username': username,
                'group_id': group_id,
                'semantic_analyses': [],
                'live_analyses': [],
                'discourse_analyses': [],
                'chat_sessions': [],
                'latest_m1': 0.0,
                'latest_m2': 0.0,
                'session_count': 0,
            }

    def get_group_summary(self, group_id: str) -> list[dict]:
        """
        Retorna lista de resúmenes por estudiante en el grupo.
        Usado por professor_ui para el dashboard de Martha.
        """
        try:
            from modules.database.sql_db import execute_query
            rows = execute_query(
                "SELECT DISTINCT id FROM users WHERE class_id = %s AND role = 'Estudiante'",
                (group_id,)
            )
            summaries = []
            for row in rows:
                username = row.get('id')
                if username:
                    summaries.append(self.get_student_summary(username, group_id))
            return summaries
        except Exception as exc:
            logger.error(f"[StudentService.get_group_summary] {exc}", exc_info=True)
            return []

    # ─── HELPERS PRIVADOS (repositorio) ────────────────────────────────────────

    def _get_semantic(self, username: str, group_id: str) -> list:
        try:
            from modules.database.semantic_mongo_db import get_student_semantic_analysis
            return get_student_semantic_analysis(username=username, group_id=group_id) or []
        except Exception as exc:
            logger.warning(f"[StudentService._get_semantic] {exc}")
            return []

    def _get_live(self, username: str, group_id: str) -> list:
        try:
            from modules.database.semantic_mongo_live_db import get_student_semantic_live_analysis
            return get_student_semantic_live_analysis(username=username, group_id=group_id) or []
        except Exception as exc:
            logger.warning(f"[StudentService._get_live] {exc}")
            return []

    def _get_discourse(self, username: str, group_id: str) -> list:
        try:
            from modules.database.discourse_mongo_db import get_student_discourse_analysis
            return get_student_discourse_analysis(username=username, group_id=group_id) or []
        except Exception as exc:
            logger.warning(f"[StudentService._get_discourse] {exc}")
            return []

    def _get_chat(self, username: str, group_id: str) -> list:
        try:
            from modules.database.chat_mongo_db import get_chat_history
            return get_chat_history(username=username, group_id=group_id) or []
        except Exception as exc:
            logger.warning(f"[StudentService._get_chat] {exc}")
            return []

    @staticmethod
    def _extract_latest_metrics(semantic_analyses: list) -> tuple[float, float]:
        """Extrae M1 y M2 del análisis más reciente."""
        if not semantic_analyses:
            return 0.0, 0.0
        latest = semantic_analyses[0]
        res = latest.get('analysis_result', {})
        m1 = float(res.get('m1_score', 0.0))
        m2 = float(
            res.get('m2_score')
            or (res.get('concept_graph') or {}).get('M2_density', 0.0)
            or latest.get('m2_score', 0.0)
        )
        return m1, m2
