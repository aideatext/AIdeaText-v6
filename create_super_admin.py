import os
import bcrypt
from modules.database.database_init import get_pg_connection, release_pg_connection
from dotenv import load_dotenv

load_dotenv()

def create_initial_admin():
    conn = get_pg_connection()
    if not conn:
        print("Error: No se pudo conectar a la base de datos.")
        return

    try:
        username = "admin_root"
        password_plana = "AdminPassword2026!"
        role = "Administrador"

        # Generar el hash compatible con tu sistema
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_plana.encode('utf-8'), salt).decode('utf-8')

        # SQL para insertar o actualizar si ya existe
        query = """
        INSERT INTO users (id, password, role) 
        VALUES (:id, :pw, :role) 
        ON CONFLICT (id) 
        DO UPDATE SET password = EXCLUDED.password, role = EXCLUDED.role
        """
        
        conn.run(query, id=username, pw=hashed_password, role=role)
        
        print("\n" + "="*30)
        print("¡SUPER ADMIN CREADO CON HASH!")
        print(f"Usuario: {username}")
        print(f"Contraseña: {password_plana}")
        print(f"Hash guardado: {hashed_password[:20]}...")
        print("="*30)
        print("\nYa puedes intentar loguearte en la web.")

    except Exception as e:
        print(f"Error al crear el usuario: {e}")
    finally:
        release_pg_connection(conn)

if __name__ == "__main__":
    create_initial_admin()
