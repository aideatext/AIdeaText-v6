# translations/es.py

COMMON = {
    # A
    'initial_instruction': "Para comenzar un nuevo análisis semántico, cargue un nuevo archivo de texto (.txt)",
    'analysis_complete': "Análisis completo y guardado. Para realizar un nuevo análisis, cargue otro archivo.",
    'current_analysis_message': "Mostrando análisis del archivo: {}. Para realizar un nuevo análisis, cargue otro archivo.",
    'upload_prompt': "Cargue un archivo para comenzar el análisis",
    'analysis_completed': "Análisis completado",
    'analysis_section': "Análisis Semántico",
    'analyze_document': 'Analizar documento',
    'analysis_saved_success': 'Análisis guardado con éxito',
    'analysis_save_error': 'Error al guardar el análisis',
    'analyze_button': "Analizar texto",
    'analyzing_doc': "Analizando documento",
    'activities_message': "Mensajes de las actividades",
    'activities_placeholder': "Espacio de las actividades",
    'analysis_placeholder': "Marcador de posición del análisis",
    'analyze_button': "Analizar",
    'analysis_types_chart': "Gráfico para el tipo de análisis",
    'analysis_from': "Análisis realizado el",
    # C
    'chat_title': "Chat de Análisis",
    'export_button': "Exportar Análisis Actual",
    'export_success': "Análisis y chat exportados correctamente.",
    'export_error': "Hubo un problema al exportar el análisis y el chat.",
    'get_text': "Obtener texto.",
    'hello': "Hola",
    # L
    'logout': "Cerrar sesión.",
    'loading_data': "Cargando datos",
    'load_selected_file': 'Cargar archivo seleccionado',
    # N
    'no_analysis': "No hay análisis disponible. Utiliza el chat para realizar un análisis.",
    'nothing_to_export': "No hay análisis o chat para exportar.",
    'results_title': "Resultados del Análisis",
    'select_language': "Selecciona un idioma",
    'student_activities': "Actividades del estudiante",
    # T
    'total_analyses': "Análisis totales",
    # W
    'welcome': "Bienvenido a AIdeaText"
}

TABS = {
    'current_situation_tab': "Mi situación actual",
    'morpho_tab': "Análisis morfosintáctico",
    'semantic_live_tab': "Semántica en vivo",
    'semantic_tab': "Análisis semántico",
    'discourse_live_tab': "Discurso en vivo",
    'discourse_tab': "Análisis del discurso",
    'activities_tab': "Mis actividades",
    'feedback_tab': "Formulario de comentarios"
}

CURRENT_SITUATION = {
    'title': "Mi Situación Actual",
    'input_prompt': "Escribe o pega tu texto aquí:",
    'first_analyze_button': "Analizar mi escritura",
    'processing': "Analizando...",
    'analysis_error': "Error al analizar el texto",
    'help': "Analizaremos tu texto para determinar su estado actual",
    
    # Radio buttons para tipo de texto
    'text_type_header': "Tipo de texto",
    'text_type_help': "Selecciona el tipo de texto para ajustar los criterios de evaluación",
    
    # Métricas
    'vocabulary_label': "Vocabulario",
    'vocabulary_help': "Riqueza y variedad del vocabulario",
    'structure_label': "Estructura", 
    'structure_help': "Organización y complejidad de oraciones",
    'cohesion_label': "Cohesión",
    'cohesion_help': "Conexión y fluidez entre ideas",
    'clarity_label': "Claridad",
    'clarity_help': "Facilidad de comprensión del texto",
    
    # Estados de métricas
    'metric_improvement': "⚠️ Por mejorar",
    'metric_acceptable': "📈 Aceptable",
    'metric_optimal': "✅ Óptimo",
    'metric_target': "Meta: {:.2f}",
    
    # Errores
    'error_interface': "Ocurrió un error al cargar la interfaz",
    'error_results': "Error al mostrar los resultados",
    'error_chart': "Error al mostrar el gráfico"
}

MORPHOSYNTACTIC = {
    #A
    'arc_diagram': "Análisis sintáctico: Diagrama de arco",
    #B
    'tab_text_baseline': "Ingresa la primera versión de tu texto",
    'tab_iterations': "Produce nuevas versiones de tu primer texto",
    
    # Pestaña 1 texto base 
    'btn_new_morpho_analysis': "Nuevo análisis morfosintático",
    'btn_analyze_baseline': "Analizar la primera versión de tu texto",
    'input_baseline_text': "Ingresa el primer texto para analizarlo",
    'warn_enter_text': "Ingrese un texto primer para analizarlo",
    'error_processing_baseline': "Error al procesar el texto inicial",
    'arc_diagram_baseline_label': "Diagrama de arco del texto inicial",
    'baseline_diagram_not_available': "Diagrama de arco del texto inicial no disponible",

    # Pestaña 2 Iteración del texto 
    'info_first_analyze_base': "Verifica la existencia del texto inicial",    
    'iteration_text_subheader': "Nueva versión del texto inicial",
    'input_iteration_text': "Ingresa una nueva versión del texto inicial y compara los arcos de ambos textos",
    'btn_analyze_iteration': "Analizar Cambios",
    'warn_enter_iteration_text': "Ingresa una nueva versión del texto inicial y compara los arcos de ambos textos",
    'iteration_saved': "Cambios guardados correctamente",
    'error_iteration': "Error procesando los nuevos cambios"
}

