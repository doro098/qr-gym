"""
CRUD de clientes y verificación de acceso.

Funciones:
- Crear / actualizar / eliminar cliente
- Lookup por id (entero) o por codigo_qr (NanoId)
- Verificación de acceso (vencimiento)
- Listados: todos, vencidos, próximos a vencer
"""
from datetime import datetime, timedelta

from db.connection import get_db_connection
from db.nanoid_util import generar_codigo_qr_unico


# ========== Crear / actualizar / eliminar ==========

def crear_cliente(nombre, apellido=None, telefono=None, vencimiento=None):
    """Crea un cliente. Genera su codigo_qr (NanoId único) automáticamente."""
    codigo_qr = generar_codigo_qr_unico()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO clientes
               (nombre, apellido, telefono, vencimiento, codigo_qr)
               VALUES (?, ?, ?, ?, ?)""",
            (nombre, apellido, telefono, vencimiento, codigo_qr),
        )
        return cursor.lastrowid


def actualizar_cliente(
    cliente_id, nombre=None, apellido=None, telefono=None, vencimiento=None
):
    """Actualiza los campos pasados (los None se ignoran)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        campos, valores = [], []
        if nombre is not None:
            campos.append("nombre = ?")
            valores.append(nombre)
        if apellido is not None:
            campos.append("apellido = ?")
            valores.append(apellido)
        if telefono is not None:
            campos.append("telefono = ?")
            valores.append(telefono)
        if vencimiento is not None:
            campos.append("vencimiento = ?")
            valores.append(vencimiento)
        if campos:
            valores.append(cliente_id)
            cursor.execute(
                f"UPDATE clientes SET {', '.join(campos)} WHERE id = ?", valores
            )
            return True
        return False


def eliminar_cliente(cliente_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        return cursor.rowcount > 0


# ========== Lookups ==========

def get_all_clientes():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes")
        return cursor.fetchall()


def get_cliente_por_id(cliente_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
        cliente = cursor.fetchone()
        return dict(cliente) if cliente else None


def get_cliente_por_codigo_qr(codigo_qr):
    """
    Devuelve el cliente cuyo codigo_qr coincide exactamente, o None si no existe.
    Es la función que usa el scanner al leer un QR.
    """
    if not codigo_qr:
        return None
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM clientes WHERE codigo_qr = ?", (codigo_qr,)
        )
        cliente = cursor.fetchone()
        return dict(cliente) if cliente else None


# ========== Verificación de acceso ==========

def cliente_tiene_acceso(cliente_id):
    """
    Devuelve True si el cliente existe y su vencimiento es hoy o futuro.
    Una sola consulta SQL, sin traer nada a memoria.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id FROM clientes
            WHERE id = ?
            AND (vencimiento IS NULL OR vencimiento >= date('now'))
        """,
            (cliente_id,),
        )
        return cursor.fetchone() is not None


def cliente_tiene_acceso_por_codigo(codigo_qr):
    """
    Igual que cliente_tiene_acceso, pero lookup por codigo_qr.
    Devuelve (tiene_acceso: bool, cliente: dict|None).
    """
    cliente = get_cliente_por_codigo_qr(codigo_qr)
    if not cliente:
        return False, None
    return cliente_tiene_acceso(cliente["id"]), cliente


# ========== Listados de vencimientos ==========

def obtener_vencimientos_proximos(dias=7):
    """Clientes cuyo vencimiento cae entre hoy y los próximos X días."""
    limite = (datetime.now().date() + timedelta(days=dias)).isoformat()
    hoy = datetime.now().date().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM clientes
            WHERE vencimiento IS NOT NULL
            AND vencimiento BETWEEN ? AND ?
            ORDER BY vencimiento ASC
        """,
            (hoy, limite),
        )
        return [dict(row) for row in cursor.fetchall()]


def obtener_clientes_vencidos():
    """Clientes cuyo vencimiento ya pasó."""
    hoy = datetime.now().date().isoformat()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM clientes
            WHERE vencimiento IS NOT NULL
            AND vencimiento < ?
            ORDER BY vencimiento DESC
        """,
            (hoy,),
        )
        return [dict(row) for row in cursor.fetchall()]
