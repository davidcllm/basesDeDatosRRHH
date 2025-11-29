from flask import Blueprint, render_template, request, redirect, url_for
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql

empleados_bp = Blueprint("empleados", __name__)

@empleados_bp.route("/empleados")
@jwt_required()
@roles_required('administrador','finanzas', 'recursos_humanos', 'invitado')
def empleados():
    cnx = get_connection()
    
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM EMPLEADO;")

    empleados = cursor.fetchall()
    print("Fetched data:", empleados)  # <-- ADD THIS LINE

    
    cursor.close()
    cnx.close()
    return render_template("empleados.html", empleados=empleados)

@empleados_bp.route("/empleados/agregar", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas', 'recursos_humanos')
def agregar_empleado():
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]

    # Backend Validation
    import re
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$", nombre):
        return "Error: El nombre solo debe contener letras y espacios.", 400
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$", apellido):
        return "Error: El apellido solo debe contener letras y espacios.", 400
    
    telefono = request.form["telefono"]
    if not re.match(r"^\d+$", telefono):
        return "Error: El teléfono solo debe contener números.", 400

    nombre_completo = f"{nombre} {apellido}"
    fecha_nacimiento = request.form["fecha_nacimiento"]
    cargo = request.form["cargo"]
    fecha_contratacion = request.form.get("fecha_contratacion")  # Optional
    historial_laboral = request.form.get("historial_laboral", "")  # Optional
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
        print("✅ Employee added successfully")
    except Exception as e:
        print("❌ Error adding employee:", str(e))
        cnx.rollback()
    finally:
        cursor.close()
        cnx.close()
    return redirect(url_for("empleados.empleados"))

@empleados_bp.route("/empleados/eliminar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas', 'recursos_humanos')
def eliminar_empleado(id):
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("DELETE FROM EMPLEADO WHERE id_empleado = %s;", (id,))
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("empleados.empleados"))

@empleados_bp.route("/empleados/editar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas', 'recursos_humanos')
def editar_empleado(id):
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]
    
    # Backend Validation
    import re
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$", nombre):
        return "Error: El nombre solo debe contener letras y espacios.", 400
    if not re.match(r"^[A-Za-zÁÉÍÓÚáéíóúñÑ\s]+$", apellido):
        return "Error: El apellido solo debe contener letras y espacios.", 400
        
    telefono = request.form["telefono"]
    if not re.match(r"^[\d\s]+$", telefono):
        return "Error: El teléfono solo debe contener números.", 400

    nombre_completo = f"{nombre} {apellido}"
    direccion = request.form["direccion"]
    fecha_nacimiento = request.form["fecha_nacimiento"]
    cargo = request.form["cargo"]
    fecha_contratacion = request.form.get("fecha_contratacion")
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
        print("❌ Error updating employee:", str(e))
        cnx.rollback()
    finally:
        cursor.close()
        cnx.close()
    return redirect(url_for("empleados.empleados"))
