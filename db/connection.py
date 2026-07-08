"""
Conexión y creación de la base de datos SQLite.

Toda otra lógica (CRUD, logs, estadísticas) vive en módulos hermanos.
Este archivo solo se ocupa de: abrir/cerrar conexiones y crear las tablas.
"""
import sqlite3
from contextlib import contextmanager

from config import DB_NAME


@contextmanager
def get_db_connection():
    """Context manager que abre, commitea y cierra una conexión SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """
    Crea las tablas si no existen. La DB arranca limpia: la columna
    codigo_qr ya forma parte del schema desde el CREATE TABLE.
    """
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT,
                telefono TEXT,
                vencimiento TEXT,
                codigo_qr TEXT UNIQUE
            )
        """)
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_clientes_codigo_qr "
            "ON clientes(codigo_qr)"
        )
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                tipo TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                resultado TEXT NOT NULL,
                cliente_id INTEGER,
                usuario_admin TEXT
            )
        """)
