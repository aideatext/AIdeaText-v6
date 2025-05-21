# modules/__init__.py

def load_auth_functions():
    from .auth.auth import authenticate_student, register_student, update_student_info, delete_student
    return {
        'authenticate_student': authenticate_student,
        'register_student': register_student,
        'update_student_info': update_student_info,
        'delete_student': delete_student
    }

# Agregar nuevo import para current_situation
def load_current_situation_functions():
    """
    Carga las funciones relacionadas con el análisis de situación actual.
    Returns:
        dict: Diccionario con las funciones de situación actual
    """
    from .studentact.current_situation_interface import (
        display_current_situation_interface,
        display_metrics_in_one_row,
        display_empty_metrics_row,
        display_metrics_analysis, 
        display_comparison_results,
        display_metrics_and_suggestions,
        display_radar_chart,
        suggest_improvement_tools,
        prepare_metrics_config
        )
    
    from .studentact.current_situation_analysis import (
            correlate_metrics,
            analyze_text_dimensions,
            analyze_clarity,
            analyze_vocabulary_diversity,
            analyze_cohesion,
            analyze_structure,
            get_dependency_depths,
            normalize_score, 
            generate_sentence_graphs, 
            generate_word_connections, 
            generate_connection_paths,         
            create_vocabulary_network,
            create_syntax_complexity_graph,
            create_cohesion_heatmap
        )
    
    return {
        'display_current_situation_interface': display_current_situation_interface,
        'display_metrics_in_one_row': display_metrics_in_one_line,
        'display_empty_metrics_row': display_empty_metrics_row,
        'display_metrics_analysis': display_metrics_analysis, 
        'display_comparison_results': display_comparison_results,
        'display_metrics_and_suggestions': display_metrics_and_suggestions,
        'display_radar_chart': display_radar_chart,
        'suggest_improvement_tools': suggest_improvement_tools,
        'prepare_metrics_config': prepare_metrics_config,
        'display_empty_metrics_row' : display_empty_metrics_row,
        'correlate_metrics': correlate_metrics,
        'analyze_text_dimensions': analyze_text_dimensions,
        'analyze_clarity': analyze_clarity,
        'analyze_vocabulary_diversity': analyze_vocabulary_diversity,
        'analyze_cohesion': analyze_cohesion,
        'analyze_structure': analyze_structure,
        'get_dependency_depths': get_dependency_depths,
        'normalize_score': normalize_score, 
        'generate_sentence_graphs': generate_sentence_graphs, 
        'generate_word_connections': generate_word_connections, 
        'generate_connection_paths': generate_connection_paths,         
        'create_vocabulary_network': create_vocabulary_network,
        'create_syntax_complexity_graph': create_syntax_complexity_graph,
        'create_cohesion_heatmap': create_cohesion_heatmap 
    }

def load_database_functions():

    from .database.database_init import (
    initialize_database_connections, 
    get_container, 
    get_mongodb
    )

    # Importar funciones SQL
    from .database.sql_db import (
        create_student_user,
        get_student_user,
        update_student_user,
        delete_student_user,
        store_application_request,
        store_student_feedback,
        record_login,
        record_logout,
        get_recent_sessions,
        get_user_total_time
    )
    
    from .database.mongo_db import (
        get_collection,
        insert_document,
        find_documents,
        update_document,
        delete_document,
    )
    
    from .database.morphosintax_mongo_db import (
        store_student_morphosyntax_result,
        get_student_morphosyntax_analysis,
        update_student_morphosyntax_analysis,
        delete_student_morphosyntax_analysis,
        get_student_morphosyntax_data
    )

    from .database.semantic_mongo_db import (
        store_student_semantic_result,
        get_student_semantic_analysis,
        update_student_semantic_analysis,
        delete_student_semantic_analysis,
        get_student_semantic_data
    )

    from .database.discourse_mongo_db import (
        store_student_discourse_result,
        get_student_discourse_analysis,
        update_student_discourse_analysis,
        delete_student_discourse_analysis,
        get_student_discourse_data
    )

    # Agregar nueva importación para current_situation
    from .database.current_situation_mongo_db import (
        store_current_situation_result,
        verify_storage,
        get_recent_sessions,
        get_student_situation_history,
        update_exercise_status
    )

    # Importar nuevas funciones de análisis morfosintáctico iterativo
    from .morphosyntax_iterative_mongo_db import (
        store_student_morphosyntax_base,
        store_student_morphosyntax_iteration,
        get_student_morphosyntax_analysis,
        update_student_morphosyntax_analysis, 
        delete_student_morphosyntax_analysis,
        get_student_morphosyntax_data
    )
    
    from .database.chat_mongo_db import store_chat_history, get_chat_history

    return {
        # Nuevas funciones morfosintácticas iterativas
        'store_student_morphosyntax_base': store_student_morphosyntax_base,
        'store_student_morphosyntax_iteration': store_student_morphosyntax_iteration,
        'get_student_morphosyntax_iterative_analysis': get_student_morphosyntax_analysis,  # Renombrada para evitar conflicto
        'update_student_morphosyntax_iterative': update_student_morphosyntax_analysis,     # Renombrada para evitar conflicto
        'delete_student_morphosyntax_iterative': delete_student_morphosyntax_analysis,     # Renombrada para evitar conflicto
        'get_student_morphosyntax_iterative_data': get_student_morphosyntax_data,  
        'store_current_situation_result': store_current_situation_result,
        'verify_storage': verify_storage,
        'get_recent_sessions': get_recent_sessions,
        'get_student_situation_history': get_student_situation_history,
        'update_exercise_status': update_exercise_status,
        'initialize_database_connections': initialize_database_connections,
        'get_container': get_container,
        'get_mongodb': get_mongodb,
        'create_student_user': create_student_user,
        'get_student_user': get_student_user,
        'update_student_user': update_student_user,
        'delete_student_user': delete_student_user,
        'store_application_request': store_application_request,
        'store_student_feedback': store_student_feedback,
        'get_collection': get_collection,
        'insert_document': insert_document,
        'find_documents': find_documents,
        'update_document': update_document,
        'delete_document': delete_document,
        'store_student_morphosyntax_result': store_student_morphosyntax_result,
        'get_student_morphosyntax_analysis': get_student_morphosyntax_analysis,
        'update_student_morphosyntax_analysis': update_student_morphosyntax_analysis,
        'delete_student_morphosyntax_analysis': delete_student_morphosyntax_analysis,
        'get_student_morphosyntax_data': get_student_morphosyntax_data,
        'store_student_semantic_result': store_student_semantic_result,
        'get_student_semantic_analysis': get_student_semantic_analysis,
        'update_student_semantic_analysis': update_student_semantic_analysis,
        'delete_student_semantic_analysis': delete_student_semantic_analysis,
        'get_student_semantic_data': get_student_semantic_data,
        'store_chat_history': store_chat_history,
        'get_chat_history': get_chat_history, 
        'store_student_discourse_result': store_student_discourse_result,
        'get_student_discourse_analysis': get_student_discourse_analysis,
        'update_student_discourse_analysis': update_student_discourse_analysis,
        'delete_student_discourse_analysis': delete_student_discourse_analysis,
        'get_student_discourse_data': get_student_discourse_data, 
        'record_login': record_login,
        'record_logout': record_logout,
        'get_recent_sessions': get_recent_sessions,
        'get_user_total_time': get_user_total_time
    }