SEMANTIC = {
    # A
    # C
    'chat_title': "Chat de Análisis Semántico",
    'chat_placeholder': "Haz una pregunta o usa un comando (/resumen, /entidades, /sentimiento, /temas, /grafo_conceptos, /grafo_entidades, /grafo_temas)",
    'clear_chat': "Limpiar chat",
    'conceptual_relations': "Relaciones Conceptuales",
    # D
    'delete_file': "Borrar archivo",
    'download_semantic_network_graph': "Descargar gráfico de red semántica",
    # E
    'error_message': "Hubo un problema al guardar el análisis semántico. Por favor, inténtelo de nuevo.",
    # F
    'file_uploader': "O cargue un archivo de texto",
    'file_upload_success': "Archivo subido y guardado exitosamente",
    'file_upload_error': 'Error al cargar el archivo',
    'file_section': "Archivos",
    'file_loaded_success': "Archivo cargado exitosamente",
    'file_load_error': "Error al cargar el archivo",
    'file_upload_error': "Error al subir y guardar el archivo",
    'file_deleted_success': 'Archivo borrado con éxito',
    'file_delete_error': 'Error al borrar el archivo',
    # G
    'graph_title': "Visualización de Análisis Semántico",
    # I
    'identified_entities': "Entidades Identificadas",
    # K
    'key_concepts': "Conceptos Clave",
    # N
    'no_analysis': "No hay análisis disponible. Por favor, cargue o seleccione un archivo.",
    'no_results': "No hay resultados disponibles. Por favor, realice un análisis primero.",
    'no_file': "Por favor, cargue un archivo para comenzar el análisis.",
    'no_file_selected': "Por favor, seleccione un archivo para comenzar el análisis.",
    # S
    ###############
    'semantic_virtual_agent_button': 'Analizar con Agente Virtual',
    'semantic_agent_ready_message': 'El agente virtual ha recibido tu análisis semántico. Abre el asistente en la barra lateral para discutir tus resultados.',
    'semantic_chat_title': 'Análisis Semántico - Asistente Virtual',
    ####
    'semantic_graph_interpretation': "Interpretación del gráfico semántico",
    'semantic_arrow_meaning': "Las flechas indican la dirección de la relación entre conceptos",
    'semantic_color_meaning': "Los colores más intensos indican conceptos más centrales en el texto",
    'semantic_size_meaning': "El tamaño de los nodos representa la frecuencia del concepto",
    'semantic_thickness_meaning': "El grosor de las líneas indica la fuerza de la conexión",
    ########
    'semantic_title': "Análisis Semántico",
    'semantic_initial_message': "Este es un chatbot de propósito general, pero tiene una función específica para el análisis visual de textos: genera un grafo con las principales entidades del texto. Para producirlo, ingrese un archivo de texto en formato txt, pdf, doc, docx o odt y pulse el botón 'analizar archivo'. Después de la generación del grafo puede interactuar con el chat en función del documento.",
    'send_button': "Enviar",
    'select_saved_file': "Seleccionar archivo guardado",
    'success_message': "Análisis semántico guardado correctamente.",
    'semantic_analyze_button': 'Análisis Semántico',
    'semantic_export_button': 'Exportar Análisis Semántico',
    'semantic_new_button': 'Nuevo Análisis Semántico',
    'semantic_file_uploader': 'Ingresar un archivo de texto para análisis semántico',
    # T
    'text_input_label': "Ingrese un texto para analizar (máx. 5,000 palabras):",
    'text_input_placeholder': "El objetivo de esta aplicación es que mejore sus habilidades de redacción...",
    'title': "AIdeaText - Análisis semántico",
    # U
    'upload_file': "Agregar un archivo",
    # W
    'warning_message': "Por favor, ingrese un texto o cargue un archivo para analizar."
}


