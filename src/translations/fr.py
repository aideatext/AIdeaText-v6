# translations/fr.py

COMMON = {
    # A
    'initial_instruction': "Pour démarrer une nouvelle analyse sémantique, téléchargez un nouveau fichier texte (.txt)",
    'analysis_complete': "Analyse terminée et enregistrée. Pour effectuer une nouvelle analyse, téléchargez un autre fichier.",
    'current_analysis_message': "Affichage de l'analyse du fichier : {}. Pour effectuer une nouvelle analyse, veuillez télécharger un autre fichier.",
    'upload_prompt': "Joindre un fichier pour démarrer l'analyse",
    'analysis_completed': "Analyse terminée",
    'analysis_section': "Analyse Sémantique",
    'analyze_document': 'Analyser le document',
    'analysis_saved_success': 'Analyse enregistrée avec succès',
    'analysis_save_error': 'Erreur lors de l\'enregistrement de l\'analyse',
    'analyze_button': "Analyser le texte",
    'analyzing_doc': "Analyse du document",
    'activities_message': "Messages d'activités",
    'activities_placeholder': "Espace réservé aux activités",
    'analysis_placeholder': "Espace réservé à l'analyse",
    'analyze_button': "Analyser",
    'analysis_types_chart': "Graphique pour le type d'analyse",
    'analysis_from': "Analyse réalisée sur",
    # C
    'chat_title': "Chat d'Analyse",
    'export_button': "Exporter l'Analyse Actuelle",
    'export_success': "Analyse et chat exportés avec succès.",
    'export_error': "Un problème est survenu lors de l'exportation de l'analyse et du chat.",
    'get_text': "Obtenir du texte.",
    'hello': "Bonjour",
    # L
    'logout': "Déconnexion.",
    'loading_data': "Chargement des données",
    'load_selected_file': 'Charger le fichier sélectionné',
    # N
    'no_analysis': "Aucune analyse disponible. Utilisez le chat pour effectuer une analyse.",
    'nothing_to_export': "Aucune analyse ou chat à exporter.",
    'results_title': "Résultats de l'Analyse",
    'select_language': "Sélectionner la langue",
    'student_activities': "Activités étudiantes",
    # T
    'total_analyses': "Analyses totales",
    # W
    'welcome': "Bienvenue à AIdeaText"
}

TABS = {
    'current_situation_tab': "Ma situation actuelle",
    'morpho_tab': "Analyse morphosyntaxique",
    'semantic_live_tab': "Sémantique en direct",
    'semantic_tab': "Analyse sémantique",
    'discourse_live_tab': "Discours en direct",
    'discourse_tab': "Analyse du discours",
    'activities_tab': "Mes activités",
    'feedback_tab': "Formulaire de commentaires"
}

CURRENT_SITUATION = {
    'title': "Ma Situation Actuelle",
    'input_prompt': "Écrivez ou collez votre texte ici :",
    'first_analyze_button': "Analyser mon écriture",
    'processing': "Analyse en cours...",
    'analysis_error': "Erreur lors de l'analyse du texte",
    'help': "Nous analyserons votre texte pour déterminer son état actuel",
    
    # Radio buttons pour type de texte
    'text_type_header': "Type de texte",
    'text_type_help': "Sélectionnez le type de texte pour ajuster les critères d'évaluation",
    
    # Métriques
    'vocabulary_label': "Vocabulaire",
    'vocabulary_help': "Richesse et variété du vocabulaire",
    'structure_label': "Structure", 
    'structure_help': "Organisation et complexité des phrases",
    'cohesion_label': "Cohésion",
    'cohesion_help': "Connexion et fluidité entre les idées",
    'clarity_label': "Clarté",
    'clarity_help': "Facilité de compréhension du texte",
    
    # États des métriques
    'metric_improvement': "⚠️ À améliorer",
    'metric_acceptable': "📈 Acceptable",
    'metric_optimal': "✅ Optimal",
    'metric_target': "Objectif : {:.2f}",
    
    # Erreurs
    'error_interface': "Une erreur s'est produite lors du chargement de l'interface",
    'error_results': "Erreur lors de l'affichage des résultats",
    'error_chart': "Erreur lors de l'affichage du graphique"
}

