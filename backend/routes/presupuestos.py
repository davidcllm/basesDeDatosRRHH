# Este archivo fue creado con ayuda de la Inteligencia Artificial de OpenAI. 
# OpenAI. (2025). ChatGPT [Modelo de lenguaje de gran tamaño]. https://chat.openai.com/chat

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql
from datetime import datetime

presupuestos_bp = Blueprint("presupuestos", __name__)

# Encontrar presupuestos
@presupuestos_bp.route("/presupuestos")
@jwt_required()
@roles_required('administrador','finanzas')
def presupuestos():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    # --- Departamentos para selects ---
    cursor.execute("SELECT id_departamento, nombre FROM DEPARTAMENTO;")
    departamentos = cursor.fetchall()

    cursor.close()
    cnx.close()

    return render_template(
        "presupuestos.html",
        departamentos=departamentos
    )

# ENDPOINTS PARA CARGAR DATOS VÍA AJAX
@presupuestos_bp.route("/presupuestos/get_presupuestos")
@jwt_required()
@roles_required('administrador','finanzas')
def get_presupuestos():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT P.id_presupuesto,
               DATE_FORMAT(P.fecha_inicio, '%Y-%m-%d') AS fecha_inicio,
               DATE_FORMAT(P.fecha_fin, '%Y-%m-%d') AS fecha_fin,
               P.monto_asignado, P.monto_utilizado, D.nombre AS departamento, 
               D.id_departamento
        FROM PRESUPUESTO P
        JOIN DEPARTAMENTO D ON P.id_departamento = D.id_departamento
        ORDER BY P.id_presupuesto DESC;
    """)
    presupuestos = cursor.fetchall()

    cursor.close()
    cnx.close()

    return jsonify(presupuestos)

@presupuestos_bp.route("/presupuestos/get_centros")
@jwt_required()
@roles_required('administrador','finanzas')
def get_centros():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT C.id_centro_costo,
               C.nombre,
               C.descipcion,
               D.nombre AS departamento
        FROM CENTRO_COSTO C
        JOIN DEPARTAMENTO D ON C.id_departamento = D.id_departamento
        ORDER BY C.id_centro_costo DESC;
    """)
    centros = cursor.fetchall()

    cursor.close()
    cnx.close()

    return jsonify(centros)

# Validar departamento existe
def validate_departamento(id_departamento):
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT id_departamento FROM DEPARTAMENTO WHERE id_departamento = %s", (id_departamento,))
    exists = cursor.fetchone()
    cursor.close()
    cnx.close()
    return exists is not None

