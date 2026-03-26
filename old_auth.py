import os
import streamlit as st
import bcrypt
import logging
from datetime import datetime, timezone

# Importamos las funciones que ya configuramos en RDS (Ohio)
from ..database.sql_db import (
    get_user,
    get_student_user,
    get_admin_user,
    create_student_user,
    update_student_user,
    delete_student_user,
    record_login
    # Nota: Si implementas record_logout en sql_db, añádelo aquí
)

logger = logging.getLogger(__name__)

def authenticate_user(username, password):
    """Autentica un usuario en RDS y registra el inicio de sesión"""
    try:
        user_item = get_user(username)
        
        if not user_item:
            logger.warning(f"Usuario no encontrado en RDS: {username}")
            return False, None
            
        # Verificación de contraseña usando bcrypt (compatible con tus hashes de Azure)
        if verify_password(user_item['password'], password):
            logger.info(f"Usuario autenticado: {username}, Rol: {user_item['role']}")
            
            try:
                session_id = record_login(username)
                if session_id:
                    st.session_state.session_id = session_id
                    st.session_state.username = username
                    st.session_state.role = user_item['role']
                    st.session_state.login_time = datetime.now(timezone.utc)
                else:
                    logger.warning("Sesión autenticada pero no se pudo registrar en RDS")
            except Exception as e:
                logger.error(f"Error al registrar sesión: {str(e)}")
            
            return True, user_item['role']
            
        logger.warning(f"Contraseña incorrecta para: {username}")
        return False, None
        
    except Exception as e:
        logger.error(f"Error crítico en autenticación: {str(e)}")
        return False, None

def authenticate_student(username, password):
    success, role = authenticate_user(username, password)
    return (True, role) if success and role == 'Estudiante' else (False, None)

def authenticate_admin(username, password):
    success, role = authenticate_user(username, password)
    return (True, role) if success and role == 'Administrador' else (False, None)

def verify_password(stored_password, provided_password):
    """Verifica el hash de bcrypt"""
    try:
        return bcrypt.checkpw(
            provided_password.encode('utf-8'), 
            stored_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Error verificando hash: {e}")
        return False

def hash_password(password):
    """Genera un nuevo hash de bcrypt para nuevos registros"""
    return bcrypt.hashpw(
        password.encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')

def logout():
    """Limpia la sesión de Streamlit"""
    # Aquí podrías llamar a record_logout(st.session_state.username, st.session_state.session_id)
    # si decides trackear el tiempo de salida en RDS.
    st.session_state.clear()
    st.rerun()

# Mantener la interfaz de funciones para no romper ui.py
register_student = create_student_user
update_student_info = update_student_user
delete_student = delete_student_user
