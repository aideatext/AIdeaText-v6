# modules/text_analysis/stopwords.py
import spacy
from typing import Set, List
import unicodedata
import logging

logger = logging.getLogger(__name__)

# Símbolos universales (Preservado del original)
SYMBOLS_AND_NUMBERS = {
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    '.', ',', ';', ':', '!', '¡', '?', '¿', '"', "'",
    '+', '-', '*', '/', '=', '<', '>', '%', '(', ')', 
    '[', ']', '{', '}', '@', '#', '$', '€', '&', '_', 
    '|', '\\', '•', '·', '…', '©', '®', '™'
}

# --- FUNCIÓN ADICIONAL INTERNA (Documentación: Manejo de acentos) ---
def _normalize_caseless(text: str) -> str:
    """Función interna para comparar palabras ignorando tildes y mayúsculas."""
    text = text.lower()
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def get_custom_stopwords(lang_code: str) -> Set[str]:
    """
    NOMBRE PRESERVADO. Ahora incluye diccionarios para ES, EN, FR, PT.
    """
    stops_by_lang = {
        'es': {'el', 'la', 'un', 'una', 'y', 'e', 'o', 'u', 'pero', 'con', 'por', 'para'},
        'en': {'the', 'a', 'an', 'and', 'but', 'if', 'or', 'with', 'for', 'at', 'by'},
        'fr': {'le', 'la', 'les', 'un', 'une', 'des', 'et', 'ou', 'mais', 'dans'},
        'pt': {'o', 'a', 'os', 'as', 'um', 'uma', 'e', 'mas', 'ou', 'com', 'por'}
    }
    return stops_by_lang.get(lang_code, stops_by_lang['en'])

def get_stopwords_for_spacy(lang_code: str, nlp) -> Set[str]:
    """
    NOMBRE PRESERVADO. Ahora normaliza las stopwords de spaCy para que 
    filtren palabras con tilde correctamente.
    """
    spacy_stops = nlp.Defaults.stop_words if hasattr(nlp.Defaults, 'stop_words') else set()
    custom_stops = get_custom_stopwords(lang_code)
    combined = spacy_stops.union(custom_stops)
    # Normalizamos todas para una comparación ciega a tildes
    return {_normalize_caseless(word) for word in combined}

def process_text(text: str, nlp, lang_code: str) -> List[str]:
    """
    NOMBRE PRESERVADO. Lógica mejorada: usa normalización para que 'Análisis' 
    sea filtrado si 'analisis' está en la lista de stopwords.
    """
    try:
        if not text: return []
        doc = nlp(text)
        stopwords = get_stopwords_for_spacy(lang_code, nlp)
        processed_tokens = []
        
        for token in doc:
            lemma = token.lemma_.lower()
            # Normalizamos el lema para la comparación
            norm_lemma = _normalize_caseless(lemma)
            
            if (norm_lemma not in stopwords and 
                not token.is_punct and 
                not token.is_space and 
                lemma not in SYMBOLS_AND_NUMBERS and
                len(norm_lemma) > 1):
                processed_tokens.append(lemma)
        return processed_tokens
    except Exception as e:
        logger.error(f"Error en process_text: {str(e)}")
        return []

def clean_text(text: str) -> str:
    """NOMBRE PRESERVADO. Limpia espacios y símbolos manteniendo caracteres latinos."""
    if not text: return ""
    cleaned = ''.join(char for char in text if char not in SYMBOLS_AND_NUMBERS)
    return ' '.join(cleaned.split()).strip()