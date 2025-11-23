from flask import Blueprint, render_template, request, redirect, url_for
from dp import get_connection

cuentas_bp = Blueprint("cuentas", __name__)

@cuentas_bp.route("/cuentas", methods=["GET", "POST"])
def cuentas():
    if request.method == "POST":
        banco = request.form["banco"]
        numero_cuenta = request.form["numero_cuenta"]
        tipo = request.form["tipo"]
        saldo = float(request.form["saldo"]) if request.form.get("saldo") else 0.0
        id_centro_costo = int(request.form["id_centro_costo"])

        cnx = get_connection()
        cursor = cnx.cursor()
        cursor.execute(
            "INSERT INTO CUENTA_CONTABLE (banco, numero_cuenta, tipo, saldo, id_centro_costo) VALUES (%s, %s, %s, %s, %s);",
            (banco, numero_cuenta, tipo, saldo, id_centro_costo)
        )
        cnx.commit()
        cursor.close()
        cnx.close()
        return redirect(url_for("cuentas.cuentas"))

    # GET: listar cuentas y cargar opciones para selects
    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM CUENTA_CONTABLE;")
    cuentas = cursor.fetchall()

    # bancos: leer desde CUENTA_CONTABLE si existe, si no usar valores distintos de CUENTA_CONTABLE
    cursor.execute("SELECT DISTINCT banco FROM CUENTA_CONTABLE;")
    bancos_rows = cursor.fetchall()
    bancos = [r["banco"] for r in bancos_rows] if bancos_rows else []
    if not bancos:
        cursor.execute("SELECT DISTINCT banco FROM CUENTA_CONTABLE;")
        bancos = [r["banco"] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT tipo FROM CUENTA_CONTABLE;")
    tipos = [r["tipo"] for r in cursor.fetchall()]

    cursor.execute("SELECT id_centro_costo, nombre FROM CENTRO_COSTO;")
    centros = cursor.fetchall()

    cursor.close()
    cnx.close()
    return render_template("cuentas.html", cuentas=cuentas, bancos=bancos, tipos=tipos, centros=centros)


@cuentas_bp.route("/cuentas/agregar_cuenta_contable", methods=["POST"])
def agregar_cuenta_contable():
    banco = request.form["banco"]
    numero_cuenta = request.form["numero_cuenta"]
    tipo = request.form["tipo"]
    saldo = float(request.form["saldo"]) if request.form.get("saldo") else 0.0
    id_centro_costo = int(request.form["id_centro_costo"])

    cnx = get_connection()
    cursor = cnx.cursor()
    cursor.execute(
        "INSERT INTO CUENTA_CONTABLE (banco, numero_cuenta, tipo, saldo, id_centro_costo) VALUES (%s, %s, %s, %s, %s);",
        (banco, numero_cuenta, tipo, saldo, id_centro_costo)
    )
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("cuentas.cuentas"))

@cuentas_bp.route("/cuentas/eliminar_cuenta_contable/<int:id_cuenta>", methods=["POST"])
def eliminar_cuenta_contable(id_cuenta):
    cnx = get_connection()
    cursor = cnx.cursor()
    # columna correcta: id_cuenta_contable
    cursor.execute("DELETE FROM CUENTA_CONTABLE WHERE id_cuenta_contable = %s;", (id_cuenta,))
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect(url_for("cuentas.cuentas"))

@cuentas_bp.route("/id_cuenta_contable/actualizar_cuenta_contable/<int:id>", methods=["POST"])
def actualizar_cuenta_contable(id):
    banco = request.form["banco"]
    numero_cuenta = request.form["numero_cuenta"]
    tipo = request.form.get("tipo", "")
    saldo = float(request.form.get("saldo") or 0.0)
    id_centro_costo = int(request.form.get("id_centro_costo") or 0)

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        UPDATE CUENTA_CONTABLE
        SET banco=%s, numero_cuenta=%s, tipo=%s, saldo=%s, id_centro_costo=%s
        WHERE id_cuenta_contable=%s
    """, (banco, numero_cuenta, tipo, saldo, id_centro_costo, id))

    cnx.commit()

    cursor.close()
    cnx.close()

    return redirect(url_for("cuentas.cuentas"))