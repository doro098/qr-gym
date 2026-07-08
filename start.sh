#!/bin/bash
# Script de inicio para QR-GYM (Raspberry Pi / Debian)
# Busca la URL del repositorio en este orden:
#   1. archivo repo.url
#   2. variable de entorno REPO_URL_ENV
#   3. argumento $1
#   4. si no, y estamos en un repo git, hace git pull
#   5. si no, usa el directorio actual

set -e  # Detener en cualquier error

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  QR-GYM - INSTALADOR Y ARRANQUE${NC}"
echo -e "${GREEN}========================================${NC}"

# ============================================================
# 1. DETERMINAR URL DEL REPOSITORIO
# ============================================================
REPO_URL=""

# 1a) Leer desde archivo repo.url si existe
if [ -f "repo.url" ]; then
    REPO_URL=$(cat repo.url | tr -d '[:space:]')
    echo -e "${YELLOW}▶ URL del repositorio leída desde repo.url: $REPO_URL${NC}"
fi

# 1b) Si no, usar variable de entorno
if [ -z "$REPO_URL" ] && [ -n "$REPO_URL_ENV" ]; then
    REPO_URL="$REPO_URL_ENV"
    echo -e "${YELLOW}▶ URL del repositorio leída desde variable REPO_URL_ENV: $REPO_URL${NC}"
fi

# 1c) Si no, usar argumento de línea de comandos
if [ -z "$REPO_URL" ] && [ -n "$1" ]; then
    REPO_URL="$1"
    echo -e "${YELLOW}▶ URL del repositorio desde argumento: $REPO_URL${NC}"
fi

# ============================================================
# 2. GESTIÓN DEL REPOSITORIO (clonar o actualizar)
# ============================================================
# CLAVE: primero chequeamos si YA estamos parados dentro de un
# repositorio git. Si es así, actualizamos en el lugar (git pull)
# en vez de intentar clonar/entrar a una subcarpeta con el mismo
# nombre (eso era lo que generaba el "qr-gym-v2/qr-gym-v2" anidado).
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${YELLOW}▶ Ya estamos dentro de un repositorio git ($(pwd)). Actualizando (git pull)...${NC}"
    git pull
elif [ -n "$REPO_URL" ]; then
    REPO_DIR=$(basename "$REPO_URL" .git)
    if [ -d "$REPO_DIR" ]; then
        echo -e "${YELLOW}▶ Actualizando repositorio existente en $REPO_DIR...${NC}"
        cd "$REPO_DIR"
        git pull
    else
        echo -e "${YELLOW}▶ Clonando repositorio desde $REPO_URL...${NC}"
        git clone "$REPO_URL"
        cd "$REPO_DIR"
    fi
else
    echo -e "${YELLOW}▶ No se pasó URL y no es un repositorio git. Usando directorio actual.${NC}"
fi

# ============================================================
# 3. ACTUALIZAR SISTEMA E INSTALAR PAQUETES APT
# ============================================================
echo -e "${YELLOW}▶ Actualizando repositorios apt...${NC}"
sudo apt update -qq && sudo apt upgrade -y -qq
echo -e "${GREEN}✔ Sistema actualizado.${NC}"

if [ -f "system-requirements.txt" ]; then
    echo -e "${YELLOW}▶ Instalando paquetes del sistema desde system-requirements.txt...${NC}"
    # Filtramos líneas vacías y comentarios (#), y limpiamos \r (CRLF)
    # por si el archivo fue editado en Windows en algún momento
    PACKAGES=$(tr -d '\r' < system-requirements.txt | grep -vE '^\s*(#|$)' | tr '\n' ' ')
    if [ -n "$PACKAGES" ]; then
        sudo apt install -y $PACKAGES
        echo -e "${GREEN}✔ Paquetes del sistema instalados.${NC}"
    else
        echo -e "${YELLOW}⚠️  system-requirements.txt está vacío, omitiendo.${NC}"
    fi
else
    echo -e "${RED}✘ No se encontró system-requirements.txt en $(pwd)${NC}"
    exit 1
