# modules/text_analysis/stopwords.py
import spacy
from typing import Set, List

def get_custom_stopwords(lang_code: str) -> Set[str]:
    """
    Retorna un conjunto de stopwords personalizadas según el idioma.
    """
    # Stopwords base en español
    # Símbolos, números y caracteres especiales

    SYMBOLS_AND_NUMBERS = {
    # Números
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    
    # Signos de puntuación básicos
    '.', ',', ';', ':', '!', '¡', '?', '¿', '"', "'", 
    
    # Símbolos matemáticos
    '+', '-', '*', '/', '=', '<', '>', '%', 
    
    # Paréntesis y otros delimitadores
    '(', ')', '[', ']', '{', '}', 
    
    # Otros símbolos comunes
    '@', '#', '$', '€', '£', '¥', '&', '_', '|', '\\', '/', 
    
    # Caracteres especiales
    '•', '·', '…', '—', '–', '°', '´', '`', '^', '¨',
    
    # Símbolos de ordenamiento
    '§', '†', '‡', '¶',
    
    # Símbolos de copyright y marcas registradas
    '©', '®', '™',
    
    # Fracciones comunes
    '½', '¼', '¾', '⅓', '⅔',
    
    # Otros caracteres especiales
    '±', '×', '÷', '∞', '≠', '≤', '≥', '≈', '∑', '∏', '√',
    
    # Espacios y caracteres de control
    ' ', '\t', '\n', '\r', '\f', '\v'
}
    spanish_stopwords = {
        'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero', 'si',
        'de', 'del', 'al', 'a', 'ante', 'bajo', 'cabe', 'con', 'contra', 'de', 'desde',
        'en', 'entre', 'hacia', 'hasta', 'para', 'por', 'según', 'sin', 'sobre', 'tras',
        'que', 'más', 'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas',
        'muy', 'mucho', 'muchos', 'muchas', 'ser', 'estar', 'tener', 'hacer', 'como',
        'cuando', 'donde', 'quien', 'cual', 'mientras', 'sino', 'pues', 'porque',
        'cada', 'cual', 'cuales', 'cuanta', 'cuantas', 'cuanto', 'cuantos', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete', 'ocho', 'nueve', 'diez',
        'once', 'doce', 'trece', 'catorce', 'quince', 'dieciséis', 'diecisiete', 'dieciocho', 'diecinueve', 'veinte',
        'treinta', 'cuarenta', 'cincuenta', 'sesenta', 'setenta', 'ochenta', 'noventa', 'cien', 'mil', 'millón',
        'primero', 'segundo', 'tercero', 'cuarto', 'quinto', 'sexto', 'séptimo', 'octavo', 'noveno', 'décimo'
    }
    
    # Stopwords base en inglés
    english_stopwords = {
        'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for',
        'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his',
        'by', 'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my',
        'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if',
        'about', 'who', 'get', 'which', 'go', 'me',     'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
        'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty',
        'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety', 'hundred', 'thousand', 'million',
        'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh', 'eighth', 'ninth', 'tenth'
    }

    french_stopwords = {
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'mais', 'si',
    'à', 'dans', 'sur', 'pour', 'en', 'vers', 'par', 'avec', 'sans', 'sous', 'sur',
    'que', 'qui', 'quoi', 'dont', 'où', 'quand', 'comment', 'pourquoi',
    'ce', 'cet', 'cette', 'ces', 'mon', 'ton', 'son', 'ma', 'ta', 'sa',
    'mes', 'tes', 'ses', 'notre', 'votre', 'leur', 'nos', 'vos', 'leurs',
    'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
    'me', 'te', 'se', 'lui', 'leur', 'y', 'en', 'plus', 'moins',
    'très', 'trop', 'peu', 'beaucoup', 'assez', 'tout', 'toute', 'tous', 'toutes',
    'autre', 'autres', 'même', 'mêmes', 'tel', 'telle', 'tels', 'telles',
    'quel', 'quelle', 'quels', 'quelles', 'quelque', 'quelques',
    'aucun', 'aucune', 'aucuns', 'aucunes', 'plusieurs', 'chaque',
    'être', 'avoir', 'faire', 'dire', 'aller', 'venir', 'voir', 'savoir',
    'pouvoir', 'vouloir', 'falloir', 'devoir', 'croire', 'sembler',
    'alors', 'ainsi', 'car', 'donc', 'or', 'ni', 'ne', 'pas', 'plus',
    'jamais', 'toujours', 'parfois', 'souvent', 'maintenant', 'après',
    'avant', 'pendant', 'depuis', 'déjà', 'encore', 'ici', 'là',
    'oui', 'non', 'peut-être', 'bien', 'mal', 'aussi', 'surtout',
    'c\'est', 'j\'ai', 'n\'est', 'd\'un', 'd\'une', 'qu\'il', 'qu\'elle', 
    'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf', 'dix',
    'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize', 'dix-sept', 'dix-huit', 'dix-neuf', 'vingt',
    'trente', 'quarante', 'cinquante', 'soixante', 'soixante-dix', 'quatre-vingts', 'quatre-vingt-dix', 'cent', 'mille', 'million',
    'premier', 'deuxième', 'troisième', 'quatrième', 'cinquième', 'sixième', 'septième', 'huitième', 'neuvième', 'dixième'
}
    
    stopwords_dict = {
        'es': spanish_stopwords,
        'en': english_stopwords,
        'fr': french_stopwords
    }
    
    # Obtener stopwords del idioma especificado o devolver conjunto vacío si no existe
    return stopwords_dict.get(lang_code, set())

