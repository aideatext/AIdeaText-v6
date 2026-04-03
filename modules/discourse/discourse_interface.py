# modules/discourse/discourse/discourse_interface.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import logging
import io  # <-- Añade esta importación

from ..utils.widget_utils import generate_unique_key
from .discourse_process import perform_discourse_analysis
from ..database.chat_mongo_db import store_chat_history
from ..database.discourse_mongo_db import store_student_discourse_result

logger = logging.getLogger(__name__)

#############################################################################################
def display_discourse_interface(lang_code, nlp_models, discourse_t):
    """
    Interfaz para el análisis del discurso
    Args:
        lang_code: Código del idioma actual
        nlp_models: Modelos de spaCy cargados
        discourse_t: Diccionario de traducciones
    """
    try:
        # 1. Inicializar estado si no existe
        if 'discourse_state' not in st.session_state:
            st.session_state.discourse_state = {
                'analysis_count': 0,
                'last_analysis': None,
                'current_files': None
            }

        # 2. Título y descripción
        # st.subheader(discourse_t.get('discourse_title', 'Análisis del Discurso'))
        st.info(discourse_t.get('initial_instruction', 
            'Cargue dos archivos de texto para realizar un análisis comparativo del discurso.'))

        # 3. Área de carga de archivos
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(discourse_t.get('file1_label', "**Documento 1 (Patrón)**"))
            uploaded_file1 = st.file_uploader(
                discourse_t.get('file_uploader1', "Cargar archivo 1"),
                type=['txt'],
                key=f"discourse_file1_{st.session_state.discourse_state['analysis_count']}"
            )

        with col2:
            st.markdown(discourse_t.get('file2_label', "**Documento 2 (Comparación)**"))
            uploaded_file2 = st.file_uploader(
                discourse_t.get('file_uploader2', "Cargar archivo 2"),
                type=['txt'],
                key=f"discourse_file2_{st.session_state.discourse_state['analysis_count']}"
            )

        # 4. Botón de análisis
        col1, col2, col3 = st.columns([1,2,1])
        with col1:
            analyze_button = st.button(
                discourse_t.get('discourse_analyze_button', 'Comparar textos'),
                key=generate_unique_key("discourse", "analyze_button"),
                type="primary",
                icon="🔍",
                disabled=not (uploaded_file1 and uploaded_file2),
                use_container_width=True
            )

        # 5. Proceso de análisis
        if analyze_button and uploaded_file1 and uploaded_file2:
            try:
                with st.spinner(discourse_t.get('processing', 'Procesando análisis...')):
                    # Leer contenido de archivos
                    text1 = uploaded_file1.getvalue().decode('utf-8')
                    text2 = uploaded_file2.getvalue().decode('utf-8')

                    # Realizar análisis
                    result = perform_discourse_analysis(
                        text1, 
                        text2, 
                        nlp_models[lang_code],
                        lang_code
                    )

                    if result['success']:
                        # Guardar estado
                        st.session_state.discourse_result = result
                        st.session_state.discourse_state['analysis_count'] += 1
                        st.session_state.discourse_state['current_files'] = (
                            uploaded_file1.name,
                            uploaded_file2.name
                        )

                        # Guardar en base de datos (Llamada Normalizada)
                        if store_student_discourse_result(
                            username=st.session_state.username,
                            group_id=st.session_state.get('group_id', 'GENERAL'),
                            text1=text1,
                            text2=text2,
                            analysis_result=result,
                            lang_code=lang_code
                        ):
                            st.success(discourse_t.get('success_message', 'Análisis guardado correctamente'))
                            
                            # Mostrar resultados
                            display_discourse_results(result, lang_code, discourse_t)
                        else:
                            st.error(discourse_t.get('error_message', 'Error al guardar el análisis'))
                    else:
                        st.error(discourse_t.get('analysis_error', 'Error en el análisis'))

            except Exception as e:
                logger.error(f"Error en análisis del discurso: {str(e)}")
                st.error(discourse_t.get('error_processing', f'Error procesando archivos: {str(e)}'))

        # 6. Mostrar resultados previos
        elif 'discourse_result' in st.session_state and st.session_state.discourse_result is not None:
            if st.session_state.discourse_state.get('current_files'):
                st.info(
                    discourse_t.get('current_analysis_message', 'Mostrando análisis de los archivos: {} y {}')
                    .format(*st.session_state.discourse_state['current_files'])
                )
            display_discourse_results(
                st.session_state.discourse_result,
                lang_code,
                discourse_t
            )

    except Exception as e:
        logger.error(f"Error general en interfaz del discurso: {str(e)}")
        st.error(discourse_t.get('general_error', 'Se produjo un error. Por favor, intente de nuevo.'))



