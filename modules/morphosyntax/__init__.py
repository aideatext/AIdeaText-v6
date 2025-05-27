from .morphosyntax_interface import (
    display_morphosyntax_interface,
    display_arc_diagram
    # display_morphosyntax_results
)

from .morphosyntax_process import (
    process_morphosyntactic_input, 
    format_analysis_results,
    perform_advanced_morphosyntactic_analysis,
    get_repeated_words_colors,
    highlight_repeated_words,
    POS_COLORS,
    POS_TRANSLATIONS
)

__all__ = [
    'display_morphosyntax_interface',
    'display_arc_diagram',
    #'display_morphosyntax_results',
    'process_morphosyntactic_input',
    'format_analysis_results',
    'perform_advanced_morphosyntactic_analysis',
    'get_repeated_words_colors',
    'highlight_repeated_words',
    'POS_COLORS',
    'POS_TRANSLATIONS'
]

