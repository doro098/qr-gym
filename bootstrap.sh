#!/bin/bash
# =============================================================================
# QR-GYM Bootstrap - Instalación para Raspberry Pi (headless / Debian Trixie)
#
# El código ya debe estar en el directorio actual (quemado en la ISO).
# No clona el repo, pero lo convierte en repositorio Git y configura el remoto.
# Ejecutar como: ./bootstrap.sh   (puede pedir sudo para apt/systemd)
# =============================================================================
set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
info()    { echo -e "${YELLOW}▶ $*${NC}"; }
success() { echo -e "${GREEN}✔ $*${NC}"; }
error()   { echo -e "${RED}✘ $*${NC}"; }

# Directorio del proyecto (donde está este script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Usuario que ejecutará los servicios
RUN_USER="${SUDO_USER:-$USER}"
if [ "$RUN_USER" = "root" ]; then
    RUN_USER="pi"   # fallback razonable
fi

# URL del repositorio (público)
REPO_URL="https://github.com/doro098/qr-gym/"   # <--- CAMBIAR POR LA URL REAL

# =============================================================================
#  1. Instalar dependencias del sistema
# =============================================================================
info "Instalando paquetes del sistema (puede pedir contraseña sudo)..."
APT_PACKAGES=(
    python3 python3-pip python3-venv python3-dev
    python3-flask python3-qrcode python3-opencv python3-rpi.gpio
    python3-zbar
    git wget hostapd dnsmasq
    build-essential cmake pkg-config
    libzbar0
    libopenblas-dev libjpeg-dev libpng-dev libtiff-dev
    libavcodec-dev libavformat-dev libswscale-dev
    libgtk2.0-dev libcanberra-gtk3-module
)
sudo apt update -qq
sudo apt install -y "${APT_PACKAGES[@]}"
success "Paquetes del sistema instalados."

# Agregar usuario al grupo gpio (para controlar la cerradura sin root)
if ! groups "$RUN_USER" | grep -q '\bgpio\b'; then
    info "Agregando $RUN_USER al grupo gpio..."
    sudo usermod -aG gpio "$RUN_USER"
    info "⚠️  Para que los permisos GPIO funcionen, cierra sesión y vuelve a entrar (o reinicia)."
fi

# =============================================================================
#  2. Convertir el directorio en repositorio Git y configurar remoto
# =============================================================================
info "Configurando repositorio Git..."
if [ ! -d "$SCRIPT_DIR/.git" ]; then
    git init
    git remote add origin "$REPO_URL"
    success "Repositorio inicializado y remoto añadido."
else
    info "El directorio ya es un repositorio Git."
    # Asegurar que el remoto esté bien configurado
    if ! git remote get-url origin >/dev/null 2>&1; then
        git remote add origin "$REPO_URL"
    fi
fi

# Descargar objetos del remoto y actualizar el código (sin hacer merge)
info "Sincronizando con el repositorio remoto..."
git fetch origin
git reset --hard origin/main   # o la rama que uses (main/master)
success "Código sincronizado con el remoto."

# =============================================================================
#  3. Crear entorno virtual (con paquetes del sistema)
# =============================================================================
VENV_DIR="$SCRIPT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    info "Creando entorno virtual en $VENV_DIR..."
    python3 -m venv --system-site-packages "$VENV_DIR"
else
    info "El entorno virtual ya existe, se reutiliza."
fi

# =============================================================================
#  4. Instalar dependencias Python
# =============================================================================
info "Instalando dependencias Python..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    info "No se encontró requirements.txt; instalando dependencias mínimas..."
    pip install nanoid pyzbar
fi
deactivate
success "Dependencias Python instaladas."

# =============================================================================
#  5. Crear script de actualización (git pull)
# =============================================================================
info "Creando script de actualización automática..."
cat > "$SCRIPT_DIR/update.sh" <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
git pull
EOF
chmod +x "$SCRIPT_DIR/update.sh"
success "update.sh creado."

# =============================================================================
#  6. Crear y habilitar los servicios systemd
# =============================================================================
info "Generando unidades systemd..."

