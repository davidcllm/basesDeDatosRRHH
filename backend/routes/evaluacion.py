# Este archivo fue creado con ayuda de la Inteligencia Artificial de OpenAI. 
# OpenAI. (2025). ChatGPT [Modelo de lenguaje de gran tamaño]. https://chat.openai.com/chat

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql
from datetime import datetime

evaluacion_bp = Blueprint("evaluacion", __name__)


def validar_fechas(fecha_inicio, fecha_fin):
    """Valida que fecha_inicio sea menor que fecha_fin"""
    try:
        fi = datetime.fromisoformat(fecha_inicio)
        ff = datetime.fromisoformat(fecha_fin)
        if fi >= ff:
            return False, "La fecha de inicio debe ser anterior a la fecha final"
        return True, ""
    except:
        return False, "Formato de fecha inválido"


def validar_tipo_evaluacion(tipo):
    """Valida que tipo no contenga números"""
    if not tipo or not isinstance(tipo, str):
        return False, "El tipo es requerido"
    if any(char.isdigit() for char in tipo):
        return False, "El tipo no puede contener números"
    if len(tipo.strip()) == 0:
        return False, "El tipo no puede estar vacío"
    return True, ""


def validar_resultado_evaluacion(resultado):
    """Valida que resultado sea un número válido"""
    if not resultado or not isinstance(resultado, str):
        return False, "El resultado es requerido"
    try:
        float(resultado)
        return True, ""
    except ValueError:
        return False, "El resultado debe ser un número válido"


def validar_resultado_capacitacion(resultado):
    """Valida que resultado sea un número entre 0 y 100"""
    if resultado == "" or resultado is None:
        return True, ""  # Es opcional
    try:
        val = float(resultado)
        if val < 0 or val > 100:
            return False, "El resultado debe estar entre 0 y 100"
        return True, ""
    except ValueError:
        return False, "El resultado debe ser un número válido"


@evaluacion_bp.route("/evaluacion")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def evaluacion():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT id_empleado, nombre_completo FROM EMPLEADO ORDER BY nombre_completo;")
    empleados = cursor.fetchall()

    cursor.execute("SELECT id_capacitacion, nombre FROM CAPACITACION ORDER BY nombre;")
    capacitaciones_lista = cursor.fetchall()

    cursor.execute("""
        SELECT id_empleado, nombre_completo 
        FROM EMPLEADO 
        WHERE id_plan_carrera IS NULL OR id_plan_carrera = 0
        ORDER BY nombre_completo;
    """)
    empleados_sin_plan = cursor.fetchall()

    cursor.close()
    cnx.close()

    return render_template(
        "evaluacion.html",
        empleados=empleados,
        capacitaciones_lista=capacitaciones_lista,
        empleados_sin_plan=empleados_sin_plan
    )


# ENDPOINTS PARA CARGAR DATOS VÍA AJAX
@evaluacion_bp.route("/evaluacion/get_evaluaciones")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def get_evaluaciones():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

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
        ORDER BY e.id_evaluacion DESC;
    """)
    evaluaciones = cursor.fetchall()

    cursor.close()
    cnx.close()

    return jsonify(evaluaciones)


@evaluacion_bp.route("/evaluacion/get_capacitaciones")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def get_capacitaciones():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT ec.`id_empleado-capacitacion`,
               c.id_capacitacion,
               c.nombre,
               c.descripcion,
               ec.fecha_inicio,
               ec.fecha_fin,
               c.proveedor,
               ec.id_empleado,
               emp.nombre_completo,
               ec.resultado,
               ec.comentarios
        FROM `EMPLEADO-CAPACITACION` ec
        LEFT JOIN CAPACITACION c ON ec.id_capacitacion = c.id_capacitacion
        LEFT JOIN EMPLEADO emp ON ec.id_empleado = emp.id_empleado
        ORDER BY ec.`id_empleado-capacitacion` DESC;
    """)
    capacitaciones = cursor.fetchall()

    cursor.close()
    cnx.close()

    return jsonify(capacitaciones)


@evaluacion_bp.route("/evaluacion/get_planes_carrera")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def get_planes_carrera():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

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

    return jsonify(planes_carrera)


