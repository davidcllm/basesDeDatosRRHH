import pymysql
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt,
    unset_jwt_cookies, set_access_cookies, verify_jwt_in_request
)
from werkzeug.security import check_password_hash
from functools import wraps

from dp import get_connection, create_user_in_db 

auth_bp = Blueprint('auth', __name__)

# Decorador reutilizable para controlar acceso por roles
def roles_required(*allowed_roles):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            # Verifica que exista un JWT válido
            verify_jwt_in_request()
            claims = get_jwt()
            rol = claims.get("rol")
            if rol not in allowed_roles:
                return jsonify({"msg": "Forbidden - role not allowed"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        cnx = None
        cursor = None
        try:
            cnx = get_connection()
            cursor = cnx.cursor()
            cursor.execute("SELECT email, password_hash, rol FROM USUARIO WHERE email = %s", (email,))
            user = cursor.fetchone()
        except Exception as e:
            flash(f"Error al conectar con la base de datos: {e}", "error")
            return render_template("login.html")
        finally:
            if cursor:
                cursor.close()
            if cnx:
                cnx.close()

        if not user:
            flash("Usuario no encontrado.", "error")
            return render_template("login.html")

        if not check_password_hash(user["password_hash"], password):
            flash("Contraseña incorrecta.", "error")
            return render_template("login.html")

        # Credenciales correctas -> crear JWT con claim 'rol' y guardarlo en cookie
        additional_claims = {"rol": user["rol"]}
        access_token = create_access_token(identity=user["email"], additional_claims=additional_claims)
        response = redirect(url_for("empleados.empleados"))
        set_access_cookies(response, access_token)

        # Guardar datos mínimos en sesión (opcional, para templates)
        session["role"] = user["rol"]
        session["email"] = user["email"]
        flash("Inicio de sesión correcto.", "success")
        return response

    # Mostrar formulario GET
    return render_template("login.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Eliminamos la posibilidad de elegir rol en el frontend; todos los registros nuevos son 'invitado'
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        rol = "invitado"  # asignación automática

        if not email or not password:
            flash("Email y contraseña son obligatorios.", "error")
            return redirect(url_for('auth.login'))

        if create_user_in_db(email, password, rol):
            flash("Usuario registrado correctamente. Espera a que el administrador te otorgue permisos.", "success")
        else:
            flash("Error al registrar usuario (tal vez el email ya existe).", "error")

    return redirect(url_for('auth.login'))


@auth_bp.route("/logout")
def logout():
    response = redirect(url_for('auth.login'))
    # Remueve el token de las cookies si se está usando 
    unset_jwt_cookies(response) 
    # Limpiar sesión
    session.clear()
    flash("Has cerrado sesión exitosamente.", "info")
    return response

# Se requiere importar get_jwt para usar esta ruta
from flask_jwt_extended import get_jwt 

@auth_bp.route("/prueba_protegida")
@jwt_required()
def prueba_protegida():
    current_user_email = get_jwt_identity()
    user_claims = get_jwt() # Obtiene los claims (incluyendo el rol)
    return jsonify(logged_in_as=current_user_email, rol=user_claims.get('rol')), 200