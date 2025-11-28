from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from dp import get_connection
import pymysql
from datetime import datetime
import re

empleados_bp = Blueprint("empleados", __name__)


def validar_fechas(fecha_contratacion, fecha_nacimiento):
    """Valida que fecha_contratacion sea menor que fecha_nacimiento"""
    try:
        fc = datetime.fromisoformat(fecha_contratacion)
        fn = datetime.fromisoformat(fecha_nacimiento)
        if fc <= fn:
            return False, "La fecha de contratación debe ser posterior a la fecha de nacimiento"
        return True, ""
    except:
        return False, "Formato de fecha inválido"


@empleados_bp.route("/empleados")
def empleados():
    cnx = get_connection()
    
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM EMPLEADO;")

    empleados = cursor.fetchall()
    
    cursor.close()
    cnx.close()
    return render_template("empleados.html", empleados=empleados)

@empleados_bp.route("/empleados/agregar", methods=["POST"])
def agregar_empleado():
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]

    # Backend Validation
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$", nombre):
        return jsonify({"error": "El nombre solo debe contener letras y espacios."}), 400
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$", apellido):
        return jsonify({"error": "El apellido solo debe contener letras y espacios."}), 400
    
    telefono = request.form["telefono"]
    if not re.match(r"^[\d\s]+$", telefono):
        return jsonify({"error": "El teléfono puede contener números y espacios."}), 400

    nombre_completo = f"{nombre} {apellido}"
    direccion = request.form["direccion"]
    fecha_nacimiento = request.form["fecha_nacimiento"]
    cargo = request.form["cargo"]
    
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$", cargo):
        return jsonify({"error": "El cargo solo debe contener letras y espacios."}), 400
    
    
    fecha_contratacion = request.form.get("fecha_contratacion")
    
    historial_laboral = request.form.get("historial_laboral", "")
    id_cuenta_bancaria = int(request.form["id_cuenta_bancaria"])
    id_plan_carrera = int(request.form["id_plan_carrera"])
    id_departamento = int(request.form["id_departamento"])

    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("""
            INSERT INTO EMPLEADO 
            (id_cuenta_bancaria, id_plan_carrera, nombre_completo, direccion, telefono, fecha_nacimiento, cargo, fecha_contratacion, historial_laboral, id_departamento)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            id_cuenta_bancaria,
            id_plan_carrera,
            nombre_completo,
            direccion,
            telefono,
            fecha_nacimiento,
            cargo,
            fecha_contratacion,
            historial_laboral,
            id_departamento
        ))
        cnx.commit()
    except Exception as e:
        cnx.rollback()
        return jsonify({"error": f"Error al agregar empleado: {str(e)}"}), 500
    finally:
        cursor.close()
        cnx.close()
    return jsonify({"success": True}), 200

@empleados_bp.route("/empleados/eliminar/<int:id>", methods=["POST"])
def eliminar_empleado(id):
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("DELETE FROM EMPLEADO WHERE id_empleado = %s;", (id,))
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("empleados.empleados"))

@empleados_bp.route("/empleados/editar/<int:id>", methods=["POST"])
def editar_empleado(id):
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]
    
    # Backend Validation
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$", nombre):
        return jsonify({"error": "El nombre solo debe contener letras y espacios."}), 400
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$", apellido):
        return jsonify({"error": "El apellido solo debe contener letras y espacios."}), 400
        
    telefono = request.form["telefono"]
    if not re.match(r"^[\d\s]+$", telefono):
        return jsonify({"error": "El teléfono solo debe contener números."}), 400

    nombre_completo = f"{nombre} {apellido}"
    direccion = request.form["direccion"]
    fecha_nacimiento = request.form["fecha_nacimiento"]
    cargo = request.form["cargo"]
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$", cargo):
        return jsonify({"error": "El cargo solo debe contener letras y espacios."}), 400
    

    fecha_contratacion = request.form.get("fecha_contratacion")
    if not fecha_contratacion:
        fecha_contratacion = None
    else:
        valido, mensaje = validar_fechas(fecha_contratacion, fecha_nacimiento)
        if not valido:
            return jsonify({"error": mensaje}), 400
    historial_laboral = request.form.get("historial_laboral", "")
    id_cuenta_bancaria = int(request.form["id_cuenta_bancaria"])
    id_plan_carrera = int(request.form["id_plan_carrera"])
    id_departamento = int(request.form["id_departamento"])

    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("""
            UPDATE EMPLEADO 
            SET id_cuenta_bancaria=%s, id_plan_carrera=%s, nombre_completo=%s, direccion=%s, telefono=%s, 
            fecha_nacimiento=%s, cargo=%s, fecha_contratacion=%s, historial_laboral=%s, id_departamento=%s
            WHERE id_empleado=%s
        """, (
            id_cuenta_bancaria, id_plan_carrera, nombre_completo, direccion, telefono, 
            fecha_nacimiento, cargo, fecha_contratacion, historial_laboral, id_departamento, id
        ))
        cnx.commit()
    except Exception as e:
        cnx.rollback()
        return jsonify({"error": f"Error al actualizar empleado: {str(e)}"}), 500
    finally:
        cursor.close()
        cnx.close()
    return jsonify({"success": True}), 200
