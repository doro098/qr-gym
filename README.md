# README.md – QR-GYM

Sistema de control de acceso por código QR para gimnasios.  
**Web app** en Flask para la gestión de clientes y generación de QRs (contenido = NanoId de 6 caracteres).  
**Módulo hardware** para Raspberry Pi que lee el QR con una cámara USB, verifica la vigencia del cliente en una base de datos SQLite y acciona una cerradura eléctrica vía GPIO.

---

## 📁 Estructura del proyecto

```
qr-gym/
├── app.py                          # Entry point de la aplicación Flask (factory + run)
├── config.py                       # Configuración centralizada (variables de entorno)
├── requirements.txt                # Dependencias pip (solo nanoid)
├── system-requirements.txt         # Paquetes del sistema (apt)
├── start.sh                        # Script de instalación y arranque (todo en uno)
├── .gitignore                      # Archivos ignorados por Git
├── README.md                       # Este documento
│
├── db/                             # Acceso a la base de datos SQLite
│   ├── __init__.py                 # Re-exporta todo para importar desde `db`
│   ├── connection.py               # get_db_connection() y init_db() (crea tablas)
│   ├── nanoid_util.py              # Generación de NanoIds únicos de 6 chars
│   ├── repo_clientes.py            # CRUD de clientes, búsquedas, verificación de acceso
│   ├── repo_logs.py                # Registro y consulta de eventos (logs)
│   └── estadisticas.py             # Consultas agregadas para dashboard y gráficos
│
├── routes/                         # Rutas de la aplicación web (Flask)
│   ├── __init__.py                 # register_all(app) – registra todos los módulos
│   ├── auth.py                     # /login, /logout y decorador `requiere_login`
│   ├── clientes.py                 # CRUD de clientes: listar, nuevo, editar, eliminar, vencimientos
│   ├── export.py                   # /exportar_csv – descarga CSV de todos los clientes
│   ├── qr.py                       # /descargar_qr/<id> – genera y descarga el QR del cliente
│   └── vistas.py                   # /inicio, /actividad, /estadisticas (páginas de solo lectura)
│
├── services/                       # Lógica de negocio reutilizable (sin dependencia de Flask)
│   ├── __init__.py
│   └── qr_service.py               # Generación de imagen QR a partir de un NanoId (BytesIO)
│
├── hardware/                       # Código específico para Raspberry Pi
│   ├── __init__.py
│   ├── scanner.py                  # Clase ScannerQR – captura y decodifica códigos QR con pyzbar
│   ├── cerradura.py                # Clase ControlCerradura – control GPIO (abrir/cerrar)
│   └── acceso.py                   # Bucle principal del sistema de acceso (orquesta scanner, DB, logs y cerradura)
│
└── templates/                      # Plantillas HTML (Jinja2)
    ├── login.html
    ├── inicio.html
    ├── clientes.html
    ├── editar_cliente.html
    ├── nuevo_cliente.html
    ├── vencimientos.html
    ├── actividad.html
    └── estadisticas.html
```

---

## 📄 Descripción detallada de cada archivo

### 🔹 Raíz del proyecto

| Archivo | Propósito |
| :------ | :-------- |
| `app.py` | Punto de entrada de la aplicación web. Crea la app Flask, inicializa la base de datos (crea tablas) y registra todas las rutas. |
| `config.py` | Configuración centralizada: rutas de la DB, credenciales, pines GPIO, tiempos, resolución de cámara, etc. Todas las variables pueden ser sobrescritas con variables de entorno. |
| `requirements.txt` | Dependencias de Python que se instalan con `pip` dentro del entorno virtual. Solo contiene `nanoid` (el resto se instala vía `apt`). |
| `system-requirements.txt` | Lista de paquetes del sistema que se instalan con `apt` (Python, Flask, OpenCV, pyzbar, RPi.GPIO, librerías, herramientas de compilación, etc.). |
| `start.sh` | Script todo‑en‑uno: clona/actualiza el repositorio, instala paquetes del sistema, crea el entorno virtual, instala dependencias pip y ofrece un menú para arrancar los servicios (web y/o acceso). |
| `.gitignore` | Ignora archivos innecesarios: `__pycache__/`, `.venv/`, `gym.db`, logs, etc. |

