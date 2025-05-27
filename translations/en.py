# translations/en.py

COMMON = {
    # A
    'initial_instruction': "To start a new semantic analysis, upload a new text file (.txt)",
    'analysis_complete': "Analysis complete and saved. To perform a new analysis, upload another file.",
    'current_analysis_message': "Showing analysis of file: {}. To perform a new analysis, please upload another file.",
    'upload_prompt': "Attach a file to start the analysis",
    'analysis_completed': "Analysis completed",
    'analysis_section': "Semantic Analysis",
    'analyze_document': 'Analyze document',
    'analysis_saved_success': 'Analysis saved successfully',
    'analysis_save_error': 'Error saving the analysis',
    'analyze_button': "Analyze text",
    'analyzing_doc': "Analyzing document",
    'activities_message':"Activities messages",
    'activities_placeholder':"Activities placeholder",
    'analysis_placeholder':"Analysis placeholder",
    'analyze_button' : "Analyze",
    'analysis_types_chart' : "Analyze type chart",
    'analysis_from': "Analysis carried out on",
    # C
    'chat_title': "Analysis Chat",
    'export_button': "Export Current Analysis",
    'export_success': "Analysis and chat exported successfully.",
    'export_error': "There was a problem exporting the analysis and chat.",
    'get_text': "Get text.",
    'hello': "Hello",
    # L
    'logout': "End session.",
    'loading_data': "Loading data",
    'load_selected_file': 'Load selected file',
    # N
    'no_analysis': "No analysis available. Use the chat to perform an analysis.",
    'nothing_to_export': "No analysis or chat to export.",
    'results_title': "Analysis Results",
    'select_language': "Language select",
    'student_activities':"Student activities",
    # T
    'total_analyses': "Total analyses",
    # W
    'welcome': "Welcome to AIdeaText"
}

TABS = {
    'current_situation_tab': "Current situation",
    'morpho_tab': "Morphosyntactic analysis",
    'semantic_live_tab': "Semantic live",
    'semantic_tab': "Semantic analysis",
    'discourse_live_tab': "Discourse live",
    'discourse_tab': "Discourse analysis",
    'activities_tab': "My activities",
    'feedback_tab': "Feedback form"
}

CURRENT_SITUATION = {
    'title': "My Current Situation",
    'input_prompt': "Write or paste your text here:",
    'first_analyze_button': "Analyze my writing",
    'processing': "Analyzing...",
    'analysis_error': "Error analyzing text",
    'help': "We will analyze your text to determine its current status",  # <-- Added this line
    # Radio buttons for text type
    'text_type_header': "Text type",
    'text_type_help': "Select the text type to adjust evaluation criteria",
    # Metrics
    'vocabulary_label': "Vocabulary",
    'vocabulary_help': "Richness and variety of vocabulary",
    'structure_label': "Structure",
    'structure_help': "Organization and complexity of sentences",
    'cohesion_label': "Cohesion",
    'cohesion_help': "Connection and fluidity between ideas",
    'clarity_label': "Clarity",
    'clarity_help': "Ease of text comprehension",
    # Metric states
    'metric_improvement': "⚠️ Needs improvement",
    'metric_acceptable': "📈 Acceptable",
    'metric_optimal': "✅ Optimal",
    'metric_target': "Goal: {:.2f}",
    # Errors
    'error_interface': "An error occurred while loading the interface",
    'error_results': "Error displaying results",
    'error_chart': "Error displaying chart"
}

