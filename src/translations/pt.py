# translations/pt.py

COMMON = {
    # A
    'initial_instruction': "Para iniciar uma nova análise semântica, carregue um novo arquivo de texto (.txt)",
    'analysis_complete': "Análise completa e salva. Para realizar uma nova análise, carregue outro arquivo.",
    'current_analysis_message': "Exibindo análise do arquivo: {}. Para realizar uma nova análise, carregue outro arquivo.",
    'upload_prompt': "Anexe um arquivo para iniciar a análise",
    'analysis_completed': "Análise concluída",
    'analysis_section': "Análise Semântica",
    'analyze_document': 'Analisar documento',
    'analysis_saved_success': 'Análise salva com sucesso',
    'analysis_save_error': 'Erro ao salvar a análise',
    'analyze_button': "Analisar texto",
    'analyzing_doc': "Analisando documento",
    'activities_message': "Mensagens de atividades",
    'activities_placeholder': "Espaço reservado para atividades",
    'analysis_placeholder': "Espaço reservado para análise",
    'analyze_button': "Analisar",
    'analysis_types_chart': "Gráfico de tipos de análise",
    'analysis_from': "Análise realizada em",
    # C
    'chat_title': "Chat de Análise",
    'export_button': "Exportar Análise Atual",
    'export_success': "Análise e chat exportados com sucesso.",
    'export_error': "Ocorreu um problema ao exportar a análise e o chat.",
    'get_text': "Obter texto.",
    'hello': "Olá",
    # L
    'logout': "Encerrar sessão.",
    'loading_data': "Carregando dados",
    'load_selected_file': 'Carregar arquivo selecionado',
    # N
    'no_analysis': "Nenhuma análise disponível. Use o chat para realizar uma análise.",
    'nothing_to_export': "Nenhuma análise ou chat para exportar.",
    'results_title': "Resultados da Análise",
    'select_language': "Selecionar idioma",
    'student_activities': "Atividades do estudante",
    # T
    'total_analyses': "Total de análises",
    # W
    'welcome': "Bem-vindo ao AIdeaText"
}

TABS = {
    'current_situation_tab': "Situação atual",
    'morpho_tab': "Análise morfossintática",
    'semantic_live_tab': "Semântica ao vivo",
    'semantic_tab': "Análise semântica",
    'discourse_live_tab': "Discurso ao vivo",
    'discourse_tab': "Análise do discurso",
    'activities_tab': "Minhas atividades",
    'feedback_tab': "Formulário de feedback"
}

CURRENT_SITUATION = {
    'title': "Minha Situação Atual",
    'input_prompt': "Escreva ou cole seu texto aqui:",
    'first_analyze_button': "Analisar minha escrita",
    'processing': "Analisando...",
    'analysis_error': "Erro ao analisar o texto",
    'help': "Analisaremos seu texto para determinar seu estado atual",

    # Radio buttons para tipo de texto
    'text_type_header': "Tipo de texto",
    'text_type_help': "Selecione o tipo de texto para ajustar os critérios de avaliação",
    
    # Métricas
    'vocabulary_label': "Vocabulário",
    'vocabulary_help': "Riqueza e variedade do vocabulário",
    'structure_label': "Estrutura", 
    'structure_help': "Organização e complexidade das frases",
    'cohesion_label': "Coesão",
    'cohesion_help': "Conexão e fluidez entre ideias",
    'clarity_label': "Clareza",
    'clarity_help': "Facilidade de compreensão do texto",
    
    # Estados de métricas
    'metric_improvement': "⚠️ Precisa melhorar",
    'metric_acceptable': "📈 Aceitável",
    'metric_optimal': "✅ Ótimo",
    'metric_target': "Meta: {:.2f}",
    
    # Errores
    'error_interface': "Ocorreu um erro ao carregar a interface",
    'error_results': "Erro ao exibir os resultados",
    'error_chart': "Erro ao exibir o gráfico"
}

