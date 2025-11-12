from flask import Blueprint, render_template

seguridad_bp = Blueprint("seguridad", __name__)

@seguridad_bp.route("/seguridad")
def seguridad():
    return render_template("seguridad.html")
