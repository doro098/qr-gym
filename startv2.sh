#!/bin/bash
# start.sh - Arranca ambos servicios y muestra logs en la misma terminal

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  QR-GYM - ARRANQUE DE SERVICIOS${NC}"
echo -e "${GREEN}========================================${NC}"

# Activar entorno virtual si existe
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No se encontró .venv, usando python del sistema${NC}"
fi

# Verificar que los archivos existan
if [ ! -f "app.py" ]; then
    echo "Error: app.py no encontrado"
    exit 1
fi
if [ ! -f "hardware/acceso.py" ]; then
    echo "Error: hardware/acceso.py no encontrado"
    exit 1
fi

# Función para matar procesos al salir (Ctrl+C)
cleanup() {
    echo -e "\n${YELLOW}Deteniendo servicios...${NC}"
    kill $WEB_PID $ACCESO_PID 2>/dev/null || true
    wait $WEB_PID $ACCESO_PID 2>/dev/null || true
    echo -e "${GREEN}Servicios detenidos.${NC}"
    exit 0
}
trap cleanup SIGINT SIGTERM

# Iniciar servicios en background
echo -e "${YELLOW}▶ Iniciando app web...${NC}"
python app.py > web.log 2>&1 &
WEB_PID=$!
echo -e "   Web PID: $WEB_PID (logs en web.log)"

echo -e "${YELLOW}▶ Iniciando control de acceso...${NC}"
PYTHONPATH=. python hardware/acceso.py > acceso.log 2>&1 &
ACCESO_PID=$!
echo -e "   Acceso PID: $ACCESO_PID (logs en acceso.log)"

echo -e "${GREEN}✔ Servicios iniciados. Mostrando logs en tiempo real (Ctrl+C para salir).${NC}"
echo -e "${GREEN}========================================${NC}"

# Mostrar logs combinados de ambos servicios
tail -f web.log acceso.log
