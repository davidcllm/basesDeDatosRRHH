# Este archivo fue creado con ayuda de la Inteligencia Artificial de OpenAI. 
# OpenAI. (2025). ChatGPT [Modelo de lenguaje de gran tamaño]. https://chat.openai.com/chat

from flask import Blueprint, render_template, request, redirect, url_for
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql

nomina_bp = Blueprint("nomina", __name__)

@nomina_bp.route("/nomina")
@jwt_required()
@roles_required('administrador','finanzas', 'recursos_humanos')
def nomina():
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT n.id_nomina, n.salario_base, n.deducciones, n.percepciones, n.total_pagar,
               n.id_empleado, e.nombre_completo
        FROM NOMINA n
        LEFT JOIN EMPLEADO e ON n.id_empleado = e.id_empleado;
    """)
    nomina = cursor.fetchall()

    cursor.execute("SELECT id_empleado, nombre_completo FROM EMPLEADO ORDER BY nombre_completo;")
    empleados = cursor.fetchall()

    cursor.execute("SELECT * FROM CUENTA_BANCARIA ORDER BY id_cuenta_bancaria;")
    cuentas_bancarias = cursor.fetchall()

    cursor.close()
    cnx.close()
    return render_template("nomina.html", nomina=nomina, empleados=empleados, cuentas_bancarias=cuentas_bancarias)


@nomina_bp.route("/nomina/agregar_nomina", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def agregar_nomina():
    id_empleado = int(request.form["id_empleado"])
    salario_base = float(request.form["salario_base"] or 0)
    deducciones = float(request.form["deducciones"] or 0)
    percepciones = float(request.form["percepciones"] or 0)
    total_pagar = salario_base + percepciones - deducciones

    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute(
        "INSERT INTO NOMINA (id_empleado, salario_base, deducciones, percepciones, total_pagar) VALUES (%s, %s, %s, %s, %s);",
        (id_empleado, salario_base, deducciones, percepciones, total_pagar)
    )
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("nomina.nomina"))


@nomina_bp.route("/nomina/eliminar_nomina/<int:id_nomina>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def eliminar_nomina(id_nomina):
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("DELETE FROM NOMINA WHERE id_nomina = %s;", (id_nomina,))
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("nomina.nomina"))


@nomina_bp.route("/nomina/editar_nomina/<int:id_nomina>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def editar_nomina(id_nomina):
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

    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("nomina.nomina"))


# ---------------------------
# CUENTAS BANCARIAS CRUD
# ---------------------------
@nomina_bp.route("/nomina/agregar_cuenta_bancaria", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def agregar_cuenta_bancaria():
    banco = request.form.get("banco", "").strip()
    numero_cuenta = request.form.get("numero_cuenta", "").strip()
    
    # Validación: solo números enteros
    if not numero_cuenta.isdigit():
        return "Error: El número de cuenta solo debe contener números enteros.", 400
    
    saldo = float(request.form.get("saldo", 0) or 0)

    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute(
        "INSERT INTO CUENTA_BANCARIA (banco, numero_cuenta, saldo) VALUES (%s, %s, %s);",
        (banco, numero_cuenta, saldo)
    )
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("nomina.nomina"))


@nomina_bp.route("/nomina/editar_cuenta_bancaria/<int:id_cuenta>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def editar_cuenta_bancaria(id_cuenta):
    banco = request.form.get("banco", "").strip()
    numero_cuenta = request.form.get("numero_cuenta", "").strip()
    
    # Validación: solo números enteros
    if not numero_cuenta.isdigit():
        return "Error: El número de cuenta solo debe contener números enteros.", 400
    
    saldo = float(request.form.get("saldo", 0) or 0)

    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("""
        UPDATE CUENTA_BANCARIA
        SET banco=%s, numero_cuenta=%s, saldo=%s
        WHERE id_cuenta_bancaria=%s
    """, (banco, numero_cuenta, saldo, id_cuenta))

    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("nomina.nomina"))


@nomina_bp.route("/nomina/eliminar_cuenta_bancaria/<int:id_cuenta>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def eliminar_cuenta_bancaria(id_cuenta):
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("DELETE FROM CUENTA_BANCARIA WHERE id_cuenta_bancaria = %s;", (id_cuenta,))
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("nomina.nomina"))