def load_ui_functions():
    # No importamos nada de ui.py aquí
    return {}  # Retornamos un diccionario vacío

def load_student_activities_v2_functions():
    from .studentact.student_activities_v2 import display_student_activities
    return {
        'display_student_progress': display_student_activities
    }

def load_morphosyntax_functions():
    from .morphosyntax.morphosyntax_interface import (
        initialize_arc_analysis_state,
        reset_arc_analysis_state,
        display_arc_diagrams,
        display_morphosyntax_results
    )
    from .morphosyntax.morphosyntax_process import (
        process_morphosyntactic_input,
        format_analysis_results,
        perform_advanced_morphosyntactic_analysis  # Añadir esta función
    )
    
    return {
        #Interface
        'initialize_arc_analysis_state': initialize_arc_analysis_state,
        'reset_arc_analysis_state': reset_morpho_state,
        'display_arc_diagrams': display_arc_diagrams,
        'display_morphosyntax_interface': display_morphosyntax_interface,
        #Process
        'process_morphosyntactic_input': process_morphosyntactic_input,
        'format_analysis_results': format_analysis_results,
        'perform_advanced_morphosyntactic_analysis': perform_advanced_morphosyntactic_analysis
    }

def load_semantic_functions():
    from .semantic.semantic_interface import (
        display_semantic_interface, 
        display_semantic_results
    )
    from modules.semantic.semantic_process import (
        process_semantic_input, 
        format_semantic_results
    )

    return {
        'display_semantic_interface': display_semantic_interface,
        'display_semantic_results': display_semantic_results,
        'process_semantic_input': process_semantic_input,
        'format_semantic_results': format_analysis_results,
    }


def load_discourse_functions():
    from .discourse.discourse_interface import (
        display_discourse_interface, 
        display_discourse_results
    )
    from modules.discourse.discourse_process import (
        perform_discourse_analysis,      # Este es el nombre correcto de la función
        extract_key_concepts,            # Función adicional que necesitamos
        generate_concept_graph,          # Función adicional que necesitamos
        calculate_similarity_matrix      # Función adicional que necesitamos
    )
    
    return {
        'display_discourse_interface': display_discourse_interface,
        'display_discourse_results': display_discourse_results,
        'perform_discourse_analysis': perform_discourse_analysis,
        'extract_key_concepts': extract_key_concepts,
        'generate_concept_graph': generate_concept_graph,
        'calculate_similarity_matrix': calculate_similarity_matrix
    }

def load_admin_functions():
    from .admin.admin_ui import admin_page
    return {
        'admin_page': admin_page
    }

def load_utils_functions():
    from .utils.spacy_utils import load_spacy_models
    return {
        'load_spacy_models': load_spacy_models
    }

def load_chatbot_functions():
    """
    Carga las funciones del módulo de chatbot
    Returns:
        dict: Diccionario con las funciones del chatbot
    """
    from modules.chatbot.sidebar_chat import (
        display_sidebar_chat
    )
    
    from modules.chatbot.chat_process import (
        ChatProcessor
    )
    
    return {
        'display_sidebar_chat': display_sidebar_chat,
        'ChatProcessor': ChatProcessor
    }

# Función para cargar todas las funciones
def load_all_functions():
    return {
        **load_auth_functions(),
        **load_database_functions(),
        # **load_ui_functions(),
        **load_admin_functions(),
        **load_morphosyntax_functions(),
        **load_semantic_functions(),
        **load_discourse_functions(),
        **load_utils_functions(),
        **load_chatbot_functions(),
        **load_student_activities_functions(),
        **load_current_situation_functions()  # Agregar el nuevo loader
    }