# ---------------------------
# AGREGAR EVALUACION
# ---------------------------
@evaluacion_bp.route("/evaluacion/agregar_evaluacion", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def agregar_evaluacion():
    id_empleado = request.form.get("id_empleado") or None
    fecha_evaluacion = request.form.get("fecha_evaluacion")
    tipo = request.form.get("tipo", "").strip()
    resultado = request.form.get("resultado", "").strip()
    observaciones = request.form.get("observaciones", "").strip()
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")

    errores = []

    # Validar tipo
    es_valido, msg = validar_tipo_evaluacion(tipo)
    if not es_valido:
        errores.append(f"Tipo: {msg}")

    # Validar resultado
    es_valido, msg = validar_resultado_evaluacion(resultado)
    if not es_valido:
        errores.append(f"Resultado: {msg}")

    # Validar fechas
    es_valido, msg = validar_fechas(fecha_inicio, fecha_fin)
    if not es_valido:
        errores.append(f"Fechas: {msg}")

    if errores:
        for error in errores:
            flash(error, "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
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
        flash("Evaluación agregada correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al agregar evaluación: {str(e)}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# EDITAR EVALUACION
# ---------------------------
@evaluacion_bp.route("/evaluacion/editar_evaluacion/<int:id_eval>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def editar_evaluacion(id_eval):
    fecha_evaluacion = request.form.get("fecha_evaluacion")
    tipo = request.form.get("tipo", "").strip()
    resultado = request.form.get("resultado", "").strip()
    observaciones = request.form.get("observaciones", "").strip()
    id_empleado = request.form.get("id_empleado") or None
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")

    errores = []

    # Validar tipo
    es_valido, msg = validar_tipo_evaluacion(tipo)
    if not es_valido:
        errores.append(f"Tipo: {msg}")

    # Validar resultado
    es_valido, msg = validar_resultado_evaluacion(resultado)
    if not es_valido:
        errores.append(f"Resultado: {msg}")

    # Validar fechas
    es_valido, msg = validar_fechas(fecha_inicio, fecha_fin)
    if not es_valido:
        errores.append(f"Fechas: {msg}")

    if errores:
        for error in errores:
            flash(error, "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
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
        flash("Evaluación actualizada correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al actualizar evaluación: {str(e)}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# ELIMINAR EVALUACION
# ---------------------------
@evaluacion_bp.route("/evaluacion/eliminar_evaluacion/<int:id_eval>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def eliminar_evaluacion(id_eval):
    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("DELETE FROM `EMPLEADO-EVALUACION` WHERE id_evaluacion=%s;", (id_eval,))
        cursor.execute("DELETE FROM EVALUACION WHERE id_evaluacion=%s;", (id_eval,))

        cnx.commit()
        flash("Evaluación eliminada correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al eliminar evaluación: {str(e)}", "error")
    finally:
        cursor.close()
        cnx.close()

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
    fecha_inicio = parsear_fecha_local(request.form.get("fecha_inicio"))
    fecha_fin = parsear_fecha_local(request.form.get("fecha_fin"))
    resultado = request.form.get("resultado", "").strip()
    comentarios = request.form.get("comentarios", "").strip()

    errores = []

    # Validar que las fechas no sean None
    if not fecha_inicio:
        errores.append("Fecha de inicio: campo requerido")
    if not fecha_fin:
        errores.append("Fecha fin: campo requerido")

    # Validar fechas (solo si ambas existen)
    if fecha_inicio and fecha_fin:
        es_valido, msg = validar_fechas(fecha_inicio, fecha_fin)
        if not es_valido:
            errores.append(f"Fechas: {msg}")

    # Validar resultado
    es_valido, msg = validar_resultado_capacitacion(resultado)
    if not es_valido:
        errores.append(f"Resultado: {msg}")

    if errores:
        for error in errores:
            flash(error, "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        resultado_val = float(resultado) if resultado else 0
        cursor.execute("""
            INSERT INTO `EMPLEADO-CAPACITACION` (id_empleado, id_capacitacion, fecha_inicio, fecha_fin, resultado, comentarios)
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (id_empleado, id_capacitacion, fecha_inicio, fecha_fin, resultado_val, comentarios))

        cnx.commit()
        flash("Capacitación agregada correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al agregar capacitación: {str(e)}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# EDITAR CAPACITACION
# ---------------------------

def parsear_fecha_local(fecha_string):
    """Convierte fecha local sin afectar por timezone"""
    if not fecha_string:
        return None
    try:
        # Toma la fecha como está, sin conversión de timezone
        return datetime.fromisoformat(fecha_string)
    except:
        return None

@evaluacion_bp.route("/evaluacion/editar_capacitacion/<int:id_empleado_capacitacion>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def editar_capacitacion(id_empleado_capacitacion):
    id_empleado = request.form.get("id_empleado") or None
    fecha_inicio = parsear_fecha_local(request.form.get("fecha_inicio"))
    fecha_fin = parsear_fecha_local(request.form.get("fecha_fin"))
    resultado = request.form.get("resultado", "").strip()
    comentarios = request.form.get("comentarios", "").strip()

    errores = []

    # Validar que las fechas no sean None
    if not fecha_inicio:
        errores.append("Fecha de inicio: campo requerido")
    if not fecha_fin:
        errores.append("Fecha fin: campo requerido")

    # Validar fechas (solo si ambas existen)
    if fecha_inicio and fecha_fin:
        es_valido, msg = validar_fechas(fecha_inicio, fecha_fin)
        if not es_valido:
            errores.append(f"Fechas: {msg}")

    # Validar resultado
    es_valido, msg = validar_resultado_capacitacion(resultado)
    if not es_valido:
        errores.append(f"Resultado: {msg}")

    if errores:
        for error in errores:
            flash(error, "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        resultado_val = float(resultado) if resultado else 0
        cursor.execute("""
            UPDATE `EMPLEADO-CAPACITACION`
            SET id_empleado=%s, fecha_inicio=%s, fecha_fin=%s, resultado=%s, comentarios=%s
            WHERE `id_empleado-capacitacion`=%s;
        """, (id_empleado, fecha_inicio, fecha_fin, resultado_val, comentarios, id_empleado_capacitacion))

        cnx.commit()
        flash("Capacitación actualizada correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al actualizar capacitación: {str(e)}", "error")
    finally:
        cursor.close()
        cnx.close()

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

    try:
        cursor.execute("DELETE FROM `EMPLEADO-CAPACITACION` WHERE `id_empleado-capacitacion`=%s;", (id_empleado_capacitacion,))

        cnx.commit()
        flash("Capacitación eliminada correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al eliminar capacitación: {str(e)}", "error")
    finally:
        cursor.close()
        cnx.close()

# ---------------------------
# AGREGAR PLAN DE CARRERA
# ---------------------------
@evaluacion_bp.route("/evaluacion/agregar_plan_carrera", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def agregar_plan_carrera():
    from datetime import datetime
    
    objetivo = request.form.get("objetivo", "").strip()
    etapas = request.form.get("etapas", "").strip()
    fecha_inicio_str = request.form.get("fecha_inicio")
    fecha_fin_str = request.form.get("fecha_fin")

    errores = []

    if not objetivo:
        errores.append("Objetivo: El objetivo es requerido")

    if not etapas:
        errores.append("Etapas: Las etapas son requeridas")

    # Convertir datetime-local a datetime object
    fecha_inicio = None
    fecha_fin = None
    
    try:
        if fecha_inicio_str:
            # datetime-local envía formato: "2026-03-01T10:00"
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        errores.append("Fecha Inicio: Formato de fecha inválido")
    
    try:
        if fecha_fin_str:
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%dT%H:%M")
    except ValueError:
        errores.append("Fecha Fin: Formato de fecha inválido")

    # Validar fechas
    if fecha_inicio and fecha_fin:
        if fecha_fin <= fecha_inicio:
            errores.append("Fechas: La fecha de fin debe ser posterior a la fecha de inicio")

    if errores:
        for error in errores:
            flash(error, "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        # Crear el plan de carrera con datetime objects
        cursor.execute("""
            INSERT INTO PLAN_CARRERA (objetivo, etapas, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s, %s);
        """, (objetivo, etapas, fecha_inicio, fecha_fin))
        
        cnx.commit()
        flash("Plan de Carrera agregado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al agregar plan de carrera: {str(e)}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("evaluacion.evaluacion"))


# ---------------------------
# EDITAR PLAN DE CARRERA
# ---------------------------
@evaluacion_bp.route("/evaluacion/editar_plan_carrera/<int:id_plan>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def editar_plan_carrera(id_plan):
    objetivo = request.form.get("objetivo", "").strip()
    etapas = request.form.get("etapas", "").strip()
    fecha_inicio = request.form.get("fecha_inicio")
    fecha_fin = request.form.get("fecha_fin")

    errores = []

    if not objetivo:
        errores.append("Objetivo: El objetivo es requerido")

    if not etapas:
        errores.append("Etapas: Las etapas son requeridas")

    # Validar fechas
    es_valido, msg = validar_fechas(fecha_inicio, fecha_fin)
    if not es_valido:
        errores.append(f"Fechas: {msg}")

    if errores:
        for error in errores:
            flash(error, "error")
        return redirect(url_for("evaluacion.evaluacion"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            UPDATE PLAN_CARRERA
            SET objetivo=%s, etapas=%s, fecha_inicio=%s, fecha_fin=%s
            WHERE id_plan_carrera=%s;
        """, (objetivo, etapas, fecha_inicio, fecha_fin, id_plan))

        cnx.commit()
        flash("Plan de Carrera actualizado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al actualizar plan de carrera: {str(e)}", "error")
    finally:
        cursor.close()
        cnx.close()

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

    try:
        # Workaround: Set id_plan_carrera to 0 instead of NULL because of NOT NULL constraint.
        cursor.execute("UPDATE EMPLEADO SET id_plan_carrera=NULL WHERE id_plan_carrera=%s;", (id_plan,))
        cursor.execute("DELETE FROM PLAN_CARRERA WHERE id_plan_carrera=%s;", (id_plan,))

        cnx.commit()
        flash("Plan de Carrera eliminado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al eliminar plan de carrera: {str(e)}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("evaluacion.evaluacion"))