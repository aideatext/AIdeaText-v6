#modules/morphosyntax/morphosyntax_interface.py
import streamlit as st
from streamlit_float import *
from streamlit_antd_components import *
from streamlit.components.v1 import html
import spacy
from spacy import displacy
import spacy_streamlit
import pandas as pd
import base64
import re

# Importar desde morphosyntax_process.py
from .morphosyntax_process import (
    process_morphosyntactic_input,
    format_analysis_results,
    perform_advanced_morphosyntactic_analysis,  # Añadir esta importación
    get_repeated_words_colors,                  # Y estas también
    highlight_repeated_words,
    POS_COLORS,
    POS_TRANSLATIONS
)

from ..utils.widget_utils import generate_unique_key

from ..database.backUp.morphosintax_mongo_db import store_student_morphosyntax_result
from ..database.chat_mongo_db import store_chat_history, get_chat_history

# from ..database.morphosintaxis_export import export_user_interactions

import logging
logger = logging.getLogger(__name__)

############################################################################################################
def display_morphosyntax_interface(lang_code, nlp_models, morpho_t):
    try:
        # 1. Inicializar el estado morfosintáctico si no existe
        if 'morphosyntax_state' not in st.session_state:
            st.session_state.morphosyntax_state = {
                'input_text': "",
                'analysis_count': 0,
                'last_analysis': None
            }

        # 2. Campo de entrada de texto con key única basada en el contador
        input_key = f"morpho_input_{st.session_state.morphosyntax_state['analysis_count']}"
        
        sentence_input = st.text_area(
            morpho_t.get('morpho_input_label', 'Enter text to analyze'),
            height=150,
            placeholder=morpho_t.get('morpho_input_placeholder', 'Enter your text here...'),
            key=input_key
        )

        # 3. Actualizar el estado con el texto actual
        st.session_state.morphosyntax_state['input_text'] = sentence_input

        # 4. Crear columnas para el botón
        col1, col2, col3 = st.columns([2,1,2])
        
        # 5. Botón de análisis en la columna central
        with col1:
            analyze_button = st.button(
                morpho_t.get('morpho_analyze_button', 'Analyze Morphosyntax'),
                key=f"morpho_button_{st.session_state.morphosyntax_state['analysis_count']}",
                type="primary",  # Nuevo en Streamlit 1.39.0
                icon="🔍",      # Nuevo en Streamlit 1.39.0
                disabled=not bool(sentence_input.strip()),  # Se activa solo cuando hay texto
                use_container_width=True
            )

        # 6. Lógica de análisis
        if analyze_button and sentence_input.strip():  # Verificar que haya texto y no solo espacios
            try:
                with st.spinner(morpho_t.get('processing', 'Processing...')):
                    # Obtener el modelo específico del idioma y procesar el texto
                    doc = nlp_models[lang_code](sentence_input)
                    
                    # Realizar análisis morfosintáctico con el mismo modelo
                    advanced_analysis = perform_advanced_morphosyntactic_analysis(
                        sentence_input, 
                        nlp_models[lang_code]
                    )    
    
                    # Guardar resultado en el estado de la sesión
                    st.session_state.morphosyntax_result = {
                        'doc': doc,
                        'advanced_analysis': advanced_analysis
                    }
    
                    # Incrementar el contador de análisis
                    st.session_state.morphosyntax_state['analysis_count'] += 1
    
                    # Guardar el análisis en la base de datos
                    if store_student_morphosyntax_result(
                        username=st.session_state.username,
                        text=sentence_input,
                        arc_diagrams=advanced_analysis['arc_diagrams']
                    ):
                        st.success(morpho_t.get('success_message', 'Analysis saved successfully'))
                        
                        # Mostrar resultados
                        display_morphosyntax_results(
                            st.session_state.morphosyntax_result, 
                            lang_code, 
                            morpho_t
                        )
                    else:
                        st.error(morpho_t.get('error_message', 'Error saving analysis'))
                    
            except Exception as e:
                logger.error(f"Error en análisis morfosintáctico: {str(e)}")
                st.error(morpho_t.get('error_processing', f'Error processing text: {str(e)}'))
                
        # 7. Mostrar resultados previos si existen
        elif 'morphosyntax_result' in st.session_state and st.session_state.morphosyntax_result is not None:
            display_morphosyntax_results(
                st.session_state.morphosyntax_result, 
                lang_code, 
                morpho_t
            )
        elif not sentence_input.strip():
            st.info(morpho_t.get('morpho_initial_message', 'Enter text to begin analysis'))
            
    except Exception as e:
        logger.error(f"Error general en display_morphosyntax_interface: {str(e)}")
        st.error("Se produjo un error. Por favor, intente de nuevo.")
        st.error(f"Detalles del error: {str(e)}")  # Añadido para mejor debugging

