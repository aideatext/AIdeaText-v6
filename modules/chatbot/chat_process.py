# modules/chatbot/chat_process.py
import os
import anthropic
import logging
from typing import Generator

logger = logging.getLogger(__name__)

class ChatProcessor:
    def __init__(self):
        """Inicializa el procesador de chat con la API de Claude"""
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY")
        )
        self.conversation_history = []
        self.semantic_context = None
        self.current_lang = 'en'

    def set_semantic_context(self, text, metrics, graph_data, lang_code='en'):
        """Configura el contexto semántico completo para el chat"""
        if not text or not metrics:
            logger.error("Faltan datos esenciales para el contexto semántico")
            raise ValueError("Texto y métricas son requeridos")
            
        self.semantic_context = {
            'full_text': text,
            'key_concepts': metrics.get('key_concepts', []),
            'concept_centrality': metrics.get('concept_centrality', {}),
            'graph_available': graph_data is not None,
            'language': lang_code
        }
        self.current_lang = lang_code
        self.conversation_history = []
        logger.info("Contexto semántico configurado correctamente")

    def _get_system_prompt(self):
        """Genera el prompt del sistema con todo el contexto necesario"""
        if not self.semantic_context:
            return "You are a helpful assistant."
            
        concepts = self.semantic_context['key_concepts']
        top_concepts = ", ".join([f"{c[0]} ({c[1]:.2f})" for c in concepts[:5]])
        
        prompts = {
            'en': f"""You are a semantic analysis expert. The user analyzed a research article.
            Full text available (abbreviated for context).
            Key concepts: {top_concepts}
            Graph available: {self.semantic_context['graph_available']}
            
            Your tasks:
            1. Answer questions about concepts and their relationships
            2. Explain the semantic network structure
            3. Suggest text improvements
            4. Provide insights based on concept centrality
            5. IMPORTANT FORMATTING: Always format citations or numerical references using brackets with a leading space (e.g., text [1], concept [2]).""",
            
            'es': f"""Eres un experto en análisis semántico. El usuario analizó un artículo de investigación.
            Texto completo disponible (abreviado para contexto).
            Conceptos clave: {top_concepts}
            Gráfico disponible: {self.semantic_context['graph_available']}
            
            Tus tareas:
            1. Responder preguntas sobre conceptos y sus relaciones
            2. Explicar la estructura de la red semántica
            3. Sugerir mejoras al texto
            4. Proporcionar insights basados en centralidad de conceptos
            5. FORMATO IMPORTANTE: Formatea siempre las citas o referencias numéricas usando corchetes y asegurando un espacio antes (por ejemplo: texto [1], concepto [2]).""",
            
            'pt': f"""Você é um especialista em análise semântica. O usuário analisou um artigo de pesquisa.
            Texto completo disponível (abreviado para contexto).
            Conceitos-chave: {top_concepts}
            Gráfico disponível: {self.semantic_context['graph_available']}
            
            Suas tarefas:
            1. Responder perguntas sobre conceitos e suas relações
            2. Explicar a estrutura da rede semântica
            3. Sugerir melhorias no texto
            4. Fornecer insights com base na centralidade dos conceitos
            5. FORMATAÇÃO IMPORTANTE: Formate sempre as citações ou referências numéricas usando colchetes e garantindo um espaço antes (por exemplo: texto [1], conceito [2]).""",
            
            'fr': f"""Vous êtes un expert en analyse sémantique. L'utilisateur a analysé un article de recherche.
            Texte complet disponible (abrégé pour le contexte).
            Concepts clés: {top_concepts}
            Graphique disponible: {self.semantic_context['graph_available']}
            
            Vos tâches:
            1. Répondre aux questions sur les concepts et leurs relations
            2. Expliquer la structure du réseau sémantique
            3. Suggérer des améliorations de texte
            4. Fournir des insights basés sur la centralité des concepts
            5. FORMATAGE IMPORTANT: Formatez toujours les citations ou les références numériques en utilisant des crochets et en assurant un espace avant (par exemple: texte [1], concept [2])."""
        }
        
        return prompts.get(self.current_lang, prompts['en'])

    def clean_generated_text(self, text):
        """Limpia caracteres especiales del texto generado SIN eliminar espacios en blanco de los extremos."""
        # Se elimina .strip() para no romper los espacios entre chunks del stream
        return text.replace("\u2588", "").replace("▌", "")

    def process_chat_input(self, message: str, lang_code: str) -> Generator[str, None, None]:
        """Procesa el mensaje con todo el contexto disponible"""
        try:
            if not self.semantic_context:
                yield "Error: Contexto semántico no configurado. Recargue el análisis."
                return
                
            if lang_code != self.current_lang:
                self.current_lang = lang_code
                logger.info(f"Idioma cambiado a: {lang_code}")

            messages = [
                {
                    "role": "user",
                    "content": f"Documento analizado (extracto):\n{self.semantic_context['full_text'][:2000]}..."
                },
                *self.conversation_history,
                {"role": "user", "content": message}
            ]

            with self.client.messages.stream(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                temperature=0.7,
                system=self._get_system_prompt(),
                messages=messages
            ) as stream:
                full_response = ""
                for chunk in stream.text_stream:
                    cleaned_chunk = self.clean_generated_text(chunk)
                    full_response += cleaned_chunk
                    yield cleaned_chunk
                
                # Opcional: Aplicar un strip final solo al guardarlo en el historial
                self.conversation_history.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": full_response.strip()}
                ])
                logger.info("Respuesta generada y guardada en historial")

        except Exception as e:
            logger.error(f"Error en process_chat_input: {str(e)}", exc_info=True)
            error_messages = {
                'en': "Error processing message. Please reload the analysis.",
                'es': "Error al procesar mensaje. Recargue el análisis.",
                'pt': "Erro ao processar mensagem. Recarregue a análise.",
                'fr': "Erreur lors du traitement du message. Veuillez recharger l'analyse."
            }
            yield error_messages.get(self.current_lang, "Processing error")