### 🔹 Carpeta `db/` – Acceso a datos

| Archivo | Propósito |
| :------ | :-------- |
| `__init__.py` | Re‑exporta todas las funciones públicas para que se puedan importar con `from db import ...`. |
| `connection.py` | Gestiona la conexión a SQLite (`get_db_connection()`) y crea las tablas `clientes` y `logs` con sus índices. **No hay migraciones**: la columna `codigo_qr` se crea directamente. |
| `nanoid_util.py` | Genera NanoIds de 6 caracteres usando `secrets` (o la librería `nanoid` si está instalada). La función `generar_codigo_qr_unico()` verifica la unicidad en la base de datos. |
| `repo_clientes.py` | CRUD de clientes: `crear_cliente`, `actualizar_cliente`, `eliminar_cliente`. Funciones de búsqueda por ID o por `codigo_qr`. Verificación de acceso (`cliente_tiene_acceso`) comparando la fecha de vencimiento con la fecha actual. |
| `repo_logs.py` | Registra eventos (`registrar_evento`) con tipo, descripción, resultado, cliente_id y usuario_admin. Consulta el historial (`obtener_historial`). |
| `estadisticas.py` | Consultas agregadas para el dashboard y la página de estadísticas: total de clientes, accesos de hoy, accesos del mes, denegados, clientes vencidos, hora pico, accesos por día de semana, por hora, top 10 clientes, etc. |

### 🔹 Carpeta `routes/` – Controladores web

| Archivo | Propósito |
| :------ | :-------- |
| `__init__.py` | Función `register_all(app)` que registra todos los módulos de rutas. |
| `auth.py` | Login (`/login`), logout (`/logout`) y el decorador `requiere_login` que protege las rutas que requieren autenticación. |
| `clientes.py` | Rutas CRUD para clientes: listar (`/`), nuevo (`/nuevo`), editar (`/editar/<id>`), eliminar (`/eliminar/<id>` – solo POST), y vencimientos próximos (`/vencimientos`). |
| `export.py` | Ruta `/exportar_csv` que descarga todos los clientes en formato CSV. |
| `qr.py` | Ruta `/descargar_qr/<id>` que obtiene el `codigo_qr` del cliente, llama a `qr_service.generar_qr_descarga()` y devuelve la imagen PNG. |
| `vistas.py` | Rutas de solo lectura: `/inicio` (dashboard), `/actividad` (historial de logs), `/estadisticas` (página con gráficos Chart.js). |

### 🔹 Carpeta `services/` – Lógica reusable

| Archivo | Propósito |
| :------ | :-------- |
| `__init__.py` | Marca el directorio como paquete. |
| `qr_service.py` | Función `generar_qr_descarga(codigo_qr)` que crea un QR con el texto `codigo_qr` usando la librería `qrcode` y devuelve un `BytesIO` listo para ser enviado como archivo. |

### 🔹 Carpeta `hardware/` – Código para Raspberry Pi

| Archivo | Propósito |
| :------ | :-------- |
| `__init__.py` | Marca el directorio como paquete. |
| `scanner.py` | Clase `ScannerQR`: inicializa la cámara (`cv2.VideoCapture`), captura frames, decodifica códigos QR usando `pyzbar` y devuelve el texto decodificado. Configurable: índice de cámara, resolución, skip_frames. |
| `cerradura.py` | Clase `ControlCerradura`: configura el GPIO, activa la cerradura (pone el pin en HIGH) durante un tiempo determinado y lo desactiva. Usa `RPi.GPIO`. |
| `acceso.py` | **Bucle principal del control de acceso**. Orquesta: 1) ScannerQR lee el QR, 2) valida que sea un NanoId de 6 caracteres, 3) verifica en la DB si el cliente tiene acceso, 4) registra el evento (EXITO/DENEGADO/ERROR), 5) si es EXITO, abre la cerradura. Incluye debounce para evitar lecturas repetidas. |

