"""
Ruta de descarga de QR:
- /descargar_qr/<id>  → PNG con QR cuyo contenido es el NanoId del cliente
"""
from flask import flash, redirect, send_file, url_for

from db.repo_clientes import get_cliente_por_id
from routes.auth import requiere_login
from services.qr_service import generar_qr_descarga


def register(app):
    @app.route("/descargar_qr/<int:cliente_id>")
    @requiere_login
    def descargar_qr(cliente_id):
        """Descarga el código QR de un cliente específico (contenido = su NanoId)."""
        cliente = get_cliente_por_id(cliente_id)
        if not cliente:
            flash("Cliente no encontrado", "error")
            return redirect(url_for("listar_clientes_html"))

        codigo_qr = cliente["codigo_qr"]
        buffer = generar_qr_descarga(codigo_qr)

        return send_file(
            buffer,
            mimetype="image/png",
            as_attachment=True,
            download_name=f"cliente_{cliente_id}_{cliente['nombre']}_{codigo_qr}.png",
        )
