"""
Generación de NanoIds únicos para la columna codigo_qr de clientes.

Usa la lib `nanoid` si está instalada; si no, usa `secrets` (CSPRNG del SO)
con el alfabeto estándar de NanoId. 6 chars → ~35 bits de entropía,
suficiente para un gimnasio (colisión esperada > 1 en 50M de códigos).
"""
import secrets

from config import NANOID_ALPHABET, NANOID_SIZE


def _generar_nanoid(size=NANOID_SIZE):
    """
    Genera un NanoId. Intenta usar la lib `nanoid` si está disponible;
    si no, usa `secrets.choice` (CSPRNG del SO) con el alfabeto estándar.
    """
    try:
        from nanoid import generate as _nanoid_generate
        return _nanoid_generate(size=size)
    except ImportError:
        return "".join(secrets.choice(NANOID_ALPHABET) for _ in range(size))


def generar_codigo_qr_unico():
    """
    Genera un NanoId de 6 chars garantizando que no exista ya en la DB.
    Reintenta hasta 10 veces por seguridad (colisión extremadamente improbable).
    """
    from db.connection import get_db_connection

    for _ in range(10):
        codigo = _generar_nanoid()
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT 1 FROM clientes WHERE codigo_qr = ?", (codigo,)
            )
            if not cur.fetchone():
                return codigo
    raise RuntimeError("No se pudo generar un codigo_qr único tras 10 intentos")