### 🔹 Carpeta `templates/` – Plantillas HTML

Todos los archivos `.html` utilizan Jinja2 y están enlazados con las rutas mediante `url_for`. Incluyen estilos CSS personalizados y Chart.js para gráficos.

---

## 🔄 Diagrama de flujo (flujo principal)

A continuación se muestran los dos flujos principales del sistema.

### 📌 Flujo del hardware (acceso.py)

```
[Inicio main()]
   │
   ├─► Inicializar ScannerQR
   ├─► Inicializar ControlCerradura
   │
   └─► Bucle infinito
         │
         ├─► scanner.escanear()  →  ¿QR detectado?
         │         │
         │         └─► NO  → esperar 50 ms y continuar
         │
         └─► SÍ → Verificar debounce (mismo código en <2 s? → ignorar)
               │
               ├─► procesar_qr(codigo)
               │     │
               │     ├─► codigo_es_valido? (6 chars alfanum + _ -)
               │     │     │
               │     │     ├─► NO → registrar_evento(ERROR) y salir
               │     │     │
               │     │     └─► SÍ → verificar_acceso(codigo)
               │     │             │
               │     │             ├─► cliente_tiene_acceso_por_codigo()
               │     │             │     │
               │     │             │     ├─► get_cliente_por_codigo_qr() → ¿existe?
               │     │             │     │     └─► NO → (False, None)
               │     │             │     │
               │     │             │     └─► SÍ → comprobar vencimiento (>= hoy)
               │     │             │           │
               │     │             │           ├─► SÍ → (True, cliente)
               │     │             │           └─► NO → (False, cliente)
               │     │             │
               │     │             └─► Retorna (permitido, mensaje, cliente_id)
               │     │
               │     ├─► registrar_evento(tipo=ACCESO, resultado=EXITO/DENEGADO/ERROR)
               │     │
               │     └─► Si permitido == True → cerradura.abrir_cerradura() (HIGH por 1 s)
               │
               └─► Continuar bucle
```

### 📌 Flujo web (creación de cliente y descarga de QR)

```
[Usuario] → /nuevo (GET) → Muestra formulario
          → POST (nombre, apellido, teléfono, vencimiento)
                │
                ├─► Validar nombre (obligatorio)
                │
                ├─► crear_cliente(nombre, ...)
                │     │
                │     ├─► generar_codigo_qr_unico()
                │     │     │
                │     │     ├─► _generar_nanoid() (6 chars)
                │     │     ├─► Verificar unicidad en DB (hasta 10 intentos)
                │     │     └─► Devuelve NanoId único
                │     │
                │     └─► INSERT en clientes (incluye codigo_qr)
                │
                ├─► registrar_evento(SISTEMA, "Nuevo cliente creado")
                │
                └─► Redirigir a lista de clientes
```

**Descarga del QR**:
```
[Usuario] → /descargar_qr/<id>
                │
                ├─► get_cliente_por_id(id) → si no existe, flash error
                │
                ├─► Obtener codigo_qr del cliente
                │
                ├─► generar_qr_descarga(codigo_qr)
                │     │
                │     ├─► qrcode.QRCode(box_size=10, border=4)
                │     ├─► add_data(codigo_qr)
                │     ├─► make_image()
                │     └─► guardar en BytesIO como PNG
                │
                └─► send_file(buffer, as_attachment, nombre_cliente_{id}_{nombre}_{codigo}.png)
```

---

## 🚀 Instalación y ejecución

### Prerrequisitos
- Raspberry Pi (o cualquier sistema Debian/Ubuntu) con Python 3.9+.
- Cámara USB compatible con OpenCV.
- Conexión a Internet para descargar paquetes.

### Pasos

1. **Clonar el repositorio** (o descargar los archivos):
   ```bash
   git clone https://github.com/tu-usuario/qr-gym.git
   cd qr-gym
   ```

