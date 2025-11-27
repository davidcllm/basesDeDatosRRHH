from flask import Blueprint, render_template, request, redirect, url_for
from dp import get_connection
import pymysql

empleados_bp = Blueprint("empleados", __name__)

@empleados_bp.route("/empleados")
def empleados():
    cnx = get_connection()
    
    cursor = cnx.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT * FROM EMPLEADO;")

    empleados = cursor.fetchall()
    print("Fetched data:", empleados)  # <-- ADD THIS LINE

    
    cursor.close()
    cnx.close()
    return render_template("empleados.html", empleados=empleados)

@empleados_bp.route("/empleados/agregar", methods=["POST"])
def agregar_empleado():
    nombre = request.form["nombre"]
    apellido = request.form["apellido"]
    nombre_completo = f"{nombre + " " + apellido}"

    direccion = request.form["direccion"]
    telefono = request.form["telefono"]
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

@empleados_bp.route("/empleados/eliminar/<int:id>")
def eliminar_empleado(id):
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("DELETE FROM EMPLEADO WHERE id_empleado = %s;", (id,))
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("empleados.empleados"))
