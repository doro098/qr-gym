#!/usr/bin/env python3
"""
Bucle principal de control de acceso.
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DEBOUNCE_SEGUNDOS, PIN_CERRADURA, TIEMPO_CERRADURA
from db.repo_clientes import verificar_acceso_completo
from db.repo_logs import registrar_evento
from hardware.cerradura import ControlCerradura
from hardware.scanner import ScannerQR

LONGITUD_NANOID = 6


def codigo_es_valido(codigo):
    if not codigo:
        return False
    codigo = codigo.strip()
    if len(codigo) != LONGITUD_NANOID:
        return False
    return all(c.isalnum() or c in "_-" for c in codigo)


def procesar_qr(codigo, cerradura, estado_anterior):
    """
    Evalúa el QR, muestra el resultado en consola, registra log SOLO si el estado cambia,
    y abre la puerta si el acceso es permitido.
    """
    if not codigo_es_valido(codigo):
        nuevo_permitido = False
        nuevo_mensaje = f"QR inválido: {codigo[:60]}"
        nuevo_resultado = "ERROR"
        cliente_id = None
        disciplina = None
    else:
        permitido, mensaje, cliente_id, disciplina = verificar_acceso_completo(codigo.strip())
        nuevo_permitido = permitido
        nuevo_mensaje = mensaje
        nuevo_resultado = "EXITO" if permitido else "DENEGADO"

    # Mostrar en consola (se ve en journalctl)
    icono = "✅" if nuevo_permitido else "⛔"
    print(f"{icono} {nuevo_mensaje}")

    # Lógica de estado para evitar logs duplicados
    anterior = estado_anterior.get(codigo)  # (permitido, disciplina)
    if anterior is None or (anterior[0] != nuevo_permitido or anterior[1] != disciplina):
        registrar_evento(
            tipo="ACCESO",
            descripcion=nuevo_mensaje,
            resultado=nuevo_resultado,
            cliente_id=cliente_id,
            disciplina=disciplina,
        )
        estado_anterior[codigo] = (nuevo_permitido, disciplina)

    # Abrir la puerta si está permitido (siempre, aunque no se registre log)
    if nuevo_permitido:
        cerradura.abrir_cerradura()


def main():
    print("=" * 50)
    print("  CONTROL DE ACCESO - GIMNASIO (GPIO / HEADLESS)")
    print("  QR basado en NanoId de 6 chars + disciplinas")
    print("=" * 50)
    print(f"GPIO cerradura : {PIN_CERRADURA}")
    print(f"Debounce       : {DEBOUNCE_SEGUNDOS} s")
    print("Para salir presiona Ctrl+C")
    print("-" * 50)

    scanner = None
    cerradura = None

    try:
        scanner = ScannerQR()
        if not scanner.iniciar():
            print("❌ Error con cámara")
            return

        cerradura = ControlCerradura(pin=PIN_CERRADURA, tiempo_activacion=TIEMPO_CERRADURA)
        cerradura.conectar()

        ultimo_codigo = ""
        ultimo_tiempo = 0
        escaneos = 0
        estado_anterior = {}  # codigo -> (permitido, disciplina)

        while True:
            codigo = scanner.escanear()
            if codigo:
                ahora = time.time()
                # Debounce configurable (desde config.py)
                if DEBOUNCE_SEGUNDOS > 0 and codigo == ultimo_codigo and (ahora - ultimo_tiempo) < DEBOUNCE_SEGUNDOS:
                    continue
                ultimo_codigo = codigo
                ultimo_tiempo = ahora
                escaneos += 1
                print(f"\n🎯 Escaneo #{escaneos}")
                procesar_qr(codigo, cerradura, estado_anterior)
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n⚠️ Interrumpido")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
    finally:
        if scanner:
            scanner.cerrar()
        if cerradura:
            cerradura.desconectar()
        print("✅ Sistema cerrado")


if __name__ == "__main__":
    main()
