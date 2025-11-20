from flask import Blueprint, render_template, request, redirect, url_for
from dp import get_connection

asistencias_bp = Blueprint("asistencias", __name__)

@asistencias_bp.route("/asistencias")
def asistencias():
    # --- AUSENCIAS ---
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("""
        SELECT A.id_ausencia, A.id_empleado, A.tipo, A.fecha_inicio, A.fecha_fin, A.motivo
        FROM AUSENCIA A;
    """)
    ausencias = cursor.fetchall()
    cursor.close()
    cnx.close()

    # --- EMPLEADOS (para el select del formulario) ---
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT id_empleado, nombre_completo FROM EMPLEADO;")
    empleados = cursor.fetchall()
    cursor.close()
    cnx.close()

    # --- EMPL-AUSENCIA (segunda tabla asignada) ---
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM `EMPLEADO-AUSENCIA`;")
    empleado_ausencias = cursor.fetchall()
    cursor.close()
    cnx.close()

    return render_template(
        "asistencias.html",
        ausencias=ausencias,
        empleados=empleados,
        empleado_ausencias=empleado_ausencias
    )


# ----------------------------------------------------
#   RUTA PARA AGREGAR AUSENCIA (POST)
# ----------------------------------------------------
@asistencias_bp.route("/asistencias/agregar_ausencia", methods=["POST"])
def agregar_ausencia():

    id_empleado = request.form["id_empleado"]
    tipo = request.form["tipo"]
    fecha_inicio = request.form["fecha_inicio"]
    fecha_fin = request.form["fecha_fin"]
    motivo = request.form["motivo"]

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        INSERT INTO AUSENCIA (id_empleado, tipo, fecha_inicio, fecha_fin, motivo)
        VALUES (%s, %s, %s, %s, %s);
    """, (id_empleado, tipo, fecha_inicio, fecha_fin, motivo))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("asistencias.asistencias"))
