"""
Paquete routes: rutas Flask.
"""
from routes import auth, clientes, export, qr, vistas, disciplinas


def register_all(app):
    auth.register(app)
    clientes.register(app)
    qr.register(app)
    export.register(app)
    vistas.register(app)
    disciplinas.register(app)   # NUEVO