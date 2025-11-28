from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql 
from datetime import datetime

proyectos_bp = Blueprint("proyectos", __name__)

#Listar proyectos (renders the template)
@proyectos_bp.route("/proyectos")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def proyectos():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    # --- Proyectos --- (no cargamos aquí la tabla completa para permitir carga bajo demanda)
    cursor.execute("""
        SELECT id_proyecto, nombre, descripcion
        FROM PROYECTO;
    """)
    proyectos = cursor.fetchall()

    # --- Empleados para el select (se usa por defecto en el template si se necesita) ---
    cursor.execute("""
        SELECT id_empleado, nombre_completo
        FROM EMPLEADO;
    """)
    empleados = cursor.fetchall()

    cursor.close()
    cnx.close()

    return render_template(
        "proyectos.html",
        proyectos=proyectos,
        empleados=empleados
    )

# --- ENDPOINT JSON: devolver proyectos (para AJAX) ---
@proyectos_bp.route("/proyectos/get_proyectos")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def get_proyectos():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT id_proyecto, nombre, descripcion FROM PROYECTO ORDER BY id_proyecto DESC;")
    data = cursor.fetchall()
    cursor.close()
    cnx.close()
    return jsonify(data)

# --- ENDPOINT JSON: devolver empleados (para selects en modales) ---
@proyectos_bp.route("/proyectos/get_empleados")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def get_empleados():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT id_empleado, nombre_completo FROM EMPLEADO ORDER BY nombre_completo;")
    data = cursor.fetchall()
    cursor.close()
    cnx.close()
    return jsonify(data)

# ENDPOINT JSON: devolver asignaciones (para AJAX)
@proyectos_bp.route("/proyectos/get_asignaciones")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def get_asignaciones():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)
    cursor.execute("""
        SELECT 
            ep.`id_empleado-proyecto` AS id,
            ep.id_empleado,
            e.nombre_completo AS empleado,
            ep.id_proyecto,
            p.nombre AS proyecto,
            ep.horas_asignadas,
            DATE_FORMAT(ep.fecha_asignacion, '%Y-%m-%d') AS fecha_asignacion,
            DATE_FORMAT(ep.fecha_entrega, '%Y-%m-%d') AS fecha_entrega
        FROM `EMPLEADO-PROYECTO` ep
        JOIN EMPLEADO e ON ep.id_empleado = e.id_empleado
        JOIN PROYECTO p ON ep.id_proyecto = p.id_proyecto
        ORDER BY ep.`id_empleado-proyecto` DESC;
    """)
    data = cursor.fetchall()
    cursor.close()
    cnx.close()
    return jsonify(data)

# --- ENDPOINT JSON: devolver departamentos (para AJAX) ---
@proyectos_bp.route("/departamentos/get_departamentos")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def get_departamentos():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT id_departamento, nombre, descripcion FROM DEPARTAMENTO ORDER BY id_departamento DESC;")
    data = cursor.fetchall()
    cursor.close()
    cnx.close()
    return jsonify(data)