MORPHOSYNTACTIC = {
    #A
    'arc_diagram': "Análise sintática: Diagrama de arco",
    #B
    'tab_text_baseline': "Produzir o primeiro texto",
    'tab_iterations': "Produzir novas versões do primeiro texto",
    
    # Pestaña 1 texto base 
    'btn_new_morpho_analysis': "Nova análise morfossintática",
    'btn_analyze_baseline': "Analisar o texto inserido",
    'input_baseline_text': "Insira o primeiro texto para analisar",
    'warn_enter_text': "Por favor, insira um texto para analisar",
    'error_processing_baseline': "Erro ao processar o texto inicial",
    'arc_diagram_baseline_label': "Diagrama de arco do texto inicial",
    'baseline_diagram_not_available': "Diagrama de arco do texto inicial não disponível",

    # Pestaña 2 Iteración del texto 
    'info_first_analyze_base': "Verifique se o texto inicial existe",
    'iteration_text_subheader': "Nova versão do texto inicial",
    'input_iteration_text': "Insira uma nova versão do texto inicial e compare os arcos de ambos os textos",
    'btn_analyze_iteration': "Analisar mudanças",
    'warn_enter_iteration_text': "Insira uma nova versão do texto inicial e compare os arcos de ambos os textos",
    'iteration_saved': "Mudanças salvas com sucesso",
    'error_iteration': "Erro ao processar as novas mudanças",
    
    #C
    'count': "Contagem",
    #D
    'dependency': "Dependência",
    'dep': "Dependência",
    #E
    'error_message': "Houve um problema ao salvar a análise. Por favor, tente novamente.",
    'examples': "Exemplos",
    #G
    'grammatical_category': "Categoria gramatical",
    #L
    'lemma': "Lema",
    'legend': "Legenda: Categorias gramaticais",
    #O
    'objects': "Objetos",
    #P
    'pos_analysis': "Análise de Classes Gramaticais",
    'percentage': "Porcentagem",
    #N
    'no_results': "Nenhum resultado disponível. Por favor, realize uma análise primeiro.",
    #M
    'morpho_analyze_button': 'Análise Morfossintática',
    'morpho_title': "AIdeaText - Análise morfológica",
    'morpho_initial_message': "Este é um chatbot de propósito geral, mas tem uma função específica para análise visual de texto: geração de diagramas de arco. Para produzi-los, digite o seguinte comando /analisis_morfosintactico [seguido por colchetes dentro dos quais você deve colocar o texto que deseja analisar]",
    'morpho_input_label': "Digite um texto para analisar (máx. 30 palavras):",
    'morpho_input_placeholder': "espaço reservado para morfossintaxe",
    'morphosyntactic_analysis_completed': 'Análise morfossintática concluída. Por favor, revise os resultados na seção seguinte.',
    'morphological_analysis': "Análise Morfológica",
    'morphology': "Morfologia",
    'morph': "Morfologia",
    #R
    'root': "Raiz",
    'repeated_words': "Palavras repetidas",
    #S
    'sentence': "Frase",
    'success_message': "Análise salva com sucesso.",
    'sentence_structure': "Estrutura da Frase",
    'subjects': "Sujeitos",
    #V
    'verbs': "Verbos",
    #T
    'title': "AIdeaText - Análise Morfológica e Sintática",
    'tag': "Etiqueta",
    #W
    'warning_message': "Por favor, digite um texto para analisar.",
    'word': "Palavra",
    'processing': 'Processando...',
    'error_processing': 'Erro de processamento',
    'morphosyntactic_analysis_error': 'Erro na análise morfossintática',
    'morphosyntactic_analysis_completed': 'Análise morfossintática concluída'
}

