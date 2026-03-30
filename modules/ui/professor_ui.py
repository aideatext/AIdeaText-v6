# modules/ui/professor_ui.py
import streamlit as st
import pandas as pd
from datetime import datetime
import logging

# Importaciones de base de datos
from ..database.sql_db import execute_query
from ..database.discourse_mongo_db import get_student_discourse_analysis

# Importación de la utilidad de decodificación
from ..utils.helpers import decode_professor_id

logger = logging.getLogger(__name__)

def professor_page():
    # 1. Obtener información del docente desde la sesión
    # Usamos el username (ID compuesto) para extraer metadatos
    prof_id = st.session_state.get('username', 'INV-GEN-GEN-GEN')
    full_name = st.session_state.get('full_name', 'Docente')
    
    # Decodificamos el ID (p.ej. MG-EDU-UNIFE-LIM)
    info = decode_professor_id(prof_id)
    
    # 2. Configuración de la Interfaz (Sidebar y Encabezado)
    st.sidebar.markdown(f"### 👩‍🏫 {full_name}")
    st.sidebar.divider()
    st.sidebar.info(f"**Institución:** {info['institucion']}\n\n**Facultad:** {info['facultad']}\n\n**Ciudad:** {info['ciudad']}")

    st.title(f"Panel del Instructor - {info['facultad']}")
    st.subheader(f"{info['institucion']}")

    # 3. Selector de Grupos Dinámico
    # Buscamos en SQL todos los class_id de estudiantes que empiecen con las iniciales de la profe (p.ej. 'MG-%')
    filtro_prefix = f"{info['iniciales']}-%"
    query_grupos = "SELECT DISTINCT class_id FROM users WHERE id LIKE %s AND role = 'Estudiante'"
    grupos_db = execute_query(query_grupos, (filtro_prefix,))
    
    lista_grupos = [g['class_id'] for g in grupos_db] if grupos_db else []

    if not lista_grupos:
        st.warning(f"No se encontraron grupos de estudiantes asociados al código {info['iniciales']}.")
        return

    # Menú desplegable para que la maestra elija qué grupo supervisar (G1, G2, etc.)
    grupo_seleccionado = st.selectbox("Seleccione el grupo a visualizar:", lista_grupos)

    # 4. TABS de Trabajo
    tab1, tab2 = st.tabs(["📝 Supervisión de Actividad", "👥 Listado de Alumnos"])

    with tab1:
        st.write(f"### Análisis de Discurso - {grupo_seleccionado}")
        
        # Recuperamos análisis de MongoDB filtrando por el grupo seleccionado
        # La función get_student_discourse_analysis ya maneja la conexión y el filtrado
        analyses = get_student_discourse_analysis(group_id=grupo_seleccionado, limit=20)
        
        if analyses:
            for ana in analyses:
                timestamp_str = ana['timestamp'].strftime('%d/%m/%Y %H:%M')
                with st.expander(f"📌 {ana.get('username')} | {timestamp_str}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption("Borrador 1")
                        st.text_area("Texto inicial", ana.get('text1', ''), height=150, key=f"t1_{ana['_id']}", disabled=True)
                    with col2:
                        st.caption("Borrador 2")
                        st.text_area("Texto final", ana.get('text2', ''), height=150, key=f"t2_{ana['_id']}", disabled=True)
                    
                    st.divider()
                    st.write("**Métricas de Evolución:**")
                    st.json(ana.get('metrics', {}))
        else:
            st.info(f"No se han registrado actividades recientes para el grupo {grupo_seleccionado}.")

    with tab2:
        st.write(f"### Estudiantes Registrados en {grupo_seleccionado}")
        
        # Consulta SQL para traer la lista de alumnos de ese grupo específico
        query_alumnos = "SELECT id as Usuario, full_name as Nombre, email as Correo FROM users WHERE class_id = %s AND role = 'Estudiante'"
        alumnos = execute_query(query_alumnos, (grupo_seleccionado,))
        
        if alumnos:
            df_alumnos = pd.DataFrame(alumnos)
            st.table(df_alumnos)
            st.download_button("Descargar Lista (CSV)", df_alumnos.to_csv(index=False), "lista_alumnos.csv", "text/csv")
        else:
            st.info("No hay alumnos inscritos en este grupo.")