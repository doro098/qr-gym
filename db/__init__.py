"""
Paquete db: acceso a la base de datos SQLite.

Submódulos:
- connection:     get_db_connection, init_db
- nanoid_util:    generación de NanoIds únicos
- repo_clientes:  CRUD de clientes + verificación de acceso
- repo_logs:      registro y consulta de eventos
- estadisticas:   agregados para dashboard
"""
from db.connection import DB_NAME, get_db_connection, init_db
from db.nanoid_util import generar_codigo_qr_unico
from db.repo_clientes import (
    actualizar_cliente,
    cliente_tiene_acceso,
    cliente_tiene_acceso_por_codigo,
    crear_cliente,
    eliminar_cliente,
    get_all_clientes,
    get_cliente_por_codigo_qr,
    get_cliente_por_id,
    obtener_clientes_vencidos,
    obtener_vencimientos_proximos,
)
from db.repo_logs import obtener_historial, registrar_evento
from db.estadisticas import obtener_datos_inicio, obtener_estadisticas

__all__ = [
    "DB_NAME",
    "get_db_connection",
    "init_db",
    "generar_codigo_qr_unico",
    "actualizar_cliente",
    "cliente_tiene_acceso",
    "cliente_tiene_acceso_por_codigo",
    "crear_cliente",
    "eliminar_cliente",
    "get_all_clientes",
    "get_cliente_por_codigo_qr",
    "get_cliente_por_id",
    "obtener_clientes_vencidos",
    "obtener_vencimientos_proximos",
    "obtener_historial",
    "registrar_evento",
    "obtener_datos_inicio",
    "obtener_estadisticas",
]
