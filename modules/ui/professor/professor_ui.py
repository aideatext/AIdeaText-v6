import streamlit as st
from modules.database.sql_db import execute_query
from modules.database.semantic_mongo_db import get_student_semantic_analysis
from modules.metrics.metrics_processor import process_semantic_data
from modules.metrics.report_generator import create_docx_report
import plotly.express as px

def professor_page():
    st.title("Panel de Cátedra - UNIFE")
    
    # 1. Obtener Grupos desde SQL
    user_prefix = st.session_state.get('username')[:2] # Ejemplo: 'MG'
    grupos_db = execute_query("SELECT DISTINCT class_id FROM users WHERE id LIKE %s", (f"{user_prefix}%",))
    lista_grupos = [g['class_id'] for g in grupos_db] if grupos_db else []

    # NIVEL 1: ESTADO GLOBAL (Todos los grupos)
    st.subheader("🌐 Nivel 1: Resumen de Cátedra")
    all_data = []
    for g in lista_grupos:
        all_data.extend(get_student_semantic_analysis(group_id=g))
    
    df_global = process_semantic_data(all_data)
    if not df_global.empty:
        fig_global = px.bar(df_global.groupby('Grupo')['M1'].mean().reset_index(), 
                            x='Grupo', y='M1', title="Promedio de Coherencia por Grupo")
        st.plotly_chart(fig_global, use_container_width=True)

    # NIVEL 2: VISIÓN POR GRUPO
    st.divider()
    st.subheader("👥 Nivel 2: Visión General del Grupo")
    grupo_sel = st.selectbox("Seleccione Grupo:", lista_grupos)
    df_grupo = df_global[df_global['Grupo'] == grupo_sel]

    if not df_grupo.empty:
        fig_line = px.line(df_grupo, x='Fecha', y='M1', color='Estudiante', markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

        # NIVEL 3: DETALLE ALUMNO
        st.divider()
        st.subheader("🔍 Nivel 3: Seguimiento por Alumno")
        est_sel = st.selectbox("Seleccione Alumno:", df_grupo['Estudiante'].unique())
        df_est = df_grupo[df_grupo['Estudiante'] == est_sel]

        # Botón Reporte
        btn_doc = create_docx_report(est_sel, df_est)
        st.download_button("📥 Descargar Reporte (.docx)", btn_doc, f"Reporte_{est_sel}.docx")