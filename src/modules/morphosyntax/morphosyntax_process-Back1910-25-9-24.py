#modules/morphosyntax/morphosyntax_process.py
from ..text_analysis.morpho_analysis import perform_advanced_morphosyntactic_analysis
from ..database.database_oldFromV2 import store_morphosyntax_result
import streamlit as st

def process_morphosyntactic_input(user_input, lang_code, nlp_models, t):
    if user_input.startswith('/analisis_morfosintactico'):
        # Extraer el texto entre corchetes
        text_to_analyze = user_input.split('[', 1)[1].rsplit(']', 1)[0]

        # Realizar el análisis morfosintáctico
        result = perform_advanced_morphosyntactic_analysis(text_to_analyze, nlp_models[lang_code])

        if result is None:
            response = t.get('morphosyntactic_analysis_error', 'Error in morphosyntactic analysis')
            return response, None, None

        # Preparar la respuesta
        response = t.get('morphosyntactic_analysis_completed', 'Morphosyntactic analysis completed')

        # Obtener todos los diagramas de arco
        visualizations = result['arc_diagram']

        return response, visualizations, result
    else:
        # Para otros tipos de input, simplemente devolver la respuesta del chatbot
        chatbot = st.session_state.morphosyntax_chatbot
        response = chatbot.generate_response(user_input, lang_code)
        return response, None, None
