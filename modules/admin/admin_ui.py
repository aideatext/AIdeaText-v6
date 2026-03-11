import streamlit as st
from datetime import datetime
from ..database.sql_db import (
    get_user,
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
from ..auth.auth import hash_password  # Agregar esta importación al inicio

#######################################################################################
def format_duration(seconds):
    """Convierte segundos a formato legible"""
    if not seconds:
        return "0h 0m"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours}h {minutes}m"

def admin_page():
    st.title("Panel de Administración")
    st.write(f"Bienvenido, {st.session_state.username}")

    # Crear tres tabs para las diferentes secciones
    tab1, tab2, tab3 = st.tabs([
        "Gestión de Usuarios",
        "Búsqueda de Usuarios",
        "Actividad de la Plataforma"
    ])

    
########################################################
    # Tab 1: Gestión de Usuarios
    with tab1:
        st.header("Crear Nuevo Usuario Estudiante")
        
        # Crear dos columnas para el formulario
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input(
                "Correo electrónico del nuevo usuario", 
                key="admin_new_username"
            )
        
        with col2:
            new_password = st.text_input(
                "Contraseña", 
                type="password", 
                key="admin_new_password"
            )
        
        if st.button("Crear Usuario", key="admin_create_user", type="primary"):
            if new_username and new_password:  # Verificamos que ambos campos tengan valor
                try:
                    # Hashear la contraseña antes de crear el usuario
                    hashed_password = hash_password(new_password)
                    if create_student_user(new_username, hashed_password, {'partitionKey': new_username}):
                        st.success(f"Usuario estudiante {new_username} creado exitosamente")
                    else:
                        st.error("Error al crear el usuario estudiante")
                except Exception as e:
                    st.error(f"Error al crear usuario: {str(e)}")
            else:
                st.warning("Por favor complete todos los campos")

#######################################################################                
    # Tab 2: Búsqueda de Usuarios
    with tab2:
        st.header("Búsqueda de Usuarios")
        
        search_col1, search_col2 = st.columns([2,1])
        
        with search_col1:
            student_username = st.text_input(
                "Nombre de usuario del estudiante", 
                key="admin_view_student"
            )
        
        with search_col2:
            search_button = st.button(
                "Buscar", 
                key="admin_view_student_data",
                type="primary"
            )

        if search_button:
            student = get_student_user(student_username)
            if student:
                # Crear tabs para diferentes tipos de información
                info_tab1, info_tab2, info_tab3 = st.tabs([
                    "Información Básica",
                    "Análisis Realizados",
                    "Tiempo en Plataforma"
                ])
                
                with info_tab1:
                    st.subheader("Información del Usuario")
                    st.json(student)

                with info_tab2:
                    st.subheader("Análisis Realizados")
                    student_data = get_student_morphosyntax_analysis(student_username)
                    if student_data:
                        st.json(student_data)
                    else:
                        st.info("No hay datos de análisis para este estudiante.")

                with info_tab3:
                    st.subheader("Tiempo en Plataforma")
                    total_time = get_user_total_time(student_username)
                    if total_time:
                        st.metric(
                            "Tiempo Total", 
                            format_duration(total_time)
                        )
                    else:
                        st.info("No hay registros de tiempo para este usuario")
            else:
                st.error("Estudiante no encontrado")

#######################################################################      
    # Tab 3: Actividad de la Plataforma
        with tab3:
            st.header("Actividad Reciente")
            
            # Agregar botón de actualización
            if st.button("Actualizar datos", key="refresh_sessions", type="primary"):
                st.rerun()
            
            # Mostrar spinner mientras carga
            with st.spinner("Cargando datos de sesiones..."):
                # Obtener sesiones recientes
                recent_sessions = get_recent_sessions(20)
            
                if recent_sessions:
                    # Crear dataframe para mostrar los datos
                    sessions_data = []
                    for session in recent_sessions:
                        try:
                            # 1. Manejar login_time (ahora es un objeto datetime)
                            login_val = session.get('loginTime')
                            if isinstance(login_val, datetime):
                                login_time = login_val.strftime("%Y-%m-%d %H:%M:%S")
                            else:
                                login_time = str(login_val) if login_val else "N/A"
                            
                            # 2. Manejar logout_time
                            logout_val = session.get('logoutTime')
                            if isinstance(logout_val, datetime):
                                logout_time = logout_val.strftime("%Y-%m-%d %H:%M:%S")
                            elif logout_val == "Activo" or not logout_val:
                                logout_time = "Activo"
                            else:
                                logout_time = str(logout_val)

                            # Agregar datos a la lista (dentro del try)
                            sessions_data.append({
                                "Usuario": session.get('username', 'Desconocido'),
                                "Inicio de Sesión": login_time,
                                "Fin de Sesión": logout_time,
                                "Duración": format_duration(session.get('sessionDuration', 0))
                            })
                        except Exception as e:
                            st.error(f"Error procesando sesión: {str(e)}")
                            continue
                    
                    # Mostrar información de depuración si hay problemas
                    with st.expander("Información de depuración", expanded=False):
                        st.write("Datos crudos recuperados:")
                        st.json(recent_sessions)
                        st.write("Datos procesados para mostrar:")
                        st.json(sessions_data)
                    
                    # Mostrar tabla con estilos
                    st.dataframe(
                        sessions_data,
                        hide_index=True,
                        column_config={
                            "Usuario": st.column_config.TextColumn("Usuario", width="medium"),
                            "Inicio de Sesión": st.column_config.TextColumn("Inicio de Sesión", width="medium"),
                            "Fin de Sesión": st.column_config.TextColumn("Fin de Sesión", width="medium"),
                            "Duración": st.column_config.TextColumn("Duración", width="small")
                        }
                    )
                    
                    # Añadir métricas resumen
                    total_sessions = len(sessions_data)
                    total_users = len(set(s['Usuario'] for s in sessions_data))
                    
                    metric_col1, metric_col2 = st.columns(2)
                    with metric_col1:
                        st.metric("Total de Sesiones", total_sessions)
                    with metric_col2:
                        st.metric("Usuarios Únicos", total_users)
                else:
                    st.info("No hay registros de sesiones recientes.")
                    
                    if st.button("Mostrar diagnóstico"):
                        st.write("Verificando la función get_recent_sessions:")
                        # Asegúrate de que get_container esté definido o importado
                        container = get_container("users_sessions")
                        if container:
                            st.success("✅ Conectado al contenedor users_sessions")
                        else:
                            st.error("❌ No se pudo conectar al contenedor")

#######################################################################      
    # Agregar una línea divisoria antes del botón
    st.markdown("---")

#######################################################################      
    # Centrar el botón de cierre de sesión
    col1, col2, col3 = st.columns([2,1,2])
    with col2:
        if st.button("Cerrar Sesión", key="admin_logout", type="primary", use_container_width=True):
            from ..auth.auth import logout
            logout()
            st.rerun()