fi

# ============================================================
# 4. CREAR ENTORNO VIRTUAL (hereda paquetes del sistema)
# ============================================================
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}▶ Creando entorno virtual en $VENV_DIR (con --system-site-packages)...${NC}"
    python3 -m venv --system-site-packages "$VENV_DIR"
else
    echo -e "${YELLOW}▶ Entorno virtual ya existe en $VENV_DIR.${NC}"
fi

# ============================================================
# 5. INSTALAR DEPENDENCIAS PIP FALTANTES
# ============================================================
echo -e "${YELLOW}▶ Instalando dependencias pip desde requirements.txt...${NC}"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo -e "${YELLOW}⚠️  No se encontró requirements.txt, omitiendo.${NC}"
fi
deactivate

echo -e "${GREEN}✔ Todas las dependencias instaladas correctamente.${NC}"

# ============================================================
# 6. PREGUNTAR SI ARRANCAR SERVICIOS
# ============================================================
echo -e "${GREEN}========================================${NC}"
echo -e "¿Deseas iniciar los servicios ahora?"
echo -e "  1) App web (Flask) en segundo plano"
echo -e "  2) Control de acceso (hardware/acceso.py) en primer plano"
echo -e "  3) Ambos (web en segundo plano, acceso en primer plano)"
echo -e "  4) Ambos en segundo plano (web + acceso)"
echo -e "  5) No iniciar ahora (solo instalar)"
read -p "Selecciona una opción [1-5]: " OPCION

source "$VENV_DIR/bin/activate"

case $OPCION in
    1)
        echo -e "${YELLOW}▶ Iniciando app web en segundo plano con nohup...${NC}"
        nohup python app.py > web.log 2>&1 &
        echo -e "${GREEN}✔ App web iniciada (PID $!). Logs en web.log${NC}"
        echo -e "Puedes acceder en http://localhost:5000"
        ;;
    2)
        echo -e "${YELLOW}▶ Iniciando control de acceso...${NC}"
        echo -e "Presiona Ctrl+C para detener."
        python hardware/acceso.py
        ;;
    3)
        echo -e "${YELLOW}▶ Iniciando app web en segundo plano...${NC}"
        nohup python app.py > web.log 2>&1 &
        WEB_PID=$!
        echo -e "${GREEN}✔ App web iniciada (PID $WEB_PID). Logs en web.log${NC}"
        echo -e "Puedes acceder en http://localhost:5000"
        echo -e ""
        echo -e "${YELLOW}▶ Iniciando control de acceso en primer plano...${NC}"
        echo -e "Presiona Ctrl+C para detener."
        python hardware/acceso.py
        # Cuando termine, matar la web si sigue corriendo
        kill $WEB_PID 2>/dev/null || true
        ;;
    4)
        echo -e "${YELLOW}▶ Iniciando app web en segundo plano...${NC}"
        nohup python app.py > web.log 2>&1 &
        WEB_PID=$!
        echo -e "${GREEN}✔ App web iniciada (PID $WEB_PID). Logs en web.log${NC}"
        echo -e ""
        echo -e "${YELLOW}▶ Iniciando control de acceso en segundo plano...${NC}"
        nohup python hardware/acceso.py > acceso.log 2>&1 &
        ACCESO_PID=$!
        echo -e "${GREEN}✔ Control de acceso iniciado (PID $ACCESO_PID). Logs en acceso.log${NC}"
        echo -e "Para detener ambos servicios:"
        echo -e "  kill $WEB_PID $ACCESO_PID"
        ;;
    5)
        echo -e "${GREEN}Instalación completa. Para iniciar manualmente:${NC}"
        echo -e "  source .venv/bin/activate"
        echo -e "  python app.py          # web"
        echo -e "  python hardware/acceso.py  # control de acceso"
        ;;
    *)
        echo -e "${RED}Opción no válida. Saliendo.${NC}"
        deactivate
        exit 1
        ;;
esac

deactivate
echo -e "${GREEN}========================================${NC}"
