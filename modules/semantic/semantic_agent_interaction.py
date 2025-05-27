# modules/semantic/semantic_agent_interaction.py
import os
import anthropic
import streamlit as st
import time
import json
import base64
import logging

from datetime import datetime, timezone
from io import BytesIO

# Local imports
from ..utils.widget_utils import generate_unique_key
from ..database.chat_mongo_db import store_chat_history

logger = logging.getLogger(__name__)

# Cache for conversation history to avoid redundant API calls
conversation_cache = {}

def get_conversation_cache_key(text, metrics, graph_data, lang_code):
    """
    Generate a cache key for conversations based on analysis data.
    """
    text_hash = hash(text[:1000])  # Only use first 1000 chars for hashing
    metrics_hash = hash(json.dumps(metrics, sort_keys=True))
    graph_hash = hash(graph_data[:100]) if graph_data else 0
    return f"{text_hash}_{metrics_hash}_{graph_hash}_{lang_code}"

def format_semantic_context(text, metrics, graph_data, lang_code):
    """
    Format the semantic analysis data for Claude's context.
    """
    formatted_data = {
        'text_sample': text[:2000],  # Limit text sample
        'key_concepts': metrics.get('key_concepts', []),
        'concept_centrality': metrics.get('concept_centrality', {}),
        'graph_description': "Network graph available" if graph_data else "No graph available",
        'language': lang_code
    }
    
    return json.dumps(formatted_data, indent=2, ensure_ascii=False)

def initiate_semantic_conversation(text, metrics, graph_data, lang_code):
    """
    Start a conversation with Claude about semantic analysis results.
    """
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("Claude API key not found in environment variables")
            return get_fallback_response(lang_code)
        
        # Check cache first
        cache_key = get_conversation_cache_key(text, metrics, graph_data, lang_code)
        if cache_key in conversation_cache:
            logger.info("Using cached conversation starter")
            return conversation_cache[cache_key]
        
        # Format context for Claude
        context = format_semantic_context(text, metrics, graph_data, lang_code)
        
        # Determine language for prompt
        if lang_code == 'es':
            system_prompt = """Eres un asistente especializado en análisis semántico de textos. 
            El usuario ha analizado un texto y quiere discutir los resultados contigo. 
            Estos son los datos del análisis:
            - Fragmento del texto analizado
            - Lista de conceptos clave identificados
            - Medidas de centralidad de los conceptos
            - Un grafo de relaciones conceptuales (si está disponible)
            
            Tu rol es:
            1. Demostrar comprensión del análisis mostrado
            2. Hacer preguntas relevantes sobre los resultados
            3. Ayudar al usuario a interpretar los hallazgos
            4. Sugerir posibles direcciones para profundizar el análisis
            
            Usa un tono profesional pero accesible. Sé conciso pero claro.
            """
            user_prompt = f"""Aquí están los resultados del análisis semántico:
            
            {context}
            
            Por favor:
            1. Haz un breve resumen de lo que notas en los resultados
            2. Formula 2-3 preguntas interesantes que podríamos explorar sobre estos datos
            3. Sugiere un aspecto del análisis que podría profundizarse
            
            Mantén tu respuesta bajo 250 palabras."""
        
        elif lang_code == 'fr':
            system_prompt = """Vous êtes un assistant spécialisé dans l'analyse sémantique de textes.
            L'utilisateur a analysé un texte et souhaite discuter des résultats avec vous.
            Voici les données d'analyse:
            - Extrait du texte analysé
            - Liste des concepts clés identifiés
            - Mesures de centralité des concepts
            - Un graphique des relations conceptuelles (si disponible)
            
            Votre rôle est:
            1. Démontrer une compréhension de l'analyse présentée
            2. Poser des questions pertinentes sur les résultats
            3. Aider l'utilisateur à interpréter les résultats
            4. Proposer des pistes pour approfondir l'analyse
            
            Utilisez un ton professionnel mais accessible. Soyez concis mais clair.
            """
            user_prompt = f"""Voici les résultats de l'analyse sémantique:
            
            {context}
            
            Veuillez:
            1. Faire un bref résumé de ce que vous remarquez dans les résultats
            2. Formuler 2-3 questions intéressantes que nous pourrions explorer
            3. Suggérer un aspect de l'analyse qui pourrait être approfondi
            
            Limitez votre réponse à 250 mots."""
            
        elif lang_code == 'pt':
            system_prompt = """Você é um assistente especializado em análise semântica de textos.
            O usuário analisou um texto e quer discutir os resultados com você.
            Aqui estão os dados da análise:
            - Trecho do texto analisado
            - Lista de conceitos-chave identificados
            - Medidas de centralidade dos conceitos
            - Um grafo de relações conceituais (se disponível)
            
            Seu papel é:
            1. Demonstrar compreensão da análise apresentada
            2. Fazer perguntas relevantes sobre os resultados
            3. Ajudar o usuário a interpretar os achados
            4. Sugerir possíveis direções para aprofundar a análise
            
            Use um tom profissional mas acessível. Seja conciso mas claro.
            """
            user_prompt = f"""Aqui estão os resultados da análise semântica:
            
            {context}
            
            Por favor:
            1. Faça um breve resumo do que você nota nos resultados
            2. Formule 2-3 perguntas interessantes que poderíamos explorar
            3. Sugira um aspecto da análise que poderia ser aprofundado
            
            Mantenha sua resposta em até 250 palavras."""
         
        else:  # Default to English
            system_prompt = """You are an assistant specialized in semantic text analysis.
            The user has analyzed a text and wants to discuss the results with you.
            Here is the analysis data:
            - Sample of the analyzed text
            - List of identified key concepts
            - Concept centrality measures
            - A concept relationship graph (if available)
            
            Your role is to:
            1. Demonstrate understanding of the shown analysis
            2. Ask relevant questions about the results
            3. Help the user interpret the findings
            4. Suggest possible directions to deepen the analysis
            
            Use a professional but accessible tone. Be concise but clear.
            """
            user_prompt = f"""Here are the semantic analysis results:
            
            {context}
            
            Please:
            1. Give a brief summary of what you notice in the results
            2. Formulate 2-3 interesting questions we could explore
            3. Suggest one aspect of the analysis that could be deepened
            
            Keep your response under 250 words."""
        
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Call Claude API
        start_time = time.time()
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        logger.info(f"Claude API call completed in {time.time() - start_time:.2f} seconds")
        
        # Extract response
        initial_response = response.content[0].text
        
        # Cache the result
        conversation_cache[cache_key] = initial_response
        
        return initial_response
        
    except Exception as e:
        logger.error(f"Error initiating semantic conversation: {str(e)}")
        return get_fallback_response(lang_code)

