"""
Rutas para gestión de disciplinas y horarios.
"""
from flask import flash, redirect, render_template, request, url_for

from db.repo_disciplinas import (
    crear_disciplina,
    obtener_disciplina_por_id,
    actualizar_disciplina,
    eliminar_disciplina,
    agregar_horario,
    eliminar_horario,
    obtener_horarios_por_disciplina,
    eliminar_horarios_de_disciplina,
    obtener_disciplinas_con_horarios,
)
from db.repo_logs import registrar_evento
from routes.auth import requiere_login


def register(app):
    @app.route("/disciplinas")
    @requiere_login
    def listar_disciplinas():
        disciplinas = obtener_disciplinas_con_horarios()
        return render_template("disciplinas.html", disciplinas=disciplinas)

    @app.route("/disciplinas/nueva", methods=["GET", "POST"])
    @requiere_login
    def nueva_disciplina():
        if request.method == "GET":
            return render_template("nueva_disciplina.html")

        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")
        if not nombre:
            flash("El nombre es obligatorio", "error")
            return redirect(url_for("nueva_disciplina"))

        dis_id = crear_disciplina(nombre, descripcion)

        # Procesar horarios (vienen como listas)
        dias = request.form.getlist("dia_semana")
        inicios = request.form.getlist("hora_inicio")
        fines = request.form.getlist("hora_fin")
        for dia, ini, fin in zip(dias, inicios, fines):
            if dia and ini and fin:
                agregar_horario(dis_id, int(dia), ini, fin)

        registrar_evento(
            tipo="SISTEMA",
            descripcion=f"Nueva disciplina creada: {nombre}",
            resultado="EXITO",
            usuario_admin="admin",
        )
        flash("Disciplina creada correctamente", "success")
        return redirect(url_for("listar_disciplinas"))

    @app.route("/disciplinas/editar/<int:disciplina_id>", methods=["GET", "POST"])
    @requiere_login
    def editar_disciplina(disciplina_id):
        disciplina = obtener_disciplina_por_id(disciplina_id)
        if not disciplina:
            flash("Disciplina no encontrada", "error")
            return redirect(url_for("listar_disciplinas"))

        if request.method == "GET":
            horarios = obtener_horarios_por_disciplina(disciplina_id)
            return render_template(
                "editar_disciplina.html",
                disciplina=disciplina,
                horarios=horarios,
            )

        # POST
        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")
        if not nombre:
            flash("El nombre es obligatorio", "error")
            return redirect(url_for("editar_disciplina", disciplina_id=disciplina_id))

        actualizar_disciplina(disciplina_id, nombre, descripcion)

        # Reemplazar horarios: eliminar todos y añadir los nuevos
        eliminar_horarios_de_disciplina(disciplina_id)
        dias = request.form.getlist("dia_semana")
        inicios = request.form.getlist("hora_inicio")
        fines = request.form.getlist("hora_fin")
        for dia, ini, fin in zip(dias, inicios, fines):
            if dia and ini and fin:
                agregar_horario(disciplina_id, int(dia), ini, fin)

        registrar_evento(
            tipo="SISTEMA",
            descripcion=f"Disciplina editada: {nombre}",
            resultado="EXITO",
            usuario_admin="admin",
        )
        flash("Disciplina actualizada correctamente", "success")
        return redirect(url_for("listar_disciplinas"))

    @app.route("/disciplinas/eliminar/<int:disciplina_id>", methods=["POST"])
    @requiere_login
    def eliminar_disciplina_route(disciplina_id):
        disciplina = obtener_disciplina_por_id(disciplina_id)
        nombre = disciplina["nombre"] if disciplina else "desconocida"
        if eliminar_disciplina(disciplina_id):
            registrar_evento(
                tipo="SISTEMA",
                descripcion=f"Disciplina eliminada: {nombre}",
                resultado="EXITO",
                usuario_admin="admin",
            )
            flash("Disciplina eliminada correctamente", "success")
        else:
            flash("No se pudo eliminar la disciplina", "error")
        return redirect(url_for("listar_disciplinas"))