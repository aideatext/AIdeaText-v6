##########modules/auth/auth.py

import os
import streamlit as st
from azure.cosmos import CosmosClient, exceptions
from azure.cosmos.exceptions import CosmosHttpResponseError
import bcrypt
import base64
from ..database.sql_db import (
    get_user,
    get_student_user,
    get_admin_user,
    create_student_user,
    update_student_user,
    delete_student_user,
    record_login,
    record_logout
)

import logging

from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def clean_and_validate_key(key):
    """Limpia y valida la clave de CosmosDB"""
    key = key.strip()
    while len(key) % 4 != 0:
        key += '='
    try:
        base64.b64decode(key)
        return key
    except:
        raise ValueError("La clave proporcionada no es válida")

# Verificar las variables de entorno
endpoint = os.getenv("COSMOS_ENDPOINT")
key = os.getenv("COSMOS_KEY")

if not endpoint or not key:
    raise ValueError("Las variables de entorno COSMOS_ENDPOINT y COSMOS_KEY deben estar configuradas")

key = clean_and_validate_key(key)


def authenticate_user(username, password):
    """Autentica un usuario y registra el inicio de sesión"""
    try:
        user_item = get_user(username)
        
        if not user_item:
            logger.warning(f"Usuario no encontrado: {username}")
            return False, None
            
        if verify_password(user_item['password'], password):
            logger.info(f"Usuario autenticado: {username}, Rol: {user_item['role']}")
            
            try:
                session_id = record_login(username)
                if session_id:
                    st.session_state.session_id = session_id
                    st.session_state.username = username
                    st.session_state.login_time = datetime.now(timezone.utc)
                    logger.info(f"Sesión iniciada: {session_id}")
                else:
                    logger.warning("No se pudo registrar la sesión")
            except Exception as e:
                logger.error(f"Error al registrar inicio de sesión: {str(e)}")
            
            return True, user_item['role']
            
        logger.warning(f"Contraseña incorrecta para usuario: {username}")
        return False, None
        
    except Exception as e:
        logger.error(f"Error durante la autenticación del usuario: {str(e)}")
        return False, None

def authenticate_student(username, password):
    """Autentica un estudiante"""
    success, role = authenticate_user(username, password)
    if success and role == 'Estudiante':
        return True, role
    return False, None

def authenticate_admin(username, password):
    """Autentica un administrador"""
    success, role = authenticate_user(username, password)
    if success and role == 'Administrador':
        return True, role
    return False, None

def register_student(username, password, additional_info=None):
    """Registra un nuevo estudiante"""
    try:
        if get_student_user(username):
            logger.warning(f"Estudiante ya existe: {username}")
            return False

        hashed_password = hash_password(password)
        
        # Asegurarse que additional_info tenga el rol correcto
        if not additional_info:
            additional_info = {}
        additional_info['role'] = 'Estudiante'
        
        success = create_student_user(username, hashed_password, additional_info)
        if success:
            logger.info(f"Nuevo estudiante registrado: {username}")
            return True
            
        logger.error(f"Error al crear estudiante: {username}")
        return False
        
    except Exception as e:
        logger.error(f"Error al registrar estudiante: {str(e)}")
        return False

def update_student_info(username, new_info):
    """Actualiza la información de un estudiante"""
    try:
        if 'password' in new_info:
            new_info['password'] = hash_password(new_info['password'])
            
        success = update_student_user(username, new_info)
        if success:
            logger.info(f"Información actualizada: {username}")
            return True
            
        logger.error(f"Error al actualizar: {username}")
        return False
        
    except Exception as e:
        logger.error(f"Error en actualización: {str(e)}")
        return False

def delete_student(username):
    """Elimina un estudiante"""
    try:
        success = delete_student_user(username)
        if success:
            logger.info(f"Estudiante eliminado: {username}")
            return True
            
        logger.error(f"Error al eliminar: {username}")
        return False
        
    except Exception as e:
        logger.error(f"Error en eliminación: {str(e)}")
        return False

def logout():
    """Cierra la sesión del usuario"""
    try:
        if 'session_id' in st.session_state and 'username' in st.session_state:
            success = record_logout(
                st.session_state.username, 
                st.session_state.session_id
            )
            if success:
                logger.info(f"Sesión cerrada: {st.session_state.username}")
            else:
                logger.warning(f"Error al registrar cierre de sesión: {st.session_state.username}")
        
    except Exception as e:
        logger.error(f"Error en logout: {str(e)}")
    finally:
        st.session_state.clear()

def hash_password(password):
    """Hashea una contraseña"""
    return bcrypt.hashpw(
        password.encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')

def verify_password(stored_password, provided_password):
    """Verifica una contraseña"""
    return bcrypt.checkpw(
        provided_password.encode('utf-8'), 
        stored_password.encode('utf-8')
    )

__all__ = [
    'authenticate_user',
    'authenticate_admin',
    'authenticate_student',
    'register_student',
    'update_student_info',
    'delete_student',
    'logout',
    'hash_password',
    'verify_password'
]