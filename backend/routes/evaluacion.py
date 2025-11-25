from flask import Blueprint, render_template, request, redirect, url_for, flash 
from dp import get_connection
import pymysql

evaluacion_bp = Blueprint("evaluacion", __name__)


@evaluacion_bp.route("/evaluacion")
def evaluacion():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    # Evaluaciones + empleado correspondiente
    cursor.execute("""
        SELECT e.id_evaluacion,
               e.fecha_evaluacion,
               e.tipo,
               e.resultado,
               e.observaciones,
               rel.id_empleado,
               emp.nombre_completo,
               rel.fecha_inicio,
               rel.fecha_fin
        FROM EVALUACION e
        LEFT JOIN `EMPLEADO-EVALUACION` rel ON e.id_evaluacion = rel.id_evaluacion
        LEFT JOIN EMPLEADO emp ON rel.id_empleado = emp.id_empleado
        ORDER BY e.id_evaluacion;
    """)
    evaluaciones = cursor.fetchall()

    # Empleados
    cursor.execute("SELECT id_empleado, nombre_completo FROM EMPLEADO ORDER BY nombre_completo;")
    empleados = cursor.fetchall()

    # Capacitaciones
    cursor.execute("SELECT * FROM CAPACITACION;")
    capacitaciones = cursor.fetchall()

    # Tabla puente empleado-capacitacion
    cursor.execute("SELECT * FROM `EMPLEADO-CAPACITACION`;")
    empleado_capacitaciones = cursor.fetchall()

    # Planes de carrera
    cursor.execute("SELECT * FROM PLAN_CARRERA;")
    planes_carrera = cursor.fetchall()

    cursor.close()
    cnx.close()

    return render_template(
        "evaluacion.html",
        evaluaciones=evaluaciones,
        empleados=empleados,
        capacitaciones=capacitaciones,
        empleado_capacitaciones=empleado_capacitaciones,
        planes_carrera=planes_carrera
    )


# ---------------------------
# AGREGAR
# ---------------------------
@evaluacion_bp.route("/evaluacion/agregar", methods=["POST"])
def agregar_evaluacion():
    id_empleado = request.form.get("id_empleado") or None
    fecha_evaluacion = request.form.get("fecha_evaluacion")
    tipo = request.form.get("tipo")
    resultado = request.form.get("resultado")
    observaciones = request.form.get("observaciones") or ""
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")

    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        flash("La fecha de inicio no puede ser posterior a la fecha final.", "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        INSERT INTO EVALUACION (fecha_evaluacion, tipo, resultado, observaciones)
        VALUES (%s, %s, %s, %s);
    """, (fecha_evaluacion, tipo, resultado, observaciones))
    id_eval = cursor.lastrowid

    if id_empleado:
        cursor.execute("""
            INSERT INTO `EMPLEADO-EVALUACION` (id_empleado, id_evaluacion, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s, %s);
        """, (id_empleado, id_eval, fecha_inicio, fecha_fin))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# EDITAR
# ---------------------------
@evaluacion_bp.route("/evaluacion/editar/<int:id_eval>", methods=["POST"])
def editar_evaluacion(id_eval):
    fecha_evaluacion = request.form.get("fecha_evaluacion")
    tipo = request.form.get("tipo")
    resultado = request.form.get("resultado")
    observaciones = request.form.get("observaciones") or ""
    id_empleado = request.form.get("id_empleado") or None
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")

    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        flash("La fecha de inicio no puede ser posterior a la fecha final.", "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        UPDATE EVALUACION
        SET fecha_evaluacion=%s, tipo=%s, resultado=%s, observaciones=%s
        WHERE id_evaluacion=%s;
    """, (fecha_evaluacion, tipo, resultado, observaciones, id_eval))

    cursor.execute("SELECT COUNT(*) AS cnt FROM `EMPLEADO-EVALUACION` WHERE id_evaluacion=%s;", (id_eval,))
    row = cursor.fetchone()

    existe = row[0] if isinstance(row, tuple) else row.get("cnt", 0)

    if existe:
        cursor.execute("""
            UPDATE `EMPLEADO-EVALUACION`
            SET id_empleado=%s, fecha_inicio=%s, fecha_fin=%s
            WHERE id_evaluacion=%s;
        """, (id_empleado, fecha_inicio, fecha_fin, id_eval))
    else:
        if id_empleado:
            cursor.execute("""
                INSERT INTO `EMPLEADO-EVALUACION` (id_empleado, id_evaluacion, fecha_inicio, fecha_fin)
                VALUES (%s, %s, %s, %s);
            """, (id_empleado, id_eval, fecha_inicio, fecha_fin))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# ELIMINAR
# ---------------------------
@evaluacion_bp.route("/evaluacion/eliminar/<int:id_eval>", methods=["POST"])
def eliminar_evaluacion(id_eval):
    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("DELETE FROM `EMPLEADO-EVALUACION` WHERE id_evaluacion=%s;", (id_eval,))
    cursor.execute("DELETE FROM EVALUACION WHERE id_evaluacion=%s;", (id_eval,))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("evaluacion.evaluacion"))
