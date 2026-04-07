# translations/__init__.py
import logging
from importlib import import_module

logger = logging.getLogger(__name__)

def get_translations(lang_code):
    # Asegurarse de que lang_code sea válido
    if lang_code not in ['es', 'en', 'fr', 'pt']:
        print(f"Invalid lang_code: {lang_code}. Defaulting to 'es'")
        lang_code = 'es'

    try:
        # Importar dinámicamente el módulo de traducción
        translation_module = import_module(f'.{lang_code}', package='translations')
        translations = getattr(translation_module, 'TRANSLATIONS', {})
    except ImportError:
        logger.warning(f"Translation module for {lang_code} not found. Falling back to English.")
        # Importar el módulo de inglés como fallback
        translation_module = import_module('.en', package='translations')
        translations = getattr(translation_module, 'TRANSLATIONS', {})

    def get_text(key, section='COMMON', default=''):
        return translations.get(section, {}).get(key, default)

    return {
        'get_text': get_text,
        **translations.get('COMMON', {}),
        **translations.get('TABS', {}),
        **translations.get('MORPHOSYNTACTIC', {}),
        **translations.get('SEMANTIC', {}),
        **translations.get('DISCOURSE', {}),
        **translations.get('ACTIVITIES', {}),
        **translations.get('FEEDBACK', {}),
        **translations.get('TEXT_TYPES', {}),
        **translations.get('CURRENT_SITUATION', {}),
        # chatbot se expone como dict anidado (NO flat) para que
        # t.get('chatbot', {}) retorne el dict completo al sidebar_chat
        'chatbot': translations.get('CHATBOT', {}),
        # sub-secciones accesibles por nombre para professor_ui y otros
        'SEMANTIC': translations.get('SEMANTIC', {}),
        'DISCOURSE': translations.get('DISCOURSE', {}),
        'FEEDBACK': translations.get('FEEDBACK', {}),
    }

# Nueva función para obtener traducciones específicas del landing page
def get_landing_translations(lang_code):
    # Asegurarse de que lang_code sea válido
    if lang_code not in ['es', 'en', 'fr', 'pt']:
        print(f"Invalid lang_code: {lang_code}. Defaulting to 'es'")
        lang_code = 'es'

    try:
        # Importar dinámicamente el módulo de traducción del landing page
        from .landing_translations import LANDING_TRANSLATIONS
        
        # Asegurarse de que el idioma esté disponible, si no usar español como fallback
        if lang_code not in LANDING_TRANSLATIONS:
            logger.warning(f"Landing translations for {lang_code} not found. Falling back to Spanish.")
            lang_code = 'es'
            
        return LANDING_TRANSLATIONS[lang_code]
    except ImportError:
        logger.warning("Landing translations module not found. Using default translations.")
        # Crear un conjunto mínimo de traducciones por defecto
        return {
            'select_language': 'Select language' if lang_code == 'en' else 'Selecciona tu idioma',
            'login': 'Login' if lang_code == 'en' else 'Iniciar Sesión',
            'register': 'Sign Up' if lang_code == 'en' else 'Registrarse',
            # Añadir más traducciones por defecto si es necesario
        }
