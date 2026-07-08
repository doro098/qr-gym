"""
Punto de entrada de la aplicación Flask.

Este archivo solo crea la app, inicializa la DB y registra las rutas.
Toda la lógica de rutas vive en `routes/`, la de DB en `db/`,
y la de hardware en `hardware/`.

Para correr:
    python app.py
"""
from flask import Flask

from config import FLASK_DEBUG, FLASK_HOST, FLASK_PORT, SECRET_KEY
from db.connection import init_db
from routes import register_all


def create_app():
    """Factory: crea y configura la app Flask."""
    app = Flask(__name__)
    app.secret_key = SECRET_KEY

    # Inicializar DB (crea tablas + migraciones) antes de servir requests
    with app.app_context():
        init_db()

    # Registrar todas las rutas (auth, clientes, qr, export, vistas)
    register_all(app)

    return app


# App global para que `flask run` y `python app.py` funcionen igual
app = create_app()


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