#####################################################################################################################
def display_discourse_results(result, lang_code, discourse_t):
    """
    Muestra los resultados del análisis del discurso
    Versión actualizada con:
    - Un solo expander para interpretación
    - Botón de descarga combinado
    - Sin mensaje de "próxima actualización"
    - Estilo consistente con semantic_interface
    """
    if not result.get('success'):
        st.warning(discourse_t.get('no_results', 'No hay resultados disponibles'))
        return

    # Estilo CSS unificado
    st.markdown("""
    <style>
    .concept-table {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 20px;
    }
    .concept-item {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 8px 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .concept-name {
        font-weight: bold;
    }
    .concept-freq {
        color: #666;
        font-size: 0.9em;
    }
    .download-btn-container {
        display: flex;
        justify-content: center;
        margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Mostrar conceptos clave para ambos documentos
    col1, col2 = st.columns(2)
    
    # Documento 1
    with col1:
        st.subheader(discourse_t.get('compare_doc1_title', 'Documento 1'))
        if 'key_concepts1' in result:
            df1 = pd.DataFrame(
                result['key_concepts1'],
                columns=[discourse_t.get('concept', 'Concepto'), discourse_t.get('frequency', 'Frecuencia')]
            )
            st.write(
                '<div class="concept-table">' + 
                ''.join([
                    f'<div class="concept-item"><span class="concept-name">{concept}</span>'
                    f'<span class="concept-freq">({freq:.2f})</span></div>'
                    for concept, freq in df1.values
                ]) + "</div>",
                unsafe_allow_html=True
            )
            
            if 'graph1' in result and result['graph1']:
                st.image(result['graph1'], width='stretch')

    # Documento 2
    with col2:
        st.subheader(discourse_t.get('compare_doc2_title', 'Documento 2'))
        if 'key_concepts2' in result:
            df2 = pd.DataFrame(
                result['key_concepts2'],
                columns=[discourse_t.get('concept', 'Concepto'), discourse_t.get('frequency', 'Frecuencia')]
            )
            st.write(
                '<div class="concept-table">' + 
                ''.join([
                    f'<div class="concept-item"><span class="concept-name">{concept}</span>'
                    f'<span class="concept-freq">({freq:.2f})</span></div>'
                    for concept, freq in df2.values
                ]) + "</div>",
                unsafe_allow_html=True
            )
            
            if 'graph2' in result and result['graph2']:
                st.image(result['graph2'], width='stretch')

    # Sección unificada de interpretación (como semantic_interface)
    st.markdown("""
    <style>
    div[data-testid="stExpander"] div[role="button"] p {
        text-align: center;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with st.expander("📊 " + discourse_t.get('semantic_graph_interpretation', "Interpretación de los gráficos")):
        st.markdown(f"""
        - 🔀 {discourse_t.get('compare_arrow_meaning', 'Las flechas indican la dirección de la relación entre conceptos')}
        - 🎨 {discourse_t.get('compare_color_meaning', 'Los colores más intensos indican conceptos más centrales en el texto')}
        - ⭕ {discourse_t.get('compare_size_meaning', 'El tamaño de los nodos representa la frecuencia del concepto')}
        - ↔️ {discourse_t.get('compare_thickness_meaning', 'El grosor de las líneas indica la fuerza de la conexión')}
        """)

    # Botón de descarga combinado (para ambas imágenes)
    if 'graph1' in result and 'graph2' in result and result['graph1'] and result['graph2']:
        # Crear figura combinada
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 10))
        
        # Mostrar primer gráfico
        if isinstance(result['graph1'], bytes):
            img1 = plt.imread(io.BytesIO(result['graph1']))
            ax1.imshow(img1)
        ax1.axis('off')
        ax1.set_title(discourse_t.get('compare_doc1_title', 'Documento 1'))
        
        # Mostrar segundo gráfico
        if isinstance(result['graph2'], bytes):
            img2 = plt.imread(io.BytesIO(result['graph2']))
            ax2.imshow(img2)
        ax2.axis('off')
        ax2.set_title(discourse_t.get('compare_doc2_title', 'Documento 2'))
        
        plt.tight_layout()
        
        # Convertir a bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        
        # Botón de descarga
        st.markdown('<div class="download-btn-container">', unsafe_allow_html=True)
        st.download_button(
            label="📥 " + discourse_t.get('download_both_graphs', "Descargar ambos gráficos"),
            data=buf,
            file_name="comparison_graphs.png",
            mime="image/png",
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        plt.close()