DISCOURSE = {
    'compare_arrow_meaning': "Las flechas indican la dirección de la relación entre conceptos",
    'compare_color_meaning': "Los colores más intensos indican conceptos más centrales en el texto",
    'compare_size_meaning': "El tamaño de los nodos representa la frecuencia del concepto",
    'compare_thickness_meaning': "El grosor de las líneas indica la fuerza de la conexión",
    'compare_doc1_title': "Documento 1",
    'compare_doc2_title': "Documento 2",
    'file1_label': "Documento Patrón",
    'file2_label': "Documento Comparado",
    'discourse_title': "AIdeaText - Análisis del discurso",
    'file_uploader1': "Cargar archivo de texto 1 (Patrón)",
    'file_uploader2': "Cargar archivo de texto 2 (Comparación)",
    'discourse_analyze_button': "Comparar textos",
    'discourse_initial_message': "Este es un chatbot de propósito general, pero tiene una función específica para el análisis visual de textos: genera dos grafos con las principales entidades de cada archivo para hacer una comparación entre ambos textos. Para producirlo, ingrese un archivo primero y otro después en formato txt, pdf, doc, docx o odt y pulse el botón 'analizar archivo'. Después de la generación del grafo puede interactuar con el chat en función del documento.",
    'analyze_button': "Analizar textos",
    'comparison': "Comparación de Relaciones Semánticas",
    'success_message': "Análisis del discurso guardado correctamente.",
    'error_message': "Hubo un problema al guardar el análisis del discurso. Por favor, inténtelo de nuevo.",
    'warning_message': "Por favor, cargue ambos archivos para analizar.",
    'no_results': "No hay resultados disponibles. Por favor, realice un análisis primero.",
    'key_concepts': "Conceptos Clave",
    'graph_not_available': "El gráfico no está disponible.",
    'concepts_not_available': "Los conceptos clave no están disponibles.",
    'comparison_not_available': "La comparación no está disponible.",
    'morphosyntax_history': "Historial de morfosintaxis",
    'analysis_of': "Análisis de"
}

ACTIVITIES = {
    # Nuevas etiquetas actualizadas
    'current_situation_activities': "Registros de la función: Mi Situación Actual",
    'morpho_activities': "Registros de mis análisis morfosintácticos",
    'semantic_activities': "Registros de mis análisis semánticos",
    'discourse_activities': "Registros de mis análisis comparados de textos",
    'chat_activities': "Registros de mis conversaciones con el tutor virtual",
    
    # Mantener otras claves existentes
    'current_situation_tab': "Mi situación actual",
    'morpho_tab': "Análisis morfosintáctico",
    'semantic_tab': "Análisis semántico",
    'discourse_tab': "Análisis comparado de textos",
    'activities_tab': "Registro de mis actividades",
    'feedback_tab': "Formulario de comentarios",
    
    # Resto de las claves que estén en el diccionario ACTIVITIES
    'analysis_types_chart_title': "Tipos de análisis realizados",
    'analysis_types_chart_x': "Tipo de análisis",
    'analysis_types_chart_y': "Cantidad",
    'analysis_from': "Análisis del",
    'assistant': "Asistente",
    'activities_summary': "Resumen de Actividades y Progreso",
    'chat_history_expander': "Historial de Chat",
    'chat_from': "Chat del",
    'combined_graph': "Gráfico combinado",
    'conceptual_relations_graph': "Gráfico de relaciones conceptuales",
    'conversation': "Conversación",
    'discourse_analyses_expander': "Historial de Análisis Comparados de Textos",
    'discourse_analyses': "Análisis Comparados de Textos",
    'discourse_history': "Histórico de Análisis Comparados de Textos",
    'document': "Documento",
    'data_load_error': "Error al cargar los datos del estudiante",
    'graph_display_error': "No se pudo mostrar el gráfico",
    'graph_doc1': "Gráfico documento 1",
    'graph_doc2': "Gráfico documento 2",
    'key_concepts': "Conceptos clave",
    'loading_data': "Cargando datos del estudiante...",
    'morphological_analysis': "Análisis Morfológico",
    'morphosyntax_analyses_expander': "Historial de Análisis Morfosintácticos",
    'morphosyntax_history': "Histórico de Análisis Morfosintácticos",
    'no_arc_diagram': "No se encontró diagrama de arco para este análisis.",
    'no_chat_history': "No se encontraron conversaciones con el Tutor Virtual.",
    'no_data_warning': "No se encontraron datos de análisis para este estudiante.",
    'progress_of': "Progreso de",
    'semantic_analyses': "Análisis Semánticos",
    'semantic_analyses_expander': "Historial de Análisis Semánticos",
    'semantic_history': "Histórico de Análisis Semánticos",
    'show_debug_data': "Mostrar datos de depuración",
    'student_debug_data': "Datos del estudiante (para depuración):",
    'summary_title': "Resumen de Actividades",
    'title': "Registro de mis actividades",
    'timestamp': "Fecha y hora",
    'total_analyses': "Total de análisis realizados:",
    'try_analysis': "Intenta realizar algunos análisis de texto primero.",
    'user': "Usuario",
    
    # Nuevas traducciones específicas para la sección de actividades
    'diagnosis_tab': "Diagnóstico",
    'recommendations_tab': "Recomendaciones",
    'key_metrics': "Métricas clave",
    'details': "Detalles",
    'analyzed_text': "Texto analizado",
    'analysis_date': "Fecha",
    'academic_article': "Artículo académico",
    'student_essay': "Trabajo universitario",
    'general_communication': "Comunicación general",
    'no_diagnosis': "No hay datos de diagnóstico disponibles",
    'no_recommendations': "No hay recomendaciones disponibles",
    'error_current_situation': "Error al mostrar análisis de situación actual",
    'no_current_situation': "No hay análisis de situación actual registrados",
    'no_morpho_analyses': "No hay análisis morfosintácticos registrados",
    'error_morpho': "Error al mostrar análisis morfosintáctico",
    'no_semantic_analyses': "No hay análisis semánticos registrados",
    'error_semantic': "Error al mostrar análisis semántico",
    'no_discourse_analyses': "No hay análisis comparados de textos registrados",
    'error_discourse': "Error al mostrar análisis comparado de textos",
    'no_chat_history': "No hay registros de conversaciones con el tutor virtual",
    'error_chat': "Error al mostrar registros de conversaciones",
    'error_loading_activities': "Error al cargar las actividades",
    'chat_date': "Fecha de conversación",
    'invalid_chat_format': "Formato de chat no válido",
    'comparison_results': "Resultados de la comparación",
    'concepts_text_1': "Conceptos Texto 1",
    'concepts_text_2': "Conceptos Texto 2",
    'no_visualization': "No hay visualización comparativa disponible",
    'no_graph': "No hay visualización disponible",
    'error_loading_graph': "Error al cargar el gráfico",
    'syntactic_diagrams': "Diagramas sintácticos"
}

