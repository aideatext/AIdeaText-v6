# modules/morphosyntax/morphosyntax_interface.py

import streamlit as st
import re
import logging
from spacy import displacy

# Se asume que la función perform_advanced_morphosyntactic_analysis
# y los métodos store_student_morphosyntax_base/iteration existen.
from ..morphosyntax.morphosyntax_process import perform_advanced_morphosyntactic_analysis
from ..database.backUp.morphosyntax_iterative_mongo_db import (
    store_student_morphosyntax_base,
    store_student_morphosyntax_iteration,
)

logger = logging.getLogger(__name__)

###########################################################################
def initialize_arc_analysis_state():
    """
    Inicializa el estado de análisis de arcos (base e iteraciones) si no existe.
    """
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
    """
    Resetea completamente el estado de análisis de arcos.
    """
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
    Genera y retorna el HTML del diagrama de arco para un `Doc` de spaCy.
    No imprime directamente en pantalla; regresa el HTML para 
    usar con `st.write(..., unsafe_allow_html=True)`.
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
            # Ajustar tamaños
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
    (Texto Base vs Iteraciones).
    """
    # CSS para layout vertical y estable
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

    # 2) Creamos pestañas: "Texto Base" y "Iteraciones"
    tabs = st.tabs(["Texto Base", "Iteraciones"])

    # =================== PESTAÑA 1: Texto Base ==========================
    with tabs[0]:
        st.subheader("Análisis de Texto Base")

        # Botón para iniciar nuevo análisis
        if st.button("Nuevo Análisis", key="btn_reset_base"):
            # Solo limpiamos el estado; si requieres forzar reload,
            # descomenta la siguiente línea:
            # st.experimental_rerun()
            reset_arc_analysis_state()

        # Textarea de texto base
        arc_state["base_text"] = st.text_area(
            "Ingrese su texto inicial",
            value=arc_state["base_text"],
            key="base_text_input",
            height=150
        )

        # Botón para analizar texto base
        if st.button("Analizar Texto Base", key="btn_analyze_base"):
            if not arc_state["base_text"].strip():
                st.warning("Ingrese un texto para analizar.")
            else:
                try:
                    # Procesar con spaCy
                    doc = nlp_models[lang_code](arc_state["base_text"])
                    # Generar HTML del arco
                    arc_html = display_arc_diagram(doc)
                    arc_state["base_diagram"] = arc_html

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
                        st.success(f"Análisis base guardado. ID: {base_id}")

                except Exception as exc:
                    st.error("Error procesando texto base")
                    logger.error(f"Error en análisis base: {str(exc)}")

        # Mostrar diagrama base
        if arc_state["base_diagram"]:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("#### Diagrama de Arco (Texto Base)")
            st.write(arc_state["base_diagram"], unsafe_allow_html=True)

    # ================== PESTAÑA 2: Iteraciones ==========================
    with tabs[1]:
        st.subheader("Análisis de Cambios / Iteraciones")

        # Verificar que exista texto base analizado
        if not arc_state["base_id"]:
            st.info("Primero analiza un texto base en la pestaña anterior.")
            return

        # Mostrar texto base como referencia (solo lectura)
        st.text_area(
            "Texto Base (solo lectura)",
            value=arc_state["base_text"],
            height=80,
            disabled=True
        )

        # Caja de texto para la iteración
        arc_state["iteration_text"] = st.text_area(
            "Texto de Iteración",
            value=arc_state["iteration_text"],
            height=150
        )

        # Botón analizar iteración
        if st.button("Analizar Cambios", key="btn_analyze_iteration"):
            if not arc_state["iteration_text"].strip():
                st.warning("Ingrese texto de iteración.")
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
                        st.success(f"Iteración guardada. ID: {iteration_id}")

                except Exception as exc:
                    st.error("Error procesando iteración")
                    logger.error(f"Error en iteración: {str(exc)}")

        # Mostrar diagrama de iteración
        if arc_state["iteration_diagram"]:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("#### Diagrama de Arco (Iteración)")
            st.write(arc_state["iteration_diagram"], unsafe_allow_html=True)

        # Comparación vertical (uno abajo del otro)
        if arc_state["base_diagram"] and arc_state["iteration_diagram"]:
            st.markdown("<hr class='divider'>", unsafe_allow_html=True)
            st.markdown("### Comparación Vertical: Base vs. Iteración")
            
            st.markdown("**Diagrama Base**")
            st.write(arc_state["base_diagram"], unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("**Diagrama Iterado**")
            st.write(arc_state["iteration_diagram"], unsafe_allow_html=True)