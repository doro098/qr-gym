"""
Scanner de códigos QR/barra usando la cámara + pyzbar.

Headless: no abre ventana, solo devuelve el texto decodificado.
Diseñado para correr en una Raspberry Pi con cámara USB.
"""
import cv2
from pyzbar.pyzbar import decode

from config import SCANNER_CAM_INDEX, SCANNER_RESOLUCION, SCANNER_SKIP_FRAMES


class ScannerQR:
    def __init__(
        self,
        cam_index=SCANNER_CAM_INDEX,
        resolucion=SCANNER_RESOLUCION,
        skip_frames=SCANNER_SKIP_FRAMES,
    ):
        self.cam_index = cam_index
        self.resolucion = resolucion
        self.skip_frames = skip_frames
        self.cam = None
        self.frame_count = 0

    def iniciar(self):
        self.cam = cv2.VideoCapture(self.cam_index)
        ancho, alto = self.resolucion
        self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, ancho)
        self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, alto)
        self.cam.set(cv2.CAP_PROP_FPS, 10)  # limitamos fps para ahorrar CPU

        if not self.cam.isOpened():
            print("❌ No se pudo abrir la cámara")
            return False

        print(f"📷 Cámara iniciada a {ancho}x{alto} (headless)")
        return True

    def _detectar(self, frame):
        """
        Detecta cualquier código (QR, DataMatrix, etc.) usando pyzbar.
        Devuelve el texto decodificado o None.
        """
        # pyzbar funciona mejor en escala de grises
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        codigos = decode(gray)
        if codigos:
            # Tomamos el primer código detectado
            return codigos[0].data.decode('utf-8')
        return None

    def escanear(self):
        if not self.cam or not self.cam.isOpened():
            return None

        self.frame_count += 1
        # Saltamos frames para mantener los 2-3 fps
        if self.frame_count % self.skip_frames != 0:
            self.cam.grab()
            return None

        ret, frame = self.cam.read()
        if not ret:
            return None

        # Como ya capturamos en 320x240, no hace falta redimensionar
        return self._detectar(frame)

    def cerrar(self):
        if self.cam and self.cam.isOpened():
            self.cam.release()
        print("📷 Cámara cerrada")