FEEDBACK = {
    'email': "Correo electrónico",
    'feedback': "Retroalimentación",
    'feedback_title': "Formulario de opinión",
    'feedback_error': "Hubo un problema al enviar el formulario. Por favor, intenta de nuevo.",
    'feedback_success': "Gracias por tu respuesta",
    'complete_all_fields': "Por favor, completa todos los campos",
    'name': "Nombre",
    'submit': "Enviar"
}

CHATBOT_TRANSLATIONS = {
    'chat_title': "Asistente AIdeaText",
    'input_placeholder': "¿Tienes alguna pregunta?",
    'initial_message': "¡Hola! Soy tu asistente. ¿En qué puedo ayudarte?",
    'expand_chat': "Abrir asistente",
    'clear_chat': "Limpiar chat",
    'processing': "Procesando...",
    'error_message': "Lo siento, ocurrió un error"
}

TEXT_TYPES = {
    'descriptivo': [
        '¿Qué estás describiendo?',
        '¿Cuáles son sus características principales?',
        '¿Cómo se ve, suena, huele o se siente?',
        '¿Qué lo hace único o especial?'
    ],
    'narrativo': [
        '¿Quién es el protagonista?',
        '¿Dónde y cuándo ocurre la historia?',
        '¿Qué evento inicia la acción?',
        '¿Qué sucede después?',
        '¿Cómo termina la historia?'
    ],
    'expositivo': [
        '¿Cuál es el tema principal?',
        '¿Qué aspectos importantes quieres explicar?',
        '¿Puedes dar ejemplos o datos que apoyen tu explicación?',
        '¿Cómo se relaciona este tema con otros conceptos?'
    ],
    'argumentativo': [
        '¿Cuál es tu tesis o argumento principal?',
        '¿Cuáles son tus argumentos de apoyo?',
        '¿Qué evidencias tienes para respaldar tus argumentos?',
        '¿Cuáles son los contraargumentos y cómo los refutas?',
        '¿Cuál es tu conclusión?'
    ],
    'instructivo': [
        '¿Qué tarea o proceso estás explicando?',
        '¿Qué materiales o herramientas se necesitan?',
        '¿Cuáles son los pasos a seguir?',
        '¿Hay precauciones o consejos importantes que mencionar?'
    ],
    'pitch': [
        '¿Qué?',
        '¿Para qué?',
        '¿Para quién?',
        '¿Cómo?'
    ]
}

# Configuración del modelo de lenguaje para español
NLP_MODEL = 'es_core_news_lg'

# Esta línea es crucial:
TRANSLATIONS = {
    'COMMON': COMMON,
    'TABS': TABS,
    'MORPHOSYNTACTIC': MORPHOSYNTACTIC,
    'SEMANTIC': SEMANTIC,
    'DISCOURSE': DISCOURSE,
    'ACTIVITIES': ACTIVITIES,
    'FEEDBACK': FEEDBACK,
    'TEXT_TYPES': TEXT_TYPES,
    'CURRENT_SITUATION': CURRENT_SITUATION,
    'NLP_MODEL': NLP_MODEL
}