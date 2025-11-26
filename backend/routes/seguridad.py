from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection

seguridad_bp = Blueprint("seguridad", __name__)

@seguridad_bp.route("/seguridad")
@jwt_required()
@roles_required('administrador')
def seguridad():
    cnx = None
    cursor = None
    try:
        cnx = get_connection()
        cursor = cnx.cursor()  # DictCursor ya configurado en get_connection()
        cursor.execute("SELECT id_usuario, email, rol FROM USUARIO ORDER BY email;")
        usuarios = cursor.fetchall()
    except Exception as e:
        usuarios = []
        flash(f"Error al obtener usuarios: {e}", "error")
    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()
    return render_template("seguridad.html", usuarios=usuarios)

@seguridad_bp.route("/seguridad/modificar_rol/<int:id_usuario>", methods=["POST"])
@jwt_required()
@roles_required('administrador')
def modificar_rol(id_usuario):
    new_rol = request.form.get("rol")
    ALLOWED_ROLES = ['administrador', 'finanzas', 'recursos_humanos']
    if new_rol not in ALLOWED_ROLES:
        flash("Rol inválido.", "error")
        return redirect(url_for("seguridad.seguridad"))

    cnx = None
    cursor = None
    try:
        cnx = get_connection()
        cursor = cnx.cursor()
        cursor.execute("UPDATE USUARIO SET rol = %s WHERE id_usuario = %s;", (new_rol, id_usuario))
        cnx.commit()
        flash("Rol actualizado correctamente.", "success")
    except Exception as e:
        if cnx:
            cnx.rollback()
        flash(f"Error al actualizar rol: {e}", "error")
    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()

    return redirect(url_for("seguridad.seguridad"))