MORPHOSYNTACTIC = {
    #A
    'arc_diagram': "Syntactic analysis: Arc diagram",
    #B
    'tab_text_baseline': "Produce first text",
    'tab_iterations': "Produce new versions of the first text",
    
    # Pestaña 1 texto base 
    'btn_new_morpho_analysis': "New morphosyntactic analysis",
    'btn_analyze_baseline': "Analyze the entered text",
    'input_baseline_text': "Enter the first text to analyze",
    'warn_enter_text': "Please enter a text to analyze",
    'error_processing_baseline': "Error processing the initial text",
    'arc_diagram_baseline_label': "Arc diagram of the initial text",
    'baseline_diagram_not_available': "Arc diagram of the initial text not available",

    # Pestaña 2 Iteración del texto 
    'info_first_analyze_base': "Check if the initial text exists",
    'iteration_text_subheader': "New version of the initial text",
    'input_iteration_text': "Enter a new version of the initial text and compare both texts' arcs",
    'btn_analyze_iteration': "Analyze changes",
    'warn_enter_iteration_text': "Enter a new version of the initial text and compare both texts' arcs",
    'iteration_saved': "Changes saved successfully",
    'error_iteration': "Error processing the new changes"
}

SEMANTIC = {
    # A
    # C
    'chat_title': "Semantic Analysis Chat",
    'chat_placeholder': "Ask a question or use a command (/summary, /entities, /sentiment, /topics, /concept_graph, /entity_graph, /topic_graph)",
    'clear_chat': "Clear chat",
    'conceptual_relations': "Conceptual Relations",
    # D
    'delete_file': "Delete file",
    'download_semantic_network_graph': "Download semantic network graph",
    # E
    'error_message': "There was a problem saving the semantic analysis. Please try again.",
    # F
    'file_uploader': "Or upload a text file",
    'file_upload_success': "File uploaded and saved successfully",
    'file_upload_error': 'Error uploading file',
    'file_section': "Files",
    'file_loaded_success': "File loaded successfully",
    'file_load_error': "Error loading file",
    'file_upload_error': "Error uploading and saving file",
    'file_deleted_success': 'File deleted successfully',
    'file_delete_error': 'Error deleting file',
     # G
    'graph_title': "Semantic Analysis Visualization",
     # I
    'identified_entities': "Identified Entities",
    # K
    'key_concepts': "Key Concepts",
    # N
    'no_analysis': "No analysis available. Please upload or select a file.",
    'no_results': "No results available. Please perform an analysis first.",
    'no_file': "Please upload a file to start the analysis.",
    'no_file_selected': "Please select an archive to start the analysis.",
    # S
    ######################
    'semantic_virtual_agent_button': 'Analyze with Virtual Agent',
    'semantic_agent_ready_message': 'The virtual agent has received your semantic analysis. Open the sidebar assistant to discuss your results.',
    'semantic_chat_title': 'Semantic Analysis - Virtual Assistant',
    ##########################
    'semantic_graph_interpretation': "Semantic Graph Interpretation",
    'semantic_arrow_meaning': "Arrows indicate the direction of the relationship between concepts",
    'semantic_color_meaning': "More intense colors indicate more central concepts in the text",
    'semantic_size_meaning': "Node size represents concept frequency",
    'semantic_thickness_meaning': "Line thickness indicates connection strength",    
    'semantic_title': "Semantic Analysis",
    'semantic_initial_message': "This is a general-purpose chatbot, but it has a specific function for visual text analysis: it generates a graph with the main entities of the text. To produce it, enter a text file in txt, pdf, doc, docx or odt format and press the 'analyze file' button. After generating the graph, you can interact with the chat based on the document.",
    'send_button': "Send",
    'select_saved_file': "Select saved file",
    'success_message': "Semantic analysis saved successfully.",
    'semantic_analyze_button': 'Semantic Analysis',
    'semantic_export_button': 'Export Semantic Analysis',
    'semantic_new_button': 'New Semantic Analysis',
    'semantic_file_uploader': 'Upload a text file for semantic analysis',
    # T
    'text_input_label': "Enter a text to analyze (max. 5,000 words):",
    'text_input_placeholder': "The purpose of this application is to improve your writing skills...",
    'title': "AIdeaText - Semantic Analysis",
    # U
    'upload_file': "Upload file",
    # W
    'warning_message': "Please enter a text or upload a file to analyze."
}