MORPHOSYNTACTIC = {
    #A
    'arc_diagram': "Analyse syntaxique : Diagramme en arc",
    #B
    'tab_text_baseline': "Produire le premier texte",
    'tab_iterations': "Produire de nouvelles versions du premier texte",
    
    # Pestaña 1 texto base 
    'btn_new_morpho_analysis': "Nouvelle analyse morphosyntaxique",
    'btn_analyze_baseline': "Analyser le texte saisi",
    'input_baseline_text': "Saisissez le premier texte à analyser",
    'warn_enter_text': "Veuillez saisir un texte à analyser",
    'error_processing_baseline': "Erreur lors du traitement du texte initial",
    'arc_diagram_baseline_label': "Diagramme en arc du texte initial",
    'baseline_diagram_not_available': "Diagramme en arc du texte initial non disponible",

    # Pestaña 2 Iteración del texto 
    'info_first_analyze_base': "Vérifiez si le texte initial existe",
    'iteration_text_subheader': "Nouvelle version du texte initial",
    'input_iteration_text': "Saisissez une nouvelle version du texte initial et comparez les arcs des deux textes",
    'btn_analyze_iteration': "Analyser les changements",
    'warn_enter_iteration_text': "Saisissez une nouvelle version du texte initial et comparez les arcs des deux textes",
    'iteration_saved': "Changements enregistrés avec succès",
    'error_iteration': "Erreur lors du traitement des nouveaux changements"
}

SEMANTIC = {
    # C
    'chat_title': "Chat d'Analyse Sémantique",
    'chat_placeholder': "Posez une question ou utilisez une commande (/résumé, /entités, /sentiment, /thèmes, /graphe_concepts, /graphe_entités, /graphe_thèmes)",
    'clear_chat': "Effacer le chat",
    'conceptual_relations': "Relations Conceptuelles",
    # D
    'delete_file': "Supprimer le fichier",
    'download_semantic_network_graph': "Télécharger le graphique du réseau sémantique",
    # E
    'error_message': "Un problème est survenu lors de l'enregistrement de l'analyse sémantique. Veuillez réessayer.",
    # F
    'file_uploader': "Ou téléchargez un fichier texte",
    'file_upload_success': "Fichier téléchargé et enregistré avec succès",
    'file_upload_error': "Erreur lors du téléchargement du fichier",
    'file_section': "Fichiers",
    'file_loaded_success': "Fichier chargé avec succès",
    'file_load_error': "Erreur lors du chargement du fichier",
    'file_upload_error': "Erreur lors du téléchargement et de l'enregistrement du fichier",
    'file_deleted_success': "Fichier supprimé avec succès",
    'file_delete_error': "Erreur lors de la suppression du fichier",
    # G
    'graph_title': "Visualisation de l'Analyse Sémantique",
    # I
    'identified_entities': "Entités Identifiées",
    # K
    'key_concepts': "Concepts Clés",
    # N
    'no_analysis': "Aucune analyse disponible. Veuillez télécharger ou sélectionner un fichier.",
    'no_results': "Aucun résultat disponible. Veuillez d'abord effectuer une analyse.",
    'no_file': "Veuillez télécharger un fichier pour commencer l'analyse.",
    'no_file_selected': "Veuillez sélectionner une archive pour démarrer l'analyse.",
    # S
    ##############
    'semantic_virtual_agent_button': 'Analyser avec l\'Agent Virtuel',
    'semantic_agent_ready_message': 'L\'agent virtuel a reçu votre analyse sémantique. Ouvrez l\'assistant dans la barre latérale pour discuter de vos résultats.',
    'semantic_chat_title': 'Analyse Sémantique - Assistant Virtuel',
    ##############
    'semantic_graph_interpretation': "Interprétation du graphique sémantique",
    'semantic_arrow_meaning': "Les flèches indiquent la direction de la relation entre les concepts",
    'semantic_color_meaning': "Les couleurs plus intenses indiquent des concepts plus centraux dans le texte",
    'semantic_size_meaning': "La taille des nœuds représente la fréquence du concept",
    'semantic_thickness_meaning': "L'épaisseur des lignes indique la force de la connexion",
    ##############
    'semantic_graph_interpretation': "Interprétation de graphes sémantiques",
    'semantic_title': "Analyse Sémantique",
    'semantic_initial_message': "Ceci est un chatbot à usage général, mais il a une fonction spécifique pour l'analyse visuelle de textes : il génère un graphe avec les principales entités du texte. Pour le produire, entrez un fichier texte au format txt, pdf, doc, docx ou odt et appuyez sur le bouton 'analyser le fichier'. Après la génération du graphe, vous pouvez interagir avec le chat en fonction du document.",
    'send_button': "Envoyer",
    'select_saved_file': "Sélectionner un fichier enregistré",
    'success_message': "Analyse sémantique enregistrée avec succès.",
    'semantic_analyze_button': 'Analyse Sémantique',
    'semantic_export_button': 'Exporter l\'Analyse Sémantique',
    'semantic_new_button': 'Nouvelle Analyse Sémantique',
    'semantic_file_uploader': "Créer un fichier de texte pour l'analyse sémantique",
    # T
    'text_input_label': "Entrez un texte à analyser (max. 5 000 mots) :",
    'text_input_placeholder': "L'objectif de cette application est d'améliorer vos compétences en rédaction...",
    'title': "AIdeaText - Analyse Sémantique",
    # U
    'upload_file': "Télécharger le fichier",
    # W
    'warning_message': "Veuillez entrer un texte ou télécharger un fichier à analyser."
}

