# Este archivo fue creado con ayuda de la Inteligencia Artificial de OpenAI. 
# OpenAI. (2025). ChatGPT [Modelo de lenguaje de gran tamaño]. https://chat.openai.com/chat

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
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
        current_email = get_jwt_identity()
        cursor.execute("SELECT id_usuario, email, rol FROM USUARIO WHERE email <> %s ORDER BY email;", (current_email,))
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
    ALLOWED_ROLES = ['administrador', 'finanzas', 'recursos_humanos', 'invitado']
    if new_rol not in ALLOWED_ROLES:
        flash("Rol inválido.", "error")
        return redirect(url_for("seguridad.seguridad"))

    cnx = None
    cursor = None
    try:
        cnx = get_connection()
        cursor = cnx.cursor()
        # Evitar que el admin modifique su propio rol: comprobar email del id recibido
        current_email = get_jwt_identity()
        cursor.execute("SELECT email FROM USUARIO WHERE id_usuario = %s;", (id_usuario,))
        row = cursor.fetchone()
        if not row:
            flash("Usuario no encontrado.", "error")
            return redirect(url_for("seguridad.seguridad"))
        if row.get("email") == current_email:
            flash("No puedes modificar tu propio rol.", "error")
            return redirect(url_for("seguridad.seguridad"))

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

@seguridad_bp.route("/seguridad/eliminar/<int:id_usuario>", methods=["POST"])
@jwt_required()
@roles_required('administrador')
def eliminar_usuario(id_usuario):
    cnx = None
    cursor = None
    try:
        cnx = get_connection()
        cursor = cnx.cursor()
        
        # Evitar que el admin se elimine a sí mismo
        current_email = get_jwt_identity()
        cursor.execute("SELECT email FROM USUARIO WHERE id_usuario = %s;", (id_usuario,))
        row = cursor.fetchone()
        if not row:
            flash("Usuario no encontrado.", "error")
            return redirect(url_for("seguridad.seguridad"))
        
        if row.get("email") == current_email:
            flash("No puedes eliminar tu propia cuenta.", "error")
            return redirect(url_for("seguridad.seguridad"))

        # Eliminar usuario
        cursor.execute("DELETE FROM USUARIO WHERE id_usuario = %s;", (id_usuario,))
        cnx.commit()
        flash("Usuario eliminado correctamente.", "success")
    except Exception as e:
        if cnx:
            cnx.rollback()
        flash(f"Error al eliminar usuario: {e}", "error")
    finally:
        if cursor:
            cursor.close()
        if cnx:
            cnx.close()

    return redirect(url_for("seguridad.seguridad"))
