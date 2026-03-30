# modules/studentact/claude_recommendations.py
import os
import anthropic
import streamlit as st
import logging
import time
import json
from datetime import datetime, timezone

# Local imports
from ..utils.widget_utils import generate_unique_key
from ..database.backUp.current_situation_mongo_db import store_current_situation_result

logger = logging.getLogger(__name__)

# Define text types
TEXT_TYPES = {
    'es': {
        'academic_article': 'artículo académico',
        'university_work': 'trabajo universitario',
        'general_communication': 'comunicación general'
    },
    'en': {
        'academic_article': 'academic article',
        'university_work': 'university work',
        'general_communication': 'general communication'
    },
    'fr': {
        'academic_article': 'article académique',
        'university_work': 'travail universitaire',
        'general_communication': 'communication générale'
    },
    'pt': {
        'academic_article': 'artigo acadêmico',
        'university_work': 'trabalho universitário',
        'general_communication': 'comunicação geral'
    }
}

# Cache for recommendations to avoid redundant API calls
recommendation_cache = {}

def get_recommendation_cache_key(text, metrics, text_type, lang_code):
    """
    Generate a cache key for recommendations.
    """
    # Create a simple hash based on text content and metrics
    text_hash = hash(text[:1000])  # Only use first 1000 chars for hashing
    metrics_hash = hash(json.dumps(metrics, sort_keys=True))
    return f"{text_hash}_{metrics_hash}_{text_type}_{lang_code}"

def format_metrics_for_claude(metrics, lang_code, text_type):
    """
    Format metrics in a way that's readable for Claude
    """
    formatted_metrics = {}
    for key, value in metrics.items():
        if isinstance(value, (int, float)):
            formatted_metrics[key] = round(value, 2)
        else:
            formatted_metrics[key] = value
    
    # Add context about what type of text this is
    text_type_label = TEXT_TYPES.get(lang_code, {}).get(text_type, text_type)
    formatted_metrics['text_type'] = text_type_label
    
    return formatted_metrics

