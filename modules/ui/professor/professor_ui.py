# modules/ui/professor/professor_ui.p
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

    # --- 2. LÓGICA DE GRUPOS (SQL) ---
    user_prefix = info['iniciales']
    query = """
        SELECT DISTINCT class_id FROM users 
        WHERE (id LIKE %s OR class_id LIKE %s) 
        AND role = 'Estudiante' 
        AND class_id != %s
    """
    grupos_db = execute_query(query, (f"{user_prefix}%", f"{user_prefix}%", prof_user))
    
    # Nombre consistente para evitar el subrayado amarillo de "no vinculado"
    lista_grupos_ids = sorted(list(set([g['class_id'] for g in grupos_db if g['class_id']])))

    if not lista_grupos_ids:
        st.warning("No se encontraron grupos de tesistas bajo su cátedra.")
        return

    # --- 3. CARGA DE DATOS (MongoDB) ---
    all_raw = []
    for g_id in lista_grupos_ids:
        data = get_student_semantic_analysis(group_id=g_id)
        all_raw.extend(data)
    
    # Procesamos los datos una sola vez para todo el tablero
    df_global = process_semantic_data(all_raw)

    # --- 4. INTERFAZ POR PESTAÑAS (TABS) ---
    tab_global, tab_grupo, tab_alumno = st.tabs([
        "🌐 Cátedra (Global)", 
        "👥 Visión por Grupo", 
        "🔍 Seguimiento Individual"
    ])

    with tab_global:
        st.subheader("Estado General de la Cátedra")
        if not df_global.empty:
            # Agrupamos por el nombre amigable del grupo
            resumen = df_global.groupby('Grupo_Display')['M1'].mean().reset_index()
            fig_bar = px.bar(resumen, x='Grupo_Display', y='M1', 
                             title="Promedio de Coherencia (M1) por Grupo",
                             labels={'Grupo_Display': 'Grupo', 'M1': 'Nivel de Coherencia'},
                             color='M1', color_continuous_scale='Viridis')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos históricos suficientes para generar el promedio global.")

    with tab_grupo:
        st.subheader("Análisis del Grupo de Tesis")
        if not df_global.empty:
            # Selector basado en los nombres amigables (ej: Grupo G1 (2025-1))
            opciones_display = sorted(df_global['Grupo_Display'].unique())
            grupo_visual = st.selectbox("Seleccione el grupo a inspeccionar:", opciones_display)
            
            # Filtramos el dataframe global para obtener solo los datos del grupo seleccionado
            df_grupo = df_global[df_global['Grupo_Display'] == grupo_visual]
            
            if not df_grupo.empty:
                # La leyenda muestra t1, t2, etc.
                fig_evol = px.line(df_grupo, x='Fecha', y='M1', color='Estudiante_ID', 
                                   markers=True, title=f"Evolución de Coherencia: {grupo_visual}")
                st.plotly_chart(fig_evol, use_container_width=True)
            else:
                st.warning(f"El grupo {grupo_visual} no tiene registros de análisis.")
        else:
            st.info("Cargando datos de grupos...")

    with tab_alumno:
        st.subheader("Seguimiento Detallado por Tesista")
        # Verificamos que se haya filtrado un grupo en la pestaña anterior
        if 'df_grupo' in locals() and not df_grupo.empty:
            est_id_sel = st.selectbox("Seleccione Tesista:", df_grupo['Estudiante_ID'].unique())
            df_est = df_grupo[df_grupo['Estudiante_ID'] == est_id_sel].sort_values('Fecha')

            # Recuperamos el username completo para el reporte
            full_username = df_est['Username_Completo'].iloc[0]

            st.markdown(f"#### Reporte Evolutivo: {full_username}")
            try:
                doc_buffer = create_docx_report(full_username, df_est)
                st.download_button(
                    label=f"📥 Descargar DOCX: {est_id_sel}",
                    data=doc_buffer,
                    file_name=f"Reporte_{full_username}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Error al generar el documento: {e}")

            st.divider()

            # Visualización de sesiones individuales
            if len(df_est) > 0:
                idx = st.select_slider(
                    "Línea de tiempo de sesiones:",
                    options=range(len(df_est)),
                    format_func=lambda i: df_est.iloc[i]['Fecha'].strftime('%d/%m %H:%M')
                )
                
                sesion_actual = df_est.iloc[idx]
                col_texto, col_metricas = st.columns([2, 1])
                
                with col_texto:
                    st.markdown("**Texto analizado:**")
                    st.info(sesion_actual['Texto'])
                
                with col_metricas:
                    st.metric("Coherencia M1", f"{sesion_actual['M1']:.4f}")
                    st.metric("Robustez M2", f"{sesion_actual['M2']:.4f}")
        else:
            st.info("Seleccione primero un grupo en la pestaña 'Visión por Grupo'.")