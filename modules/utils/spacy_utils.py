# modules/spacy_utils.py
import spacy

def load_spacy_models():
    import spacy
    return {
        "es": spacy.load("es_core_news_md")
    }

#def load_spacy_models():
#    return {
#        'es': spacy.load("es_core_news_lg"),
#        'en': spacy.load("en_core_web_lg"),
#        'fr': spacy.load("fr_core_news_lg"),
#        'pt': spacy.load("pt_core_news_lg")
#    }

