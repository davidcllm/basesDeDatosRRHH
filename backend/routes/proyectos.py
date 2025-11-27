from flask import Blueprint, render_template, request, redirect, url_for
from flask_jwt_extended import jwt_required
from routes.auth import roles_required
from dp import get_connection
import pymysql 

proyectos_bp = Blueprint("proyectos", __name__)

#Listar proyectos
@proyectos_bp.route("/proyectos")
@jwt_required()
@roles_required('administrador','recursos_humanos')
def proyectos():

    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    # --- Proyectos ---
    cursor.execute("""
        SELECT id_proyecto, nombre, descripcion
        FROM PROYECTO;
    """)
    proyectos = cursor.fetchall()

    # --- Empleados para el select ---
    cursor.execute("""
        SELECT id_empleado, nombre_completo
        FROM EMPLEADO;
    """)
    empleados = cursor.fetchall()

    # --- Empleados asignados a proyectos ---
    cursor.execute("""
        SELECT ep.id_empleado, ep.id_proyecto, ep.horas_asignadas,
               ep.fecha_asignacion, ep.fecha_entrega,
               e.nombre_completo,
               p.nombre AS nombre_proyecto
        FROM `EMPLEADO-PROYECTO` ep
        JOIN EMPLEADO e ON ep.id_empleado = e.id_empleado
        JOIN PROYECTO p ON ep.id_proyecto = p.id_proyecto;
    """)
    asignaciones = cursor.fetchall()

    cursor.close()
    cnx.close()

    return render_template(
        "proyectos.html",
        proyectos=proyectos,
        empleados=empleados,
        asignaciones=asignaciones
    )

#crear proyectos
@proyectos_bp.route("/proyectos/crear", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def crear_proyecto():

    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        INSERT INTO PROYECTO (nombre, descripcion)
        VALUES (%s, %s);
    """, (nombre, descripcion))

    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect(url_for("proyectos.proyectos"))

#eliminar
@proyectos_bp.route("/proyectos/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def eliminar_proyecto(id):

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("DELETE FROM PROYECTO WHERE id_proyecto = %s;", (id,))
    cnx.commit()

    cursor.close()
    cnx.close()

    return redirect(url_for("proyectos.proyectos"))

#Actualizar
@proyectos_bp.route("/proyectos/actualizar/<int:id>", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def actualizar_proyecto(id):

    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]

    cnx = get_connection()
    cursor = cnx.cursor()

    cursor.execute("""
        UPDATE PROYECTO
        SET nombre=%s, descripcion=%s
        WHERE id_proyecto=%s
    """, (nombre, descripcion, id))

    cnx.commit()

    cursor.close()
    cnx.close()

    return redirect(url_for("proyectos.proyectos"))

#Asignar empleado a proyecto
@proyectos_bp.route("/proyectos/asignar", methods=["POST"])
@jwt_required()
@roles_required('administrador','recursos_humanos')
def asignar_empleado():

    id_empleado = request.form["id_empleado"]
    id_proyecto = request.form["id_proyecto"]
    horas = request.form["horas_asignadas"]
    fecha_asignacion = request.form["fecha_asignacion"]
    fecha_entrega = request.form["fecha_entrega"]

    cnx = get_connection()
    cursor = cnx.cursor()

    try:
        cursor.execute("""
            INSERT INTO `EMPLEADO-PROYECTO` 
            (id_empleado, id_proyecto, horas_asignadas, fecha_asignacion, fecha_entrega)
            VALUES (%s, %s, %s, %s, %s)
        """, (id_empleado, id_proyecto, horas, fecha_asignacion, fecha_entrega))

        cnx.commit()

    except Exception as e:
        print("Error asignando:", e)

    cursor.close()
    cnx.close()

    return redirect(url_for("proyectos.proyectos"))
