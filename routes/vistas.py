"""
Rutas de vistas (solo lectura, presentan datos):
- /inicio         → dashboard
- /actividad      → historial de eventos
- /estadisticas   → página de estadísticas con gráficos
"""
from datetime import datetime

from flask import render_template

from db.estadisticas import obtener_datos_inicio, obtener_estadisticas
from db.repo_logs import obtener_historial
from routes.auth import requiere_login


_MESES_ES = [
    "",
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]
_DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _fecha_hoy_es():
    """Devuelve la fecha de hoy en formato 'lunes 8 de julio de 2026'."""
    hoy = datetime.now()
    return f"{_DIAS_ES[hoy.weekday()]} {hoy.day} de {_MESES_ES[hoy.month]} de {hoy.year}"


def register(app):
    @app.route("/inicio")
    @requiere_login
    def inicio():
        """Página de inicio / dashboard"""
        datos = obtener_datos_inicio()
        return render_template("inicio.html", datos=datos, fecha_hoy=_fecha_hoy_es())

    @app.route("/actividad")
    @requiere_login
    def mostrar_actividad():
        """Muestra el historial de eventos del sistema"""
        logs = obtener_historial(limite=200)
        return render_template("actividad.html", logs=logs)

    @app.route("/estadisticas")
    @requiere_login
    def mostrar_estadisticas():
        """Página de estadísticas con gráficos."""
        data = obtener_estadisticas()
        return render_template("estadisticas.html", **data)