DISCOURSE = {
    'compare_arrow_meaning': "Arrows indicate the direction of the relationship between concepts",
    'compare_color_meaning': "More intense colors indicate more central concepts in the text",
    'compare_size_meaning': "Node size represents concept frequency",
    'compare_thickness_meaning': "Line thickness indicates connection strength", 
    'compare_doc1_title': "Document 1",
    'compare_doc2_title': "Document 2",
    'file1_label': "Pattern Document",
    'file2_label': "Compared Document",
    'discourse_title': "AIdeaText - Discourse Analysis",
    'file_uploader1': "Upload text file 1 (Pattern)",
    'file_uploader2': "Upload text file 2 (Comparison)",
    'discourse_analyze_button': "Compare texts",
    'discourse_initial_message': "This is a general purpose chatbot, but it has a specific function for visual text analysis: it generates two graphs with the main entities of each file to make a comparison between both texts. To produce it, enter one file first and then another in txt, pdf, doc, docx or odt format and press the 'analyze file' button. After the graph is generated, you can interact with the chat based on the document.",
    'analyze_button': "Analyze texts",
    'comparison': "Comparison of Semantic Relations",
    'success_message': "Discourse analysis saved successfully.",
    'error_message': "There was a problem saving the discourse analysis. Please try again.",
    'warning_message': "Please upload both files to analyze.",
    'no_results': "No results available. Please perform an analysis first.",
    'key_concepts': "Key Concepts",
    'graph_not_available': "The graph is not available.",
    'concepts_not_available': "Key concepts are not available.",
    'comparison_not_available': "The comparison is not available.",
    'warning_message': "Please enter a text or upload a file to analyze.",
    'morphosyntax_history': "Morphosyntax history",
    'analysis_of': "Analysis of"
}

ACTIVITIES = {
    # Nuevas etiquetas actualizadas
    'current_situation_activities': "Records of function: My Current Situation",
    'morpho_activities': "Records of my morphosyntactic analyses",
    'semantic_activities': "Records of my semantic analyses",
    'discourse_activities': "Records of my text comparison analyses",
    'chat_activities': "Records of my conversations with the virtual tutor",
    
    # Mantener otras claves existentes
    'current_situation_tab': "Current situation",
    'morpho_tab': "Morphosyntactic analysis",
    'semantic_tab': "Semantic analysis",
    'discourse_tab': "Text comparison analysis",
    'activities_tab': "My activities record",
    'feedback_tab': "Feedback form",
    
    # Resto de las claves que estén en el diccionario ACTIVITIES
    'analysis_types_chart_title': "Types of analyses performed",
    'analysis_types_chart_x': "Analysis type",
    'analysis_types_chart_y': "Count",
    'analysis_from': "Analysis from",
    'assistant': "Assistant",
    'activities_summary': "Activities and Progress Summary",
    'chat_history_expander': "Chat History",
    'chat_from': "Chat from",
    'combined_graph': "Combined Graph",
    'conceptual_relations_graph': "Conceptual Relations Graph",
    'conversation': "Conversation",
    'discourse_analyses_expander': "Text Comparison Analyses History",  # Actualizado
    'discourse_analyses': "Text Comparison Analyses",  # Actualizado
    'discourse_history': "Text Comparison Analysis History",  # Actualizado
    'document': "Document",
    'data_load_error': "Error loading student data",
    'graph_display_error': "Could not display the graph",
    'graph_doc1': "Graph document 1",
    'graph_doc2': "Graph document 2",
    'key_concepts': "Key concepts",
    'loading_data': "Loading student data...",
    'morphological_analysis': "Morphological Analysis",
    'morphosyntax_analyses_expander': "Morphosyntactic Analyses History",
    'morphosyntax_history': "Morphosyntactic Analysis History",
    'no_arc_diagram': "No arc diagram found for this analysis.",
    'no_chat_history': "No conversations with the Virtual Tutor were found.",  # Actualizado
    'no_data_warning': "No analysis data found for this student.",
    'progress_of': "Progress of",
    'semantic_analyses': "Semantic Analyses",
    'semantic_analyses_expander': "Semantic Analyses History",
    'semantic_history': "Semantic Analysis History",
    'show_debug_data': "Show debug data",
    'student_debug_data': "Student data (for debugging):",
    'summary_title': "Activities Summary",
    'title': "My Activities Record",  # Actualizado
    'timestamp': "Timestamp",
    'total_analyses': "Total analyses performed:",
    'try_analysis': "Try performing some text analyses first.",
    'user': "User",
    
    # Nuevas traducciones específicas para la sección de actividades
    'diagnosis_tab': "Diagnosis",
    'recommendations_tab': "Recommendations",
    'key_metrics': "Key metrics",
    'details': "Details",
    'analyzed_text': "Analyzed text",
    'analysis_date': "Date",
    'academic_article': "Academic article",
    'student_essay': "Student essay",
    'general_communication': "General communication",
    'no_diagnosis': "No diagnosis data available",
    'no_recommendations': "No recommendations available",
    'error_current_situation': "Error displaying current situation analysis",
    'no_current_situation': "No current situation analyses recorded",
    'no_morpho_analyses': "No morphosyntactic analyses recorded",
    'error_morpho': "Error displaying morphosyntactic analysis",
    'no_semantic_analyses': "No semantic analyses recorded",
    'error_semantic': "Error displaying semantic analysis",
    'no_discourse_analyses': "No text comparison analyses recorded",  # Actualizado
    'error_discourse': "Error displaying text comparison analysis",  # Actualizado
    'no_chat_history': "No conversation records with the virtual tutor",  # Actualizado
    'error_chat': "Error displaying conversation records",  # Actualizado
    'error_loading_activities': "Error loading activities",
    'chat_date': "Conversation date",
    'invalid_chat_format': "Invalid chat format",
    'comparison_results': "Comparison results",
    'concepts_text_1': "Concepts Text 1",
    'concepts_text_2': "Concepts Text 2",
    'no_visualization': "No comparative visualization available",
    'no_graph': "No visualization available",
    'error_loading_graph': "Error loading graph",
    'syntactic_diagrams': "Syntactic diagrams"
}

