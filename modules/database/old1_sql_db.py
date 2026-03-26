from .database_init import get_pg_connection, release_pg_connection
from datetime import datetime, timezone
import logging
import uuid
import json

logger = logging.getLogger(__name__)

def execute_query(query, params=None, fetch=True):
    conn = get_pg_connection()
    if not conn:
        return None
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        if fetch:
            result = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row)) for row in result]
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error SQL: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        release_pg_connection(conn)

def get_user(username, role=None):
    query = "SELECT * FROM users WHERE id = %s"
    params = [username]
    if role:
        query += " AND role = %s"
        params.append(role)
    result = execute_query(query, params)
    return result[0] if result else None

def get_admin_user(username):
    return get_user(username, role='Administrador')

def get_student_user(username):
    return get_user(username, role='Estudiante')

def get_teacher_user(username):
    return get_user(username, role='Profesor')

def create_user(username, password, role, additional_info=None):
    query = """
        INSERT INTO users (id, password, role, timestamp, additional_info)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
    """
    params = (username, password, role, datetime.now(timezone.utc), json.dumps(additional_info or {}))
    return execute_query(query, params, fetch=False)

def create_student_user(username, password, additional_info=None):
    return create_user(username, password, 'Estudiante', additional_info)

def create_admin_user(username, password, additional_info=None):
    return create_user(username, password, 'Administrador', additional_info)

def record_login(username):
    session_id = str(uuid.uuid4())
    query = "INSERT INTO users_sessions (id, username, login_time, type) VALUES (%s, %s, %s, 'session')"
    params = (session_id, username, datetime.now(timezone.utc))
    if execute_query(query, params, fetch=False):
        return session_id
    return None

def store_student_feedback(username, name, email, feedback):
    query = """
        INSERT INTO user_feedback (id, username, name, email, feedback, role, timestamp)
        VALUES (%s, %s, %s, %s, %s, 'Estudiante', %s)
    """
    params = (str(uuid.uuid4()), username, name, email, feedback, datetime.now(timezone.utc))
    return execute_query(query, params, fetch=False)

def store_application_request(username, request_type, status, details=None):
    query = "INSERT INTO application_requests (id, username, request_type, status, details) VALUES (%s, %s, %s, %s, %s)"
    params = (str(uuid.uuid4()), username, request_type, status, json.dumps(details or {}))
    return execute_query(query, params, fetch=False)

# --- FUNCIONES DE ACTUALIZACIÓN (UPDATE) ---

def update_user(username, updates):
    """
    Actualiza campos específicos de un usuario.
    'updates' debe ser un diccionario con los campos a cambiar.
    """
    if not updates:
        return False
        
    # Construimos la consulta dinámicamente
    set_clauses = []
    params = []
    
    for key, value in updates.items():
        if key == 'additional_info':
            set_clauses.append(f"{key} = %s")
            params.append(json.dumps(value))
        else:
            set_clauses.append(f"{key} = %s")
            params.append(value)
            
    params.append(username)
    query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s"
    
    return execute_query(query, params, fetch=False)

def update_student_user(username, updates):
    """Alias requerido por modules.auth"""
    return update_user(username, updates)

# --- FUNCIONES DE ELIMINACIÓN (DELETE) ---

def delete_user(username):
    """Elimina un usuario de la base de datos RDS"""
    query = "DELETE FROM users WHERE id = %s"
    params = (username,)
    return execute_query(query, params, fetch=False)

def delete_student_user(username):
    """Alias requerido por modules.auth / ui"""
    return delete_user(username)

def delete_admin_user(username):
    """Alias para eliminar administradores"""
    return delete_user(username)

# --- FUNCIONES DE SESIÓN ADICIONALES ---

def record_logout(username, session_id):
    """Registra la hora de salida del usuario en RDS"""
    query = "UPDATE users_sessions SET logout_time = %s WHERE id = %s AND username = %s"
    params = (datetime.now(timezone.utc), session_id, username)
    return execute_query(query, params, fetch=False)
