
import spacy
nlp = spacy.load("es_core_news_md")
doc = nlp("Texto de prueba")
print("OK:", [t.text for t in doc])
