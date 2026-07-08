"""
Autenticación: login, logout, y el decorador `requiere_login`.

`requiere_login` se importa desde los demás módulos de routes para
proteger sus rutas.
"""
from functools import wraps

from flask import flash, redirect, render_template, request, session, url_for

from config import CONTRASEÑA_ADMIN, USUARIO_ADMIN
from db.repo_logs import registrar_evento


def requiere_login(f):
    """Decorador: redirige a /login si no hay sesión activa."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logueado" not in session:
            flash("Debes iniciar sesión", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


def register(app):
    @app.route("/login", methods=["GET", "POST"])
    def login():
        """Página de login"""
        if request.method == "POST":
            usuario = request.form.get("usuario")
            contraseña = request.form.get("contraseña")

            if usuario == USUARIO_ADMIN and contraseña == CONTRASEÑA_ADMIN:
                session["logueado"] = True
                registrar_evento(
                    tipo="SISTEMA",
                    descripcion=f"Inicio de sesión exitoso — usuario: {usuario}",
                    resultado="EXITO",
                    usuario_admin=usuario,
                )
                flash("¡Bienvenido!", "success")
                return redirect(url_for("inicio"))
            else:
                registrar_evento(
                    tipo="SISTEMA",
                    descripcion=f"Intento de login fallido — usuario: {usuario}",
                    resultado="DENEGADO",
                    usuario_admin=usuario,
                )
                flash("Usuario o contraseña incorrectos", "error")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        """Cierra la sesión"""
        if "logueado" in session:
            registrar_evento(
                tipo="SISTEMA",
                descripcion="Cierre de sesión",
                resultado="EXITO",
                usuario_admin="admin",
            )
        session.clear()
        flash("Sesión cerrada", "success")
        return redirect(url_for("login"))
