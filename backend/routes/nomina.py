from flask import Blueprint, render_template

nomina_bp = Blueprint("nomina", __name__)

@nomina_bp.route("/nomina")
def nomina():
    return render_template("nomina.html")
