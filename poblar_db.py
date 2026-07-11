#!/usr/bin/env python3
"""
Script para poblar la base de datos con datos masivos (200 clientes y logs de un mes).

Uso:
    python poblar_db.py

Genera:
    - 200 clientes con nombres realistas
    - 5 disciplinas con horarios
    - ~500-1000 logs de acceso distribuidos en 30 días
    - Logs del sistema adicionales
"""

import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from db.connection import get_db_connection, init_db
from db.repo_clientes import crear_cliente, get_all_clientes
from db.repo_disciplinas import (
    crear_disciplina,
    agregar_horario,
    asignar_disciplina_a_cliente,
    obtener_disciplinas,
)
from db.repo_logs import registrar_evento

# ============================================================
# DATOS DE EJEMPLO
# ============================================================

DISCIPLINAS = [
    {
        "nombre": "Boxeo",
        "descripcion": "Entrenamiento de boxeo y defensa personal",
        "horarios": [
            {"dia": 0, "inicio": "08:00", "fin": "12:00"},
            {"dia": 0, "inicio": "16:00", "fin": "20:00"},
            {"dia": 2, "inicio": "08:00", "fin": "12:00"},
            {"dia": 2, "inicio": "16:00", "fin": "20:00"},
            {"dia": 4, "inicio": "08:00", "fin": "12:00"},
        ]
    },
    {
        "nombre": "Yoga",
        "descripcion": "Clases de yoga y meditación",
        "horarios": [
            {"dia": 1, "inicio": "07:00", "fin": "09:00"},
            {"dia": 1, "inicio": "18:00", "fin": "20:00"},
            {"dia": 3, "inicio": "07:00", "fin": "09:00"},
            {"dia": 3, "inicio": "18:00", "fin": "20:00"},
            {"dia": 5, "inicio": "09:00", "fin": "11:00"},
        ]
    },
    {
        "nombre": "CrossFit",
        "descripcion": "Entrenamiento funcional de alta intensidad",
        "horarios": [
            {"dia": 0, "inicio": "06:00", "fin": "08:00"},
            {"dia": 0, "inicio": "12:00", "fin": "14:00"},
            {"dia": 1, "inicio": "06:00", "fin": "08:00"},
            {"dia": 2, "inicio": "06:00", "fin": "08:00"},
            {"dia": 3, "inicio": "06:00", "fin": "08:00"},
            {"dia": 4, "inicio": "06:00", "fin": "08:00"},
            {"dia": 5, "inicio": "08:00", "fin": "10:00"},
        ]
    },
    {
        "nombre": "Natación",
        "descripcion": "Entrenamiento en piscina",
        "horarios": [
            {"dia": 0, "inicio": "10:00", "fin": "13:00"},
            {"dia": 2, "inicio": "10:00", "fin": "13:00"},
            {"dia": 4, "inicio": "10:00", "fin": "13:00"},
            {"dia": 5, "inicio": "15:00", "fin": "18:00"},
        ]
    },
    {
        "nombre": "Spinning",
        "descripcion": "Clases de ciclismo indoor",
        "horarios": [
            {"dia": 0, "inicio": "18:00", "fin": "19:30"},
            {"dia": 1, "inicio": "18:00", "fin": "19:30"},
            {"dia": 2, "inicio": "18:00", "fin": "19:30"},
            {"dia": 3, "inicio": "18:00", "fin": "19:30"},
            {"dia": 4, "inicio": "18:00", "fin": "19:30"},
        ]
    },
]

