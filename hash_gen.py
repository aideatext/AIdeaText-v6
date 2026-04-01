import bcrypt
password = "TuPasswordSecreto123" # <--- Pon aquí la que quieras usar
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"Tu hash es: {hashed}")
