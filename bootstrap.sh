#!/bin/bash
# =============================================================================
#  QR-GYM Bootstrap - instala todo lo necesario y deja el sistema listo
#  para arrancar solo en cada reinicio de la Raspberry Pi.
# =============================================================================
set -e

# Colores / helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'
info()    { echo -e "${YELLOW}▶ $*${NC}"; }
success() { echo -e "${GREEN}✔ $*${NC}"; }
error()   { echo -e "${RED}✘ $*${NC}"; }

REPO_URL="https://github.com/doro098/qr-gym"
REPO_DIR="$HOME/qr-gym"
RUN_USER="${SUDO_USER:-$USER}"

# =============================================================================
#  1. Instalar dependencias del sistema
# =============================================================================
info "Instalando paquetes del sistema..."
APT_PACKAGES=(
        python3
        python3-pip
        python3-venv
        python3-dev
        python3-flask
        python3-qrcode
        python3-opencv
        python3-rpi.gpio
        git
        wget
        build-essential
        cmake
        pkg-config
        libzbar0
        libopenblas-dev
        libjpeg-dev
        libpng-dev
        libtiff-dev
        libavcodec-dev
        libavformat-dev
        libswscale-dev
        libgtk2.0-dev
        libcanberra-gtk3-module
)
sudo apt update -qq
sudo apt install -y "${APT_PACKAGES[@]}"
success "Paquetes del sistema instalados."

# El usuario que corre los servicios necesita pertenecer al grupo gpio
# para poder controlar la cerradura sin correr todo como root.
if ! groups "$RUN_USER" | grep -q '\bgpio\b'; then
    info "Agregando $RUN_USER al grupo gpio..."
    sudo usermod -aG gpio "$RUN_USER"
    info "(vas a necesitar cerrar sesión y volver a entrar, o reiniciar, para que tome efecto)"
fi

# =============================================================================
#  2. Clonar (o actualizar) el repositorio
# =============================================================================
if [ -d "$REPO_DIR/.git" ]; then
    info "El repositorio ya existe en $REPO_DIR, actualizando..."
    git -C "$REPO_DIR" pull
else
    info "Clonando repositorio en $REPO_DIR..."
    git clone "$REPO_URL" "$REPO_DIR"
fi
success "Repositorio listo en $REPO_DIR."

# =============================================================================
#  3. Crear entorno virtual e instalar dependencias Python
# =============================================================================
cd "$REPO_DIR"
VENV_DIR="$REPO_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    info "Creando entorno virtual..."
    python3 -m venv --system-site-packages "$VENV_DIR"
fi

info "Instalando dependencias pip..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
deactivate
success "Dependencias Python instaladas."

# =============================================================================
#  4. Crear y habilitar los servicios systemd
# =============================================================================
info "Generando unidades systemd..."

# --- Servicio web (Flask) ---
sudo tee /etc/systemd/system/qr-gym-web.service > /dev/null <<EOF
[Unit]
Description=QR-GYM - App web (Flask)
After=network.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$REPO_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$VENV_DIR/bin/python $REPO_DIR/app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# --- Servicio de control de acceso (hardware) ---
sudo tee /etc/systemd/system/qr-gym-acceso.service > /dev/null <<EOF
[Unit]
Description=QR-GYM - Control de acceso (hardware)
After=network.target qr-gym-web.service

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$REPO_DIR
# PYTHONPATH incluye la raíz del repo para que "from config import ..."
# funcione aunque acceso.py viva en hardware/
Environment=PYTHONPATH=$REPO_DIR
Environment=PYTHONUNBUFFERED=1
ExecStart=$VENV_DIR/bin/python $REPO_DIR/hardware/acceso.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

success "Unidades systemd creadas."

info "Recargando systemd y habilitando servicios..."
sudo systemctl daemon-reload
sudo systemctl enable --now qr-gym-web.service
sudo systemctl enable --now qr-gym-acceso.service

success "Servicios habilitados. Van a arrancar solos en cada reinicio."
echo ""
echo "Comandos útiles:"
echo "  sudo systemctl status qr-gym-web       # estado del servidor web"
echo "  sudo systemctl status qr-gym-acceso    # estado del control de acceso"
echo "  journalctl -u qr-gym-web -f            # logs del servidor web en vivo"
echo "  journalctl -u qr-gym-acceso -f         # logs del control de acceso en vivo"
echo "  sudo systemctl restart qr-gym-acceso    # reiniciar el control de acceso"
