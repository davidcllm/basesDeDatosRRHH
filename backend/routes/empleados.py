from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from pymysql.err import IntegrityError
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
    cursor.execute("""
        SELECT e.*, 
               pc.objetivo AS plan_carrera_objetivo,
               cb.numero_cuenta AS cuenta_banco,
               d.nombre AS departamento_nombre
        FROM EMPLEADO e
        LEFT JOIN PLAN_CARRERA pc ON e.id_plan_carrera = pc.id_plan_carrera
        LEFT JOIN CUENTA_BANCARIA cb ON e.id_cuenta_bancaria = cb.id_cuenta_bancaria
        LEFT JOIN DEPARTAMENTO d ON e.id_departamento = d.id_departamento;
    """)
    empleados = cursor.fetchall()
    print("Fetched data:", empleados)

    cursor.execute("SELECT * FROM DEPARTAMENTO;")
    departamentos = cursor.fetchall()

    cursor.execute("SELECT id_plan_carrera, objetivo FROM PLAN_CARRERA;")
    planes_carrera = cursor.fetchall()

    cursor.execute("SELECT * FROM CUENTA_BANCARIA ORDER BY id_cuenta_bancaria;")
    cuentas_bancarias = cursor.fetchall()

    cursor.close()
    cnx.close()
    return render_template("empleados.html", empleados=empleados, departamentos=departamentos, planes_carrera=planes_carrera, cuentas_bancarias=cuentas_bancarias)

@empleados_bp.route("/empleados/agregar", methods=["POST"])
@jwt_required()
@roles_required('administrador', 'recursos_humanos')
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
    direccion = request.form["direccion"]

    if fecha_contratacion <= fecha_nacimiento:
        return "Error: La fecha de contratación debe ser mayor a la fecha de nacimiento.", 400
    
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
@roles_required('administrador', 'recursos_humanos')
def eliminar_empleado(id):
    cnx = get_connection()
    cursor = cnx.cursor()
    try:
        cursor.execute("DELETE FROM EMPLEADO WHERE id_empleado = %s;", (id,))
        cnx.commit()
        return jsonify({"success": True, "message": "Empleado eliminado correctamente"}), 200
    except IntegrityError as e:
        cnx.rollback()
        
        # Check specific tables to provide more detail
        related_tables = {
            "NOMINA": "Nómina",
            "EMPLEADO-CAPACITACION": "Capacitaciones",
            "EMPLEADO-PROYECTO": "Proyectos",
            "EMPLEADO-BENEFICIO": "Beneficios",
            "EMPLEADO-AUSENCIA": "Ausencias (Asignadas)",
            "AUSENCIA": "Ausencias (Registro)",
            "EMPLEADO-EVALUACION": "Evaluaciones",
            "ASISTENCIA": "Asistencias"
        }
        
        found_in = []
        try:
            check_cursor = cnx.cursor()
            for table, readable_name in related_tables.items():
                # Use string formatting for table name since it can't be parameterized directly
                # But validate table name against our whitelist above to prevent SQL injection
                if table in related_tables:
                    check_cursor.execute(f"SELECT 1 FROM `{table}` WHERE id_empleado = %s LIMIT 1", (id,))
                    if check_cursor.fetchone():
                        found_in.append(readable_name)
            check_cursor.close()
        except Exception as check_err:
            print(f"Error checking related tables: {check_err}")

        # Fallback: If manual checks didn't find anything, check the error message text
        if not found_in:
            error_str = str(e)
            for table, readable_name in related_tables.items():
                if table in error_str:
                    found_in.append(readable_name)
                    break

        message = "No se puede eliminar el empleado porque tiene registros asociados."
        if not found_in:
            # Last resort: Include the raw error
            message += f" (Error técnico: {str(e)})"

        print(f"Delete failed: {str(e)}")

        return jsonify({
            "success": False, 
            "message": message,
            "details": found_in
        }), 409
    except Exception as e:
        cnx.rollback()
        print("❌ Error deleting employee:", str(e))
        return jsonify({"success": False, "message": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        cnx.close()

@empleados_bp.route("/empleados/editar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador', 'recursos_humanos')
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
