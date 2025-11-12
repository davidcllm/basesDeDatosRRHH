from flask import Blueprint, render_template

proyectos_bp = Blueprint("proyectos", __name__)

@proyectos_bp.route("/proyectos")
def proyectos():
    return render_template("proyectos.html")