def generate_claude_recommendations(text, metrics, text_type, lang_code):
    """
    Generate personalized recommendations using Claude API.
    """
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("Claude API key not found in environment variables")
            return get_fallback_recommendations(lang_code)
        
        # Check cache first
        cache_key = get_recommendation_cache_key(text, metrics, text_type, lang_code)
        if cache_key in recommendation_cache:
            logger.info("Using cached recommendations")
            return recommendation_cache[cache_key]
        
        # Format metrics for Claude
        formatted_metrics = format_metrics_for_claude(metrics, lang_code, text_type)
        
        # Determine language for prompt
        if lang_code == 'es':
            system_prompt = """Eres un asistente especializado en análisis de textos académicos y comunicación escrita. 
            Tu tarea es analizar el texto del usuario y proporcionar recomendaciones personalizadas.
            Usa un tono constructivo y específico. Sé claro y directo con tus sugerencias.
            """
            user_prompt = f"""Por favor, analiza este texto de tipo '{formatted_metrics['text_type']}' 
            y proporciona recomendaciones personalizadas para mejorarlo.
            
            MÉTRICAS DE ANÁLISIS:
            {json.dumps(formatted_metrics, indent=2, ensure_ascii=False)}
            
            TEXTO A ANALIZAR:
            {text[:2000]}  # Limitamos el texto para evitar exceder tokens
            
            Proporciona tu análisis con el siguiente formato:
            1. Un resumen breve (2-3 frases) del análisis general 
            2. 3-4 recomendaciones específicas y accionables (cada una de 1-2 frases)
            3. Un ejemplo concreto de mejora tomado del propio texto del usuario
            4. Una sugerencia sobre qué herramienta de AIdeaText usar (Análisis Morfosintáctico, Análisis Semántico o Análisis del Discurso)
            
            Tu respuesta debe ser concisa y no exceder los 300 palabras."""
        
        elif lang_code == 'fr':
            system_prompt = """Vous êtes un assistant spécialisé dans l'analyse de textes académiques et de communication écrite.
            Votre tâche est d'analyser le texte de l'utilisateur et de fournir des recommandations personnalisées.
            Utilisez un ton constructif et spécifique. Soyez clair et direct dans vos suggestions.
            """
            user_prompt = f"""Veuillez analyser ce texte de type '{formatted_metrics['text_type']}' 
            et fournir des recommandations personnalisées pour l'améliorer.
            
            MÉTRIQUES D'ANALYSE:
            {json.dumps(formatted_metrics, indent=2, ensure_ascii=False)}
            
            TEXTE À ANALYSER:
            {text[:2000]}
            
            Fournissez votre analyse avec le format suivant:
            1. Un résumé bref (2-3 phrases) de l'analyse générale
            2. 3-4 recommandations spécifiques et réalisables (chacune de 1-2 phrases)
            3. Un exemple concret d'amélioration tiré du texte même de l'utilisateur
            4. Une suggestion sur quel outil AIdeaText utiliser (Analyse Morphosyntaxique, Analyse Sémantique ou Analyse du Discours)
            
            Votre réponse doit être concise et ne pas dépasser 300 mots."""
            
        elif lang_code == 'pt':
            system_prompt = """Você é um assistente especializado na análise de textos acadêmicos e comunicação escrita.
            Sua tarefa é analisar o texto do usuário e fornecer recomendações personalizadas.
            Use um tom construtivo e específico. Seja claro e direto com suas sugestões.
            """
            user_prompt = f"""Por favor, analise este texto do tipo '{formatted_metrics['text_type']}' 
            e forneça recomendações personalizadas para melhorá-lo.
            
            MÉTRICAS DE ANÁLISE:
            {json.dumps(formatted_metrics, indent=2, ensure_ascii=False)}
            
            TEXTO PARA ANALISAR:
            {text[:2000]}
            
            Forneça sua análise com o seguinte formato:
            1. Um breve resumo (2-3 frases) da análise geral
            2. 3-4 recomendações específicas e acionáveis (cada uma com 1-2 frases)
            3. Um exemplo concreto de melhoria retirado do próprio texto do usuário
            4. Uma sugestão sobre qual ferramenta do AIdeaText usar (Análise Morfossintática, Análise Semântica ou Análise do Discurso)
            
            Sua resposta deve ser concisa e não exceder 300 palavras."""
         
        else:
            # Default to English
            system_prompt = """You are an assistant specialized in analyzing academic texts and written communication.
            Your task is to analyze the user's text and provide personalized recommendations.
            Use a constructive and specific tone. Be clear and direct with your suggestions.
            """
            user_prompt = f"""Please analyze this text of type '{formatted_metrics['text_type']}' 
            and provide personalized recommendations to improve it.
            
            ANALYSIS METRICS:
            {json.dumps(formatted_metrics, indent=2, ensure_ascii=False)}
            
            TEXT TO ANALYZE:
            {text[:2000]}  # Limiting text to avoid exceeding tokens
            
            Provide your analysis with the following format:
            1. A brief summary (2-3 sentences) of the general analysis
            2. 3-4 specific and actionable recommendations (each 1-2 sentences)
            3. A concrete example of improvement taken from the user's own text
            4. A suggestion about which AIdeaText tool to use (Morphosyntactic Analysis, Semantic Analysis or Discourse Analysis)
            
            Your response should be concise and not exceed 300 words."""
        
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Call Claude API
        start_time = time.time()
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        logger.info(f"Claude API call completed in {time.time() - start_time:.2f} seconds")
        
        # Extract recommendations
        recommendations = response.content[0].text
        
        # Cache the result
        recommendation_cache[cache_key] = recommendations
        
        return recommendations
    except Exception as e:
        logger.error(f"Error generating recommendations with Claude: {str(e)}")
        return get_fallback_recommendations(lang_code)

