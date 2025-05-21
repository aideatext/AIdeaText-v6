#morphosyntax_interface.py

import streamlit as st
import re
import logging
from spacy import displacy

# Funciones de análisis y DB que ya tienes en tus módulos
from ..morphosyntax.morphosyntax_process import perform_advanced_morphosyntactic_analysis
from ..database.morphosyntax_iterative_mongo_db import (
    store_student_morphosyntax_base,
    store_student_morphosyntax_iteration,
)

from translations import get_translations 

logger = logging.getLogger(__name__)

###########################################################################
def initialize_arc_analysis_state():
    """Inicializa el estado de análisis de arcos (base e iteraciones) si no existe."""
    if "arc_analysis_state" not in st.session_state:
        st.session_state.arc_analysis_state = {
            "base_id": None,
            "base_text": "",
            "base_diagram": None,
            "iteration_text": "",
            "iteration_diagram": None,
        }
        logger.info("Estado de análisis de arcos inicializado.")

###########################################################################
def reset_arc_analysis_state():
    """Resetea completamente el estado de análisis de arcos."""
    st.session_state.arc_analysis_state = {
        "base_id": None,
        "base_text": "",
        "base_diagram": None,
        "iteration_text": "",
        "iteration_diagram": None,
    }
    logger.info("Estado de arcos reseteado.")

###########################################################################
def display_arc_diagram(doc):
    """
    Genera y retorna el HTML del diagrama de arco para un Doc de spaCy.
    No imprime directamente; retorna el HTML para usar con st.write(...).
    """
    try:
        diagram_html = ""
        for sent in doc.sents:
            svg_html = displacy.render(
                sent,
                style="dep",
                options={
                    "distance": 100,
                    "arrow_spacing": 20,
                    "word_spacing": 30
                }
            )
            # Ajustar tamaños en el SVG resultante
            svg_html = svg_html.replace('height="375"', 'height="200"')
            svg_html = re.sub(
                r'<svg[^>]*>',
                lambda m: m.group(0).replace('height="450"', 'height="300"'),
                svg_html
            )
            svg_html = re.sub(
                r'<g [^>]*transform="translate\((\d+),(\d+)\)"',
                lambda m: f'<g transform="translate({m.group(1)},50)"',
                svg_html
            )
            # Envolver en contenedor
            diagram_html += f'<div class="arc-diagram-container">{svg_html}</div>'
        return diagram_html

    except Exception as e:
        logger.error(f"Error en display_arc_diagram: {str(e)}")
        return "<p style='color:red;'>Error generando diagrama</p>"

