# modules/__init__.py

def load_auth_functions():
    from .auth.auth import authenticate_user, register_user
    return {
        'authenticate_user': authenticate_user,
        'register_user': register_user
    }

def load_database_function():
    from .database.database_oldFromV2 import (
        initialize_mongodb_connection,
        initialize_database_connections,
        create_admin_user,
        create_student_user,
        get_user,
        get_student_data,
        get_user_files,
        delete_file,
        store_application_request,
        store_user_feedback,
        store_morphosyntax_result,
        store_semantic_result,
        store_discourse_analysis_result,
        store_chat_history,
        export_analysis_and_chat,
        manage_file_contents
    )
    return {
        'initialize_mongodb_connection': initialize_mongodb_connection,
        'initialize_database_connections': initialize_database_connections,
        'create_admin_user': create_admin_user,
        'create_student_user': create_student_user,
        'get_user': get_user,
        'get_student_data': get_student_data,
        'get_user_files': get_user_files,
        'delete_file': delete_file,
        'store_application_request': store_application_request,
        'store_user_feedback': store_user_feedback,
        'store_morphosyntax_result': store_morphosyntax_result,
        'store_semantic_result': store_semantic_result,
        'store_discourse_analysis_result': store_discourse_analysis_result,
        'store_chat_history': store_chat_history,
        'export_analysis_and_chat': export_analysis_and_chat,
        'manage_file_contents': manage_file_contents
    }

def load_ui_functions():
    # No importamos nada de ui.py aquí
    return {}  # Retornamos un diccionario vacío


def load_student_activities_functions():
    from .studentact.student_activities_v2 import display_student_progress
    return {
        'display_student_progress': display_student_progress
    }

def load_morphosyntax_functions():
    from .morphosyntax.morphosyntax_interface import display_morphosyntax_interface
    from .morphosyntax.morphosyntax_process import process_morphosyntactic_input
    return {
        'display_morphosyntax_interface': display_morphosyntax_interface,
        'process_morphosyntactic_input': process_morphosyntactic_input
    }

def load_semantic_functions():
    from .semantic.semantic_interface_68ok import display_semantic_interface
    from .semantic.semantic_process import process_semantic_input
    return {
        'display_semantic_interface': display_semantic_interface,
        'process_semantic_input': process_semantic_input
    }

def load_discourse_functions():
    from .discourse.discourse_interface import display_discourse_interface
    from .discourse.discourse_process import process_discourse_input
    return {
        'display_discourse_interface': display_discourse_interface,
        'process_discourse_input': process_discourse_input
    }

def load_email_functions():
    from .email.email import send_email_notification
    return {
        'send_email_notification': send_email_notification
    }

def load_admin_functions():
    from .admin.admin_ui import admin_page
    return {
        'admin_page': admin_page
    }

def load_text_analysis_functions():
    from .text_analysis.morpho_analysis import (
        generate_arc_diagram,
        perform_advanced_morphosyntactic_analysis,
        perform_pos_analysis,
        perform_morphological_analysis,
        analyze_sentence_structure,
        get_repeated_words_colors,
        highlight_repeated_words,
    )
    from .text_analysis.semantic_analysis import (
        perform_semantic_analysis,
        generate_summary,
        extract_entities,
        analyze_sentiment,
        create_topic_graph,
        visualize_topic_graph,
        ENTITY_LABELS
    )
    from .text_analysis.discourse_analysis import (
        perform_discourse_analysis,
        compare_semantic_analysis
    )
    return {
        'generate_arc_diagram': generate_arc_diagram,
        'perform_advanced_morphosyntactic_analysis': perform_advanced_morphosyntactic_analysis,
        'perform_pos_analysis': perform_pos_analysis,
        'perform_morphological_analysis': perform_morphological_analysis,
        'analyze_sentence_structure': analyze_sentence_structure,
        'get_repeated_words_colors': get_repeated_words_colors,
        'highlight_repeated_words': highlight_repeated_words,
        'perform_semantic_analysis': perform_semantic_analysis,
        'generate_summary': generate_summary,
        'extract_entities': extract_entities,
        'analyze_sentiment': analyze_sentiment,
        'create_topic_graph': create_topic_graph,
        'visualize_topic_graph': visualize_topic_graph,
        'ENTITY_LABELS': ENTITY_LABELS,
        'perform_discourse_analysis': perform_discourse_analysis,
        'compare_semantic_analysis': compare_semantic_analysis
    }

def load_utils_functions():
    from .utils.spacy_utils import load_spacy_models
    return {
        'load_spacy_models': load_spacy_models
    }

def load_chatbot_functions():
    from .chatbot.chatbot import (
        ClaudeAPIChat,
        initialize_chatbot,
        process_chat_input,
        get_connectors,
        handle_semantic_commands,
        generate_topics_visualization,
        extract_topics,
        get_semantic_chatbot_response
    )
    return {
        'ClaudeAPIChat': ClaudeAPIChat,
        'initialize_chatbot': initialize_chatbot,
        'process_chat_input': process_chat_input,
        'get_connectors': get_connectors,
        'handle_semantic_commands': handle_semantic_commands,
        'generate_topics_visualization': generate_topics_visualization,
        'extract_topics': extract_topics,
        'get_semantic_chatbot_response': get_semantic_chatbot_response
    }

# Función para cargar todas las funciones
def load_all_functions():
    return {
        **load_auth_functions(),
        **load_database_function(),
        # **load_ui_functions(),
        **load_admin_functions(),
        **load_morphosyntax_functions(),
        **load_semantic_functions(),
        **load_discourse_functions(),
        **load_text_analysis_functions(),
        **load_utils_functions(),
        **load_chatbot_functions(),
        **load_email_functions()
        **load_student_activities_functions()  # Añadimos las nuevas funciones de actividades del estudiante
    }