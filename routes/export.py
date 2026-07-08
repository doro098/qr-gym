"""
Ruta de exportación CSV:
- /exportar_csv  → descarga todos los clientes como CSV
"""
import csv
import io

from flask import make_response

from db.repo_clientes import get_all_clientes
from routes.auth import requiere_login


def register(app):
    @app.route("/exportar_csv")
    @requiere_login
    def exportar_csv():
        """Exporta todos los clientes a CSV"""
        clientes = get_all_clientes()
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["id", "nombre", "telefono", "vencimiento"])
        for c in clientes:
            writer.writerow([c["id"], c["nombre"], c["telefono"], c["vencimiento"]])

        response = make_response(buffer.getvalue().encode("utf-8"))
        response.headers["Content-Disposition"] = "attachment; filename=clientes.csv"
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        return response
