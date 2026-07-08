"""
Control de la cerradura eléctrica vía GPIO de la Raspberry Pi.

La cerradura se abre mientras el pin esté HIGH; vuelve a cerrar al pasar
a LOW. Solo se activa por `tiempo_activacion` segundos por llamada.
"""
import time

import RPi.GPIO as GPIO

from config import PIN_CERRADURA, TIEMPO_CERRADURA


class ControlCerradura:
    def __init__(self, pin=PIN_CERRADURA, tiempo_activacion=TIEMPO_CERRADURA):
        self.pin = pin
        self.tiempo_activacion = tiempo_activacion  # segundos que permanece HIGH
        self._configurado = False

    def conectar(self):
        """Configura el GPIO (se llama una vez al inicio)."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)
        self._configurado = True
        print(f"🔌 GPIO {self.pin} configurado como salida")
        return True

    def abrir_cerradura(self, tiempo_segundos=None):
        """
        Activa el GPIO por el tiempo especificado (o el default).
        La cerradura se abre mientras el pin esté HIGH.
        """
        if not self._configurado:
            if not self.conectar():
                return False

        tiempo = tiempo_segundos if tiempo_segundos is not None else self.tiempo_activacion
        print(f"🔓 Activando GPIO {self.pin} por {tiempo} segundos")
        GPIO.output(self.pin, GPIO.HIGH)
        time.sleep(tiempo)
        GPIO.output(self.pin, GPIO.LOW)
        print("🔒 GPIO desactivado")
        return True

    def desconectar(self):
        """Limpia la configuración GPIO."""
        if self._configurado:
            GPIO.output(self.pin, GPIO.LOW)
            GPIO.cleanup(self.pin)
            print("🔌 GPIO liberado")