##################################################################################
##################################################################################
def get_fallback_recommendations(lang_code):
    """
    Return fallback recommendations if Claude API fails
    """
    if lang_code == 'es':
        return """
        **Análisis General**
        Tu texto presenta una estructura básica adecuada, pero hay áreas que pueden mejorarse para mayor claridad y cohesión.
        **Recomendaciones**:
        - Intenta variar tu vocabulario para evitar repeticiones innecesarias
        - Considera revisar la longitud de tus oraciones para mantener un mejor ritmo
        - Asegúrate de establecer conexiones claras entre las ideas principales
        - Revisa la consistencia en el uso de tiempos verbales
        **Herramienta recomendada**: 
        Te sugerimos utilizar el Análisis Morfosintáctico para identificar patrones en tu estructura de oraciones.
        """
        
    elif lang_code == 'fr':
        return """
        **Analyse Générale**
        Votre texte présente une structure de base adéquate, mais certains aspects pourraient être améliorés pour plus de clarté et de cohésion.
        
        **Recommandations**:
        - Essayez de varier votre vocabulaire pour éviter les répétitions inutiles
        - Envisagez de revoir la longueur de vos phrases pour maintenir un meilleur rythme
        - Assurez-vous d'établir des liens clairs entre les idées principales
        - Vérifiez la cohérence dans l'utilisation des temps verbaux
        
        **Outil recommandé**: 
        Nous vous suggérons d'utiliser l'Analyse Morphosyntaxique pour identifier les modèles dans la structure de vos phrases.
        """
    
    elif lang_code == 'pt':
        return """
        **Análise Geral**
        Seu texto apresenta uma estrutura básica adequada, mas há áreas que podem ser melhoradas para maior clareza e coesão.
        
        **Recomendações**:
        - Tente variar seu vocabulário para evitar repetições desnecessárias
        - Considere revisar o comprimento de suas frases para manter um melhor ritmo
        - Certifique-se de estabelecer conexões claras entre as ideias principais
        - Revise a consistência no uso dos tempos verbais
        
        **Ferramenta recomendada**: 
        Sugerimos utilizar a Análise Morfossintática para identificar padrões na sua estrutura de frases.
        """
    
    else:
        return """
        **General Analysis**
        Your text presents an adequate basic structure, but there are areas that can be improved for better clarity and cohesion.
        
        **Recommendations**:
        - Try to vary your vocabulary to avoid unnecessary repetition
        - Consider reviewing the length of your sentences to maintain a better rhythm
        - Make sure to establish clear connections between main ideas
        - Check consistency in the use of verb tenses
        
        **Recommended tool**: 
        We suggest using Morphosyntactic Analysis to identify patterns in your sentence structure.
        """


#######################################
#######################################
def store_recommendations(username, text, metrics, text_type, recommendations):
    """
    Store the recommendations in the database
    """
    try:
        # Importar la función de almacenamiento de recomendaciones
        from ..database.backUp.claude_recommendations_mongo_db import store_claude_recommendation
        
        # Guardar usando la nueva función especializada
        result = store_claude_recommendation(
            username=username,
            text=text,
            metrics=metrics,
            text_type=text_type,
            recommendations=recommendations
        )
        
        logger.info(f"Recommendations stored successfully: {result}")
        return result
    except Exception as e:
        logger.error(f"Error storing recommendations: {str(e)}")
        return False


##########################################
##########################################
def display_personalized_recommendations(text, metrics, text_type, lang_code, t):
    """
    Display personalized recommendations based on text analysis
    """
    try:
        # Generate recommendations
        recommendations = generate_claude_recommendations(text, metrics, text_type, lang_code)
        
        # Format and display recommendations in a nice container
        st.markdown("### 📝 " + t.get('recommendations_title', 'Personalized Recommendations'))
        
        with st.container():
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 10px; 
                background-color: #f8f9fa; margin-bottom: 20px;">
                {recommendations}
            </div>
            """, unsafe_allow_html=True)
            
            # Add prompt to use assistant
            st.info("💡 **" + t.get('assistant_prompt', 'For further improvement:') + "** " + 
                   t.get('assistant_message', 'Open the virtual assistant (powered by Claude AI) in the upper left corner by clicking the arrow next to the logo.'))
            
            # Add save button
            col1, col2, col3 = st.columns([1,1,1])
            with col2:
                if st.button(
                    t.get('save_button', 'Save Analysis'),
                    key=generate_unique_key("claude_recommendations", "save"),
                    type="primary",
                    use_container_width=True
                ):
                    if 'username' in st.session_state:
                        success = store_recommendations(
                            st.session_state.username,
                            text,
                            metrics,
                            text_type,
                            recommendations
                        )
                        if success:
                            st.success(t.get('save_success', 'Analysis saved successfully'))
                        else:
                            st.error(t.get('save_error', 'Error saving analysis'))
                    else:
                        st.error(t.get('login_required', 'Please log in to save analysis'))
    
    except Exception as e:
        logger.error(f"Error displaying recommendations: {str(e)}")
        st.error(t.get('recommendations_error', 'Error generating recommendations. Please try again later.'))