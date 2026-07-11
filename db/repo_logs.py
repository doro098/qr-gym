"""
Registro y consulta de eventos (tabla logs).
"""
from datetime import datetime, timedelta

from db.connection import get_db_connection


def registrar_evento(tipo, descripcion, resultado, cliente_id=None, usuario_admin=None, disciplina=None):
    """Registra un evento. Ahora acepta disciplina (nombre)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        fecha = datetime.now().isoformat(sep=" ", timespec="seconds")
        cursor.execute(
            """INSERT INTO logs
               (fecha, tipo, descripcion, resultado, cliente_id, usuario_admin, disciplina)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (fecha, tipo, descripcion, resultado, cliente_id, usuario_admin, disciplina),
        )
        return cursor.lastrowid


def obtener_historial(limit=100, offset=0):
    """Obtiene logs con paginación por número de registros."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM logs ORDER BY fecha DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cursor.fetchall()]


def contar_logs():
    """Devuelve el número total de logs."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM logs")
        return cursor.fetchone()[0]


# ----- FUNCIONES PARA PAGINACIÓN POR DÍAS -----

def obtener_dias_con_logs(limite=30):
    """
    Devuelve una lista de fechas (YYYY-MM-DD) que tienen logs,
    ordenadas de más reciente a más antigua, hasta un máximo de 'limite' días.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT substr(fecha, 1, 10) as dia
            FROM logs
            ORDER BY dia DESC
            LIMIT ?
        """, (limite,))
        return [row["dia"] for row in cursor.fetchall()]


def obtener_logs_por_dia(fecha):
    """
    Devuelve todos los logs de una fecha determinada (YYYY-MM-DD),
    ordenados por hora descendente (más reciente primero).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM logs
            WHERE fecha >= ? || ' 00:00:00' AND fecha <= ? || ' 23:59:59'
            ORDER BY fecha DESC
        """, (fecha, fecha))
        return [dict(row) for row in cursor.fetchall()]