# Nombres y apellidos comunes en español
NOMBRES = [
    "Ana", "Carlos", "María", "Juan", "Laura", "Pedro", "Sofía", "Miguel",
    "Elena", "David", "Carmen", "Javier", "Isabel", "José", "Lucía", "Antonio",
    "Paula", "Manuel", "Marta", "Pablo", "Rosa", "Francisco", "Patricia", "Jesús",
    "Teresa", "Luis", "Ana", "Alberto", "Silvia", "Diego", "Mónica", "Sergio",
    "Raquel", "Víctor", "Beatriz", "Jorge", "Julia", "Álvaro", "Nuria", "Óscar",
    "Sara", "Enrique", "Claudia", "Roberto", "Miriam", "Jose", "Olga", "Rafael",
    "Lorena", "Ignacio", "Eva", "Daniel", "Patricia", "María", "Santiago", "Ángela",
    "Iván", "Lola", "Gonzalo", "Alicia", "Alejandro", "Cristina", "Fernando", "Pilar",
    "Hugo", "Natalia", "Andrés", "Dolores", "Marcos", "Ainhoa", "Adrián", "Clara",
    "Irene", "Carlos", "Manuela", "Joaquín", "Inés", "Agustín", "Lidia", "Emilio",
    "Esther", "Ángel", "Diana", "Lorenzo", "Rocío", "César", "Juana", "Ramiro",
    "Carla", "Gilberto", "Marianela", "Felipe", "Nora", "Reynaldo", "Aída", "Arturo",
    "Alba", "Eduardo", "Candelaria", "Francisco", "Josefa", "Modesto", "Ruth"
]

APELLIDOS = [
    "García", "López", "Martínez", "Pérez", "Sánchez", "Ramírez", "Torres", "Flores",
    "Gómez", "Díaz", "Romero", "Molina", "Ortega", "Reyes", "Mendoza", "Vargas",
    "Fernández", "González", "Rodríguez", "Jiménez", "Ruiz", "Álvarez", "Hernández",
    "Moreno", "Muñoz", "Navarro", "Romero", "Álvarez", "Lozano", "Pascual", "Cruz",
    "Santos", "Pardo", "Mora", "Iglesias", "Blanco", "Cabrera", "Costa", "Marín",
    "Peña", "Núñez", "Ramos", "Vega", "Gil", "Suárez", "Díaz", "Serrano", "Moya",
    "Benítez", "Cortés", "Gallego", "Castro", "Soto", "Vázquez", "Calvo", "Solís",
    "Ramos", "Guerrero", "Prieto", "Sanz", "Hidalgo", "Ibáñez", "Lara", "Cano",
    "Lucas", "Sáez", "Méndez", "Montero", "Ponce", "Lorenzo", "Nieto", "Campos",
    "Márquez", "Pina", "Valero", "Soto", "Varela", "Gálvez", "Acosta", "Santana",
    "Bautista", "Delgado", "Quintero", "Trujillo", "Ríos", "Puga", "Sosa", "Estrada",
    "Herrera", "Armas", "Mesa", "Correa", "Pineda", "Montes", "Gamboa", "Villalba",
    "López", "Orta", "Sierra", "Balboa", "Conde", "Salazar"
]

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def calcular_fecha_vencimiento(estado):
    """
    Genera una fecha de vencimiento según el estado:
    - 'vigente': fecha futura entre 1 y 365 días
    - 'vencido': fecha pasada entre 1 y 90 días
    - 'sin_fecha': None (acceso libre)
    """
    hoy = datetime.now().date()
    if estado == 'sin_fecha':
        return None
    if estado == 'vigente':
        dias = random.randint(1, 365)
        return (hoy + timedelta(days=dias)).isoformat()
    else:  # 'vencido'
        dias = random.randint(1, 90)
        return (hoy - timedelta(days=dias)).isoformat()


def generar_cliente(disciplinas):
    """Genera un cliente aleatorio con su lista de disciplinas."""
    nombre = random.choice(NOMBRES)
    apellido = random.choice(APELLIDOS)
    telefono = f"6{random.randint(10000000, 99999999)}"

    # Distribución de vencimientos: 60% vigentes, 25% vencidos, 15% sin fecha
    prob = random.random()
    if prob < 0.60:
        estado = 'vigente'
    elif prob < 0.85:
        estado = 'vencido'
    else:
        estado = 'sin_fecha'

    vencimiento = calcular_fecha_vencimiento(estado)

    # Seleccionar disciplinas (0 a 3)
    num_disciplinas = random.randint(0, 3)
    disciplinas_seleccionadas = random.sample(disciplinas, min(num_disciplinas, len(disciplinas)))
    ids_disciplinas = [d['id'] for d in disciplinas_seleccionadas]

    return {
        'nombre': nombre,
        'apellido': apellido,
        'telefono': telefono,
        'vencimiento': vencimiento,
        'disciplinas_ids': ids_disciplinas,
        'estado': estado
    }


