from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql 
from datetime import datetime

proyectos_bp = Blueprint("proyectos", __name__)

# helper: validar longitudes (se usaba antes pero no estaba definido)
def validate_proyecto_lengths(nombre, descripcion):
    if len(nombre) == 0:
        return False, "El nombre no puede estar vacío."
    if len(nombre) > 45:
        return False, "El nombre no puede exceder 45 caracteres."
    if len(descripcion) == 0:
        return False, "La descripción no puede estar vacía."
    if len(descripcion) > 145:
        return False, "La descripción no puede exceder 145 caracteres."
    return True, ""

#Listar proyectos (renders the template)
@proyectos_bp.route("/proyectos")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def proyectos():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    # --- Proyectos --- (no cargamos aquí la tabla completa para permitir carga bajo demanda)
    cursor.execute("""
        SELECT id_proyecto, nombre, descripcion,
               DATE_FORMAT(fecha_inicio, '%Y-%m-%d') AS fecha_inicio,
               DATE_FORMAT(fecha_fin, '%Y-%m-%d') AS fecha_fin
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
    cursor.execute("""
        SELECT id_proyecto, nombre, descripcion,
               DATE_FORMAT(fecha_inicio, '%Y-%m-%d') AS fecha_inicio,
               DATE_FORMAT(fecha_fin, '%Y-%m-%d') AS fecha_fin
        FROM PROYECTO
        ORDER BY id_proyecto DESC;
    """)
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
        # Verificar si hay presupuestos asignados
        cursor.execute("SELECT 1 FROM PRESUPUESTO WHERE id_departamento = %s LIMIT 1;", (id,))
        if cursor.fetchone():
            flash("No se puede eliminar el departamento porque tiene presupuestos asignados.", "error")
            return redirect(url_for("proyectos.proyectos"))

        # Verificar si hay empleados asignados
        cursor.execute("SELECT 1 FROM EMPLEADO WHERE id_departamento = %s LIMIT 1;", (id,))
        if cursor.fetchone():
            flash("No se puede eliminar el departamento porque tiene empleados asignados.", "error")
            return redirect(url_for("proyectos.proyectos"))
        
        # Verificar si hay centros de costo asignados
        cursor.execute("SELECT 1 FROM CENTRO_COTO WHERE id_departamento = %s LIMIT 1;", (id,))
        if cursor.fetchone():
            flash("No se puede eliminar el departamento porque tiene centros de costo asignados.", "error")
            return redirect(url_for("proyectos.proyectos"))

        # Si no hay dependencias, proceder a eliminar
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
    fecha_inicio = request.form.get("fecha_inicio", "").strip()
    fecha_fin = request.form.get("fecha_fin", "").strip()

    # Validar que no estén vacíos y longitudes
    valid, msg = validate_proyecto_lengths(nombre, descripcion)
    if not valid:
        flash(msg, "error")
        return redirect(url_for("proyectos.proyectos"))

    # Validar fechas
    if not fecha_inicio or not fecha_fin:
        flash("Debe ingresar fecha de inicio y fecha de fin.", "error")
        return redirect(url_for("proyectos.proyectos"))

    try:
        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        if fi >= ff:
            flash("La fecha de inicio debe ser anterior a la fecha de fin.", "error")
            return redirect(url_for("proyectos.proyectos"))
    except Exception:
        flash("Formato de fecha inválido. Use YYYY-MM-DD.", "error")
        return redirect(url_for("proyectos.proyectos"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            INSERT INTO PROYECTO (nombre, descripcion, fecha_inicio, fecha_fin)
            VALUES (%s, %s, %s, %s);
        """, (nombre, descripcion, fecha_inicio, fecha_fin))

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
        # Verificar si hay empleados asignados al proyecto
        cursor.execute("SELECT 1 FROM `EMPLEADO-PROYECTO` WHERE id_proyecto = %s LIMIT 1;", (id,))
        empleado_asignado = cursor.fetchone()

        if empleado_asignado:
            flash("No se puede eliminar el proyecto porque tiene empleados asignados.", "error")
            return redirect(url_for("proyectos.proyectos"))

        # Si no hay empleados, proceder a eliminar
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
    fecha_inicio = request.form.get("fecha_inicio", "").strip()
    fecha_fin = request.form.get("fecha_fin", "").strip()

    # Validar que no estén vacíos y longitudes
    valid, msg = validate_proyecto_lengths(nombre, descripcion)
    if not valid:
        flash(msg, "error")
        return redirect(url_for("proyectos.proyectos"))

    if not fecha_inicio or not fecha_fin:
        flash("Debe ingresar fecha de inicio y fecha de fin.", "error")
        return redirect(url_for("proyectos.proyectos"))

    try:
        fi = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        ff = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        if fi >= ff:
            flash("La fecha de inicio debe ser anterior a la fecha de fin.", "error")
            return redirect(url_for("proyectos.proyectos"))
    except Exception:
        flash("Formato de fecha inválido. Use YYYY-MM-DD.", "error")
        return redirect(url_for("proyectos.proyectos"))

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            UPDATE PROYECTO
            SET nombre=%s, descripcion=%s, fecha_inicio=%s, fecha_fin=%s
            WHERE id_proyecto=%s
        """, (nombre, descripcion, fecha_inicio, fecha_fin, id))

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

    # Validar formato y orden de fechas
    try:
        fi = datetime.strptime(fecha_asignacion, "%Y-%m-%d").date()
        ff = datetime.strptime(fecha_entrega, "%Y-%m-%d").date()
        if fi >= ff:
            flash("La fecha de asignación debe ser anterior a la fecha de entrega.", "error")
            return redirect(url_for("proyectos.proyectos"))
    except Exception:
        flash("Formato de fecha inválido. Use YYYY-MM-DD.", "error")
        return redirect(url_for("proyectos.proyectos"))

    # Obtener rango del proyecto y validar que las fechas estén dentro
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT DATE_FORMAT(fecha_inicio, '%%Y-%%m-%%d') AS fecha_inicio, DATE_FORMAT(fecha_fin, '%%Y-%%m-%%d') AS fecha_fin FROM PROYECTO WHERE id_proyecto = %s", (id_proyecto,))
    proj = cursor.fetchone()
    if not proj:
        cursor.close()
        cnx.close()
        flash("Proyecto no encontrado.", "error")
        return redirect(url_for("proyectos.proyectos"))

    try:
        proj_start = datetime.strptime(proj['fecha_inicio'], "%Y-%m-%d").date()
        proj_end = datetime.strptime(proj['fecha_fin'], "%Y-%m-%d").date()
    except Exception:
        cursor.close()
        cnx.close()
        flash("Fechas del proyecto inválidas.", "error")
        return redirect(url_for("proyectos.proyectos"))

    if fi < proj_start or ff > proj_end:
        cursor.close()
        cnx.close()
        flash(f"Las fechas de asignación deben estar entre {proj['fecha_inicio']} y {proj['fecha_fin']}.", "error")
        return redirect(url_for("proyectos.proyectos"))

    # insertar asignación
    try:
        cursor = cnx.cursor()
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

    # validaciones básicas (empleado/proyecto/horas)
    if not id_empleado or not id_empleado.isdigit():
        flash("Empleado inválido.", "error")
        return redirect(url_for("proyectos.proyectos"))

    if not id_proyecto or not id_proyecto.isdigit():
        flash("Proyecto inválido.", "error")
        return redirect(url_for("proyectos.proyectos"))

    try:
        horas_int = int(horas)
        if horas_int <= 0:
            raise ValueError
    except ValueError:
        flash("Las horas asignadas deben ser un entero positivo.", "error")
        return redirect(url_for("proyectos.proyectos"))

    # validar fechas y orden
    try:
        fecha_a = datetime.strptime(fecha_asignacion, "%Y-%m-%d").date()
        fecha_f = datetime.strptime(fecha_entrega, "%Y-%m-%d").date()
        if fecha_a >= fecha_f:
            flash("La fecha de asignación debe ser anterior a la fecha de entrega.", "error")
            return redirect(url_for("proyectos.proyectos"))
    except Exception:
        flash("Fechas inválidas.", "error")
        return redirect(url_for("proyectos.proyectos"))

    # validar que fechas estén dentro del rango del proyecto
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT DATE_FORMAT(fecha_inicio, '%%Y-%%m-%%d') AS fecha_inicio, DATE_FORMAT(fecha_fin, '%%Y-%%m-%%d') AS fecha_fin FROM PROYECTO WHERE id_proyecto = %s", (id_proyecto,))
    proj = cursor.fetchone()
    if not proj:
        cursor.close()
        cnx.close()
        flash("Proyecto no encontrado.", "error")
        return redirect(url_for("proyectos.proyectos"))

    try:
        proj_start = datetime.strptime(proj['fecha_inicio'], "%Y-%m-%d").date()
        proj_end = datetime.strptime(proj['fecha_fin'], "%Y-%m-%d").date()
    except Exception:
        cursor.close()
        cnx.close()
        flash("Fechas del proyecto inválidas.", "error")
        return redirect(url_for("proyectos.proyectos"))

    if fecha_a < proj_start or fecha_f > proj_end:
        cursor.close()
        cnx.close()
        flash(f"Las fechas de asignación deben estar entre {proj['fecha_inicio']} y {proj['fecha_fin']}.", "error")
        return redirect(url_for("proyectos.proyectos"))

    # Proceder a actualizar
    cnx2 = get_connection()
    cursor2 = cnx2.cursor()
    try:
        cursor2.execute("""
            UPDATE `EMPLEADO-PROYECTO`
            SET id_empleado=%s, id_proyecto=%s, horas_asignadas=%s, fecha_asignacion=%s, fecha_entrega=%s
            WHERE `id_empleado-proyecto`=%s
        """, (id_empleado, id_proyecto, horas_int, fecha_asignacion, fecha_entrega, id))
        cnx2.commit()
        flash("Asignación actualizada correctamente.", "success")
    except Exception as e:
        cnx2.rollback()
        flash(f"Error al actualizar asignación: {e}", "error")
    finally:
        cursor2.close()
        cnx2.close()

    return redirect(url_for("proyectos.proyectos"))

# Eliminar asignación
@proyectos_bp.route("/proyectos/asignacion/eliminar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def eliminar_asignacion(id):
    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("DELETE FROM `EMPLEADO-PROYECTO` WHERE `id_empleado-proyecto` = %s", (id,))
        cnx.commit()
        flash("Asignación eliminada correctamente.", "success")
    except Exception as e:
        cnx.rollback()
        flash(f"Error al eliminar la asignación: {e}", "error")
    finally:
        cursor.close()
        cnx.close()
    return redirect(url_for("proyectos.proyectos"))
