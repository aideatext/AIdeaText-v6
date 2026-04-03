# modules/services/__init__.py
# Capa de servicios — separa lógica de negocio de UI y de base de datos.
# Principio CLAUDE.md regla 2: queries separados de lógica.
# Compatibilidad ShortTerm→LongTerm: al migrar a FastAPI, solo se cambia
# el transporte (Streamlit→HTTP), no la lógica de este módulo.

from .analysis_service import AnalysisService
from .student_service import StudentService
from .metrics_service import MetricsService

__all__ = ['AnalysisService', 'StudentService', 'MetricsService']
