from flask import Blueprint, render_template

asistencias_bp = Blueprint("asistencias", __name__)

@asistencias_bp.route("/asistencias")
def asistencias():
    return render_template("asistencias.html")
