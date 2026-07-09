# QR-GYM

Sistema de gestión de clientes para gimnasios con autenticación por código QR, diseñado para Raspberry Pi Zero 2W. Incluye panel web, API de acceso y control de cerradura mediante GPIO.

<table>
  <tr>
    <td><img src="/.github/screenshot1.png" width="400"/></td>
    <td><img src="/.github/screenshot2.png" width="400"/></td>
  </tr>
  <tr>
    <td><img src="/.github/screenshot3.png" width="400"/></td>
    <td><img src="/.github/screenshot4.png" width="400"/></td>
  </tr>
</table>

## Instalación

Solo necesitas descargar y ejecutar el script de instalación automática:

```
wget https://raw.githubusercontent.com/doro098/qr-gym-v2/main/bootstrap.sh
chmod +x bootstrap.sh
./bootstrap.sh
```

El script:

- Instala todas las dependencias del sistema (Python, OpenCV, GPIO, ZBar, etc.)
- Clona el repositorio en `~/qr-gym-v2`
- Crea un entorno virtual e instala los paquetes Python
- Configura y habilita dos servicios systemd:
  - `qr-gym-web` (servidor Flask en el puerto 5000)
  - `qr-gym-acceso` (control de acceso por hardware)

Los servicios arrancan automáticamente en cada reinicio.

## Uso

Accede a la interfaz web desde cualquier navegador en la misma red:

```
http://<ip_de_la_pi>:5000
```

Credenciales por defecto: `admin` / `1234`

### Funcionalidades principales

- Alta, edición y eliminación de clientes
- Descarga de código QR individual (NanoID de 6 caracteres)
- Escaneo de QR para verificar acceso (hardware)
- Registro de intentos de acceso (éxito/denegado)
- Panel de estadísticas y gráficos de uso
- Listado de vencimientos próximos

## Comandos útiles

```
# Estado de los servicios
sudo systemctl status qr-gym-web
sudo systemctl status qr-gym-acceso

# Logs en tiempo real
journalctl -u qr-gym-web -f
journalctl -u qr-gym-acceso -f

# Reiniciar servicios
sudo systemctl restart qr-gym-web
sudo systemctl restart qr-gym-acceso
```

## Desarrollo

Estructura del proyecto:

- `routes/` – Rutas Flask (auth, clientes, QR, vistas)
- `db/` – Acceso a SQLite (CRUD, logs, estadísticas)
- `hardware/` – Código para cámara y GPIO (scanner, cerradura, bucle principal)
- `services/` – Lógica reutilizable (generación de QR y NanoID)
- `templates/` – Plantillas HTML

Para añadir nuevas funcionalidades, sigue el patrón existente. La configuración se centraliza en `config.py` y se puede modificar mediante variables de entorno (ver archivo).