# --- Servicio de configuración Wi-Fi (se ejecuta antes que todo) ---
sudo tee /etc/systemd/system/wifi-setup.service > /dev/null <<EOF
[Unit]
Description=Wi-Fi setup with AP and QR/form
After=network.target
Before=qr-gym-acceso.service qr-gym-web.service

[Service]
Type=oneshot
ExecStart=$VENV_DIR/bin/python $SCRIPT_DIR/wifi_setup.py
User=root
StandardOutput=journal
StandardError=journal
RemainAfterExit=no

[Install]
WantedBy=multi-user.target
EOF

# --- Servicio de actualización (git pull, después de tener red) ---
sudo tee /etc/systemd/system/qr-gym-update.service > /dev/null <<EOF
[Unit]
Description=QR-GYM - Actualizar repositorio (git pull)
Wants=network-online.target
After=network-online.target wifi-setup.service
Before=qr-gym-web.service qr-gym-acceso.service

[Service]
Type=oneshot
User=$RUN_USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=$SCRIPT_DIR/update.sh
RemainAfterExit=no

[Install]
WantedBy=multi-user.target
EOF

# --- Servicio web (Flask) ---
sudo tee /etc/systemd/system/qr-gym-web.service > /dev/null <<EOF
[Unit]
Description=QR-GYM - App web (Flask)
After=network.target wifi-setup.service qr-gym-update.service
Requires=wifi-setup.service

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$SCRIPT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$VENV_DIR/bin/python $SCRIPT_DIR/app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# --- Servicio de control de acceso (hardware + cámara) ---
sudo tee /etc/systemd/system/qr-gym-acceso.service > /dev/null <<EOF
[Unit]
Description=QR-GYM - Control de acceso (hardware)
After=network.target wifi-setup.service qr-gym-update.service
Requires=wifi-setup.service

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$SCRIPT_DIR
Environment=PYTHONPATH=$SCRIPT_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$VENV_DIR/bin/python $SCRIPT_DIR/hardware/acceso.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

success "Unidades systemd creadas."

# =============================================================================
#  7. Programar reinicio diario a las 00:00 (cron)
# =============================================================================
info "Configurando reinicio automático a las 00:00..."
CRON_JOB="0 0 * * * /sbin/reboot"
if ! sudo crontab -l 2>/dev/null | grep -qF "$CRON_JOB"; then
    (sudo crontab -l 2>/dev/null; echo "$CRON_JOB") | sudo crontab -
    success "Reinicio programado añadido al crontab de root."
else
    info "El reinicio ya estaba programado."
fi

# =============================================================================
#  8. Habilitar y arrancar servicios
# =============================================================================
info "Recargando systemd, habilitando e iniciando servicios..."
sudo systemctl daemon-reload
sudo systemctl enable wifi-setup.service
sudo systemctl enable qr-gym-update.service
sudo systemctl enable qr-gym-web.service
sudo systemctl enable qr-gym-acceso.service

# Arrancar wifi-setup (si ya hay Wi-Fi, sale rápido)
sudo systemctl start wifi-setup.service || true

# =============================================================================
#  9. Resumen final
# =============================================================================
success "✅ ¡Instalación completada!"
echo ""
echo "📌 Comandos útiles:"
echo "  sudo systemctl status wifi-setup       # estado de la configuración Wi-Fi"
echo "  sudo systemctl status qr-gym-update    # estado del git pull"
echo "  sudo systemctl status qr-gym-web       # estado del servidor web"
echo "  sudo systemctl status qr-gym-acceso    # estado del control de acceso"
echo "  journalctl -u wifi-setup -f            # logs del setup Wi-Fi en vivo"
echo "  journalctl -u qr-gym-web -f            # logs del web en vivo"
echo "  journalctl -u qr-gym-acceso -f         # logs del acceso en vivo"
echo ""
echo "🌐 Si no hay Wi-Fi configurada, la Pi creará el AP 'QR-GYM-SETUP'."
echo "   Conéctate a él y visita http://192.168.4.1 para configurar la red."
echo ""
echo "🔄 El sistema se reiniciará automáticamente todos los días a las 00:00."
echo "   (puedes cancelarlo con 'sudo crontab -e' y eliminar la línea)"