DISCOURSE = {
    'compare_arrow_meaning': "Les flèches indiquent la direction de la relation entre les concepts",
    'compare_color_meaning': "Les couleurs plus intenses indiquent des concepts plus centraux dans le texte",
    'compare_size_meaning': "La taille des nœuds représente la fréquence du concept",
    'compare_thickness_meaning': "L'épaisseur des lignes indique la force de la connexion",
    'compare_doc1_title': "Document 1",
    'compare_doc2_title': "Document 2",
    'file1_label': "Document Modèle",
    'file2_label': "Document Comparé",
    'discourse_title': "AIdeaText - Analyse du discours",
    'file_uploader1': "Télécharger le fichier texte 1 (Modèle)",
    'file_uploader2': "Télécharger le fichier texte 2 (Comparaison)",
    'discourse_analyze_button': "Comparer des textes",
    'discourse_initial_message': "C'est un chatbot de proposition générale, mais il a une fonction spécifique pour l'analyse visuelle des textes : générer des graphiques avec les principales entités de chaque fichier pour faire une comparaison entre plusieurs textes. Pour produire, insérer un premier fichier et l'autre après au format txt, pdf, doc, docx ou odt et appuyez sur le bouton 'analyser les archives'. Après la génération du graphique, vous pouvez interagir avec le chat en fonction du document.",
    'analyze_button': "Analyser les textes",
    'comparison': "Comparaison des Relations Sémantiques",
    'success_message': "Analyse du discours enregistrée avec succès.",
    'error_message': "Un problème est survenu lors de l'enregistrement de l'analyse du discours. Veuillez réessayer.",
    'warning_message': "Veuillez télécharger les deux fichiers à analyser.",
    'no_results': "Aucun résultat disponible. Veuillez d'abord effectuer une analyse.",
    'key_concepts': "Concepts Clés",
    'graph_not_available': "Le graphique n'est pas disponible.",
    'concepts_not_available': "Les concepts clés ne sont pas disponibles.",
    'comparison_not_available': "La comparaison n'est pas disponible.",
    'morphosyntax_history': "Historique morphosyntaxique",
    'analysis_of': "Analyse de"
}

