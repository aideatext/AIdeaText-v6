# modules/chatbot/chat_process.py
import os
import json
import boto3
import logging
import base64
from typing import Generator
from botocore.config import Config

logger = logging.getLogger(__name__)

class ChatProcessor:
    def __init__(self):
        """Inicializa el procesador de chat con AWS Bedrock (Jamba 1.5 Large)"""
        # Configurar cliente de Bedrock
        self.bedrock = boto3.client(
            'bedrock-runtime',
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            config=Config(
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                }
            )
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
            'graph_data': graph_data,  # Guardamos el grafo para usarlo en el chat
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
4. Provide insights based on concept centrality""",
            
            'es': f"""Eres un experto en análisis semántico. El usuario analizó un artículo de investigación.
Texto completo disponible (abreviado para contexto).
Conceptos clave: {top_concepts}
Gráfico disponible: {self.semantic_context['graph_available']}

Tus tareas:
1. Responder preguntas sobre conceptos y sus relaciones
2. Explicar la estructura de la red semántica
3. Sugerir mejoras al texto
4. Proporcionar insights basados en centralidad de conceptos""",
            
            'pt': f"""Você é um especialista em análise semântica. O usuário analisou um artigo de pesquisa.
Texto completo disponível (abreviado para contexto).
Conceitos-chave: {top_concepts}
Gráfico disponível: {self.semantic_context['graph_available']}

Suas tarefas:
1. Responder perguntas sobre conceitos e suas relações
2. Explicar a estrutura da rede semântica
3. Sugerir melhorias no texto
4. Fornecer insights com base na centralidade dos conceitos""",
            
            'fr': f"""Vous êtes un expert en analyse sémantique. L'utilisateur a analysé un article de recherche.
Texte complet disponible (abrégé pour le contexte).
Concepts clés: {top_concepts}
Graphique disponible: {self.semantic_context['graph_available']}

Vos tâches:
1. Répondre aux questions sur les concepts et leurs relations
2. Expliquer la structure du réseau sémantique
3. Suggérer des améliorations de texte
4. Fournir des insights basés sur la centralité des concepts"""
        }
        
        return prompts.get(self.current_lang, prompts['en'])

    def clean_generated_text(self, text):
        """Limpia caracteres especiales del texto generado"""
        return text.replace("\u2588", "").replace("▌", "").strip()

    def _build_multimodal_content(self, message):
        """Construye el contenido multimodal con texto + grafo si está disponible"""
        content_parts = []
        
        # 1. Añadir el texto del documento
        if self.semantic_context and 'full_text' in self.semantic_context:
            content_parts.append(
                f"Documento analizado (extracto):\n{self.semantic_context['full_text'][:1500]}..."
            )
        
        # 2. Añadir conceptos clave
        if self.semantic_context and 'key_concepts' in self.semantic_context:
            concepts = self.semantic_context['key_concepts'][:5]
            content_parts.append(f"Conceptos clave: {concepts}")
        
        # 3. Añadir el grafo si está disponible (en base64)
        if self.semantic_context and self.semantic_context.get('graph_available'):
            graph_data = self.semantic_context.get('graph_data')
            if graph_data:
                # Si el grafo ya es base64, lo usamos directamente
                if isinstance(graph_data, str) and graph_data.startswith('iVBOR'):
                    content_parts.append(f"![Grafo](data:image/png;base64,{graph_data})")
                else:
                    content_parts.append("Grafo disponible para consultas visuales.")
        
        # 4. Añadir el mensaje actual del usuario
        content_parts.append(f"Pregunta del usuario: {message}")
        
        return "\n\n".join(content_parts)

    def process_chat_input(self, message: str, lang_code: str) -> Generator[str, None, None]:
        """Procesa el mensaje con todo el contexto disponible usando Jamba 1.5 en Bedrock"""
        try:
            if not self.semantic_context:
                yield "Error: Contexto semántico no configurado. Recargue el análisis."
                return
                
            # Actualizar idioma si es diferente
            if lang_code != self.current_lang:
                self.current_lang = lang_code
                logger.info(f"Idioma cambiado a: {lang_code}")

            # Construir el contenido multimodal
            user_content = self._build_multimodal_content(message)

            # Construir mensajes para Jamba (formato específico)
            messages = []
            
            # Añadir system prompt
            messages.append({
                "role": "system",
                "content": self._get_system_prompt()
            })
            
            # Añadir historial de conversación (últimos 4 intercambios para no exceder contexto)
            for msg in self.conversation_history[-8:]:  # 8 mensajes = 4 intercambios
                messages.append(msg)
            
            # Añadir mensaje actual del usuario
            messages.append({
                "role": "user",
                "content": user_content
            })

            # Preparar el cuerpo de la petición para Jamba 1.5 Large
            request_body = {
                "messages": messages,
                "max_tokens": 2000,
                "temperature": 0.7,
                "top_p": 0.9,
                "stop": [],
                "n": 1
            }

            # Llamar a Bedrock (sin streaming por ahora, Jamba no soporta streaming nativo)
            response = self.bedrock.invoke_model(
                modelId='ai21.jamba-1-5-large-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )

            # Procesar la respuesta
            response_body = json.loads(response['body'].read())
            
            # Extraer el texto de la respuesta (formato específico de Jamba)
            if 'choices' in response_body and len(response_body['choices']) > 0:
                full_response = response_body['choices'][0]['message']['content']
            else:
                full_response = "Lo siento, no pude generar una respuesta."

            # Limpiar la respuesta
            clean_response = self.clean_generated_text(full_response)

            # Simular streaming para mantener compatibilidad con la interfaz
            # Dividimos la respuesta en fragmentos para simular streaming
            chunk_size = 50
            for i in range(0, len(clean_response), chunk_size):
                yield clean_response[i:i+chunk_size]
            
            # Guardar respuesta en historial
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": clean_response})
            
            # Mantener historial manejable (últimos 20 mensajes)
            if len(self.conversation_history) > 40:
                self.conversation_history = self.conversation_history[-40:]
                
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