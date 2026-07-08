"""
Bucle principal del control de acceso del gimnasio.

Orquesta:
1. ScannerQR   → lee el QR de la cámara (devuelve un texto)
2. validar     → comprueba que sea un NanoId válido de 6 chars
3. verificar   → lookup en DB por codigo_qr, comprueba vencimiento
4. registrar   → deja log del resultado (EXITO / DENEGADO / ERROR)
5. cerradura   → si todo OK, abre el GPIO por 1 segundo

Entradas:
- QR válido y cliente vigente → abre cerradura + log EXITO
- QR válido pero cliente vencido → log DENEGADO
- QR no reconocido o formato inválido → log ERROR/DENEGADO

Para ejecutar en la Raspberry:
    python hardware/acceso.py
o
    python -m hardware.acceso
"""
import sys
from pathlib import Path

# Añadir la carpeta raíz del proyecto al path de módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

import time

from config import DEBOUNCE_SEGUNDOS, PIN_CERRADURA, TIEMPO_CERRADURA
from db.repo_clientes import cliente_tiene_acceso_por_codigo
from db.repo_logs import registrar_evento
from hardware.cerradura import ControlCerradura
from hardware.scanner import ScannerQR

LONGITUD_NANOID = 6  # longitud esperada del codigo_qr


def codigo_es_valido(codigo):
    """
    Validación ligera del NanoId escaneado.
    No es estricta (no conocemos el alfabeto exacto que podría haberse usado),
    pero filtra obvios errores: vacío, longitud incorrecta, o cosas que claramente
    no son un NanoId (ej: el QR viejo "Cliente ID: 5\nNombre: Juan").
    """
    if not codigo:
        return False
    codigo = codigo.strip()
    if len(codigo) != LONGITUD_NANOID:
        return False
    # Aceptamos el alfabeto estándar de NanoId: A-Za-z0-9_-
    return all(c.isalnum() or c in "_-" for c in codigo)


def verificar_acceso(codigo_qr):
    """
    Lookup directo por codigo_qr (NanoId). Devuelve (permitido, mensaje, cliente_id).
    cliente_id se usa para registrar el evento en logs (la FK sigue siendo entera).
    """
    permitido, cliente = cliente_tiene_acceso_por_codigo(codigo_qr)
    if not cliente:
        return False, f"QR no reconocido: {codigo_qr}", None

    nombre = cliente["nombre"]
    vencimiento = cliente.get("vencimiento") or "Sin fecha"
    cliente_id = cliente["id"]

    if not permitido:
        return False, f"ACCESO DENEGADO — {nombre} (vencido: {vencimiento})", cliente_id
    return True, f"ACCESO PERMITIDO — {nombre} (vence: {vencimiento})", cliente_id


def procesar_qr(codigo, cerradura):
    """Procesa el texto escaneado por el scanner."""
    if not codigo_es_valido(codigo):
        print(f"❌ QR inválido (no es un NanoId de {LONGITUD_NANOID} chars): {codigo[:60]!r}")
        registrar_evento(
            tipo="ACCESO",
            descripcion=f"QR inválido: {codigo[:60]}",
            resultado="ERROR",
        )
        return

    permitido, mensaje, cliente_id = verificar_acceso(codigo.strip())
    print(f"{'✅' if permitido else '⛔'} {mensaje}")
    registrar_evento(
        tipo="ACCESO",
        descripcion=mensaje,
        resultado="EXITO" if permitido else "DENEGADO",
        cliente_id=cliente_id,
    )
    if permitido:
        cerradura.abrir_cerradura()


def main():
    print("=" * 50)
    print("  CONTROL DE ACCESO - GIMNASIO (GPIO / HEADLESS)")
    print("  QR basado en NanoId de 6 chars")
    print("=" * 50)
    print(f"GPIO cerradura : {PIN_CERRADURA}")
    print("Para salir presiona Ctrl+C")
    print("-" * 50)

    scanner = ScannerQR()
    cerradura = ControlCerradura(pin=PIN_CERRADURA, tiempo_activacion=TIEMPO_CERRADURA)

    if not scanner.iniciar():
        print("❌ Error con cámara")
        return

    cerradura.conectar()

    ultimo_codigo = ""
    ultimo_tiempo = 0
    escaneos = 0

    try:
        while True:
            codigo = scanner.escanear()
            if codigo:
                ahora = time.time()
                if codigo == ultimo_codigo and ahora - ultimo_tiempo < DEBOUNCE_SEGUNDOS:
                    continue
                ultimo_codigo = codigo
                ultimo_tiempo = ahora
                escaneos += 1
                print(f"\n🎯 Escaneo #{escaneos}")
                procesar_qr(codigo, cerradura)
            time.sleep(0.05)   # evita saturar CPU
    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido")
    finally:
        scanner.cerrar()
        cerradura.desconectar()
        print("✅ Sistema cerrado")


if __name__ == "__main__":
    main()
