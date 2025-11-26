from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required
from routes.auth import roles_required

seguridad_bp = Blueprint("seguridad", __name__)

@seguridad_bp.route("/seguridad")
@jwt_required()
@roles_required('administrador')
def seguridad():
    return render_template("seguridad.html")
