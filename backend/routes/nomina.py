from flask import Blueprint, render_template, request, redirect, url_for
from dp import get_connection


nomina_bp = Blueprint("nomina", __name__)

@nomina_bp.route("/nomina")
def nomina():
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM NOMINA;")
    nomina = cursor.fetchall()
    cursor.close()
    cnx.close()

    cnx = get_connection()
    cursor = cnx.cursor() # dictionary=True
    cursor.execute("SELECT id_empleado, nombre_completo FROM EMPLEADO;")
    empleados = cursor.fetchall()
    cursor.close()
    cnx.close()

    return render_template("nomina.html", nomina=nomina, empleados=empleados)

'''
@nomina_bp.route("/empleados")
def obtener_empleados():
    cnx = get_connection()
    cursor = cnx.cursor(dictionary=True)
    cursor.execute("SELECT id_empleado, nombre, apellido FROM EMPLEADO;")
    empleados = cursor.fetchall()
    cursor.close()
    cnx.close()
    return {"emplados", empleados}
'''


@nomina_bp.route("/nomina/agregar_salario", methods=["POST"])
def agregar():

    id_empleado = int(request.form["id_empleado"])
    salario_base = float(request.form["salario_base"])
    deducciones = float(request.form["deducciones"])
    percepciones = float(request.form["percepciones"])
    total_paga = salario_base + percepciones - deducciones

    cnx = get_connection() 
    cursor = cnx.cursor()
    cursor.execute(
        "INSERT INTO NOMINA (salario_base, empleado, deducciones, percepciones, total_paga)" \
        "VALUES (%s %s %s %s %s);",
        (id_empleado, salario_base, deducciones, percepciones ,total_paga))
    
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("nomina.nomina"))

