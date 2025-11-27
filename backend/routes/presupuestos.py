from flask import Blueprint, render_template, request, redirect, url_for
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql

presupuestos_bp = Blueprint("presupuestos", __name__)


#Encontrar presupuestos
@presupuestos_bp.route("/presupuestos")
@jwt_required()
@roles_required('administrador','finanzas')
def presupuestos():

    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    # --- Presupuestos con nombre del departamento ---
    cursor.execute("""
        SELECT P.id_presupuesto, P.periodo, P.monto_asignado, 
               P.monto_utilizado, D.nombre AS departamento
        FROM PRESUPUESTO P
        JOIN DEPARTAMENTO D ON P.id_departamento = D.id_departamento
        ORDER BY P.id_presupuesto DESC;
    """)
    presupuestos = cursor.fetchall()

    # --- Departamentos para selects ---
    cursor.execute("""
        SELECT id_departamento, nombre
        FROM DEPARTAMENTO;
    """)
    departamentos = cursor.fetchall()

        # --- LISTAR PRESUPUESTOS ---
    cursor.execute("""
        SELECT P.id_presupuesto, P.periodo, P.monto_asignado, 
               P.monto_utilizado, D.nombre AS departamento
        FROM PRESUPUESTO P
        JOIN DEPARTAMENTO D ON P.id_departamento = D.id_departamento
        ORDER BY P.id_presupuesto DESC;
    """)
    presupuestos = cursor.fetchall()

    # --- LISTAR CENTROS DE COSTO ---
    cursor.execute("""
        SELECT C.id_centro_costo,
               C.nombre,
               C.descipcion,
               D.nombre AS departamento
        FROM CENTRO_COSTO C
        JOIN DEPARTAMENTO D ON C.id_departamento = D.id_departamento
        ORDER BY C.id_centro_costo DESC;
    """)
    centros = cursor.fetchall()

    cursor.close()
    cnx.close()

    return render_template(
        "presupuestos.html",
        presupuestos=presupuestos,
        centros=centros,
        departamentos=departamentos
    )

#Crear presupuestos
@presupuestos_bp.route("/presupuestos/crear", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def crear_presupuesto():

    periodo = request.form["periodo"]
    asignado = request.form["monto_asignado"]
    utilizado = request.form["monto_utilizado"]
    departamento = request.form["id_departamento"]

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        INSERT INTO PRESUPUESTO (periodo, monto_asignado, monto_utilizado, id_departamento)
        VALUES (%s, %s, %s, %s)
    """, (periodo, asignado, utilizado, departamento))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))


#Editar presupuesto
@presupuestos_bp.route("/presupuestos/actualizar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def actualizar_presupuesto(id):

    periodo = request.form["periodo"]
    asignado = request.form["monto_asignado"]
    utilizado = request.form["monto_utilizado"]
    departamento = request.form["id_departamento"]

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        UPDATE PRESUPUESTO
        SET periodo=%s, monto_asignado=%s, monto_utilizado=%s, id_departamento=%s
        WHERE id_presupuesto=%s
    """, (periodo, asignado, utilizado, departamento, id))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))


#Eliminar presupuesto
@presupuestos_bp.route("/presupuestos/eliminar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def eliminar_presupuesto(id):

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("DELETE FROM PRESUPUESTO WHERE id_presupuesto=%s", (id,))
    cnx.commit()

    cursor.close()
    cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))

#centro costo
@presupuestos_bp.route("/centro_costo/crear", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def crear_centro_costo():

    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    id_departamento = request.form["id_departamento"]

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        INSERT INTO CENTRO_COSTO (nombre, descipcion, id_departamento)
        VALUES (%s, %s, %s)
    """, (nombre, descripcion, id_departamento))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))


@presupuestos_bp.route("/centro_costo/actualizar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def actualizar_centro_costo(id):

    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    id_departamento = request.form["id_departamento"]

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        UPDATE CENTRO_COSTO
        SET nombre=%s, descipcion=%s, id_departamento=%s
        WHERE id_centro_costo=%s
    """, (nombre, descripcion, id_departamento, id))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))


@presupuestos_bp.route("/centro_costo/eliminar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','finanzas')
def eliminar_centro_costo(id):

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("DELETE FROM CENTRO_COSTO WHERE id_centro_costo=%s", (id,))
    cnx.commit()

    cursor.close()
    cnx.close()

    return redirect(url_for("presupuestos.presupuestos"))