SEMANTIC = {
    # C
    'chat_title': "Chat de Análise Semântica",
    'chat_placeholder': "Faça uma pergunta ou use um comando (/resumo, /entidades, /sentimento, /tópicos, /grafo_conceitos, /grafo_entidades, /grafo_tópicos)",
    'clear_chat': "Limpar chat",
    'conceptual_relations': "Relações Conceituais",
    # D
    'delete_file': "Excluir arquivo",
    'download_semantic_network_graph': "Baixar gráfico de rede semântica",
    # E
    'error_message': "Houve um problema ao salvar a análise semântica. Por favor, tente novamente.",
    # F
    'file_uploader': "Ou carregue um arquivo de texto",
    'file_upload_success': "Arquivo carregado e salvo com sucesso",
    'file_upload_error': 'Erro ao carregar arquivo',
    'file_section': "Arquivos",
    'file_loaded_success': "Arquivo carregado com sucesso",
    'file_load_error': "Erro ao carregar arquivo",
    'file_upload_error': "Erro ao carregar e salvar arquivo",
    'file_deleted_success': 'Arquivo excluído com sucesso',
    'file_delete_error': 'Erro ao excluir arquivo',
    # G
    'graph_title': "Visualização da Análise Semântica",
    # I
    'identified_entities': "Entidades Identificadas",
    # K
    'key_concepts': "Conceitos-Chave",
    # N
    'no_analysis': "Nenhuma análise disponível. Por favor, carregue ou selecione um arquivo.",
    'no_results': "Nenhum resultado disponível. Por favor, realize uma análise primeiro.",
    'no_file': "Por favor, carregue um arquivo para iniciar a análise.",
    'no_file_selected': "Por favor, selecione um arquivo para iniciar a análise.",
    # S
    ###################
    'semantic_virtual_agent_button': 'Analisar com Agente Virtual',
    'semantic_agent_ready_message': 'O agente virtual recebeu sua análise semântica. Abra o assistente na barra lateral para discutir seus resultados.',
    'semantic_chat_title': 'Análise Semântica - Assistente Virtual',
    ####
    'semantic_graph_interpretation': "Interpretação do gráfico semântico",
    'semantic_arrow_meaning': "As setas indicam a direção da relação entre os conceitos",
    'semantic_color_meaning': "Cores mais intensas indicam conceitos mais centrais no texto",
    'semantic_size_meaning': "O tamanho dos nós representa a frequência do conceito",
    'semantic_thickness_meaning': "A espessura das linhas indica a força da conexão",
    ####
    'semantic_graph_interpretation': "Interpretação de gráficos semânticos",
    'semantic_title': "Análise Semântica",
    'semantic_initial_message': "Este é um chatbot de propósito geral, mas tem uma função específica para análise visual de texto: gera um grafo com as principais entidades do texto. Para produzi-lo, insira um arquivo de texto em formato txt, pdf, doc, docx ou odt e pressione o botão 'analisar arquivo'. Após a geração do grafo, você pode interagir com o chat com base no documento.",
    'send_button': "Enviar",
    'select_saved_file': "Selecionar arquivo salvo",
    'success_message': "Análise semântica salva com sucesso.",
    'semantic_analyze_button': 'Análise Semântica',
    'semantic_export_button': 'Exportar Análise Semântica',
    'semantic_new_button': 'Nova Análise Semântica',
    'semantic_file_uploader': 'Carregar um arquivo de texto para análise semântica',
    # T
    'text_input_label': "Digite um texto para analisar (máx. 5.000 palavras):",
    'text_input_placeholder': "O objetivo desta aplicação é melhorar suas habilidades de escrita...",
    'title': "AIdeaText - Análise Semântica",
    # U
    'upload_file': "Carregar arquivo",
    # W
    'warning_message': "Por favor, digite um texto ou carregue um arquivo para analisar."
}

DISCOURSE = {
    'compare_arrow_meaning': "As setas indicam a direção da relação entre os conceitos",
    'compare_color_meaning': "Cores mais intensas indicam conceitos mais centrais no texto",
    'compare_size_meaning': "O tamanho dos nós representa a frequência do conceito",
    'compare_thickness_meaning': "A espessura das linhas indica a força da conexão",
    'compare_doc1_title': "Documento 1",
    'compare_doc2_title': "Documento 2",
    'file1_label': "Documento Padrão",
    'file2_label': "Documento Comparado",
    'discourse_title': "AIdeaText - Análise do Discurso",
    'file_uploader1': "Carregar arquivo de texto 1 (Padrão)",
    'file_uploader2': "Carregar arquivo de texto 2 (Comparação)",
    'discourse_analyze_button': "Comparar textos",
    'discourse_initial_message': "Este é um chatbot de propósito geral, mas tem uma função específica para análise visual de texto: gera dois grafos com as principais entidades de cada arquivo para fazer uma comparação entre ambos os textos. Para produzi-lo, insira um arquivo primeiro e depois outro em formato txt, pdf, doc, docx ou odt e pressione o botão 'analisar arquivo'. Após a geração do grafo, você pode interagir com o chat com base no documento.",
    'analyze_button': "Analisar textos",
    'comparison': "Comparação de Relações Semânticas",
    'success_message': "Análise do discurso salva com sucesso.",
    'error_message': "Houve um problema ao salvar a análise do discurso. Por favor, tente novamente.",
    'warning_message': "Por favor, carregue ambos os arquivos para analisar.",
    'no_results': "Nenhum resultado disponível. Por favor, realize uma análise primeiro.",
    'key_concepts': "Conceitos-Chave",
    'graph_not_available': "O grafo não está disponível.",
    'concepts_not_available': "Os conceitos-chave não estão disponíveis.",
    'comparison_not_available': "A comparação não está disponível.",
    'morphosyntax_history': "Histórico morfossintático",
    'analysis_of': "Análise de"
}

