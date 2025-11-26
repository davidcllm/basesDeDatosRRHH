from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql

asistencias_bp = Blueprint("asistencias", __name__)

@asistencias_bp.route("/asistencias")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def asistencias():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT a.id_ausencia, a.id_empleado, a.tipo, a.fecha_inicio, a.fecha_fin, a.motivo,
               e.nombre_completo
        FROM AUSENCIA a
        LEFT JOIN EMPLEADO e ON a.id_empleado = e.id_empleado;
    """)
    ausencias = cursor.fetchall()

    cursor.execute("SELECT id_empleado, nombre_completo FROM EMPLEADO ORDER BY nombre_completo;")
    empleados = cursor.fetchall()

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
#   AGREGAR AUSENCIA
# ----------------------------------------------------
@asistencias_bp.route("/asistencias/agregar_ausencia", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def agregar_ausencia():

    id_empleado = request.form["id_empleado"]
    tipo = request.form["tipo"]
    fecha_inicio = request.form["fecha_inicio"]
    fecha_fin = request.form["fecha_fin"]
    motivo = request.form["motivo"]

    # VALIDACIÓN: inicio no puede ser mayor a fin
    if fecha_inicio > fecha_fin:
        flash("La fecha de inicio no puede ser posterior a la fecha final.", "error")
        return redirect(url_for("asistencias.asistencias"))

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        INSERT INTO AUSENCIA (id_empleado, tipo, fecha_inicio, fecha_fin, motivo)
        VALUES (%s, %s, %s, %s, %s);
    """, (id_empleado, tipo, fecha_inicio, fecha_fin, motivo))

    id_ausencia = cursor.lastrowid

    cursor.execute("""
        INSERT INTO `EMPLEADO-AUSENCIA` (id_empleado, id_ausencia, fecha_inicio, fecha_final)
        VALUES (%s, %s, %s, %s);
    """, (id_empleado, id_ausencia, fecha_inicio, fecha_fin))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("asistencias.asistencias"))


# ----------------------------------------------------
#   EDITAR AUSENCIA
# ----------------------------------------------------
@asistencias_bp.route("/asistencias/editar/<int:id_ausencia>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def editar_ausencia(id_ausencia):

    id_empleado = request.form["id_empleado"]
    tipo = request.form["tipo"]
    fecha_inicio = request.form["fecha_inicio"]
    fecha_fin = request.form["fecha_fin"]
    motivo = request.form["motivo"]

    # VALIDACIÓN: inicio no puede ser mayor a fin
    if fecha_inicio > fecha_fin:
        flash("La fecha de inicio no puede ser posterior a la fecha final.", "error")
        return redirect(url_for("asistencias.asistencias"))

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        UPDATE AUSENCIA
        SET id_empleado=%s, tipo=%s, fecha_inicio=%s, fecha_fin=%s, motivo=%s
        WHERE id_ausencia=%s;
    """, (id_empleado, tipo, fecha_inicio, fecha_fin, motivo, id_ausencia))

    cursor.execute("""
        UPDATE `EMPLEADO-AUSENCIA`
        SET id_empleado=%s, fecha_inicio=%s, fecha_final=%s
        WHERE id_ausencia=%s;
    """, (id_empleado, fecha_inicio, fecha_fin, id_ausencia))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("asistencias.asistencias"))


# ----------------------------------------------------
#   ELIMINAR AUSENCIA
# ----------------------------------------------------
@asistencias_bp.route("/asistencias/eliminar/<int:id_ausencia>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def eliminar_ausencia(id_ausencia):

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("DELETE FROM `EMPLEADO-AUSENCIA` WHERE id_ausencia=%s;", (id_ausencia,))
    cursor.execute("DELETE FROM AUSENCIA WHERE id_ausencia=%s;", (id_ausencia,))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("asistencias.asistencias"))
