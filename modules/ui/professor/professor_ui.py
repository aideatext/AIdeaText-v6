import streamlit as st
import plotly.express as px
from datetime import datetime
from ...database.sql_db import execute_query
from ...database.semantic_mongo_db import get_student_semantic_analysis
from ...metrics.metrics_processor import process_semantic_data
from ...metrics.report_generator import create_docx_report
from ...utils.helpers import decode_professor_id

def professor_page():
    # 1. Configuración del Panel Lateral (Sidebar)
    prof_user = st.session_state.get('username', 'MG-EDU-UNIFE-LIM')
    full_name = st.session_state.get('full_name', 'Docente')
    info = decode_professor_id(prof_user)
    
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/Logo_UNIFE.png/220px-Logo_UNIFE.png", width=100) # Opcional: Logo UNIFE
        st.markdown(f"### 👩‍🏫 {full_name}")
        st.divider()
        st.info(f"**Institución:**\n{info['institucion']}\n\n**Facultad:**\n{info['facultad']}")
        st.caption(f"ID Sesión: {prof_user}")

    st.title("Panel de Gestión Académica - AIdeaText")
    
    # 2. Obtener Grupos Reales (Limpieza de Nombres)
    # Filtramos para obtener los IDs de clase (ej. MG-G1-2025) y no el ID del profesor
    user_prefix = prof_user[:2]
    query = "SELECT DISTINCT class_id FROM users WHERE id LIKE %s AND role = 'Estudiante'"
    grupos_db = execute_query(query, (f"{user_prefix}%",))
    
    # IMPORTANTE: Filtramos para que no aparezca el ID del profesor en la lista de grupos
    lista_grupos = [g['class_id'] for g in grupos_db if g['class_id'] != prof_user]
    
    if not lista_grupos:
        st.warning("No se encontraron grupos de tesistas registrados bajo su cátedra.")
        return

    # 3. Carga y Procesamiento de Datos
    all_raw = []
    for g in lista_grupos:
        all_raw.extend(get_student_semantic_analysis(group_id=g))
    
    df_global = process_semantic_data(all_raw)

    # 4. Organización por Pestañas (Tabs)
    tab1, tab2, tab3 = st.tabs(["🌐 Cátedra (Global)", "👥 Grupos", "🔍 Tesistas"])

    with tab1:
        st.subheader("Estado Global de la Cátedra")
        if not df_global.empty:
            resumen = df_global.groupby('Grupo')['M1'].mean().reset_index()
            fig_bar = px.bar(resumen, x='Grupo', y='M1', title="Promedio de Coherencia por Grupo",
                             color='M1', color_continuous_scale='GnBu')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Esperando datos de los grupos...")

    with tab2:
        st.subheader("Visión General del Grupo")
        grupo_sel = st.selectbox("Seleccione el grupo a supervisar:", lista_grupos, key="sel_grupo")
        
        df_grupo = df_global[df_global['Grupo'] == grupo_sel]
        if not df_grupo.empty:
            fig_evol = px.line(df_grupo, x='Fecha', y='M1', color='Estudiante', markers=True,
                               title=f"Evolución Semántica - {grupo_sel}")
            st.plotly_chart(fig_evol, use_container_width=True)
        else:
            st.warning("Este grupo aún no tiene registros de análisis.")

    with tab3:
        st.subheader("Seguimiento Detallado por Tesista")
        # Solo mostramos alumnos del grupo seleccionado en la pestaña anterior
        if not df_grupo.empty:
            est_sel = st.selectbox("Seleccione Tesista:", df_grupo['Estudiante'].unique())
            df_est = df_grupo[df_grupo['Estudiante'] == est_sel].sort_values('Fecha')

            # Bloque de Reporte
            st.markdown("#### 📄 Documentación")
            try:
                # Generamos el buffer del reporte
                doc_buffer = create_docx_report(est_sel, df_est)
                st.download_button(
                    label=f"📥 Descargar Reporte Evolutivo: {est_sel}",
                    data=doc_buffer,
                    file_name=f"Reporte_Progreso_{est_sel}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Error al preparar el reporte: {e}")

            st.divider()
            
            # Navegación por sesiones
            idx = st.select_slider("Seleccione sesión para revisar texto:", options=range(len(df_est)),
                                   format_func=lambda i: df_est.iloc[i]['Fecha'].strftime('%d/%m %H:%M'))
            
            sesion = df_est.iloc[idx]
            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown("**Texto del Estudiante:**")
                st.caption(f"Fecha: {sesion['Fecha'].strftime('%d/%m/%Y %H:%M')}")
                st.write(sesion['Texto'])
            with c2:
                st.metric("Coherencia M1", f"{sesion['M1']:.4f}")
                st.metric("Robustez M2", f"{sesion['M2']:.4f}")
        else:
            st.info("Seleccione un grupo con datos en la pestaña anterior.")