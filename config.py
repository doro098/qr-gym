"""
Configuración centralizada del sistema.

Toda constante configurable debería vivir acá. Las variables de entorno
tienen un fallback razonable para desarrollo local; en producción conviene
definirlas explícitamente (ej: en un archivo .env o systemd Environment=).
"""
import os
from pathlib import Path

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
DB_NAME = os.getenv("GYM_DB", str(BASE_DIR / "gym.db"))

# --- Flask ---
SECRET_KEY = os.getenv("GYM_SECRET_KEY", "clave_secreta_para_mensajes_flash_y_sesiones")
FLASK_HOST = os.getenv("GYM_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("GYM_PORT", "5000"))
FLASK_DEBUG = os.getenv("GYM_DEBUG", "0") == "1"

# --- Auth admin ---
USUARIO_ADMIN = os.getenv("GYM_ADMIN_USER", "admin")
CONTRASEÑA_ADMIN = os.getenv("GYM_ADMIN_PASS", "1234")

# --- Hardware (Raspberry Pi) ---
PIN_CERRADURA = int(os.getenv("GYM_PIN_CERRADURA", "17"))
TIEMPO_CERRADURA = float(os.getenv("GYM_TIEMPO_CERRADURA", "1"))
DEBOUNCE_SEGUNDOS = float(os.getenv("GYM_DEBOUNCE", "2"))

# --- Scanner ---
SCANNER_CAM_INDEX = int(os.getenv("GYM_CAM_INDEX", "0"))
SCANNER_RESOLUCION = (
    int(os.getenv("GYM_CAM_WIDTH", "320")),
    int(os.getenv("GYM_CAM_HEIGHT", "240")),
)
SCANNER_SKIP_FRAMES = int(os.getenv("GYM_SKIP_FRAMES", "2"))

# --- QR / NanoId ---
NANOID_SIZE = 6
NANOID_ALPHABET = "_-0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
