"""
Paquete db: acceso a la base de datos SQLite.
"""
from db.connection import DB_NAME, get_db_connection, init_db
from db.nanoid_util import generar_codigo_qr_unico
from db.estadisticas import obtener_datos_inicio, obtener_estadisticas
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
    verificar_acceso_completo,
)
from db.repo_logs import (
    obtener_historial,
    registrar_evento,
    contar_logs,
    obtener_dias_con_logs,
    obtener_logs_por_dia
)
from db.repo_disciplinas import (
    crear_disciplina,
    obtener_disciplinas,
    obtener_disciplina_por_id,
    actualizar_disciplina,
    eliminar_disciplina,
    agregar_horario,
    eliminar_horario,
    obtener_horarios_por_disciplina,
    asignar_disciplina_a_cliente,
    remover_disciplina_de_cliente,
    obtener_disciplinas_de_cliente,
    reemplazar_disciplinas_de_cliente,
    cliente_tiene_disciplina_activa,
    obtener_disciplinas_con_horarios,
)

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
    "verificar_acceso_completo",
    "obtener_historial",
    "registrar_evento",
    "contar_logs",
    "obtener_dias_con_logs",
    "obtener_logs_por_dia",
    "obtener_datos_inicio",
    "obtener_estadisticas",
    "crear_disciplina",
    "obtener_disciplinas",
    "obtener_disciplina_por_id",
    "actualizar_disciplina",
    "eliminar_disciplina",
    "agregar_horario",
    "eliminar_horario",
    "obtener_horarios_por_disciplina",
    "asignar_disciplina_a_cliente",
    "remover_disciplina_de_cliente",
    "obtener_disciplinas_de_cliente",
    "reemplazar_disciplinas_de_cliente",
    "cliente_tiene_disciplina_activa",
    "obtener_disciplinas_con_horarios",
]
