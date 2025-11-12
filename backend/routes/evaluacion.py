from flask import Blueprint, render_template

evaluacion_bp = Blueprint("evaluacion", __name__)

@evaluacion_bp.route("/evaluacion")
def evaluacion():
    return render_template("evaluacion.html")
