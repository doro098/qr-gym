"""
Paquete hardware: código que corre en la Raspberry Pi.

- scanner:   lee QRs desde la cámara
- cerradura: controla el GPIO de la cerradura eléctrica
- acceso:    bucle principal que orquesta scanner + cerradura + DB

`acceso.py` es el entry point: `python -m hardware.acceso` o
`python hardware/acceso.py` desde la Raspberry.
"""
