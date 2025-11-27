from flask import Blueprint, render_template, request, redirect, url_for, flash 
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql

evaluacion_bp = Blueprint("evaluacion", __name__)


@evaluacion_bp.route("/evaluacion")
@jwt_required()
@roles_required('administrador','recursos_humanos')
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

    # Capacitaciones CON JOIN para obtener empleado, resultado y comentarios
    cursor.execute("""
        SELECT ec.`id_empleado-capacitacion`,
               c.id_capacitacion,
               c.nombre,
               c.descripcion,
               c.fecha_inicio,
               c.fecha_fin,
               c.proveedor,
               ec.id_empleado,
               emp.nombre_completo,
               ec.resultado,
               ec.comentarios
        FROM CAPACITACION c
        LEFT JOIN `EMPLEADO-CAPACITACION` ec ON c.id_capacitacion = ec.id_capacitacion
        LEFT JOIN EMPLEADO emp ON ec.id_empleado = emp.id_empleado
        ORDER BY c.id_capacitacion DESC;
    """)
    capacitaciones = cursor.fetchall()

    # Planes de carrera CON JOIN para obtener empleado
    cursor.execute("""
        SELECT pc.id_plan_carrera,
               pc.objetivo,
               pc.etapas,
               pc.fecha_inicio,
               pc.fecha_fin,
               emp.id_empleado,
               emp.nombre_completo
        FROM PLAN_CARRERA pc
        LEFT JOIN EMPLEADO emp ON pc.id_plan_carrera = emp.id_plan_carrera
        ORDER BY pc.id_plan_carrera DESC;
    """)
    planes_carrera = cursor.fetchall()

    cursor.close()
    cnx.close()

    return render_template(
        "evaluacion.html",
        evaluaciones=evaluaciones,
        empleados=empleados,
        capacitaciones=capacitaciones,
        planes_carrera=planes_carrera
    )


# ---------------------------
# AGREGAR EVALUACION
# ---------------------------
@evaluacion_bp.route("/evaluacion/agregar", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
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

    flash("Evaluación agregada correctamente.", "success")
    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# EDITAR EVALUACION
# ---------------------------
@evaluacion_bp.route("/evaluacion/editar/<int:id_eval>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
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

    existe = row["cnt"] if isinstance(row, dict) else row[0]

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

    flash("Evaluación actualizada correctamente.", "success")
    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# ELIMINAR EVALUACION
# ---------------------------
@evaluacion_bp.route("/evaluacion/eliminar/<int:id_eval>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def eliminar_evaluacion(id_eval):
    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("DELETE FROM `EMPLEADO-EVALUACION` WHERE id_evaluacion=%s;", (id_eval,))
    cursor.execute("DELETE FROM EVALUACION WHERE id_evaluacion=%s;", (id_eval,))

    cnx.commit()
    cursor.close()
    cnx.close()

    flash("Evaluación eliminada correctamente.", "success")
    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# AGREGAR CAPACITACION
# ---------------------------
@evaluacion_bp.route("/evaluacion/agregar_capacitacion", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def agregar_capacitacion():
    id_empleado = request.form.get("id_empleado") or None
    id_capacitacion = request.form.get("id_capacitacion")
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")
    resultado = request.form.get("resultado") or 0
    comentarios = request.form.get("comentarios") or ""

    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        flash("La fecha de inicio no puede ser posterior a la fecha final.", "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        INSERT INTO `EMPLEADO-CAPACITACION` (id_empleado, id_capacitacion, fecha_inicio, fecha_fin, resultado, comentarios)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, (id_empleado, id_capacitacion, fecha_inicio, fecha_fin, resultado, comentarios))

    cnx.commit()
    cursor.close()
    cnx.close()

    flash("Capacitación agregada correctamente.", "success")
    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# EDITAR CAPACITACION
# ---------------------------
@evaluacion_bp.route("/evaluacion/editar_capacitacion/<int:id_empleado_capacitacion>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def editar_capacitacion(id_empleado_capacitacion):
    id_empleado = request.form.get("id_empleado") or None
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")
    resultado = request.form.get("resultado") or 0
    comentarios = request.form.get("comentarios") or ""

    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        flash("La fecha de inicio no puede ser posterior a la fecha final.", "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        UPDATE `EMPLEADO-CAPACITACION`
        SET id_empleado=%s, fecha_inicio=%s, fecha_fin=%s, resultado=%s, comentarios=%s
        WHERE `id_empleado-capacitacion`=%s;
    """, (id_empleado, fecha_inicio, fecha_fin, resultado, comentarios, id_empleado_capacitacion))

    cnx.commit()
    cursor.close()
    cnx.close()

    flash("Capacitación actualizada correctamente.", "success")
    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# ELIMINAR CAPACITACION
# ---------------------------
@evaluacion_bp.route("/evaluacion/eliminar_capacitacion/<int:id_empleado_capacitacion>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def eliminar_capacitacion(id_empleado_capacitacion):
    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("DELETE FROM `EMPLEADO-CAPACITACION` WHERE `id_empleado-capacitacion`=%s;", (id_empleado_capacitacion,))

    cnx.commit()
    cursor.close()
    cnx.close()

    flash("Capacitación eliminada correctamente.", "success")
    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# AGREGAR PLAN DE CARRERA
# ---------------------------
@evaluacion_bp.route("/evaluacion/agregar_plan_carrera", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def agregar_plan_carrera():
    objetivo = request.form.get("objetivo")
    etapas = request.form.get("etapas")
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")

    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        flash("La fecha de inicio no puede ser posterior a la fecha final.", "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        INSERT INTO PLAN_CARRERA (objetivo, etapas, fecha_inicio, fecha_fin)
        VALUES (%s, %s, %s, %s);
    """, (objetivo, etapas, fecha_inicio, fecha_fin))

    cnx.commit()
    cursor.close()
    cnx.close()

    flash("Plan de Carrera agregado correctamente.", "success")
    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# EDITAR PLAN DE CARRERA
# ---------------------------
@evaluacion_bp.route("/evaluacion/editar_plan_carrera/<int:id_plan>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def editar_plan_carrera(id_plan):
    objetivo = request.form.get("objetivo")
    etapas = request.form.get("etapas")
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")

    if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
        flash("La fecha de inicio no puede ser posterior a la fecha final.", "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        UPDATE PLAN_CARRERA
        SET objetivo=%s, etapas=%s, fecha_inicio=%s, fecha_fin=%s
        WHERE id_plan_carrera=%s;
    """, (objetivo, etapas, fecha_inicio, fecha_fin, id_plan))

    cnx.commit()
    cursor.close()
    cnx.close()

    flash("Plan de Carrera actualizado correctamente.", "success")
    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# ELIMINAR PLAN DE CARRERA
# ---------------------------
@evaluacion_bp.route("/evaluacion/eliminar_plan_carrera/<int:id_plan>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def eliminar_plan_carrera(id_plan):
    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("DELETE FROM PLAN_CARRERA WHERE id_plan_carrera=%s;", (id_plan,))

    cnx.commit()
    cursor.close()
    cnx.close()

    flash("Plan de Carrera eliminado correctamente.", "success")
    return redirect(url_for("evaluacion.evaluacion"))