def continue_conversation(conversation_history, new_message, lang_code):
    """
    Continue an existing conversation about semantic analysis.
    """
    try:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("Claude API key not found in environment variables")
            return get_fallback_response(lang_code)
        
        # Prepare conversation history for Claude
        messages = []
        for msg in conversation_history:
            messages.append({
                "role": "user" if msg["sender"] == "user" else "assistant",
                "content": msg["message"]
            })
        
        # Add the new message
        messages.append({"role": "user", "content": new_message})
        
        # System prompt based on language
        if lang_code == 'es':
            system_prompt = """Continúa la conversación sobre el análisis semántico.
            Sé conciso pero útil. Responde en español."""
        elif lang_code == 'fr':
            system_prompt = """Continuez la conversation sur l'analyse sémantique.
            Soyez concis mais utile. Répondez en français."""
        elif lang_code == 'pt':
            system_prompt = """Continue a conversa sobre a análise semântica.
            Seja conciso mas útil. Responda em português."""
        else:
            system_prompt = """Continue the conversation about semantic analysis.
            Be concise but helpful. Respond in English."""
        
        # Initialize Claude client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Call Claude API
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1024,
            temperature=0.7,
            system=system_prompt,
            messages=messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        logger.error(f"Error continuing semantic conversation: {str(e)}")
        return get_fallback_response(lang_code)