def generar_log_acceso(cliente, disciplinas, fecha):
    """
    Genera un log de acceso simulado para un cliente en una fecha dada.
    Devuelve (descripcion, resultado, disciplina_nombre)
    """
    nombre = cliente['nombre']
    vencimiento = cliente['vencimiento']
    disciplinas_ids = cliente['disciplinas_ids']

    # Verificar vencimiento
    hoy = datetime.now().date()
    esta_vencido = False
    if vencimiento:
        try:
            fecha_venc = datetime.strptime(vencimiento, "%Y-%m-%d").date()
            esta_vencido = fecha_venc < hoy
        except:
            esta_vencido = False

    # Determinar si tiene disciplina activa (simulación)
    tiene_disciplina = len(disciplinas_ids) > 0
    disciplina_activa = None
    if tiene_disciplina:
        # 60% de probabilidad de que la disciplina esté activa (simulando horario)
        if random.random() < 0.6:
            disciplina_activa = random.choice([d for d in disciplinas if d['id'] in disciplinas_ids])['nombre']

    # Decidir resultado
    if esta_vencido:
        return f"ACCESO DENEGADO — {nombre} (vencido: {vencimiento})", "DENEGADO", None
    elif tiene_disciplina and not disciplina_activa:
        return f"ACCESO DENEGADO — {nombre} (ninguna disciplina activa)", "DENEGADO", None
    else:
        # Simular éxito/error
        if random.random() < 0.85:  # 85% éxito
            if disciplina_activa:
                return f"ACCESO PERMITIDO — {nombre} ({disciplina_activa})", "EXITO", disciplina_activa
            else:
                return f"ACCESO PERMITIDO — {nombre} (vence: {vencimiento or 'sin fecha'})", "EXITO", None
        else:
            return "Error de lectura — QR no reconocido", "ERROR", None