FEEDBACK = {
    'email': "Email",
    'feedback': "Feedback",
    'feedback_title': "Feedback form",
    'feedback_error': "There was a problem submitting the form. Please try again.",
    'feedback_success': "Thank for your feedback",
    'complete_all_fields': "Please, complete all fields",
    'name': "Name",
    'submit': "Submit"
}


CHATBOT_TRANSLATIONS = {
        'chat_title': "AIdeaText Assistant",
        'input_placeholder': "Any questions?",
        'initial_message': "Hi! I'm your assistant. How can I help?",
        'expand_chat': "Open assistant",
        'clear_chat': "Clear chat",
        'processing': "Processing...",
        'error_message': "Sorry, an error occurred"
}

TEXT_TYPES = {
        'descriptive': [
            'What are you describing?',
            'What are its main characteristics?',
            'How does it look, sound, smell, or feel?',
            'What makes it unique or special?'
        ],
        'narrative': [
            'Who is the protagonist?',
            'Where and when does the story take place?',
            'What event starts the action?',
            'What happens next?',
            'How does the story end?'
        ],
        'expository': [
            'What is the main topic?',
            'What important aspects do you want to explain?',
            'Can you provide examples or data to support your explanation?',
            'How does this topic relate to other concepts?'
        ],
        'argumentative': [
            'What is your main thesis or argument?',
            'What are your supporting arguments?',
            'What evidence do you have to back up your arguments?',
            'What are the counterarguments and how do you refute them?',
            'What is your conclusion?'
        ],
        'instructive': [
            'What task or process are you explaining?',
            'What materials or tools are needed?',
            'What are the steps to follow?',
            'Are there any important precautions or tips to mention?'
        ],
        'pitch': [
            'What?',
            'What for?',
            'For whom?',
            'How?'
        ]
    }

# Configuration of the language model for English
NLP_MODEL = 'en_core_web_lg'

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
    'CURRENT_SITUATION': CURRENT_SITUATION,  # Añadir esta línea
    'NLP_MODEL': NLP_MODEL
}