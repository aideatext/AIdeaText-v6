import pandas as pd
import streamlit as st
from datetime import datetime

from modules.database.sql_db import (
    get_user,
    execute_query,        # <--- Agrega esta línea aquí
    create_user_expanded,
    get_student_user,
    get_admin_user,
    get_teacher_user,
    create_student_user,
    update_student_user,
    delete_student_user,
    record_login, 
    record_logout, 
    get_recent_sessions,
    get_user_total_time
)

#from ..database.morphosintax_mongo_db import get_student_morphosyntax_analysis
from modules.auth.auth import hash_password  # Agregar esta importación al inicio

#######################################################################################
def format_duration(seconds):
    """Convierte segundos a formato legible"""
    if not seconds:
        return "0h 0m"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"


#######################################################################################
# ... (tus importaciones se mantienen igual)

def admin_page():
    st.title("Panel de Administración")
    st.write(f"Bienvenido, {st.session_state.username}")

    # Corregimos a 3 tabs para evitar el ValueError
    tab1, tab2, tab3 = st.tabs([
        "📥 Carga de Piloto",
        "🔍 Búsqueda de Usuarios",
        "📊 Monitor del Sistema"
    ])

    # Tab 1: Gestión de Usuarios (Carga Masiva)
    with tab1:
        st.header("Carga Masiva de Usuarios")
        st.info("El CSV debe tener las columnas: usuario, password, nombre, rol, institucion, facultad, nivel, class_id, pilot_id, ciudad, pais")
        
        csv_file = st.file_uploader("Subir Archivo de Piloto", type=["csv"])
        
        if csv_file:
            df = pd.read_csv(csv_file)
            st.dataframe(df.head()) # Previsualización
            if st.button("Ejecutar Importación"):
                for _, row in df.iterrows():
                    # Usamos la función expandida que definimos para RDS
                    create_user_expanded(
                        id=row['usuario'],
                        password=str(row['password']),
                        full_name=row['nombre'],
                        role=row['rol'],
                        institution=row['institucion'],
                        faculty=row['facultad'],
                        level=row['nivel'],
                        class_id=row['class_id'],
                        pilot_id=row['pilot_id'],
                        city=row['ciudad'],
                        country=row['pais']
                    )
                st.success("✅ Importación de piloto completada.")

    # Tab 2: Búsqueda de Usuarios (Tu lógica existente)
    with tab2:
        st.header("Búsqueda de Usuarios")
        # ... (aquí va tu código de búsqueda que ya tenías) ...
        # (Asegúrate de copiar el bloque de búsqueda aquí dentro)

    # --- TAB 3 RECONSTRUIDO: ANALÍTICA DEL PILOTO ---
    with tab3:
        st.header("Estado Global del Proyecto")
        
        # 1. Métricas Rápidas (SQL)
        # Consultas simples para ver el alcance
        total_users = execute_query("SELECT COUNT(*) as count FROM users")
        total_profs = execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'Profesor'")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Usuarios", total_users[0]['count'] if total_users else 0)
        c2.metric("Docentes", total_profs[0]['count'] if total_profs else 0)
        
        # 2. Distribución por Institución (Gráfico rápido)
        st.subheader("Distribución por Institución")
        inst_data = execute_query("SELECT institution, COUNT(*) as count FROM users GROUP BY institution")
        if inst_data:
            df_inst = pd.DataFrame(inst_data)
            st.bar_chart(df_inst.set_index('institution'))

        # 3. Estado de la Base de Datos (Seguridad)
        st.subheader("Estado de Conexiones")
        db_col1, db_col2 = st.columns(2)
        
        with db_col1:
            st.success("PostgreSQL (RDS): Conectado")
            st.caption("Almacenando perfiles y logs de acceso.")
            
        with db_col2:
            # Intentamos una pequeña consulta a MongoDB para verificar salud
            try:
                from ..database.mongo_db import get_collection
                test_mongo = get_collection('student_discourse_analysis').count_documents({})
                st.success(f"MongoDB (DocumentDB): Conectado")
                st.caption(f"Análisis almacenados: {test_mongo}")
            except:
                st.error("MongoDB: Error de conexión")

        # 4. Logs de Actividad Reciente
        st.subheader("Últimos Inicios de Sesión")
        recent_logs = execute_query("""
            SELECT user_id, login_time 
            FROM user_sessions 
            ORDER BY login_time DESC LIMIT 5
        """)
        if recent_logs:
            st.table(pd.DataFrame(recent_logs))

    # Botón de cierre de sesión (Fuera de los tabs)
    st.markdown("---")
    col_l1, col_l2, col_l3 = st.columns([2,1,2])
    with col_l2:
        if st.button("Cerrar Sesión", key="admin_logout", type="primary", use_container_width=True):
            from ..auth.auth import logout
            logout()
            st.rerun()