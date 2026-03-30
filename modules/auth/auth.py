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

        # Ya que tu sql_db.py devuelve diccionarios:
        db_username = user.get('id')
        db_password = user.get('password')
        db_role = user.get('role')
        db_group_id = user.get('group_id', 'GENERAL') # Valor por defecto

        if verify_password(db_password, password):
            # Guardamos el group_id en la sesión de Streamlit inmediatamente
            st.session_state.group_id = db_group_id
            st.session_state.username = db_username
            st.session_state.role = db_role
            
            return {'id': db_username, 'username': db_username, 'role': db_role, 'group_id': db_group_id}
        
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
