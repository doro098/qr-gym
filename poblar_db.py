#!/usr/bin/env python3
"""
Pobla la base de datos con datos de prueba para desarrollo.

Ejecuta:
    python poblar_db.py
"""

import random
import sqlite3
from datetime import datetime, timedelta

from db.connection import get_db_connection
from db.repo_clientes import crear_cliente
from db.repo_logs import registrar_evento

# -------------------------------------------------------------------
# Configuración
# -------------------------------------------------------------------
CANTIDAD_CLIENTES = 30
CANTIDAD_LOGS = 200

NOMBRES = ["Ana", "Luis", "María", "Carlos", "Lucía", "Javier", "Sofía", "Miguel",
           "Elena", "Pablo", "Laura", "David", "Carmen", "José", "Isabel", "Raúl",
           "Marta", "Jorge", "Clara", "Andrés", "Paula", "Hugo", "Valeria", "Diego"]
APELLIDOS = ["García", "Martínez", "López", "González", "Pérez", "Sánchez", "Ramírez",
             "Torres", "Flores", "Rivera", "Morales", "Cruz", "Ortiz", "Reyes", "Gutiérrez"]

# -------------------------------------------------------------------
# Funciones auxiliares
# -------------------------------------------------------------------
def random_date(start, end):
    """Fecha aleatoria entre dos fechas."""
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)

def random_phone():
    return f"6{random.randint(10000000, 99999999)}"

def random_vencimiento():
    hoy = datetime.now().date()
    dias = random.randint(-30, 90)  # entre vencidos y futuros
    return (hoy + timedelta(days=dias)).isoformat()

def random_texto():
    acciones = ["Ingreso al gimnasio", "Salida", "Acceso por QR", "Acceso manual",
                "Registro de entrada", "Intento de acceso"]
    return random.choice(acciones)

# -------------------------------------------------------------------
# Poblado
# -------------------------------------------------------------------
def poblar():
    print("📦 Poblando base de datos con datos de prueba...")

    # Limpiar tablas (opcional: eliminar datos previos)
    with get_db_connection() as conn:
        conn.execute("DELETE FROM logs")
        conn.execute("DELETE FROM clientes")
        conn.execute("DELETE FROM sqlite_sequence")  # reinicia autoincrement
        print("   - Tablas limpias")

    # 1. Crear clientes
    clientes_ids = []
    for i in range(CANTIDAD_CLIENTES):
        nombre = random.choice(NOMBRES)
        apellido = random.choice(APELLIDOS)
        telefono = random_phone()
        vencimiento = random_vencimiento()
        cliente_id = crear_cliente(nombre, apellido, telefono, vencimiento)
        clientes_ids.append(cliente_id)
        print(f"   + Cliente #{cliente_id}: {nombre} {apellido} (vence {vencimiento})")
    print(f"✅ Creados {len(clientes_ids)} clientes")

    # 2. Generar logs
    hoy = datetime.now()
    hace_un_mes = hoy - timedelta(days=30)

    tipos = ["ACCESO", "SISTEMA"]
    resultados_acceso = ["EXITO", "DENEGADO"]
    resultados_sistema = ["EXITO", "ERROR"]

    for i in range(CANTIDAD_LOGS):
        fecha = random_date(hace_un_mes, hoy)
        tipo = random.choice(tipos)

        if tipo == "ACCESO":
            cliente_id = random.choice(clientes_ids)
            resultado = random.choices(
                resultados_acceso,
                weights=[0.75, 0.25]  # 75% éxito, 25% denegado
            )[0]
            descripcion = f"Acceso QR - Cliente #{cliente_id}"
        else:  # SISTEMA
            cliente_id = None
            resultado = random.choices(
                resultados_sistema,
                weights=[0.9, 0.1]
            )[0]
            descripcion = random.choice([
                "Inicio de sesión", "Cierre de sesión", "Cliente editado",
                "Nuevo cliente creado", "Eliminación de cliente", "Backup realizado"
            ])

        registrar_evento(
            tipo=tipo,
            descripcion=descripcion,
            resultado=resultado,
            cliente_id=cliente_id,
            usuario_admin="admin" if tipo == "SISTEMA" else None
        )
        if i % 20 == 0:
            print(f"   . Logs generados: {i+1}/{CANTIDAD_LOGS}")

    print(f"✅ Creados {CANTIDAD_LOGS} logs")

    # 3. Resumen
    with get_db_connection() as conn:
        total_clientes = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
        total_logs = conn.execute("SELECT COUNT(*) FROM logs").fetchone()[0]
        print("\n📊 Resumen final:")
        print(f"   - Clientes: {total_clientes}")
        print(f"   - Logs:     {total_logs}")

    print("\n🎉 ¡Base de datos poblada! Ahora puedes visitar las páginas:")

if __name__ == "__main__":
    poblar()