# Crear presupuestos (antes crear_presupuesto)
@presupuestos_bp.route("/presupuestos/crear", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def crear_presupuesto():
    fecha_inicio = request.form.get("fecha_inicio", "").strip()
    fecha_fin = request.form.get("fecha_fin", "").strip()
    asignado = request.form.get("monto_asignado", "").strip()
    utilizado = request.form.get("monto_utilizado", "").strip()
    id_departamento = request.form.get("id_departamento", "").strip()

    # Validar fechas (YYYY-MM-DD)
    try:
        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        if fi > ff:
            flash("La fecha de inicio no puede ser posterior a la fecha de fin.", "error")
            return redirect(url_for("presupuestos.presupuestos"))
    except Exception:
        flash("Fechas inválidas. Use formato YYYY-MM-DD.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    # Validar montos son números positivos
    try:
        asignado_float = float(asignado)
        utilizado_float = float(utilizado)
        if asignado_float <= 0 or utilizado_float < 0:
            flash("Los montos deben ser números positivos.", "error")
            return redirect(url_for("presupuestos.presupuestos"))
    except ValueError:
        flash("Los montos deben ser números válidos.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    # Validar monto utilizado <= monto asignado
    if utilizado_float > asignado_float:
        flash("El monto utilizado no puede ser mayor al monto asignado.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    # Validar departamento existe
    if not id_departamento or not id_departamento.isdigit() or not validate_departamento(id_departamento):
        flash("Debe seleccionar un departamento válido.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            INSERT INTO PRESUPUESTO (fecha_inicio, fecha_fin, monto_asignado, monto_utilizado, id_departamento)
            VALUES (%s, %s, %s, %s, %s)
        """, (fecha_inicio, fecha_fin, asignado_float, utilizado_float, id_departamento))
        cnx.commit()
        flash("Presupuesto creado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al crear presupuesto: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))

# Editar presupuesto (actualizar_presupuesto)
@presupuestos_bp.route("/presupuestos/actualizar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def actualizar_presupuesto(id):
    fecha_inicio = request.form.get("fecha_inicio", "").strip()
    fecha_fin = request.form.get("fecha_fin", "").strip()
    asignado = request.form.get("monto_asignado", "").strip()
    utilizado = request.form.get("monto_utilizado", "").strip()
    id_departamento = request.form.get("id_departamento", "").strip()

    # Validar fechas (YYYY-MM-DD)
    try:
        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        if fi > ff:
            flash("La fecha de inicio no puede ser posterior a la fecha de fin.", "error")
            return redirect(url_for("presupuestos.presupuestos"))
    except Exception:
        flash("Fechas inválidas. Use formato YYYY-MM-DD.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    # Validar montos
    try:
        asignado_float = float(asignado)
        utilizado_float = float(utilizado)
        if asignado_float <= 0 or utilizado_float < 0:
            flash("Los montos deben ser números positivos.", "error")
            return redirect(url_for("presupuestos.presupuestos"))
    except ValueError:
        flash("Los montos deben ser números válidos.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    if utilizado_float > asignado_float:
        flash("El monto utilizado no puede ser mayor al monto asignado.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    if not id_departamento or not id_departamento.isdigit() or not validate_departamento(id_departamento):
        flash("Debe seleccionar un departamento válido.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            UPDATE PRESUPUESTO
            SET fecha_inicio=%s, fecha_fin=%s, monto_asignado=%s, monto_utilizado=%s, id_departamento=%s
            WHERE id_presupuesto=%s
        """, (fecha_inicio, fecha_fin, asignado_float, utilizado_float, id_departamento, id))
        cnx.commit()
        flash("Presupuesto actualizado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al actualizar presupuesto: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))

# Eliminar presupuesto
@presupuestos_bp.route("/presupuestos/eliminar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def eliminar_presupuesto(id):
    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("DELETE FROM PRESUPUESTO WHERE id_presupuesto=%s", (id,))
        cnx.commit()
        flash("Presupuesto eliminado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al eliminar presupuesto: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))

# Centro costo - validaciones
def validate_centro_costo_lengths(nombre, descripcion):
    if len(nombre) > 45:
        return False, "El nombre no puede exceder 45 caracteres."
    if len(descripcion) > 100:
        return False, "La descripción no puede exceder 100 caracteres."
    return True, ""

# Crear centro costo
@presupuestos_bp.route("/centro_costo/crear", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def crear_centro_costo():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    id_departamento = request.form.get("id_departamento", "").strip()

    # Validar longitudes
    valid, msg = validate_centro_costo_lengths(nombre, descripcion)
    if not valid:
        flash(msg, "error")
        return redirect(url_for("presupuestos.presupuestos"))

    # Validar que no estén vacíos
    if not nombre or not descripcion:
        flash("El nombre y descripción no pueden estar vacíos.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    # Validar departamento existe
    if not id_departamento or not id_departamento.isdigit():
        flash("Debe seleccionar un departamento válido.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    if not validate_departamento(id_departamento):
        flash("El departamento seleccionado no existe.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            INSERT INTO CENTRO_COSTO (nombre, descipcion, id_departamento)
            VALUES (%s, %s, %s)
        """, (nombre, descripcion, id_departamento))
        cnx.commit()
        flash("Centro de costo creado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al crear centro de costo: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))

# Actualizar centro costo
@presupuestos_bp.route("/centro_costo/actualizar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def actualizar_centro_costo(id):
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    id_departamento = request.form.get("id_departamento", "").strip()

    # Validar longitudes
    valid, msg = validate_centro_costo_lengths(nombre, descripcion)
    if not valid:
        flash(msg, "error")
        return redirect(url_for("presupuestos.presupuestos"))

    # Validar que no estén vacíos
    if not nombre or not descripcion:
        flash("El nombre y descripción no pueden estar vacíos.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    # Validar departamento existe
    if not id_departamento or not id_departamento.isdigit():
        flash("Debe seleccionar un departamento válido.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    if not validate_departamento(id_departamento):
        flash("El departamento seleccionado no existe.", "error")
        return redirect(url_for("presupuestos.presupuestos"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            UPDATE CENTRO_COSTO
            SET nombre=%s, descipcion=%s, id_departamento=%s
            WHERE id_centro_costo=%s
        """, (nombre, descripcion, id_departamento, id))
        cnx.commit()
        flash("Centro de costo actualizado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al actualizar centro de costo: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))

# Eliminar centro costo
@presupuestos_bp.route("/centro_costo/eliminar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def eliminar_centro_costo(id):
    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        # Verificar si hay cuentas contables asociadas
        cursor.execute("SELECT 1 FROM CUENTA_CONTABLE WHERE id_centro_costo = %s LIMIT 1;", (id,))
        if cursor.fetchone():
            flash("No se puede eliminar el centro de costo porque tiene cuentas contables asociadas.", "error")
            return redirect(url_for("presupuestos.presupuestos"))

        # Si no hay dependencias, proceder a eliminar
        cursor.execute("DELETE FROM CENTRO_COSTO WHERE id_centro_costo=%s", (id,))
        cnx.commit()
        flash("Centro de costo eliminado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al eliminar centro de costo: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))