ACTIVITIES = {
    # Nouvelles étiquettes mises à jour
    'current_situation_activities': "Registres de la fonction : Ma Situation Actuelle",
    'morpho_activities': "Registres de mes analyses morphosyntaxiques",
    'semantic_activities': "Registres de mes analyses sémantiques",
    'discourse_activities': "Registres de mes analyses de comparaison de textes",
    'chat_activities': "Registres de mes conversations avec le tuteur virtuel",
    
    # Maintenir d'autres clés existantes
    'current_situation_tab': "Ma situation actuelle",
    'morpho_tab': "Analyse morphosyntaxique",
    'semantic_tab': "Analyse sémantique",
    'discourse_tab': "Analyse de comparaison de textes",
    'activities_tab': "Mon registre d'activités",
    'feedback_tab': "Formulaire de commentaires",
    
    # Reste des clés qui sont dans le dictionnaire ACTIVITIES
    'analysis_types_chart_title': "Types d'analyses effectuées",
    'analysis_types_chart_x': "Type d'analyse",
    'analysis_types_chart_y': "Nombre",
    'analysis_from': "Analyse du",
    'assistant': "Assistant",
    'activities_summary': "Résumé des Activités et Progrès",
    'chat_history_expander': "Historique des Conversations",
    'chat_from': "Conversation du",
    'combined_graph': "Graphique combiné",
    'conceptual_relations_graph': "Graphique des relations conceptuelles",
    'conversation': "Conversation",
    'discourse_analyses_expander': "Historique des Analyses de Comparaison de Textes",  # Mis à jour
    'discourse_analyses': "Analyses de Comparaison de Textes",  # Mis à jour
    'discourse_history': "Historique des Analyses de Comparaison de Textes",  # Mis à jour
    'document': "Document",
    'data_load_error': "Erreur lors du chargement des données de l'étudiant",
    'graph_display_error': "Impossible d'afficher le graphique",
    'graph_doc1': "Graphique document 1",
    'graph_doc2': "Graphique document 2",
    'key_concepts': "Concepts clés",
    'loading_data': "Chargement des données de l'étudiant...",
    'morphological_analysis': "Analyse Morphologique",
    'morphosyntax_analyses_expander': "Historique des Analyses Morphosyntaxiques",
    'morphosyntax_history': "Historique des Analyses Morphosyntaxiques",
    'no_arc_diagram': "Aucun diagramme en arc trouvé pour cette analyse.",
    'no_chat_history': "Aucune conversation avec le Tuteur Virtuel n'a été trouvée.",  # Mis à jour
    'no_data_warning': "Aucune donnée d'analyse trouvée pour cet étudiant.",
    'progress_of': "Progrès de",
    'semantic_analyses': "Analyses Sémantiques",
    'semantic_analyses_expander': "Historique des Analyses Sémantiques",
    'semantic_history': "Historique des Analyses Sémantiques",
    'show_debug_data': "Afficher les données de débogage",
    'student_debug_data': "Données de l'étudiant (pour le débogage) :",
    'summary_title': "Résumé des Activités",
    'title': "Mon Registre d'Activités",  # Mis à jour
    'timestamp': "Horodatage",
    'total_analyses': "Total des analyses effectuées :",
    'try_analysis': "Essayez d'effectuer d'abord quelques analyses de texte.",
    'user': "Utilisateur",
    
    # Nouvelles traductions spécifiques pour la section activités
    'diagnosis_tab': "Diagnostic",
    'recommendations_tab': "Recommandations",
    'key_metrics': "Métriques clés",
    'details': "Détails",
    'analyzed_text': "Texte analysé",
    'analysis_date': "Date",
    'academic_article': "Article académique",
    'student_essay': "Dissertation d'étudiant",
    'general_communication': "Communication générale",
    'no_diagnosis': "Aucune donnée de diagnostic disponible",
    'no_recommendations': "Aucune recommandation disponible",
    'error_current_situation': "Erreur lors de l'affichage de l'analyse de la situation actuelle",
    'no_current_situation': "Aucune analyse de situation actuelle enregistrée",
    'no_morpho_analyses': "Aucune analyse morphosyntaxique enregistrée",
    'error_morpho': "Erreur lors de l'affichage de l'analyse morphosyntaxique",
    'no_semantic_analyses': "Aucune analyse sémantique enregistrée",
    'error_semantic': "Erreur lors de l'affichage de l'analyse sémantique",
    'no_discourse_analyses': "Aucune analyse de comparaison de textes enregistrée",
    'error_discourse': "Erreur lors de l'affichage de l'analyse de comparaison de textes",
    'no_chat_history': "Aucun enregistrement de conversation avec le tuteur virtuel",
    'error_chat': "Erreur lors de l'affichage des enregistrements de conversation",
    'error_loading_activities': "Erreur lors du chargement des activités",
    'chat_date': "Date de conversation",
    'invalid_chat_format': "Format de chat invalide",
    'comparison_results': "Résultats de la comparaison",
    'concepts_text_1': "Concepts Texte 1",
    'concepts_text_2': "Concepts Texte 2",
    'no_visualization': "Aucune visualisation comparative disponible",
    'no_graph': "Aucune visualisation disponible",
    'error_loading_graph': "Erreur lors du chargement du graphique",
    'syntactic_diagrams': "Diagrammes syntaxiques"
}