ACTIVITIES = {
    # Nuevas etiquetas actualizadas
    'current_situation_activities': "Registros da função: Minha Situação Atual",
    'morpho_activities': "Registros das minhas análises morfossintáticas",
    'semantic_activities': "Registros das minhas análises semânticas",
    'discourse_activities': "Registros das minhas análises de comparação de textos",
    'chat_activities': "Registros das minhas conversas com o tutor virtual",
    
    # Mantener otras claves existentes
    'current_situation_tab': "Situação atual",
    'morpho_tab': "Análise morfossintática",
    'semantic_tab': "Análise semântica",
    'discourse_tab': "Análise de comparação de textos",
    'activities_tab': "Meu registro de atividades",
    'feedback_tab': "Formulário de feedback",
    
    # Resto de las claves que estén en el diccionario ACTIVITIES
    'analysis_types_chart_title': "Tipos de análises realizadas",
    'analysis_types_chart_x': "Tipo de análise",
    'analysis_types_chart_y': "Contagem",
    'analysis_from': "Análise de",
    'assistant': "Assistente",
    'activities_summary': "Resumo de Atividades e Progresso",
    'chat_history_expander': "Histórico de Chat",
    'chat_from': "Chat de",
    'combined_graph': "Grafo Combinado",
    'conceptual_relations_graph': "Grafo de Relações Conceituais",
    'conversation': "Conversa",
    'discourse_analyses_expander': "Histórico de Análises de Comparação de Textos",  # Actualizado
    'discourse_analyses': "Análises de Comparação de Textos",  # Actualizado
    'discourse_history': "Histórico de Análise de Comparação de Textos",  # Actualizado
    'document': "Documento",
    'data_load_error': "Erro ao carregar dados do estudante",
    'graph_display_error': "Não foi possível exibir o grafo",
    'graph_doc1': "Grafo documento 1",
    'graph_doc2': "Grafo documento 2",
    'key_concepts': "Conceitos-chave",
    'loading_data': "Carregando dados do estudante...",
    'morphological_analysis': "Análise Morfológica",
    'morphosyntax_analyses_expander': "Histórico de Análises Morfossintáticas",
    'morphosyntax_history': "Histórico de Análise Morfossintática",
    'no_arc_diagram': "Nenhum diagrama de arco encontrado para esta análise.",
    'no_chat_history': "Nenhuma conversa com o Tutor Virtual foi encontrada.",  # Actualizado
    'no_data_warning': "Nenhum dado de análise encontrado para este estudante.",
    'progress_of': "Progresso de",
    'semantic_analyses': "Análises Semânticas",
    'semantic_analyses_expander': "Histórico de Análises Semânticas",
    'semantic_history': "Histórico de Análise Semântica",
    'show_debug_data': "Mostrar dados de depuração",
    'student_debug_data': "Dados do estudante (para depuração):",
    'summary_title': "Resumo de Atividades",
    'title': "Meu Registro de Atividades",  # Actualizado
    'timestamp': "Data e hora",
    'total_analyses': "Total de análises realizadas:",
    'try_analysis': "Tente realizar algumas análises de texto primeiro.",
    'user': "Usuário",
    
    # Nuevas traducciones específicas para la sección de actividades
    'diagnosis_tab': "Diagnóstico",
    'recommendations_tab': "Recomendações",
    'key_metrics': "Métricas chave",
    'details': "Detalhes",
    'analyzed_text': "Texto analisado",
    'analysis_date': "Data",
    'academic_article': "Artigo acadêmico",
    'student_essay': "Trabalho acadêmico",
    'general_communication': "Comunicação geral",
    'no_diagnosis': "Nenhum dado de diagnóstico disponível",
    'no_recommendations': "Nenhuma recomendação disponível",
    'error_current_situation': "Erro ao exibir análise da situação atual",
    'no_current_situation': "Nenhuma análise de situação atual registrada",
    'no_morpho_analyses': "Nenhuma análise morfossintática registrada",
    'error_morpho': "Erro ao exibir análise morfossintática",
    'no_semantic_analyses': "Nenhuma análise semântica registrada",
    'error_semantic': "Erro ao exibir análise semântica",
    'no_discourse_analyses': "Nenhuma análise de comparação de textos registrada",
    'error_discourse': "Erro ao exibir análise de comparação de textos",
    'no_chat_history': "Nenhum registro de conversa com o tutor virtual",
    'error_chat': "Erro ao exibir registros de conversa",
    'error_loading_activities': "Erro ao carregar atividades",
    'chat_date': "Data da conversa",
    'invalid_chat_format': "Formato de chat inválido",
    'comparison_results': "Resultados da comparação",
    'concepts_text_1': "Conceitos Texto 1",
    'concepts_text_2': "Conceitos Texto 2",
    'no_visualization': "Nenhuma visualização comparativa disponível",
    'no_graph': "Nenhuma visualização disponível",
    'error_loading_graph': "Erro ao carregar gráfico",
    'syntactic_diagrams': "Diagramas sintáticos"
}

