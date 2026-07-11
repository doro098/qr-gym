#!/usr/bin/env python3
"""
Punto de acceso Wi‑Fi con formulario web y escáner QR para configurar la red.
Se ejecuta al arranque si no hay conexión Wi‑Fi.
Escucha indefinidamente hasta que se configure la red.
"""

import os
import re
import sys
import time
import socket
import threading
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Añadir ruta del proyecto para importar scanner
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hardware.scanner import ScannerQR

# Configuración del AP (sin cambios)
AP_SSID = "QR-GYM-SETUP"
AP_PASSWORD = ""  # Sin contraseña (o pon una si quieres)
AP_INTERFACE = "wlan0"
AP_IP = "192.168.4.1"
AP_NETMASK = "255.255.255.0"
DHCP_RANGE = "192.168.4.2,192.168.4.20,255.255.255.0,24h"

# Archivos de configuración (ya no usaremos wpa_supplicant)
HOSTAPD_CONF = "/etc/hostapd/hostapd.conf"
DNSMASQ_CONF = "/etc/dnsmasq.conf"
# WPA_SUPPLICANT ya no se usa

# Interfaz Wi‑Fi
WLAN_INTERFACE = "wlan0"

# Variables globales
wifi_credentials = None
credentials_event = threading.Event()
scanner = None


def wifi_conectado():
    """Devuelve True si la interfaz inalámbrica está conectada a una red usando nmcli."""
    # Usamos nmcli para obtener el estado de la conexión activa
    resultado = os.popen("nmcli -t -f DEVICE,TYPE,STATE device status | grep wlan0").read().strip()
    # Buscamos "connected" en el estado
    if "connected" in resultado:
        return True
    # También podríamos comprobar si hay una IP
    ip = os.popen(f"ip -4 addr show {WLAN_INTERFACE} | grep inet").read().strip()
    return bool(ip)


def parse_wifi_qr(data):
    """Parsea QR Wi‑Fi: WIFI:T:WPA;S:nombre;P:contraseña;;"""
    ssid_match = re.search(r"S:([^;]+)", data)
    pwd_match = re.search(r"P:([^;]+)", data)
    if ssid_match and pwd_match:
        return ssid_match.group(1), pwd_match.group(1)
    return None, None


def configurar_wifi(ssid, password):
    """
    Configura la red Wi‑Fi usando nmcli.
    Borra cualquier conexión previa con el mismo SSID y crea una nueva.
    """
    # Escapar posibles caracteres especiales en SSID y password (nmcli lo maneja bien con comillas)
    # Usamos comillas simples para evitar expansión de shell
    comando_borrar = f"sudo nmcli connection delete '{ssid}' 2>/dev/null"
    os.system(comando_borrar)

    comando_conectar = f"sudo nmcli device wifi connect '{ssid}' password '{password}'"
    resultado = os.system(comando_conectar)

    if resultado == 0:
        print(f"✅ Wi‑Fi configurada con SSID: {ssid} (NetworkManager)")
        return True
    else:
        print(f"❌ Error al configurar Wi‑Fi con nmcli (código {resultado})")
        return False


def iniciar_ap():
    """Configura y arranca el punto de acceso (hostapd + dnsmasq). (sin cambios)"""
    print("📶 Configurando punto de acceso...")

    # Configurar hostapd
    with open(HOSTAPD_CONF, "w") as f:
        f.write(f"""interface={AP_INTERFACE}
driver=nl80211
ssid={AP_SSID}
hw_mode=g
channel=6
wmm_enabled=1
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
""")
    if AP_PASSWORD:
        with open(HOSTAPD_CONF, "a") as f:
            f.write(f"wpa=2\nwpa_passphrase={AP_PASSWORD}\nwpa_key_mgmt=WPA-PSK\n")

    # Configurar dnsmasq (DHCP)
    with open(DNSMASQ_CONF, "w") as f:
        f.write(f"""interface={AP_INTERFACE}
dhcp-range={DHCP_RANGE}
dhcp-option=3,{AP_IP}
dhcp-option=6,{AP_IP}
server=8.8.8.8
no-resolv
""")

    # Asignar IP estática a la interfaz
    os.system(f"sudo ip addr flush dev {AP_INTERFACE}")
    os.system(f"sudo ip addr add {AP_IP}/24 dev {AP_INTERFACE}")
    os.system(f"sudo ip link set {AP_INTERFACE} up")

    # Arrancar servicios
    os.system("sudo systemctl unmask hostapd")
    os.system("sudo systemctl enable hostapd")
    os.system("sudo systemctl start hostapd")
    os.system("sudo systemctl enable dnsmasq")
    os.system("sudo systemctl start dnsmasq")

    print(f"✅ AP '{AP_SSID}' activo en {AP_IP}")