############################################################################################################
def display_morphosyntax_results(result, lang_code, morpho_t):
    """
    Muestra los resultados del análisis morfosintáctico.
    Args:
        result: Resultado del análisis
        lang_code: Código del idioma
        t: Diccionario de traducciones
    """
    # Obtener el diccionario de traducciones morfosintácticas
    # morpho_t = t.get('MORPHOSYNTACTIC', {})
    
    if result is None:
        st.warning(morpho_t.get('no_results', 'No results available'))
        return

    doc = result['doc']
    advanced_analysis = result['advanced_analysis']
    
    # Mostrar leyenda
    st.markdown(f"##### {morpho_t.get('legend', 'Legend: Grammatical categories')}")
    legend_html = "<div style='display: flex; flex-wrap: wrap;'>"
    for pos, color in POS_COLORS.items():
        if pos in POS_TRANSLATIONS[lang_code]:
            legend_html += f"<div style='margin-right: 10px;'><span style='background-color: {color}; padding: 2px 5px;'>{POS_TRANSLATIONS[lang_code][pos]}</span></div>"
    legend_html += "</div>"
    st.markdown(legend_html, unsafe_allow_html=True)

    # Mostrar análisis de palabras repetidas
    word_colors = get_repeated_words_colors(doc)
    with st.expander(morpho_t.get('repeated_words', 'Repeated words'), expanded=True):
        highlighted_text = highlight_repeated_words(doc, word_colors)
        st.markdown(highlighted_text, unsafe_allow_html=True)
    
    # Mostrar estructura de oraciones
    with st.expander(morpho_t.get('sentence_structure', 'Sentence structure'), expanded=True):
        for i, sent_analysis in enumerate(advanced_analysis['sentence_structure']):
            sentence_str = (
                f"**{morpho_t.get('sentence', 'Sentence')} {i+1}** "  # Aquí está el cambio
                f"{morpho_t.get('root', 'Root')}: {sent_analysis['root']} ({sent_analysis['root_pos']}) -- "  # Y aquí
                f"{morpho_t.get('subjects', 'Subjects')}: {', '.join(sent_analysis['subjects'])} -- "  # Y aquí
                f"{morpho_t.get('objects', 'Objects')}: {', '.join(sent_analysis['objects'])} -- "  # Y aquí
                f"{morpho_t.get('verbs', 'Verbs')}: {', '.join(sent_analysis['verbs'])}"  # Y aquí
            )
            st.markdown(sentence_str)

    # Mostrar análisis de categorías gramaticales # Mostrar análisis morfológico
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander(morpho_t.get('pos_analysis', 'Part of speech'), expanded=True):
            pos_df = pd.DataFrame(advanced_analysis['pos_analysis'])
            
            # Traducir las etiquetas POS a sus nombres en el idioma seleccionado
            pos_df['pos'] = pos_df['pos'].map(lambda x: POS_TRANSLATIONS[lang_code].get(x, x))
            
            # Renombrar las columnas para mayor claridad
            pos_df = pos_df.rename(columns={
                'pos': morpho_t.get('grammatical_category', 'Grammatical category'),
                'count': morpho_t.get('count', 'Count'),
                'percentage': morpho_t.get('percentage', 'Percentage'),
                'examples': morpho_t.get('examples', 'Examples')
            })
                        
            # Mostrar el dataframe
            st.dataframe(pos_df)
    
    with col2:
        with st.expander(morpho_t.get('morphological_analysis', 'Morphological Analysis'), expanded=True):
            # 1. Crear el DataFrame inicial
            morph_df = pd.DataFrame(advanced_analysis['morphological_analysis'])
            
            # 2. Primero renombrar las columnas usando las traducciones de la interfaz
            column_mapping = {
                'text': morpho_t.get('word', 'Word'),
                'lemma': morpho_t.get('lemma', 'Lemma'),
                'pos': morpho_t.get('grammatical_category', 'Grammatical category'),
                'dep': morpho_t.get('dependency', 'Dependency'),
                'morph': morpho_t.get('morphology', 'Morphology')
            }
            
            # 3. Aplicar el renombrado
            morph_df = morph_df.rename(columns=column_mapping)
            
            # 4. Traducir las categorías gramaticales usando POS_TRANSLATIONS global
            grammatical_category = morpho_t.get('grammatical_category', 'Grammatical category')
            morph_df[grammatical_category] = morph_df[grammatical_category].map(lambda x: POS_TRANSLATIONS[lang_code].get(x, x))
    
            # 2.2 Traducir dependencias usando traducciones específicas
            dep_translations = {
                    
                'es': {
                    'ROOT': 'RAÍZ', 'nsubj': 'sujeto nominal', 'obj': 'objeto', 'iobj': 'objeto indirecto',
                    'csubj': 'sujeto clausal', 'ccomp': 'complemento clausal', 'xcomp': 'complemento clausal abierto',
                    'obl': 'oblicuo', 'vocative': 'vocativo', 'expl': 'expletivo', 'dislocated': 'dislocado',
                    'advcl': 'cláusula adverbial', 'advmod': 'modificador adverbial', 'discourse': 'discurso',
                    'aux': 'auxiliar', 'cop': 'cópula', 'mark': 'marcador', 'nmod': 'modificador nominal',
                    'appos': 'aposición', 'nummod': 'modificador numeral', 'acl': 'cláusula adjetiva',
                    'amod': 'modificador adjetival', 'det': 'determinante', 'clf': 'clasificador',
                    'case': 'caso', 'conj': 'conjunción', 'cc': 'coordinante', 'fixed': 'fijo',
                    'flat': 'plano', 'compound': 'compuesto', 'list': 'lista', 'parataxis': 'parataxis',
                    'orphan': 'huérfano', 'goeswith': 'va con', 'reparandum': 'reparación', 'punct': 'puntuación'
                },
                    
                'en': {
                    'ROOT': 'ROOT', 'nsubj': 'nominal subject', 'obj': 'object',
                    'iobj': 'indirect object', 'csubj': 'clausal subject', 'ccomp': 'clausal complement', 'xcomp': 'open clausal complement',
                    'obl': 'oblique', 'vocative': 'vocative', 'expl': 'expletive', 'dislocated': 'dislocated', 'advcl': 'adverbial clause modifier',
                    'advmod': 'adverbial modifier', 'discourse': 'discourse element', 'aux': 'auxiliary', 'cop': 'copula', 'mark': 'marker',
                    'nmod': 'nominal modifier', 'appos': 'appositional modifier', 'nummod': 'numeric modifier', 'acl': 'clausal modifier of noun',
                    'amod': 'adjectival modifier', 'det': 'determiner', 'clf': 'classifier', 'case': 'case marking',
                    'conj': 'conjunct', 'cc': 'coordinating conjunction', 'fixed': 'fixed multiword expression',
                    'flat': 'flat multiword expression', 'compound': 'compound', 'list': 'list', 'parataxis': 'parataxis', 'orphan': 'orphan',
                    'goeswith': 'goes with', 'reparandum': 'reparandum', 'punct': 'punctuation'
                },
                    
                'fr': {
                    'ROOT': 'RACINE', 'nsubj': 'sujet nominal', 'obj': 'objet', 'iobj': 'objet indirect',
                    'csubj': 'sujet phrastique', 'ccomp': 'complément phrastique', 'xcomp': 'complément phrastique ouvert', 'obl': 'oblique',
                    'vocative': 'vocatif', 'expl': 'explétif', 'dislocated': 'disloqué', 'advcl': 'clause adverbiale', 'advmod': 'modifieur adverbial',
                    'discourse': 'élément de discours', 'aux': 'auxiliaire', 'cop': 'copule', 'mark': 'marqueur', 'nmod': 'modifieur nominal',
                    'appos': 'apposition', 'nummod': 'modifieur numéral', 'acl': 'clause relative', 'amod': 'modifieur adjectival', 'det': 'déterminant',
                    'clf': 'classificateur', 'case': 'marqueur de cas', 'conj': 'conjonction', 'cc': 'coordination', 'fixed': 'expression figée',
                    'flat': 'construction plate', 'compound': 'composé', 'list': 'liste', 'parataxis': 'parataxe', 'orphan': 'orphelin',
                    'goeswith': 'va avec', 'reparandum': 'réparation', 'punct': 'ponctuation'
                }
            }
    
            dependency = morpho_t.get('dependency', 'Dependency')
            morph_df[dependency] = morph_df[dependency].map(lambda x: dep_translations[lang_code].get(x, x))
                
            morph_translations = {
                'es': {
                    'Gender': 'Género', 'Number': 'Número', 'Case': 'Caso', 'Definite': 'Definido',
                    'PronType': 'Tipo de Pronombre', 'Person': 'Persona', 'Mood': 'Modo',
                    'Tense': 'Tiempo', 'VerbForm': 'Forma Verbal', 'Voice': 'Voz',
                    'Fem': 'Femenino', 'Masc': 'Masculino', 'Sing': 'Singular', 'Plur': 'Plural',
                    'Ind': 'Indicativo', 'Sub': 'Subjuntivo', 'Imp': 'Imperativo', 'Inf': 'Infinitivo',
                    'Part': 'Participio', 'Ger': 'Gerundio', 'Pres': 'Presente', 'Past': 'Pasado',
                    'Fut': 'Futuro', 'Perf': 'Perfecto', 'Imp': 'Imperfecto'
                },
                    
                'en': {
                    'Gender': 'Gender', 'Number': 'Number', 'Case': 'Case', 'Definite': 'Definite', 'PronType': 'Pronoun Type', 'Person': 'Person',
                    'Mood': 'Mood', 'Tense': 'Tense', 'VerbForm': 'Verb Form', 'Voice': 'Voice',
                    'Fem': 'Feminine', 'Masc': 'Masculine', 'Sing': 'Singular', 'Plur': 'Plural', 'Ind': 'Indicative',
                    'Sub': 'Subjunctive', 'Imp': 'Imperative', 'Inf': 'Infinitive', 'Part': 'Participle',
                    'Ger': 'Gerund', 'Pres': 'Present', 'Past': 'Past', 'Fut': 'Future', 'Perf': 'Perfect', 'Imp': 'Imperfect'
                },
                    
                'fr': {
                    'Gender': 'Genre', 'Number': 'Nombre', 'Case': 'Cas', 'Definite': 'Défini', 'PronType': 'Type de Pronom',
                    'Person': 'Personne', 'Mood': 'Mode', 'Tense': 'Temps', 'VerbForm': 'Forme Verbale', 'Voice': 'Voix',
                    'Fem': 'Féminin', 'Masc': 'Masculin', 'Sing': 'Singulier', 'Plur': 'Pluriel', 'Ind': 'Indicatif',
                    'Sub': 'Subjonctif', 'Imp': 'Impératif', 'Inf': 'Infinitif', 'Part': 'Participe',
                    'Ger': 'Gérondif', 'Pres': 'Présent', 'Past': 'Passé', 'Fut': 'Futur', 'Perf': 'Parfait', 'Imp': 'Imparfait'
                }
            }            
    
            def translate_morph(morph_string, lang_code):
                for key, value in morph_translations[lang_code].items():
                    morph_string = morph_string.replace(key, value)
                return morph_string
                
            morphology = morpho_t.get('morphology', 'Morphology')
            morph_df[morphology] = morph_df[morphology].apply(lambda x: translate_morph(x, lang_code))
                
            st.dataframe(morph_df)

    # Mostrar diagramas de arco
    with st.expander(morpho_t.get('arc_diagram', 'Syntactic analysis: Arc diagram'), expanded=True):
        sentences = list(doc.sents)
        arc_diagrams = []
        
        for i, sent in enumerate(sentences):
            st.subheader(f"{morpho_t.get('sentence', 'Sentence')} {i+1}")
            html = displacy.render(sent, style="dep", options={"distance": 100})
            html = html.replace('height="375"', 'height="200"')
            html = re.sub(r'<svg[^>]*>', lambda m: m.group(0).replace('height="450"', 'height="300"'), html)
            html = re.sub(r'<g [^>]*transform="translate\((\d+),(\d+)\)"', 
                         lambda m: f'<g transform="translate({m.group(1)},50)"', html)
            st.write(html, unsafe_allow_html=True)
            arc_diagrams.append(html)

    # Botón de exportación
    # if st.button(morpho_t.get('export_button', 'Export Analysis')):
    #    pdf_buffer = export_user_interactions(st.session_state.username, 'morphosyntax')
    #    st.download_button(
    #        label=morpho_t.get('download_pdf', 'Download PDF'),
    #        data=pdf_buffer,
    #        file_name="morphosyntax_analysis.pdf",
    #        mime="application/pdf"
    #    )