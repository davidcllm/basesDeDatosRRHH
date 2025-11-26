from flask import Blueprint, render_template, request, redirect, url_for
from dp import get_connection

empleados_bp = Blueprint("empleados", __name__)

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
    email = request.form["email"]

    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute(
        "INSERT INTO EMPLEADO (nombre, apellido, email) VALUES (%s, %s, %s);",
        (nombre, apellido, email)
    )
    cnx.commit()
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
