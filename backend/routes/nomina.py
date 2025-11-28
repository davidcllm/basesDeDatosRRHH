from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql
import re

nomina_bp = Blueprint("nomina", __name__)

@nomina_bp.route("/nomina")
@jwt_required()
@roles_required('administrador','finanzas', 'recursos_humanos')
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
@jwt_required()
@roles_required('administrador','finanzas')
def agregar_nomina():
    # leer formulario
    id_empleado = request.form.get("id_empleado")
    salario_base_str = request.form.get("salario_base", "")
    deducciones_str = request.form.get("deducciones", "")
    percepciones_str = request.form.get("percepciones", "")

    if not id_empleado:
        return jsonify({"error": "Debe seleccionar un empleado."}), 400

    if not salario_base_str or re.match(r"^\s*$", salario_base_str):
        return jsonify({"error": "El salario base no puede estar vacío."}), 400
    if not deducciones_str or re.match(r"^\s*$", deducciones_str):
        return jsonify({"error": "Las deducciones no pueden estar vacías."}), 400
    if not percepciones_str or re.match(r"^\s*$", percepciones_str):
        return jsonify({"error": "Las percepciones no pueden estar vacías."}), 400

    try:
        salario_base = float(salario_base_str)
        deducciones = float(deducciones_str)
        percepciones = float(percepciones_str)
    except ValueError:
        return jsonify({"error": "Los valores deben ser numéricos."}), 400

    # calcular total en servidor
    total_pagar = salario_base + percepciones - deducciones

    if total_pagar < 0:
        return jsonify({"error": "El total a pagar no puede ser negativo."}), 400

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
    return jsonify({"success": True}), 200


@nomina_bp.route("/nomina/eliminar_nomina/<int:id_nomina>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
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
@jwt_required()
@roles_required('administrador','finanzas')
def editar_nomina(id_nomina):
    # sólo permitir editar salario_base, deducciones y percepciones
    salario_base = request.form.get("salario_base", "")
    deducciones = request.form.get("deducciones", "")
    percepciones = request.form.get("percepciones", "")

    if not salario_base or re.match(r"^\s*$", salario_base):
        return jsonify({"error": "El salario base no puede estar vacío."}), 400
    if not deducciones or re.match(r"^\s*$", deducciones):
        return jsonify({"error": "Las deducciones no pueden estar vacías."}), 400
    if not percepciones or re.match(r"^\s*$", percepciones):
        return jsonify({"error": "Las percepciones no pueden estar vacías."}), 400
    
    try:
        salario_base = float(salario_base)
        deducciones = float(deducciones)
        percepciones = float(percepciones)
    except ValueError:
        return jsonify({"error": "Los valores deben ser numéricos."}), 400
    
    total_pagar = salario_base + percepciones - deducciones

    if total_pagar < 0:
        return jsonify({"error": "El total a pagar no puede ser negativo."}), 400

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
    return jsonify({"success": True}), 200