FEEDBACK = {
    'email': "Email",
    'feedback': "Feedback",
    'feedback_title': "Formulário de feedback",
    'feedback_error': "Houve um problema ao enviar o formulário. Por favor, tente novamente.",
    'feedback_success': "Obrigado pelo seu feedback",
    'complete_all_fields': "Por favor, preencha todos os campos",
    'name': "Nome",
    'submit': "Enviar"
}

CHATBOT_TRANSLATIONS = {
    'chat_title': "Assistente AIdeaText",
    'input_placeholder': "Alguma pergunta?",
    'initial_message': "Olá! Sou seu assistente. Como posso ajudar?",
    'expand_chat': "Abrir assistente",
    'clear_chat': "Limpar chat",
    'processing': "Processando...",
    'error_message': "Desculpe, ocorreu um erro"
}

TEXT_TYPES = {
    'descritivo': [
        'O que você está descrevendo?',
        'Quais são suas principais características?',
        'Como é a aparência, som, cheiro ou sensação?',
        'O que o torna único ou especial?'
    ],
    'narrativo': [
        'Quem é o protagonista?',
        'Onde e quando a história se passa?',
        'Qual evento inicia a ação?',
        'O que acontece depois?',
        'Como a história termina?'
    ],
    'expositivo': [
        'Qual é o tema principal?',
        'Quais aspectos importantes você quer explicar?',
        'Você pode fornecer exemplos ou dados para apoiar sua explicação?',
        'Como este tema se relaciona com outros conceitos?'
    ],
    'argumentativo': [
        'Qual é sua tese ou argumento principal?',
        'Quais são seus argumentos de apoio?',
        'Que evidências você tem para sustentar seus argumentos?',
        'Quais são os contra-argumentos e como você os refuta?',
        'Qual é sua conclusão?'
    ],
    'instrutivo': [
        'Que tarefa ou processo você está explicando?',
        'Quais materiais ou ferramentas são necessários?',
        'Quais são os passos a seguir?',
        'Existem precauções importantes ou dicas a mencionar?'
    ],
    'pitch': [
        'O quê?',
        'Para quê?',
        'Para quem?',
        'Como?'
    ]
}

# Configuração do modelo de linguagem para Português
NLP_MODEL = 'pt_core_news_lg'

# Esta linha é crucial:
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