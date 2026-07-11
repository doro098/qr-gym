"""
CRUD de disciplinas, horarios y relación con clientes.
"""
from datetime import datetime

from db.connection import get_db_connection


# ---------- Disciplinas ----------
def crear_disciplina(nombre, descripcion=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO disciplinas (nombre, descripcion) VALUES (?, ?)",
            (nombre, descripcion)
        )
        return cursor.lastrowid


def obtener_disciplinas():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM disciplinas ORDER BY nombre")
        return [dict(row) for row in cursor.fetchall()]


def obtener_disciplina_por_id(disciplina_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM disciplinas WHERE id = ?", (disciplina_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def actualizar_disciplina(disciplina_id, nombre, descripcion=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE disciplinas SET nombre = ?, descripcion = ? WHERE id = ?",
            (nombre, descripcion, disciplina_id)
        )
        return cursor.rowcount > 0


def eliminar_disciplina(disciplina_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM disciplinas WHERE id = ?", (disciplina_id,))
        return cursor.rowcount > 0


# ---------- Horarios ----------
def agregar_horario(disciplina_id, dia_semana, hora_inicio, hora_fin):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO horarios
               (disciplina_id, dia_semana, hora_inicio, hora_fin)
               VALUES (?, ?, ?, ?)""",
            (disciplina_id, dia_semana, hora_inicio, hora_fin)
        )
        return cursor.lastrowid


def eliminar_horario(horario_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM horarios WHERE id = ?", (horario_id,))
        return cursor.rowcount > 0


def obtener_horarios_por_disciplina(disciplina_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM horarios WHERE disciplina_id = ? ORDER BY dia_semana, hora_inicio",
            (disciplina_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def eliminar_horarios_de_disciplina(disciplina_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM horarios WHERE disciplina_id = ?", (disciplina_id,))


# ---------- Relación cliente-disciplina ----------
def asignar_disciplina_a_cliente(cliente_id, disciplina_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO cliente_disciplina (cliente_id, disciplina_id) VALUES (?, ?)",
            (cliente_id, disciplina_id)
        )
        return cursor.rowcount > 0


def remover_disciplina_de_cliente(cliente_id, disciplina_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM cliente_disciplina WHERE cliente_id = ? AND disciplina_id = ?",
            (cliente_id, disciplina_id)
        )
        return cursor.rowcount > 0


def obtener_disciplinas_de_cliente(cliente_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.* FROM disciplinas d
            JOIN cliente_disciplina cd ON d.id = cd.disciplina_id
            WHERE cd.cliente_id = ?
            ORDER BY d.nombre
        """, (cliente_id,))
        return [dict(row) for row in cursor.fetchall()]


def reemplazar_disciplinas_de_cliente(cliente_id, lista_ids_disciplinas):
    """
    Reemplaza todas las disciplinas del cliente por las que se pasan en la lista.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Eliminar todas las actuales
        cursor.execute("DELETE FROM cliente_disciplina WHERE cliente_id = ?", (cliente_id,))
        # Insertar las nuevas
        for dis_id in lista_ids_disciplinas:
            cursor.execute(
                "INSERT INTO cliente_disciplina (cliente_id, disciplina_id) VALUES (?, ?)",
                (cliente_id, dis_id)
            )
        return True


# ---------- Verificación de disciplina activa ----------
def cliente_tiene_disciplina_activa(cliente_id, dia_semana=None, hora_actual=None):
    """
    Devuelve (bool, nombre_disciplina) indicando si el cliente tiene alguna
    disciplina activa en el día y hora dados.
    Si no se pasan día/hora, usa el momento actual.
    """
    if dia_semana is None:
        dia_semana = datetime.now().weekday()  # 0=lunes, 6=domingo
    if hora_actual is None:
        hora_actual = datetime.now().time().strftime("%H:%M")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.nombre
            FROM cliente_disciplina cd
            JOIN disciplinas d ON cd.disciplina_id = d.id
            JOIN horarios h ON h.disciplina_id = d.id
            WHERE cd.cliente_id = ?
              AND h.dia_semana = ?
              AND h.hora_inicio <= ?
              AND h.hora_fin >= ?
            LIMIT 1
        """, (cliente_id, dia_semana, hora_actual, hora_actual))
        row = cursor.fetchone()
        if row:
            return True, row["nombre"]
        return False, None


# ---------- Obtener disciplinas con sus horarios ----------
def obtener_disciplinas_con_horarios():
    """Devuelve lista de disciplinas, cada una con su lista de horarios."""
    disciplinas = obtener_disciplinas()
    for d in disciplinas:
        d["horarios"] = obtener_horarios_por_disciplina(d["id"])
    return disciplinas