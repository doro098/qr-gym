"""
Rutas de gestión de clientes.
"""
from datetime import datetime

from flask import flash, redirect, render_template, request, url_for

from db.repo_clientes import (
    actualizar_cliente,
    crear_cliente,
    eliminar_cliente,
    get_all_clientes,
    get_cliente_por_id,
    obtener_vencimientos_proximos,
)
from db.repo_logs import registrar_evento
from db.repo_disciplinas import (
    obtener_disciplinas,
    obtener_disciplinas_de_cliente,
    reemplazar_disciplinas_de_cliente,
)
from routes.auth import requiere_login


def register(app):
    @app.route("/")
    @requiere_login
    def listar_clientes_html():
        clientes = get_all_clientes()
        clientes_lista = [dict(cliente) for cliente in clientes]
        proximos_vencimientos = obtener_vencimientos_proximos(7)
        ids_proximos = [c["id"] for c in proximos_vencimientos]
        return render_template(
            "clientes.html",
            clientes=clientes_lista,
            ids_proximos=ids_proximos,
            ids_vencidos=[],
        )

    @app.route("/editar/<int:cliente_id>", methods=["GET", "POST"])
    @requiere_login
    def editar_cliente(cliente_id):
        cliente = get_cliente_por_id(cliente_id)
        if not cliente:
            flash("Cliente no encontrado", "error")
            return redirect(url_for("listar_clientes_html"))

        if request.method == "GET":
            # Obtener disciplinas disponibles y las del cliente
            todas = obtener_disciplinas()
            del_cliente = obtener_disciplinas_de_cliente(cliente_id)
            ids_del_cliente = [d["id"] for d in del_cliente]
            return render_template(
                "editar_cliente.html",
                cliente=cliente,
                disciplinas=todas,
                disciplinas_cliente=ids_del_cliente,
            )

        # POST
        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        telefono = request.form.get("telefono")
        vencimiento = request.form.get("vencimiento")
        disciplinas_seleccionadas = request.form.getlist("disciplinas")  # lista de ids

        if not nombre:
            flash("El nombre es obligatorio", "error")
            return redirect(url_for("editar_cliente", cliente_id=cliente_id))

        actualizar_cliente(
            cliente_id=cliente_id,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            vencimiento=vencimiento if vencimiento else None,
        )

        # Reemplazar disciplinas
        ids_int = [int(x) for x in disciplinas_seleccionadas if x.isdigit()]
        reemplazar_disciplinas_de_cliente(cliente_id, ids_int)

        registrar_evento(
            tipo="SISTEMA",
            descripcion=f"Cliente editado — ID {cliente_id}: {nombre}",
            resultado="EXITO",
            cliente_id=cliente_id,
            usuario_admin="admin",
        )
        flash("Cliente actualizado correctamente", "success")
        return redirect(url_for("listar_clientes_html"))

    @app.route("/nuevo", methods=["GET", "POST"])
    @requiere_login
    def nuevo_cliente():
        if request.method == "GET":
            todas = obtener_disciplinas()
            return render_template("nuevo_cliente.html", disciplinas=todas)

        nombre = request.form.get("nombre")
        apellido = request.form.get("apellido")
        telefono = request.form.get("telefono")
        vencimiento = request.form.get("vencimiento")
        disciplinas_seleccionadas = request.form.getlist("disciplinas")

        if not nombre:
            flash("El nombre es obligatorio", "error")
            return redirect(url_for("nuevo_cliente"))

        nuevo_id = crear_cliente(
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            vencimiento=vencimiento if vencimiento else None,
        )

        ids_int = [int(x) for x in disciplinas_seleccionadas if x.isdigit()]
        if ids_int:
            from db.repo_disciplinas import reemplazar_disciplinas_de_cliente
            reemplazar_disciplinas_de_cliente(nuevo_id, ids_int)

        registrar_evento(
            tipo="SISTEMA",
            descripcion=f"Nuevo cliente creado — ID {nuevo_id}: {nombre}",
            resultado="EXITO",
            cliente_id=nuevo_id,
            usuario_admin="admin",
        )
        flash(f"Cliente creado correctamente con ID: {nuevo_id}", "success")
        return redirect(url_for("listar_clientes_html"))

    @app.route("/eliminar/<int:cliente_id>", methods=["POST"])
    @requiere_login
    def eliminar_cliente_route(cliente_id):
        cliente = get_cliente_por_id(cliente_id)
        nombre = cliente["nombre"] if cliente else "desconocido"

        if eliminar_cliente(cliente_id):
            registrar_evento(
                tipo="SISTEMA",
                descripcion=f"Cliente eliminado — ID {cliente_id}: {nombre}",
                resultado="EXITO",
                cliente_id=cliente_id,
                usuario_admin="admin",
            )
            flash("Cliente eliminado correctamente", "success")
        else:
            registrar_evento(
                tipo="SISTEMA",
                descripcion=f"Intento fallido de eliminar cliente ID {cliente_id}",
                resultado="ERROR",
                cliente_id=cliente_id,
                usuario_admin="admin",
            )
            flash("No se pudo eliminar el cliente", "error")

        return redirect(url_for("listar_clientes_html"))

    @app.route("/vencimientos")
    @requiere_login
    def mostrar_vencimientos():
        proximos = obtener_vencimientos_proximos(30)
        hoy = datetime.now().date()
        for cliente in proximos:
            if cliente["vencimiento"]:
                fecha_venc = datetime.strptime(cliente["vencimiento"], "%Y-%m-%d").date()
                dias_restantes = (fecha_venc - hoy).days
                cliente["dias_restantes"] = dias_restantes
        return render_template("vencimientos.html", clientes=proximos)