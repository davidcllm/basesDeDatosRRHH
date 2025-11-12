from flask import Blueprint, render_template

cuentas_bp = Blueprint("cuentas", __name__)

@cuentas_bp.route("/cuentas")
def cuentas():
    return render_template("cuentas.html")