2. **Ejecutar el script de instalación y arranque**:
   ```bash
   chmod +x start.sh
   ./start.sh
   ```
   - Si quieres que el script clone/actualice automáticamente tu repositorio, crea un archivo `repo.url` con la URL de tu repo o pásala como argumento:
     ```bash
     ./start.sh https://github.com/tu-usuario/qr-gym.git
     ```
   - El script:
     - Actualiza el sistema (`apt update && apt upgrade`).
     - Instala todos los paquetes de `system-requirements.txt`.
     - Crea un entorno virtual `.venv` con `--system-site-packages`.
     - Instala `nanoid` desde `requirements.txt`.
     - Muestra un menú para iniciar los servicios.

3. **Opcional – Iniciar manualmente**:
   ```bash
   source .venv/bin/activate
   python app.py               # Servidor web en http://0.0.0.0:5000
   python hardware/acceso.py   # Control de acceso (necesita cámara y GPIO)
   ```

---

## ⚙️ Configuración (variables de entorno)

Todas las opciones se pueden sobrescribir con variables de entorno. Ejemplo:
```bash
export GYM_ADMIN_PASS="miPasswordSegura"
export GYM_PIN_CERRADURA=18
export GYM_DEBUG=1
python app.py
```

| Variable | Default | Descripción |
| :------- | :------ | :---------- |
| `GYM_DB` | `./gym.db` | Ruta a la base de datos SQLite |
| `GYM_SECRET_KEY` | `clave_secreta_...` | Clave secreta de Flask |
| `GYM_HOST` | `0.0.0.0` | Host de escucha |
| `GYM_PORT` | `5000` | Puerto |
| `GYM_DEBUG` | `0` | Modo debug (1 para activar) |
| `GYM_ADMIN_USER` | `admin` | Usuario del panel web |
| `GYM_ADMIN_PASS` | `1234` | Contraseña del panel web |
| `GYM_PIN_CERRADURA` | `17` | GPIO (BCM) de la cerradura |
| `GYM_TIEMPO_CERRADURA` | `1` | Segundos que permanece abierta |
| `GYM_DEBOUNCE` | `2` | Segundos de debounce del scanner |
| `GYM_CAM_INDEX` | `0` | Índice de la cámara (normalmente 0) |
| `GYM_CAM_WIDTH` | `320` | Ancho de captura (píxeles) |
| `GYM_CAM_HEIGHT` | `240` | Alto de captura |
| `GYM_SKIP_FRAMES` | `2` | Frames a saltar para ahorrar CPU |

---

## 🧪 Notas técnicas

- **NanoId**: se usa como identificador único para los QRs (6 caracteres). La entropía es suficiente para un gimnasio (colisiones esperadas > 1 en 50M de códigos). La generación usa `secrets` (CSPRNG) o la librería `nanoid` si está disponible.
- **Base de datos**: SQLite con dos tablas: `clientes` (nombre, apellido, teléfono, vencimiento, codigo_qr) y `logs` (fecha, tipo, descripción, resultado, cliente_id, usuario_admin).
- **Seguridad**: las rutas web (excepto `/login`) están protegidas por el decorador `requiere_login`. Las contraseñas se almacenan en texto plano en la configuración (se recomienda usar variables de entorno en producción).
- **Hardware**: el módulo `hardware/acceso.py` está diseñado para ejecutarse en una Raspberry Pi. Si se ejecuta en otro sistema, fallará al importar `RPi.GPIO`. Para pruebas sin hardware, se puede comentar esa importación y simular la cerradura.
- **Logs**: todos los eventos (accesos, inicios de sesión, creación/edición de clientes) se registran con fecha y hora en la tabla `logs`. La página `/actividad` muestra los últimos 200 eventos.

---

## 🛠️ Dependencias

### Paquetes del sistema (`system-requirements.txt`)
Se instalan con `apt` y proporcionan Python, Flask, OpenCV, pyzbar, RPi.GPIO, librerías de compresión de imágenes, etc.

### Dependencias pip (`requirements.txt`)
- `nanoid==2.0.0` – generación de identificadores únicos.

---

## 📝 Licencia

Este proyecto es de código abierto y puede ser utilizado y modificado libremente.

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un *issue* o un *pull request* en el repositorio.

---

¡Disfruta de tu sistema de acceso QR! 🚀