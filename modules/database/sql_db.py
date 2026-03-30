import os
import pg8000.native
import logging
import json
from .database_init import get_pg_connection, release_pg_connection

logger = logging.getLogger(__name__)

def execute_query(query, params=None, fetch=True):
    """Ejecuta una consulta en PostgreSQL usando pg8000.native"""
    conn = get_pg_connection()
    if not conn:
        return None
    try:
        # IMPORTANTE: pg8000.native usa parámetros posicionales en el SQL 
        # pero la función run los recibe como argumentos. 
        # Cambiamos los %s por marcadores que pg8000 entienda.
        
        # Ajustamos el query de %s a :1, :2, etc. para pg8000
        formatted_query = query
        if params:
            for i in range(len(params)):
                formatted_query = formatted_query.replace("%s", f":{i+1}", 1)
            
            # Pasamos los parámetros como un diccionario para la sintaxis :n
            param_dict = {f"{i+1}": v for i, v in enumerate(params)}
            result = conn.run(formatted_query, **param_dict)
        else:
            result = conn.run(formatted_query)
        
        if fetch and result:
            columns = [column['name'] for column in conn.columns]
            return [dict(zip(columns, row)) for row in result]
        return result
    except Exception as e:
        logger.error(f"Error ejecutando consulta SQL: {e}")
        return None
    finally:
        release_pg_connection(conn)

# --- BÚSQUEDA DE USUARIOS ---
def get_user(username):
    """Busca un usuario por ID y devuelve todos sus campos, incluyendo los de multi-tenancy."""
    # Al usar SELECT *, nos aseguramos de traer group_id, institution y academic_stage
    query = "SELECT * FROM users WHERE id = %s"
    result = execute_query(query, (username,))
    return result[0] if result else None

def get_admin_user(username):
    return get_user(username, role='Administrador')

def get_student_user(username):
    return get_user(username, role='Estudiante')

def get_teacher_user(username):
    return get_user(username, role='Profesor')

# --- CREACIÓN DE USUARIOS (Añadiendo group_id) ---
def create_user_expanded(username, password, role, class_id, institution, academic_stage, faculty, pilot_id, city, country, full_name=None):
    query = """
        INSERT INTO users (
            id, password, role, class_id, institution, academic_stage, 
            faculty, pilot_id, city, country, full_name, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    """
    params = (
        username, password, role, class_id, institution, 
        academic_stage, faculty, pilot_id, city, country, full_name
    )
    return execute_query(query, params, fetch=False)


##############################################

def create_student_user(username, password, group_id, institution, academic_stage, faculty, full_name=None, email=None):
    """
    Crea un estudiante con la jerarquía completa en RDS.
    """
    query = """
        INSERT INTO users (id, password, role, group_id, institution, academic_stage, faculty, full_name, email, created_at)
        VALUES (%s, %s, 'Estudiante', %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
    """
    # El orden de params debe coincidir exactamente con los %s del query
    params = (
        username, 
        password, 
        group_id, 
        institution, 
        academic_stage, 
        faculty, 
        full_name, 
        email
    )
    return execute_query(query, params, fetch=False)

###################################
def create_teacher_user(username, password, institution, faculty, full_name=None, email=None):
    """Crea un usuario con rol Profesor en RDS."""
    query = """
        INSERT INTO users (id, password, role, institution, faculty, academic_stage, group_id, full_name, email, created_at)
        VALUES (%s, %s, 'Profesor', %s, %s, 'N/A', 'ADMIN_FACULTY', %s, %s, CURRENT_TIMESTAMP)
    """
    params = (username, password, institution, faculty, full_name, email)
    return execute_query(query, params, fetch=False)

###############################################################

def create_admin_user(username, password, additional_info=None):
    return create_user(username, password, 'Administrador', additional_info)

# --- GESTIÓN DE SESIONES ---
def record_login(username):
    query = "INSERT INTO users_sessions (username, login_time, type) VALUES (%s, CURRENT_TIMESTAMP, 'login') RETURNING id"
    result = execute_query(query, (username,))
    return result[0]['id'] if result else None

def record_logout(username, session_id):
    query = "UPDATE users_sessions SET logout_time = CURRENT_TIMESTAMP WHERE id = %s AND username = %s"
    return execute_query(query, (session_id, username), fetch=False)

# --- MANTENIMIENTO ---
def update_student_user(username, new_info):
    if not new_info: return False
    set_clauses = [f"{k} = %s" for k in new_info.keys()]
    params = list(new_info.values()) + [username]
    query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s"
    return execute_query(query, params, fetch=False)

def delete_student_user(username):
    return execute_query("DELETE FROM users WHERE id = %s", (username,), fetch=False)

# --- SOLICITUDES Y FEEDBACK ---
def store_application_request(name, lastname, email, institution, current_role, desired_role, reason):
    query = "INSERT INTO application_requests (username, request_type, status, details, timestamp) VALUES (%s, %s, 'pending', %s, CURRENT_TIMESTAMP)"
    details = json.dumps({"name": name, "lastname": lastname, "institution": institution, "current_role": current_role, "reason": reason})
    return execute_query(query, (email, desired_role, details), fetch=False)

def store_student_feedback(username, name, email, feedback):
    query = "INSERT INTO student_feedback (username, feedback_text, category, timestamp) VALUES (%s, %s, 'Estudiante', CURRENT_TIMESTAMP)"
    full_feedback = f"De: {name} ({email}) - Msg: {feedback}"
    return execute_query(query, (username, full_feedback), fetch=False)

# --- REPORTES ---
def get_recent_sessions(limit=10):
    query = "SELECT username, login_time as \"loginTime\", logout_time as \"logoutTime\" FROM users_sessions ORDER BY login_time DESC LIMIT %s"
    return execute_query(query, (limit,))

def get_user_total_time(username):
    query = "SELECT SUM(EXTRACT(EPOCH FROM (logout_time - login_time))) / 60 as total FROM users_sessions WHERE username = %s"
    result = execute_query(query, (username,))
    return result[0]['total'] if result and result[0]['total'] else 0
