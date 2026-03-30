import logging
import streamlit as st
import bcrypt
from modules.database.sql_db import (
    get_user, 
    create_student_user, 
    create_teacher_user, 
    create_admin_user,
    update_student_user,
    delete_student_user,
    record_login,
    record_logout
)

logger = logging.getLogger(__name__)

#################################
def hash_password(password):
    """Genera un hash de bcrypt para la contraseña"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

##############################################
def verify_password(stored_password, provided_password):
    """Verifica la contraseña contra el hash almacenado"""
    try:
        # Si la contraseña en DB es un hash de bcrypt
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verificando password: {e}")
        # En caso de que se haya guardado como texto plano por error durante la migración
        return stored_password == provided_password

##################################################
def authenticate_user(username, password):
    try:
        user = get_user(username)
        if not user:
            return None

        # Obtenemos los datos del diccionario (resultado de execute_query en sql_db)
        db_password = user.get('password')
        
        if verify_password(db_password, password):
            # Sincronizamos TODA la jerarquía multitenant
            st.session_state.username = user.get('id')
            st.session_state.role = user.get('role')
            st.session_state.institution = user.get('institution')
            st.session_state.faculty = user.get('faculty')
            st.session_state.academic_stage = user.get('academic_stage')
            
            # Mapeo de Grupos: Usamos class_id (SQL) pero mantenemos group_id por compatibilidad
            val_group = user.get('class_id')
            st.session_state.class_id = val_group
            st.session_state.group_id = val_group  # <--- Esto arregla la visualización del profesor
            
            st.session_state.pilot_id = user.get('pilot_id')
            st.session_state.city = user.get('city')
            st.session_state.country = user.get('country')
            
            return user
        
        return None
    except Exception as e:
        logger.error(f"Error en authenticate_user: {e}")
        return None

#########################################################
def authenticate_student(username, password):
    user = authenticate_user(username, password)
    if user and user.get('role') == 'Estudiante':
        return user
    return None

def authenticate_admin(username, password):
    user = authenticate_user(username, password)
    if user and user.get('role') == 'Administrador':
        return user
    return None

def register_student(username, password, email=None, full_name=None):
    hashed_pw = hash_password(password)
    return create_student_user(username, hashed_pw, email, full_name)

def update_student_info(username, updated_data):
    return update_student_user(username, updated_data)

def delete_student(username):
    return delete_student_user(username)

def logout():
    st.session_state.clear()
    st.rerun()
