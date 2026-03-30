import streamlit as st
import pandas as pd
from datetime import datetime
from ..database.sql_db import execute_query
# Importamos los módulos de MongoDB que preparamos antes
from ..database.discourse_mongo_db import get_collection as get_discourse_col

def professor_page():
    st.title("Panel del Instructor")
    
    # Extraemos el group_id del profesor desde la sesión
    prof_group = st.session_state.get('group_id')
    prof_inst = st.session_state.get('institution')
    
    st.sidebar.info(f"📍 {prof_inst} | Grupo: {prof_group}")

    if not prof_group or prof_group == 'GENERAL':
        st.error("Usted no tiene un grupo asignado. Contacte al administrador.")
        return

    # TABS solo para SU grupo
    tab1, tab2 = st.tabs(["📝 Supervisión de Borradores", "👥 Miembros del Grupo"])

    with tab1:
        st.subheader(f"Evolución de Escritura - Grupo {prof_group}")
        # Filtramos MongoDB estrictamente por el grupo del profesor
        col = get_discourse_col('student_discourse_analysis')
        # Buscamos análisis donde el group_id coincida
        analyses = list(col.find({"group_id": prof_group}).sort("timestamp", -1))
        
        if analyses:
            for ana in analyses:
                with st.expander(f"Análisis de {ana.get('username')} - {ana['timestamp'].strftime('%H:%M %d/%m')}"):
                    # Mostrar comparativa de textos y métricas...
                    st.json(ana.get('metrics', {}))
        else:
            st.info("Aún no hay actividad de borradores en su grupo.")

    with tab2:
        st.subheader("Lista de Estudiantes")
        # SQL: Solo traer estudiantes que tengan el mismo group_id que el profesor
        query = "SELECT full_name, email FROM users WHERE group_id = %s AND role = 'Estudiante'"
        students = execute_query(query, (prof_group,))
        if students:
            st.table(pd.DataFrame(students))