def get_fallback_response(lang_code):
    """
    Return fallback response if Claude API fails.
    """
    if lang_code == 'es':
        return """Parece que hay un problema técnico. Por favor intenta de nuevo más tarde.
        
        Mientras tanto, aquí hay algunas preguntas que podrías considerar sobre tu análisis:
        1. ¿Qué conceptos tienen la mayor centralidad y por qué podría ser?
        2. ¿Hay conexiones inesperadas entre conceptos en tu grafo?
        3. ¿Cómo podrías profundizar en las relaciones entre los conceptos clave?"""
        
    elif lang_code == 'fr':
        return """Il semble y avoir un problème technique. Veuillez réessayer plus tard.
        
        En attendant, voici quelques questions que vous pourriez considérer:
        1. Quels concepts ont la plus grande centralité et pourquoi?
        2. Y a-t-il des connexions inattendues entre les concepts?
        3. Comment pourriez-vous approfondir les relations entre les concepts clés?"""
    
    elif lang_code == 'pt':
        return """Parece haver um problema técnico. Por favor, tente novamente mais tarde.
        
        Enquanto isso, aqui estão algumas perguntas que você poderia considerar:
        1. Quais conceitos têm maior centralidade e por que isso pode ocorrer?
        2. Há conexões inesperadas entre conceitos no seu grafo?
        3. Como você poderia aprofundar as relações entre os conceitos-chave?"""
    
    else:
        return """There seems to be a technical issue. Please try again later.
        
        Meanwhile, here are some questions you might consider about your analysis:
        1. Which concepts have the highest centrality and why might that be?
        2. Are there unexpected connections between concepts in your graph?
        3. How could you explore the relationships between key concepts further?"""

def store_conversation(username, text, metrics, graph_data, conversation):
    try:
        result = store_chat_history(
            username=username,
            messages=conversation,
            analysis_type='semantic_analysis',
            metadata={
                'text_sample': text[:500],
                'key_concepts': metrics.get('key_concepts', []),
                'graph_available': bool(graph_data)
            }
        )
        logger.info(f"Conversación semántica guardada: {result}")
        return result
    except Exception as e:
        logger.error(f"Error almacenando conversación semántica: {str(e)}")
        return False

def display_semantic_chat(text, metrics, graph_data, lang_code, t):
    """
    Display the chat interface for semantic analysis discussion.
    """
    try:
        # Initialize session state for conversation if not exists
        if 'semantic_chat' not in st.session_state:
            st.session_state.semantic_chat = {
                'history': [],
                'initialized': False
            }
        
        # Container for chat display
        chat_container = st.container()
        
        # Initialize conversation if not done yet
        if not st.session_state.semantic_chat['initialized']:
            with st.spinner(t.get('initializing_chat', 'Initializing conversation...')):
                initial_response = initiate_semantic_conversation(
                    text, metrics, graph_data, lang_code
                )
                
                st.session_state.semantic_chat['history'].append({
                    "sender": "assistant",
                    "message": initial_response
                })
                st.session_state.semantic_chat['initialized'] = True
                
                # Store initial conversation
                if 'username' in st.session_state:
                    store_conversation(
                        st.session_state.username,
                        text,
                        metrics,
                        graph_data,
                        st.session_state.semantic_chat['history']
                    )
        
        # Display chat history
        with chat_container:
            st.markdown("### 💬 " + t.get('semantic_discussion', 'Semantic Analysis Discussion'))
            
            for msg in st.session_state.semantic_chat['history']:
                if msg["sender"] == "user":
                    st.chat_message("user").write(msg["message"])
                else:
                    st.chat_message("assistant").write(msg["message"])
        
        # Input for new message
        user_input = st.chat_input(
            t.get('chat_input_placeholder', 'Ask about your semantic analysis...')
        )
        
        if user_input:
            # Add user message to history
            st.session_state.semantic_chat['history'].append({
                "sender": "user",
                "message": user_input
            })
            
            # Display user message immediately
            with chat_container:
                st.chat_message("user").write(user_input)
                with st.spinner(t.get('assistant_thinking', 'Assistant is thinking...')):
                    # Get assistant response
                    assistant_response = continue_conversation(
                        st.session_state.semantic_chat['history'],
                        user_input,
                        lang_code
                    )
                    
                    # Add assistant response to history
                    st.session_state.semantic_chat['history'].append({
                        "sender": "assistant",
                        "message": assistant_response
                    })
                    
                    # Display assistant response
                    st.chat_message("assistant").write(assistant_response)
            
            # Store updated conversation
            if 'username' in st.session_state:
                store_conversation(
                    st.session_state.username,
                    text,
                    metrics,
                    graph_data,
                    st.session_state.semantic_chat['history']
                )
    
    except Exception as e:
        logger.error(f"Error displaying semantic chat: {str(e)}")
        st.error(t.get('chat_error', 'Error in chat interface. Please try again.'))