def generar_logs_masivos(clientes, disciplinas, num_logs=800):
    """Genera logs de acceso masivos para todo un mes."""
    print(f"  Generando ~{num_logs} logs de acceso...")

    hoy = datetime.now()
    inicio_periodo = hoy - timedelta(days=30)

    logs_creados = 0
    batch_size = 100

    with get_db_connection() as conn:
        cursor = conn.cursor()

        for i in range(num_logs):
            # Seleccionar cliente aleatorio
            cliente = random.choice(clientes)

            # Fecha aleatoria en los últimos 30 días
            delta = hoy - inicio_periodo
            segundos_aleatorios = random.randint(0, int(delta.total_seconds()))
            fecha = inicio_periodo + timedelta(seconds=segundos_aleatorios)
            fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S")

            # Generar log
            desc, resultado, disciplina = generar_log_acceso(cliente, disciplinas, fecha)

            # Insertar directamente (más rápido)
            cursor.execute(
                """INSERT INTO logs
                   (fecha, tipo, descripcion, resultado, cliente_id, usuario_admin, disciplina)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (fecha_str, "ACCESO", desc, resultado, cliente['id'], None, disciplina)
            )
            logs_creados += 1

            # Commit cada batch_size
            if logs_creados % batch_size == 0:
                conn.commit()
                print(f"    ... {logs_creados} logs generados")

        conn.commit()

    print(f"    ✓ {logs_creados} logs de acceso creados")


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("  POBLADOR MASIVO - QR-GYM (200 clientes, logs de 30 días)")
    print("=" * 70)

    # 1. Resetear base de datos
    print("\n[1] Reseteando base de datos...")
    from config import DB_NAME
    db_path = Path(DB_NAME)
    if db_path.exists():
        db_path.unlink()
        print(f"    ✓ {db_path} eliminado")

    init_db()
    print("    ✓ Tablas creadas")

    # 2. Crear disciplinas
    print("\n[2] Creando disciplinas...")
    disciplinas_ids = []
    for disc_data in DISCIPLINAS:
        dis_id = crear_disciplina(disc_data["nombre"], disc_data["descripcion"])
        disciplinas_ids.append({
            'id': dis_id,
            'nombre': disc_data["nombre"],
            'descripcion': disc_data["descripcion"]
        })
        for horario in disc_data["horarios"]:
            agregar_horario(dis_id, horario["dia"], horario["inicio"], horario["fin"])
        print(f"    ✓ Disciplina '{disc_data['nombre']}' creada")

    disciplinas = obtener_disciplinas()
    print(f"    Total: {len(disciplinas)} disciplinas")

    # 3. Crear 200 clientes
    print("\n[3] Creando 200 clientes...")
    clientes_creados = []
    for i in range(200):
        cliente_data = generar_cliente(disciplinas)
        cliente_id = crear_cliente(
            nombre=cliente_data['nombre'],
            apellido=cliente_data['apellido'],
            telefono=cliente_data['telefono'],
            vencimiento=cliente_data['vencimiento']
        )

        # Asignar disciplinas
        for dis_id in cliente_data['disciplinas_ids']:
            asignar_disciplina_a_cliente(cliente_id, dis_id)

        clientes_creados.append({
            'id': cliente_id,
            'nombre': cliente_data['nombre'],
            'apellido': cliente_data['apellido'],
            'vencimiento': cliente_data['vencimiento'],
            'disciplinas_ids': cliente_data['disciplinas_ids'],
            'estado': cliente_data['estado']
        })

        if (i + 1) % 50 == 0:
            print(f"    ... {i + 1} clientes creados")

    print(f"    ✓ {len(clientes_creados)} clientes creados")

    # Contar estados
    vigentes = sum(1 for c in clientes_creados if c['estado'] == 'vigente')
    vencidos = sum(1 for c in clientes_creados if c['estado'] == 'vencido')
    sin_fecha = sum(1 for c in clientes_creados if c['estado'] == 'sin_fecha')
    print(f"    Distribución: {vigentes} vigentes, {vencidos} vencidos, {sin_fecha} sin fecha")

    # 4. Generar logs masivos
    print("\n[4] Generando logs de acceso (últimos 30 días)...")
    num_logs = random.randint(700, 1200)  # Entre 700 y 1200 logs
    generar_logs_masivos(clientes_creados, disciplinas, num_logs)

    # 5. Logs del sistema adicionales
    print("\n[5] Generando logs del sistema...")
    acciones_sistema = [
        ("Inicio de sesión exitoso — usuario: admin", "EXITO"),
        ("Cierre de sesión", "EXITO"),
        ("Intento de login fallido — usuario: test", "DENEGADO"),
        ("Nuevo cliente creado desde admin", "EXITO"),
        ("Cliente eliminado desde admin", "EXITO"),
    ]
    for _ in range(random.randint(30, 50)):
        desc, res = random.choice(acciones_sistema)
        fecha = datetime.now() - timedelta(days=random.randint(0, 30))
        fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO logs
                   (fecha, tipo, descripcion, resultado, cliente_id, usuario_admin, disciplina)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (fecha_str, "SISTEMA", desc, res, None, "admin", None)
            )
    print("    ✓ Logs del sistema generados")

    # 6. Resumen final
    print("\n" + "=" * 70)
    print("  RESUMEN FINAL")
    print("=" * 70)

    from db.estadisticas import obtener_datos_inicio, obtener_estadisticas
    stats = obtener_datos_inicio()
    estadisticas = obtener_estadisticas()

    print(f"\n  📊 Clientes totales:     {stats['total_clientes']}")
    print(f"  📊 Disciplinas:           {len(disciplinas)}")
    print(f"  📊 Accesos hoy:           {stats['accesos_hoy']}")
    print(f"  📊 Denegados hoy:         {stats['denegados_hoy']}")
    print(f"  📊 Clientes vencidos:     {stats['clientes_vencidos']}")
    print(f"  📊 Accesos este mes:      {estadisticas['stats']['accesos_mes']}")
    print(f"  📊 Denegados este mes:    {estadisticas['stats']['denegados_mes']}")
    print(f"  📊 Hora pico:             {estadisticas['stats']['hora_pico']}")

    print("\n✅ Población completada con éxito!")
    print(f"   Base de datos: {DB_NAME}")
    print("\n   Ahora puedes ejecutar 'python app.py' y explorar el sistema.")
    print("=" * 70)


if __name__ == "__main__":
    main()
