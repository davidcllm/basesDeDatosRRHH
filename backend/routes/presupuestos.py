from flask import Blueprint, render_template

presupuestos_bp = Blueprint("presupuestos", __name__)

@presupuestos_bp.route("/presupuestos")
def presupuestos():
    return render_template("presupuestos.html")
