"""
Conexión y creación de la base de datos SQLite.
"""
import sqlite3
from contextlib import contextmanager

from config import DB_NAME


@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db_connection() as conn:
        # Tabla clientes
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

        # Tabla logs (con columna disciplina)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                tipo TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                resultado TEXT NOT NULL,
                cliente_id INTEGER,
                usuario_admin TEXT,
                disciplina TEXT
            )
        """)

        # --- NUEVAS TABLAS PARA DISCIPLINAS ---
        conn.execute("""
            CREATE TABLE IF NOT EXISTS disciplinas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS horarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                disciplina_id INTEGER NOT NULL,
                dia_semana INTEGER NOT NULL,
                hora_inicio TEXT NOT NULL,
                hora_fin TEXT NOT NULL,
                FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id) ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS cliente_disciplina (
                cliente_id INTEGER NOT NULL,
                disciplina_id INTEGER NOT NULL,
                PRIMARY KEY (cliente_id, disciplina_id),
                FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE,
                FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id) ON DELETE CASCADE
            )
        """)

        # Índices
        conn.execute("CREATE INDEX IF NOT EXISTS idx_horarios_disciplina ON horarios(disciplina_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cliente_disciplina_cliente ON cliente_disciplina(cliente_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cliente_disciplina_disciplina ON cliente_disciplina(disciplina_id)")