###########################################################################
def display_morphosyntax_interface(lang_code, nlp_models, morpho_t):
    """
    Interfaz principal para la visualización de diagramas de arco
    (Texto Base vs Iteraciones), usando traducciones con morpho_t.
    """
    # CSS para layout y estilo
    st.markdown("""
        <style>
        .stTextArea textarea {
            font-size: 1rem;
            line-height: 1.5;
            min-height: 100px !important;
            height: 100px !important;
        }
        .arc-diagram-container {
            width: 100%;
            padding: 0.5rem;
            margin: 0.5rem 0;
        }
        .divider {
            height: 3px;
            border: none;
            background-color: #333;
            margin: 2rem 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # 1) Inicializar estados
    initialize_arc_analysis_state()
    arc_state = st.session_state.arc_analysis_state

    # 2) Crear pestañas con etiquetas traducidas
    tab_text_base = morpho_t.get('tab_text_baseline', 'Ingresa la primera versión de tu texto')
    tab_iterations = morpho_t.get('tab_iterations', 'Produce nuevas versiones de tu primer texto')
    tabs = st.tabs([tab_text_base, tab_iterations])

    # =================== PESTAÑA 1: Texto Base ==========================
    with tabs[0]:
        # st.subheader(morpho_t.get('analysis_base_subheader', "Análisis de Texto Base"))

        # Textarea de texto base
        arc_state["base_text"] = st.text_area(
            morpho_t.get('input_baseline_text', "Ingresa el primer texto para analizarlo"),
            value=arc_state["base_text"],
            key="base_text_input",
            height=150
        )

        # Botón para analizar texto base
        if st.button(morpho_t.get('btn_analyze_baseline', "Analizar la primera versión de tu texto"), key="btn_analyze_base"):
            if not arc_state["base_text"].strip():
                st.warning(morpho_t.get('warn_enter_text', "Ingrese un texto nuevo para analizarlo."))
            else:
                try:
                    # Procesar con spaCy
                    doc = nlp_models[lang_code](arc_state["base_text"])
                    base_arc_html = display_arc_diagram(doc)
                    arc_state["base_diagram"] = base_arc_html

                    # Guardar en Mongo
                    analysis = perform_advanced_morphosyntactic_analysis(
                        arc_state["base_text"],
                        nlp_models[lang_code]
                    )
                    base_id = store_student_morphosyntax_base(
                        username=st.session_state.username,
                        text=arc_state["base_text"],
                        arc_diagrams=analysis["arc_diagrams"]
                    )
                    if base_id:
                        arc_state["base_id"] = base_id
                        saved_msg = morpho_t.get('analysis_base_saved', "Análisis base guardado. ID: {base_id}")
                        st.success(saved_msg.format(base_id=base_id))

                except Exception as exc:
                    st.error(morpho_t.get('error_processing_baseline', "Error al procesar el texto inicial"))
                    logger.error(f"Error en análisis base: {str(exc)}")

        # Botón para iniciar nuevo análisis
        if st.button(morpho_t.get('btn_new_morpho_analysis', "Nuevo análisis morfosintático"), key="btn_reset_base"):
            # Si fuera necesario recargar la app por completo:
            # st.experimental_rerun()
            reset_arc_analysis_state()
        
        # Mostrar diagrama base
        if arc_state["base_diagram"]:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown(f"#### {morpho_t.get('arc_diagram_baseline_label', 'Diagrama de arco del texto inicial')}")
            st.write(arc_state["base_diagram"], unsafe_allow_html=True)
        else:
            if arc_state["base_text"].strip():
                # Solo mostrar si ya hay texto base pero no se ha procesado
                st.info(morpho_t.get('baseline_diagram_not_available', "Diagrama de arco del texto inicial no disponible."))

    # ================== PESTAÑA 2: Iteraciones ==========================
    with tabs[1]:
        #st.subheader(morpho_t.get('iteration_text_subheader', "Nueva versión del texto inicial"))

        # Verificar que exista un texto base
        if not arc_state["base_id"]:
            st.info(morpho_t.get('info_first_analyze_base',
                                 "Verifica la existencia de un texto anterior."))
            return

        # --- 1) Mostrar SIEMPRE el diagrama base arriba ---
        st.markdown(f"#### {morpho_t.get('arc_diagram_base_label', 'Diagrama de arco del texto inicial')}")
        if arc_state["base_diagram"]:
            st.write(arc_state["base_diagram"], unsafe_allow_html=True)
        else:
            st.info(morpho_t.get('baseline_diagram_not_available', "Diagrama de arco del texto inicial no disponible."))

        # --- 2) Caja de texto para la iteración ---
        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        #st.subheader(morpho_t.get('iteration_text_subheader', "Ingresa una nueva versión del texto inicial y compara los arcos de ambos textos"))

        arc_state["iteration_text"] = st.text_area(
            morpho_t.get('input_iteration_text', "Ingresa una nueva versión del texto inicial y compara los arcos de ambos textos"),
            value=arc_state["iteration_text"],
            height=150
        )

        # Botón para analizar iteración
        if st.button(morpho_t.get('btn_analyze_iteration', "Analizar Cambios"), key="btn_analyze_iteration"):
            if not arc_state["iteration_text"].strip():
                st.warning(morpho_t.get('warn_enter_iteration_text', "Ingresa una nueva versión del texto inicial y compara los arcos de ambos textos."))
            else:
                try:
                    # Procesar con spaCy
                    doc_iter = nlp_models[lang_code](arc_state["iteration_text"])
                    arc_html_iter = display_arc_diagram(doc_iter)
                    arc_state["iteration_diagram"] = arc_html_iter

                    # Guardar en Mongo
                    analysis_iter = perform_advanced_morphosyntactic_analysis(
                        arc_state["iteration_text"],
                        nlp_models[lang_code]
                    )
                    iteration_id = store_student_morphosyntax_iteration(
                        username=st.session_state.username,
                        base_id=arc_state["base_id"],
                        original_text=arc_state["base_text"],
                        iteration_text=arc_state["iteration_text"],
                        arc_diagrams=analysis_iter["arc_diagrams"]
                    )
                    if iteration_id:
                        saved_iter_msg = morpho_t.get('iteration_saved', "Cambios guardados correctamente. ID: {iteration_id}")
                        st.success(saved_iter_msg.format(iteration_id=iteration_id))

                except Exception as exc:
                    st.error(morpho_t.get('error_iteration', "Error procesando los nuevos cambios"))
                    logger.error(f"Error en iteración: {str(exc)}")

        
        # --- 3) Mostrar diagrama de iteración debajo ---
        if arc_state["iteration_diagram"]:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown(f"#### {morpho_t.get('arc_diagram_iteration_label', 'Diagrama de Arco (Iteración)')}")
            st.write(arc_state["iteration_diagram"], unsafe_allow_html=True)
