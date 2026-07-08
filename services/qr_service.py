"""
Generación de códigos QR.

Vive en `services/` (no en `routes/`) porque no depende de Flask.
Esto permite reutilizarlo desde scripts CLI, tests, u otros procesos
sin arrastrar toda la app web.

El contenido del QR es SOLO el NanoId del cliente (6 chars). El scanner
en la Raspberry lee ese texto y lo resuelve contra la columna `codigo_qr`
de la DB.
"""
from io import BytesIO

import qrcode


def generar_qr_descarga(codigo_qr):
    """
    Genera un PNG con el QR cuyo contenido es `codigo_qr` (NanoId).
    Devuelve un BytesIO listo para enviar como archivo.

    Uso típico desde una ruta Flask:
        buffer = generar_qr_descarga(cliente["codigo_qr"])
        return send_file(buffer, mimetype="image/png", as_attachment=True, ...)
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(codigo_qr)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    return buffer
