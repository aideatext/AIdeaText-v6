import streamlit as st
import plotly.express as px
from datetime import datetime
import logging

# Importaciones modulares
from modules.database.sql_db import execute_query
from modules.database.semantic_mongo_db import get_student_semantic_analysis
from modules.metrics.metrics_processor import process_semantic_data
from modules.metrics.report_generator import create_docx_report
from modules.utils.helpers import decode_professor_id

logger = logging.getLogger(__name__)

def professor_page():
    # 1. Recuperar contexto del Profesor
    prof_user = st.session_state.get('username', 'MG-EDU-UNIFE-LIM')
    full_name = st.session_state.get('full_name', 'Docente')
    
    # Intentar decodificar info institucional
    try:
        info = decode_professor_id(prof_user)
    except:
        info = {'institucion': 'UNIFE', 'facultad': 'Educación', 'iniciales': 'MG'}

    # --- SIDEBAR (Panel Lateral) ---
    with st.sidebar:
        st.markdown(f"### 👩‍🏫 {full_name}")
        st.divider()
        st.markdown(f"**Institución:**\n{info['institucion']}")
        st.markdown(f"**Facultad:**\n{info['facultad']}")
        st.divider()
        st.caption(f"Cátedra: {info['iniciales']}")

    st.title("Panel de Gestión Académica")

    # --- LÓGICA DE GRUPOS ---
    # Buscamos grupos en SQL que empiecen con las iniciales del profesor
    user_prefix = info['iniciales']
    query = "SELECT DISTINCT class_id FROM users WHERE (id LIKE %s OR class_id LIKE %s) AND role = 'Estudiante'"
    grupos_db = execute_query(query, (f"{user_prefix}%", f"{user_prefix}%"))
    
    # Extraer lista de IDs de clase únicos
    lista_grupos = sorted(list(set([g['class_id'] for g in grupos_db if g['class_id']])))

    if not lista_grupos:
        st.warning("No se encontraron grupos de tesistas bajo su cátedra en la base de datos SQL.")
        # Opcional: mostrar un botón para refrescar o contactar soporte
        return

    # --- CARGA DE DATOS (Nivel Global) ---
    all_raw = []
    for g in lista_grupos:
        # Llamada a Mongo usando el procesador modular
        data = get_student_semantic_analysis(group_id=g)
        all_raw.extend(data)
    
    df_global = process_semantic_data(all_raw)

    # --- INTERFAZ POR PESTAÑAS (TABS) ---
    tab_global, tab_grupo, tab_alumno = st.tabs([
        "🌐 Cátedra (Global)", 
        "👥 Visión por Grupo", 
        "🔍 Seguimiento Individual"
    ])

    with tab_global:
        st.subheader("Estado General de los Grupos")
        if not df_global.empty:
            resumen = df_global.groupby('Grupo')['M1'].mean().reset_index()
            fig_bar = px.bar(resumen, x='Grupo', y='M1', 
                             title="Promedio de Coherencia (M1) por Grupo",
                             color='M1', color_continuous_scale='Viridis')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos históricos suficientes para generar el promedio global.")

    with tab_grupo:
        st.subheader("Análisis del Grupo de Tesis")
        grupo_sel = st.selectbox("Seleccione el grupo a inspeccionar:", lista_grupos)
        
        df_grupo = df_global[df_global['Grupo'] == grupo_sel] if not df_global.empty else None
        
        if df_grupo is not None and not df_grupo.empty:
            fig_evol = px.line(df_grupo, x='Fecha', y='M1', color='Estudiante', 
                               markers=True, title=f"Evolución de Coherencia: {grupo_sel}")
            st.plotly_chart(fig_evol, use_container_width=True)
        else:
            st.warning(f"El grupo {grupo_sel} no tiene registros de análisis semántico.")

    with tab_alumno:
        st.subheader("Detalle por Tesista")
        if df_grupo is not None and not df_grupo.empty:
            est_sel = st.selectbox("Seleccione Alumno:", df_grupo['Estudiante'].unique())
            df_est = df_grupo[df_grupo['Estudiante'] == est_sel].sort_values('Fecha')

            # Descarga de Reporte
            st.markdown("#### Reporte Evolutivo")
            try:
                # Usamos el generador modular de reportes
                doc_buffer = create_docx_report(est_sel, df_est)
                st.download_button(
                    label=f"📥 Descargar DOCX: {est_sel}",
                    data=doc_buffer,
                    file_name=f"Reporte_{est_sel}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Error generando reporte: {e}")

            st.divider()

            # Navegador de sesiones (Slider)
            if len(df_est) > 0:
                idx = st.select_slider(
                    "Historial de sesiones:",
                    options=range(len(df_est)),
                    format_func=lambda i: df_est.iloc[i]['Fecha'].strftime('%d/%m %H:%M')
                )
                
                sel = df_est.iloc[idx]
                col_t, col_m = st.columns([2, 1])
                with col_t:
                    st.markdown("**Discurso del alumno:**")
                    st.info(sel['Texto'])
                with col_m:
                    st.metric("Coherencia M1", f"{sel['M1']:.4f}")
                    st.metric("Robustez M2", f"{sel['M2']:.4f}")
        else:
            st.info("Seleccione un grupo con datos en la pestaña anterior.")