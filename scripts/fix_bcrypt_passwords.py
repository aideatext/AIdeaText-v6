"""
scripts/fix_bcrypt_passwords.py
================================
Diagnóstico y reparación de hashes bcrypt corruptos en PostgreSQL (RDS).

Causa raíz del error "Invalid salt":
  - Columna `password` puede ser VARCHAR con tamaño insuficiente (< 60 chars)
  - Contraseñas antiguas guardadas como texto plano
  - Hashes truncados durante migración

Acciones:
  1. ALTER TABLE users ALTER COLUMN password TYPE TEXT  (idempotente, no pierde datos)
  2. Lista los usuarios con hashes inválidos
  3. Resetea sus contraseñas a TEMP_PASSWORD (requiere confirmación interactiva)

Uso (desde el directorio raíz del proyecto, con .env activo):
  python scripts/fix_bcrypt_passwords.py [--reset] [--dry-run]

Flags:
  --dry-run   Solo muestra qué haría, sin modificar nada
  --reset     Resetea contraseñas inválidas a TEMP_PASSWORD (pide confirmación)
"""

import os
import sys
import argparse
import logging
import bcrypt
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

TEMP_PASSWORD = "TempPass2026!"   # Contraseña temporal para usuarios con hash roto
BCRYPT_PREFIX = ("$2b$", "$2a$", "$2y$")


# ─── Conexión ────────────────────────────────────────────────────────────────

def get_conn():
    """Abre una conexión pg8000 usando las variables de entorno."""
    try:
        import pg8000.native
        conn = pg8000.native.Connection(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_DATABASE"),
            timeout=15,
        )
        return conn
    except Exception as e:
        logger.error(f"No se pudo conectar a PostgreSQL: {e}")
        sys.exit(1)


def run_query(conn, sql, params=None, fetch=True):
    """Ejecuta SQL con pg8000 usando sintaxis :1, :2, ..."""
    formatted = sql
    if params:
        for i in range(len(params)):
            formatted = formatted.replace("%s", f":{i+1}", 1)
        param_dict = {str(i + 1): v for i, v in enumerate(params)}
        result = conn.run(formatted, **param_dict)
    else:
        result = conn.run(formatted)

    if fetch and result:
        cols = [c["name"] for c in conn.columns]
        return [dict(zip(cols, row)) for row in result]
    return []


# ─── Lógica principal ────────────────────────────────────────────────────────

def is_valid_bcrypt(hash_str: str) -> bool:
    """Devuelve True si el string tiene formato bcrypt válido."""
    if not hash_str:
        return False
    if not isinstance(hash_str, str):
        return False
    if not any(hash_str.startswith(p) for p in BCRYPT_PREFIX):
        return False
    if len(hash_str) < 60:
        return False
    # Intentar una verificación real (bcrypt sabe si el salt es válido)
    try:
        bcrypt.checkpw(b"probe", hash_str.encode("utf-8"))
    except ValueError:
        return False
    except Exception:
        pass  # checkpw puede lanzar otros errores si la contraseña no matchea — eso está bien
    return True


def fix_column_type(conn, dry_run: bool):
    """
    Asegura que la columna `password` sea TEXT para nunca truncar hashes (60+ chars).
    """
    logger.info("Paso 1 — Verificando tipo de columna `password`...")
    rows = run_query(
        conn,
        "SELECT data_type, character_maximum_length "
        "FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'password'"
    )
    if not rows:
        logger.warning("  No se encontró la columna `password` en la tabla `users`.")
        return

    col = rows[0]
    dtype = col["data_type"]
    max_len = col["character_maximum_length"]
    logger.info(f"  Tipo actual: {dtype}({max_len})")

    needs_alter = dtype in ("character varying", "varchar", "char") and (max_len is None or max_len < 72)
    if dtype == "text":
        logger.info("  ✅ Columna ya es TEXT — sin cambios necesarios.")
        return

    if dry_run:
        logger.info("  [DRY-RUN] ALTER TABLE users ALTER COLUMN password TYPE TEXT")
    else:
        logger.info("  Ejecutando ALTER TABLE...")
        run_query(conn, "ALTER TABLE users ALTER COLUMN password TYPE TEXT", fetch=False)
        logger.info("  ✅ Columna convertida a TEXT.")


def audit_hashes(conn) -> list:
    """Devuelve lista de usuarios con hashes inválidos."""
    logger.info("Paso 2 — Auditando hashes bcrypt...")
    users = run_query(conn, "SELECT id, password FROM users")
    broken = []
    for u in users:
        if not is_valid_bcrypt(u.get("password", "")):
            broken.append(u["id"])
            logger.warning(f"  ⚠️  Usuario inválido: {u['id']}  hash='{str(u.get('password', ''))[:30]}...'")

    if not broken:
        logger.info("  ✅ Todos los hashes son válidos — sin usuarios rotos.")
    else:
        logger.info(f"  Encontrados {len(broken)} usuario(s) con hash inválido.")
    return broken


def reset_passwords(conn, broken_ids: list, dry_run: bool):
    """Re-hashea las contraseñas de los usuarios con hashes inválidos."""
    if not broken_ids:
        return

    new_hash = bcrypt.hashpw(TEMP_PASSWORD.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    logger.info(f"Paso 3 — Reseteando {len(broken_ids)} contraseña(s) a TEMP_PASSWORD...")

    for uid in broken_ids:
        if dry_run:
            logger.info(f"  [DRY-RUN] UPDATE users SET password=<nuevo_hash> WHERE id='{uid}'")
        else:
            run_query(
                conn,
                "UPDATE users SET password = %s WHERE id = %s",
                (new_hash, uid),
                fetch=False,
            )
            logger.info(f"  ✅ Contraseña reseteada para: {uid}")

    logger.info("")
    logger.info(f"  Contraseña temporal: {TEMP_PASSWORD}")
    logger.info("  ⚠️  Notifica a los usuarios afectados para que cambien su contraseña.")


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Repara hashes bcrypt corruptos en RDS")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra cambios sin ejecutar")
    parser.add_argument("--reset", action="store_true", help="Resetea contraseñas inválidas")
    args = parser.parse_args()

    if args.dry_run:
        logger.info("=== MODO DRY-RUN — ningún cambio será guardado ===\n")

    conn = get_conn()
    logger.info("Conectado a PostgreSQL.\n")

    fix_column_type(conn, dry_run=args.dry_run)
    logger.info("")
    broken_ids = audit_hashes(conn)

    if args.reset and broken_ids:
        if not args.dry_run:
            confirm = input(f"\n¿Resetear contraseña de {len(broken_ids)} usuario(s)? [s/N]: ")
            if confirm.strip().lower() != "s":
                logger.info("Operación cancelada.")
                conn.close()
                return
        reset_passwords(conn, broken_ids, dry_run=args.dry_run)
    elif broken_ids and not args.reset:
        logger.info("\n  Usa --reset para resetear las contraseñas inválidas.")

    conn.close()
    logger.info("\nListo.")


if __name__ == "__main__":
    main()
