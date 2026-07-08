"""
Registro y consulta de eventos (tabla logs).

Un evento tiene:
- tipo:        'SISTEMA' | 'ACCESO' | (otros que surjan)
- descripcion: texto libre
- resultado:   'EXITO' | 'DENEGADO' | 'ERROR'
- cliente_id:  FK entera (opcional)
- usuario_admin: quién disparó el evento (opcional)
"""
from datetime import datetime

from db.connection import get_db_connection


def registrar_evento(tipo, descripcion, resultado, cliente_id=None, usuario_admin=None):
    """Registra un evento en la tabla logs. Transacción atómica e independiente."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fecha = datetime.now().isoformat(sep=" ", timespec="seconds")
        cursor.execute(
            """INSERT INTO logs
               (fecha, tipo, descripcion, resultado, cliente_id, usuario_admin)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (fecha, tipo, descripcion, resultado, cliente_id, usuario_admin),
        )
        return cursor.lastrowid


def obtener_historial(limite=100):
    """Devuelve los últimos N eventos ordenados por fecha descendente."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs ORDER BY fecha DESC LIMIT ?", (limite,))
        return [dict(row) for row in cursor.fetchall()]
