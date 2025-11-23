from flask import Blueprint, render_template, request, redirect, url_for
from dp import get_connection
import pymysql

nomina_bp = Blueprint("nomina", __name__)

@nomina_bp.route("/nomina")
def nomina():
    cnx = get_connection()
    # usar DictCursor explícito para consistencia
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT n.id_nomina, n.salario_base, n.deducciones, n.percepciones, n.total_pagar,
               en.id_empleado, e.nombre_completo
        FROM NOMINA n
        LEFT JOIN `EMPLEADO-NOMINA` en ON n.id_nomina = en.id_nomina
        LEFT JOIN EMPLEADO e ON en.id_empleado = e.id_empleado;
    """)
    nomina = cursor.fetchall()

    # traer todos los empleados (ordenados)
    cursor.execute("SELECT id_empleado, nombre_completo FROM EMPLEADO ORDER BY nombre_completo;")
    empleados = cursor.fetchall()

    cursor.close()
    cnx.close()
    return render_template("nomina.html", nomina=nomina, empleados=empleados)


@nomina_bp.route("/nomina/agregar_nomina", methods=["POST"])
def agregar_nomina():
    # leer formulario
    id_empleado = int(request.form["id_empleado"])
    salario_base = float(request.form["salario_base"] or 0)
    deducciones = float(request.form["deducciones"] or 0)
    percepciones = float(request.form["percepciones"] or 0)
    # calcular total en servidor
    total_pagar = salario_base + percepciones - deducciones

    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute(
        "INSERT INTO NOMINA (salario_base, deducciones, percepciones, total_pagar) VALUES (%s, %s, %s, %s);",
        (salario_base, deducciones, percepciones, total_pagar)
    )
    nomina_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO `EMPLEADO-NOMINA` (id_empleado, id_nomina, fecha_inicio, fecha_fin) VALUES (%s, %s, NOW(), NOW());",
        (id_empleado, nomina_id)
    )
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("nomina.nomina"))


@nomina_bp.route("/nomina/eliminar_nomina/<int:id_nomina>", methods=["POST"])
def eliminar_nomina(id_nomina):
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("DELETE FROM `EMPLEADO-NOMINA` WHERE id_nomina = %s;", (id_nomina,))
    cursor.execute("DELETE FROM NOMINA WHERE id_nomina = %s;", (id_nomina,))
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("nomina.nomina"))


@nomina_bp.route("/nomina/editar_nomina/<int:id_nomina>", methods=["POST"])
def editar_nomina(id_nomina):
    # sólo permitir editar salario_base, deducciones y percepciones
    salario_base = float(request.form.get("salario_base", 0) or 0)
    deducciones = float(request.form.get("deducciones", 0) or 0)
    percepciones = float(request.form.get("percepciones", 0) or 0)
    total_pagar = salario_base + percepciones - deducciones

    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("""
        UPDATE NOMINA
        SET salario_base=%s, deducciones=%s, percepciones=%s, total_pagar=%s
        WHERE id_nomina=%s
    """, (salario_base, deducciones, percepciones, total_pagar, id_nomina))

    # NO tocar la tabla EMPLADO-NOMINA: el empleado no es editable desde aquí
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("nomina.nomina"))