def process_text(text: str, lang_code: str, nlp) -> List[str]:
    """
    Procesa un texto completo, removiendo stopwords, símbolos y números.
    
    Args:
        text (str): Texto a procesar
        lang_code (str): Código del idioma ('es', 'en', 'fr')
        nlp: Modelo de spaCy cargado
    
    Returns:
        List[str]: Lista de tokens procesados
    """
    try:
        # Obtener stopwords personalizadas
        custom_stopwords = get_custom_stopwords(lang_code)
        
        # Procesar el texto con spaCy
        doc = nlp(text)
        
        # Filtrar y procesar tokens
        processed_tokens = []
        for token in doc:
            # Convertir a minúsculas y obtener el lema
            lemma = token.lemma_.lower()
            
            # Aplicar filtros
            if (len(lemma) >= 2 and  # Longitud mínima
                lemma not in custom_stopwords and  # No es stopword
                not token.is_punct and  # No es puntuación
                not token.is_space and  # No es espacio
                lemma not in SYMBOLS_AND_NUMBERS and  # No es símbolo o número
                not any(char in string.punctuation for char in lemma) and  # No contiene puntuación
                not any(char.isdigit() for char in lemma)):  # No contiene números
                
                processed_tokens.append(lemma)
        
        return processed_tokens
        
    except Exception as e:
        logger.error(f"Error en process_text: {str(e)}")
        return []

def clean_text(text: str) -> str:
    """
    Limpia un texto removiendo caracteres especiales y normalizando espacios.
    
    Args:
        text (str): Texto a limpiar
    
    Returns:
        str: Texto limpio
    """
    # Remover caracteres especiales y números
    cleaned = ''.join(char for char in text if char not in SYMBOLS_AND_NUMBERS)
    
    # Normalizar espacios
    cleaned = ' '.join(cleaned.split())
    
    return cleaned.strip()

def get_stopwords_for_spacy(lang_code: str, nlp) -> Set[str]:
    """
    Combina stopwords personalizadas con las de spaCy.
    
    Args:
        lang_code (str): Código del idioma
        nlp: Modelo de spaCy
        
    Returns:
        Set[str]: Conjunto combinado de stopwords
    """
    custom_stops = get_custom_stopwords(lang_code)
    spacy_stops = nlp.Defaults.stop_words if hasattr(nlp.Defaults, 'stop_words') else set()
    
    return custom_stops.union(spacy_stops)

# Asegúrate de exportar todas las funciones necesarias
__all__ = [
    'get_custom_stopwords',
    'process_text',
    'clean_text',
    'get_stopwords_for_spacy',
    'SYMBOLS_AND_NUMBERS'
]