# Crear departamento
@proyectos_bp.route("/departamentos/crear", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def crear_departamento():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    if not nombre or not descripcion:
        flash("Nombre y descripción son obligatorios.", "error")
        return redirect(url_for("proyectos.proyectos"))

    if len(nombre) > 45:
        flash("El nombre no puede exceder 45 caracteres.", "error")
        return redirect(url_for("proyectos.proyectos"))

    if len(descripcion) > 145:
        flash("La descripción no puede exceder 145 caracteres.", "error")
        return redirect(url_for("proyectos.proyectos"))

    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("INSERT INTO DEPARTAMENTO (nombre, descripcion) VALUES (%s, %s);", (nombre, descripcion))
        cnx.commit()
        flash("Departamento creado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al crear departamento: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("proyectos.proyectos"))

# Actualizar departamento
@proyectos_bp.route("/departamentos/actualizar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def actualizar_departamento(id):
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    if not nombre or not descripcion:
        flash("Nombre y descripción son obligatorios.", "error")
        return redirect(url_for("proyectos.proyectos"))

    if len(nombre) > 45:
        flash("El nombre no puede exceder 45 caracteres.", "error")
        return redirect(url_for("proyectos.proyectos"))

    if len(descripcion) > 145:
        flash("La descripción no puede exceder 145 caracteres.", "error")
        return redirect(url_for("proyectos.proyectos"))

    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("UPDATE DEPARTAMENTO SET nombre=%s, descripcion=%s WHERE id_departamento=%s", (nombre, descripcion, id))
        cnx.commit()
        flash("Departamento actualizado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al actualizar departamento: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("proyectos.proyectos"))

# Eliminar departamento
@proyectos_bp.route("/departamentos/eliminar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def eliminar_departamento(id):
    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("DELETE FROM DEPARTAMENTO WHERE id_departamento=%s", (id,))
        cnx.commit()
        flash("Departamento eliminado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al eliminar departamento: {e}", "error")
    finally:
        cursor.close()
        cnx.close()
    return redirect(url_for("proyectos.proyectos"))

#crear proyectos
@proyectos_bp.route("/proyectos/crear", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def crear_proyecto():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    # Validar que no estén vacíos
    if not nombre or not descripcion:
        flash("El nombre y descripción no pueden estar vacíos.", "error")
        return redirect(url_for("proyectos.proyectos"))

    # Validar longitudes
    valid, msg = validate_proyecto_lengths(nombre, descripcion)
    if not valid:
        flash(msg, "error")
        return redirect(url_for("proyectos.proyectos"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            INSERT INTO PROYECTO (nombre, descripcion)
            VALUES (%s, %s);
        """, (nombre, descripcion))

        cnx.commit()
        flash("Proyecto creado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al crear proyecto: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("proyectos.proyectos"))

#eliminar
@proyectos_bp.route("/proyectos/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def eliminar_proyecto(id):

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("DELETE FROM PROYECTO WHERE id_proyecto = %s;", (id,))
        cnx.commit()
        flash("Proyecto eliminado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al eliminar proyecto: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("proyectos.proyectos"))

#Actualizar
@proyectos_bp.route("/proyectos/actualizar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def actualizar_proyecto(id):
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()

    # Validar que no estén vacíos
    if not nombre or not descripcion:
        flash("El nombre y descripción no pueden estar vacíos.", "error")
        return redirect(url_for("proyectos.proyectos"))

    # Validar longitudes
    valid, msg = validate_proyecto_lengths(nombre, descripcion)
    if not valid:
        flash(msg, "error")
        return redirect(url_for("proyectos.proyectos"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            UPDATE PROYECTO
            SET nombre=%s, descripcion=%s
            WHERE id_proyecto=%s
        """, (nombre, descripcion, id))

        cnx.commit()
        flash("Proyecto actualizado correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al actualizar proyecto: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("proyectos.proyectos"))

#Asignar empleado a proyecto
@proyectos_bp.route("/proyectos/asignar", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def asignar_empleado():
    id_empleado = request.form.get("id_empleado", "").strip()
    id_proyecto = request.form.get("id_proyecto", "").strip()
    horas = request.form.get("horas_asignadas", "").strip()
    fecha_asignacion = request.form.get("fecha_asignacion", "").strip()
    fecha_entrega = request.form.get("fecha_entrega", "").strip()

    # Validar que empleado esté seleccionado
    if not id_empleado or not id_empleado.isdigit():
        flash("Debe seleccionar un empleado válido.", "error")
        return redirect(url_for("proyectos.proyectos"))

    # Validar que horas sea número positivo
    try:
        horas_int = int(horas)
        if horas_int <= 0:
            flash("Las horas asignadas deben ser un número positivo.", "error")
            return redirect(url_for("proyectos.proyectos"))
    except ValueError:
        flash("Las horas asignadas deben ser un número válido.", "error")
        return redirect(url_for("proyectos.proyectos"))

    # Validar que fecha_asignacion no sea posterior a fecha_entrega
    if fecha_asignacion >= fecha_entrega:
        flash("La fecha de asignación no puede ser igual o posterior a la fecha de entrega.", "error")
        return redirect(url_for("proyectos.proyectos"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            INSERT INTO `EMPLEADO-PROYECTO` 
            (id_empleado, id_proyecto, horas_asignadas, fecha_asignacion, fecha_entrega)
            VALUES (%s, %s, %s, %s, %s)
        """, (id_empleado, id_proyecto, horas_int, fecha_asignacion, fecha_entrega))

        cnx.commit()
        flash("Empleado asignado al proyecto correctamente.", "success")

    except Exception as e:
        cnx.rollback()
        flash(f"Error al asignar empleado: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("proyectos.proyectos"))

# Actualizar asignación (editar)
@proyectos_bp.route("/proyectos/asignacion/actualizar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def actualizar_asignacion(id):
    id_empleado = request.form.get("id_empleado", "").strip()
    id_proyecto = request.form.get("id_proyecto", "").strip()
    horas = request.form.get("horas_asignadas", "").strip()
    fecha_asignacion = request.form.get("fecha_asignacion", "").strip()
    fecha_entrega = request.form.get("fecha_entrega", "").strip()

    # validaciones básicas
    if not id_empleado or not id_empleado.isdigit() or not validate_empleado(id_empleado):
        flash("Empleado inválido.", "error")
        return redirect(url_for("proyectos.proyectos"))

    if not id_proyecto or not id_proyecto.isdigit() or not validate_proyecto(id_proyecto):
        flash("Proyecto inválido.", "error")
        return redirect(url_for("proyectos.proyectos"))

    try:
        horas_int = int(horas)
        if horas_int <= 0:
            raise ValueError
    except ValueError:
        flash("Las horas asignadas deben ser un entero positivo.", "error")
        return redirect(url_for("proyectos.proyectos"))

    # validar fechas (formato YYYY-MM-DD) y orden
    try:
        fecha_a = datetime.strptime(fecha_asignacion, "%Y-%m-%d").date()
        fecha_f = datetime.strptime(fecha_entrega, "%Y-%m-%d").date()
        if fecha_a >= fecha_f:
            flash("La fecha de asignación debe ser anterior a la fecha de entrega.", "error")
            return redirect(url_for("proyectos.proyectos"))
    except Exception:
        flash("Fechas inválidas.", "error")
        return redirect(url_for("proyectos.proyectos"))

    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("""
            UPDATE `EMPLEADO-PROYECTO`
            SET id_empleado=%s, id_proyecto=%s, horas_asignadas=%s, fecha_asignacion=%s, fecha_entrega=%s
            WHERE `id_empleado-proyecto`=%s
        """, (id_empleado, id_proyecto, horas_int, fecha_asignacion, fecha_entrega, id))
        cnx.commit()
        flash("Asignación actualizada correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al actualizar asignación: {e}", "error")
    finally:
        cursor.close()
        cnx.close()

    return redirect(url_for("proyectos.proyectos"))

# Eliminar asignación
@proyectos_bp.route("/proyectos/asignacion/eliminar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def eliminar_asignacion(id):
    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("DELETE FROM `EMPLEADO-PROYECTO` WHERE `id_empleado-proyecto`=%s", (id,))
        cnx.commit()
        flash("Asignación eliminada correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al eliminar asignación: {e}", "error")
    finally:
        cursor.close()
        cnx.close()
    return redirect(url_for("proyectos.proyectos"))
