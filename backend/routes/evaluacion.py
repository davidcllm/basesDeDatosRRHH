from flask import Blueprint, render_template
from dp import get_connection

evaluacion_bp = Blueprint("evaluacion", __name__)

@evaluacion_bp.route("/evaluacion")
def evaluacion():

    # ================== EVALUACION ==================
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM EVALUACION;")
    evaluaciones = cursor.fetchall()
    cursor.close()
    cnx.close()

    # ================== EMPLEADO - EVALUACION ==================
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM `EMPLEADO-EVALUACION`;")
    empleado_evaluaciones = cursor.fetchall()
    cursor.close()
    cnx.close()

    # ================== CAPACITACION ==================
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM CAPACITACION;")
    capacitaciones = cursor.fetchall()
    cursor.close()
    cnx.close()

    # ================== EMPLEADO - CAPACITACION ==================
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM `EMPLEADO-CAPACITACION`;")
    empleado_capacitaciones = cursor.fetchall()
    cursor.close()
    cnx.close()

    # ================== PLAN CARRERA ==================
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM PLAN_CARRERA;")
    planes_carrera = cursor.fetchall()
    cursor.close()
    cnx.close()

    return render_template(
        "evaluacion.html",
        evaluaciones=evaluaciones,
        empleado_evaluaciones=empleado_evaluaciones,
        capacitaciones=capacitaciones,
        empleado_capacitaciones=empleado_capacitaciones,
        planes_carrera=planes_carrera
    )