FEEDBACK = {
    'email': "E-mail",
    'feedback': "Retour",
    'feedback_title': "Formulaire de commentaires",
    'feedback_error': "Un problème est survenu lors de l'envoi du formulaire. Veuillez réessayer.",
    'feedback_success': "Merci pour votre retour",
    'complete_all_fields': "Veuillez remplir tous les champs",
    'name': "Nom",
    'submit': "Envoyer"
}

CHATBOT_TRANSLATIONS = {
    'chat_title': "Assistant AIdeaText",
    'input_placeholder': "Des questions ?",
    'initial_message': "Bonjour ! Je suis votre assistant. Comment puis-je vous aider ?",
    'expand_chat': "Ouvrir l'assistant",
    'clear_chat': "Effacer la conversation",
    'processing': "Traitement en cours...",
    'error_message': "Désolé, une erreur s'est produite"
}

TEXT_TYPES = {
    "descriptif": [
        "Que décrivez-vous ?",
        "Quelles sont ses principales caractéristiques ?",
        "À quoi ressemble-t-il, quel son produit-il, quelle odeur dégage-t-il ou quelle sensation procure-t-il ?",
        "Qu'est-ce qui le rend unique ou spécial ?"
    ],
    "narratif": [
        "Qui est le protagoniste ?",
        "Où et quand se déroule l'histoire ?",
        "Quel événement déclenche l'action ?",
        "Que se passe-t-il ensuite ?",
        "Comment se termine l'histoire ?"
    ],
    "explicatif": [
        "Quel est le sujet principal ?",
        "Quels aspects importants voulez-vous expliquer ?",
        "Pouvez-vous donner des exemples ou des données pour appuyer votre explication ?",
        "Comment ce sujet est-il lié à d'autres concepts ?"
    ],
    "argumentatif": [
        "Quelle est votre thèse ou argument principal ?",
        "Quels sont vos arguments de soutien ?",
        "Quelles preuves avez-vous pour étayer vos arguments ?",
        "Quels sont les contre-arguments et comment les réfutez-vous ?",
        "Quelle est votre conclusion ?"
    ],
    "instructif": [
        "Quelle tâche ou quel processus expliquez-vous ?",
        "Quels matériaux ou outils sont nécessaires ?",
        "Quelles sont les étapes à suivre ?",
        "Y a-t-il des précautions ou des conseils importants à mentionner ?"
    ],
    "pitch": [
        "Quoi ?",
        "Pour quoi ?",
        "Pour qui ?",
        "Comment ?"
    ]
}

# Configuration du modèle de langage pour le français
NLP_MODEL = 'fr_core_news_lg'

# Cette ligne est cruciale:
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