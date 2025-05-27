### auth.py
import os
from azure.cosmos import CosmosClient, exceptions
import bcrypt
import base64

################################################################################################################
def clean_and_validate_key(key):
    key = key.strip()
    while len(key) % 4 != 0:
        key += '='
    try:
        base64.b64decode(key)
        return key
    except:
        raise ValueError("La clave proporcionada no es válida")

# Azure Cosmos DB configuration
endpoint = os.environ.get("COSMOS_ENDPOINT")
key = os.environ.get("COSMOS_KEY")

if not endpoint or not key:
    raise ValueError("Las variables de entorno COSMOS_ENDPOINT y COSMOS_KEY deben estar configuradas")

key = clean_and_validate_key(key)

try:
    client = CosmosClient(endpoint, key)
    database = client.get_database_client("user_database")
    container = database.get_container_client("users")
    # Prueba de conexión
    database_list = list(client.list_databases())
    print(f"Conexión exitosa. Bases de datos encontradas: {len(database_list)}")
except Exception as e:
    print(f"Error al conectar con Cosmos DB: {str(e)}")
    raise

#############################################################################################################3
def hash_password(password):
    """Hash a password for storing."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

################################################################################################################
def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))
    
################################################################################################################
def register_user(username, password, additional_info=None):
    try:
        query = f"SELECT * FROM c WHERE c.id = '{username}'"
        existing_user = list(container.query_items(query=query, enable_cross_partition_query=True))
        
        if existing_user:
            return False  # User already exists
        
        new_user = {
            'id': username,
            'password': hash_password(password),
            'role': 'Estudiante',
            'additional_info': additional_info or {}
        }
        
        new_user['partitionKey'] = username
        
        container.create_item(body=new_user)
        return True
    except exceptions.CosmosHttpResponseError as e:
        print(f"Error al registrar usuario: {str(e)}")
        return False

        
################################################################################################################
def authenticate_user(username, password):
    """Authenticate a user."""
    try:
        query = f"SELECT * FROM c WHERE c.id = '{username}'"
        results = list(container.query_items(query=query, partition_key=username))
        
        if results:
            stored_user = results[0]
            if verify_password(stored_user['password'], password):
                return True
    except exceptions.CosmosHttpResponseError:
        pass
    
    return False


################################################################################################################
def get_user_role(username):
    """Get the role of a user."""
    try:
        query = f"SELECT c.role FROM c WHERE c.id = '{username}'"
        results = list(container.query_items(query=query, partition_key=username))
        
        if results:
            return results[0]['role']
    except exceptions.CosmosHttpResponseError:
        pass
    
    return None

################################################################################################################
def update_user_info(username, new_info):
    """Update user information."""
    try:
        query = f"SELECT * FROM c WHERE c.id = '{username}'"
        results = list(container.query_items(query=query, partition_key=username))
        
        if results:
            user = results[0]
            user['additional_info'].update(new_info)
            container.upsert_item(user, partition_key=username)
            return True
    except exceptions.CosmosHttpResponseError:
        pass
    
    return False

################################################################################################################
def delete_user(username):
    """Delete a user."""
    try:
        query = f"SELECT * FROM c WHERE c.id = '{username}'"
        results = list(container.query_items(query=query, partition_key=username))
        
        if results:
            user = results[0]
            container.delete_item(item=user['id'], partition_key=username)
            return True
    except exceptions.CosmosHttpResponseError:
        pass
    
    return False