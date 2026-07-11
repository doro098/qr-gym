"""
Rutas de vistas (solo lectura, presentan datos):
- /inicio         → dashboard
- /actividad      → historial de eventos
- /estadisticas   → página de estadísticas con gráficos
"""
from datetime import datetime, timedelta
from flask import render_template, request

from db.estadisticas import obtener_datos_inicio, obtener_estadisticas
from db.repo_logs import obtener_historial, obtener_dias_con_logs, obtener_logs_por_dia
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
        page = request.args.get('page', 1, type=int)
        if page < 1:
            page = 1

        # Obtener lista de días con logs (últimos 30 días)
        dias = obtener_dias_con_logs(limite=30)
        if not dias:
            return render_template("actividad.html", logs=[], page=1, total_pages=0, total=0, titulo_fecha=None, fecha_iso=None)

        total_pages = len(dias)
        if page > total_pages:
            page = total_pages

        fecha_seleccionada = dias[page - 1]
        logs = obtener_logs_por_dia(fecha_seleccionada)

        # Formatear fecha para mostrar bonito
        fecha_dt = datetime.strptime(fecha_seleccionada, "%Y-%m-%d").date()
        hoy = datetime.now().date()
        ayer = hoy - timedelta(days=1)

        if fecha_dt == hoy:
            titulo_fecha = "Hoy"
        elif fecha_dt == ayer:
            titulo_fecha = "Ayer"
        else:
            dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
            meses = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
                     "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
            titulo_fecha = f"{dias_semana[fecha_dt.weekday()]} {fecha_dt.day} de {meses[fecha_dt.month]} de {fecha_dt.year}"

        return render_template(
            "actividad.html",
            logs=logs,
            page=page,
            total_pages=total_pages,
            total=len(logs),
            titulo_fecha=titulo_fecha,
            fecha_iso=fecha_seleccionada
        )

    @app.route("/estadisticas")
    @requiere_login
    def mostrar_estadisticas():
        """Página de estadísticas con gráficos."""
        data = obtener_estadisticas()
        return render_template("estadisticas.html", **data)
