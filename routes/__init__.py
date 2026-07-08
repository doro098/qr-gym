"""
Paquete routes: rutas Flask, agrupadas por dominio.

Cada módulo expone `register(app)` que define las rutas contra `app`.
Esto evita Blueprints (que agregarían prefijos a url_for) y mantiene
compatibilidad con templates existentes.

Módulos:
- auth:     login, logout, decorador requiere_login
- clientes: listar, editar, nuevo, eliminar, vencimientos
- qr:       /descargar_qr/<id>
- export:   /exportar_csv
- vistas:   inicio, actividad, estadisticas
"""
from routes import auth, clientes, export, qr, vistas


def register_all(app):
    """Registra todas las rutas en la app Flask."""
    auth.register(app)
    clientes.register(app)
    qr.register(app)
    export.register(app)
    vistas.register(app)
