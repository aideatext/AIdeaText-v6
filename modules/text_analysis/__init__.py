# modules/text_analysis/__init__.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Importaciones de morpho_analysis
from .morpho_analysis import (
    perform_advanced_morphosyntactic_analysis,
    get_repeated_words_colors,
    highlight_repeated_words,
    generate_arc_diagram,
    get_detailed_pos_analysis,
    get_morphological_analysis,
    get_sentence_structure_analysis,
    POS_COLORS,
    POS_TRANSLATIONS
)

# Importaciones de semantic_analysis
from .semantic_analysis import (
    create_concept_graph,
    visualize_concept_graph,
    identify_key_concepts
)