def detener_ap():
    """Detiene el punto de acceso y restaura la configuración de red."""
    print("🔄 Deteniendo AP...")
    os.system("sudo systemctl stop hostapd")
    os.system("sudo systemctl stop dnsmasq")
    os.system("sudo systemctl disable hostapd")
    os.system("sudo systemctl disable dnsmasq")
    os.system(f"sudo ip addr flush dev {AP_INTERFACE}")
    # Reiniciar NetworkManager para que retome el control de la interfaz
    os.system("sudo systemctl restart NetworkManager")
    print("✅ AP detenido, NetworkManager reiniciado.")


# ---------- Servidor HTTP con formulario (sin cambios) ----------
class SetupHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silenciar logs

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>Configurar Wi‑Fi</title>
<style>
body { font-family: sans-serif; max-width: 500px; margin: 2rem auto; padding: 1rem; background: #f5f5f5; }
h1 { color: #195083; }
label { font-weight: bold; }
input { width: 100%; padding: 8px; margin: 8px 0 16px; border: 1px solid #ccc; border-radius: 4px; }
button { background: #195083; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
button:hover { background: #0f3a60; }
</style>
</head>
<body>
<h1>Configuración de Wi‑Fi</h1>
<p>Introduce los datos de tu red para conectar la Raspberry Pi.</p>
<form method="POST" action="/">
<label>SSID (nombre de la red):</label><input type="text" name="ssid" required>
<label>Contraseña:</label><input type="password" name="password" required>
<button type="submit">Conectar</button>
</form>
<p style="margin-top:2rem;font-size:14px;color:#666;">También puedes escanear un código QR con formato WIFI:T:...;S:...;P:...;;</p>
</body>
</html>"""
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length).decode("utf-8")
            params = urllib.parse.parse_qs(post_data)
            ssid = params.get("ssid", [""])[0].strip()
            password = params.get("password", [""])[0].strip()
            if ssid:
                global wifi_credentials
                wifi_credentials = (ssid, password)
                credentials_event.set()
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h2>¡Conectando a la red! Espera unos segundos...</h2>")
            else:
                self.send_error(400)


def servidor_web():
    server = HTTPServer(("0.0.0.0", 80), SetupHandler)
    print("🌐 Servidor web en http://192.168.4.1 (puerto 80)")
    while not credentials_event.is_set():
        server.handle_request()
    server.server_close()
    print("📡 Servidor web detenido.")


def escanear_qr():
    global wifi_credentials, scanner
    scanner = ScannerQR()
    if not scanner.iniciar():
        print("❌ No se pudo iniciar la cámara.")
        return

    print("📷 Escaneando QR de Wi‑Fi...")
    while not credentials_event.is_set():
        codigo = scanner.escanear()
        if codigo and codigo.startswith("WIFI:"):
            ssid, password = parse_wifi_qr(codigo)
            if ssid and password:
                print(f"✅ QR detectado: SSID='{ssid}'")
                wifi_credentials = (ssid, password)
                credentials_event.set()
                break
        time.sleep(0.1)
    scanner.cerrar()


def main():
    # Si ya hay conexión, salir
    if wifi_conectado():
        print("✅ Wi‑Fi ya conectada. Saliendo.")
        sys.exit(0)

    # Iniciar AP
    iniciar_ap()

    # Lanzar hilo del servidor web
    web_thread = threading.Thread(target=servidor_web, daemon=True)
    web_thread.start()

    # Lanzar hilo del escáner QR
    qr_thread = threading.Thread(target=escanear_qr, daemon=True)
    qr_thread.start()

    # Esperar hasta que se configure la red
    credentials_event.wait()

    # Obtener credenciales
    ssid, password = wifi_credentials

    # Configurar Wi‑Fi
    if configurar_wifi(ssid, password):
        # Detener AP
        detener_ap()

        # Esperar unos segundos para que la interfaz se estabilice
        time.sleep(3)

        print("✅ Configuración completada. Reiniciando para arrancar el sistema de acceso...")
        os.system("sudo reboot")
    else:
        print("❌ Falló la configuración de la red. Reiniciando para reintentar.")
        os.system("sudo reboot")


if __name__ == "__main__":
    main()
