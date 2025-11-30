
from flask import Blueprint, render_template, request
from dp import get_connection
import pymysql
import logging

reportes_bp = Blueprint("reportes", __name__)

@reportes_bp.route("/reportes")
def reportes():
    cnx = None
    cursor = None

    try:
        cnx = get_connection()
        cursor = cnx.cursor(pymysql.cursors.DictCursor)

        # Obtener el tipo de reporte a mostrar
        tipo = request.args.get('tipo', 'todos')

        # Inicializar todos los reportes como vacíos
        rep_nomina = []
        rep_ausencias = []
        rep_evaluaciones = []
        rep_capacitaciones = []
        rep_proyectos = []
        rep_presupuestos = []

        if tipo == 'nomina' or tipo == 'todos':
            cursor.execute("""
                SELECT 
                    n.id_nomina,
                    e.nombre_completo,
                    n.salario_base,
                    n.deducciones,
                    n.percepciones,
                    n.total_pagar
                FROM NOMINA n
                JOIN EMPLEADO e ON n.id_empleado = e.id_empleado
                ORDER BY n.id_nomina DESC;
            """)
            rep_nomina = cursor.fetchall()

        if tipo == 'ausencias' or tipo == 'todos':
            cursor.execute("""
                SELECT 
                    e.nombre_completo,
                    a.tipo,
                    a.fecha_inicio,
                    a.fecha_fin,
                    a.motivo
                FROM AUSENCIA a
                JOIN EMPLEADO e ON a.id_empleado = e.id_empleado
                ORDER BY a.fecha_inicio DESC;
            """)
            rep_ausencias = cursor.fetchall()

        if tipo == 'evaluaciones' or tipo == 'todos':
            cursor.execute("""
                SELECT 
                    e.nombre_completo,
                    ev.fecha_evaluacion,
                    ev.tipo,
                    ev.resultado,
                    ev.observaciones
                FROM EVALUACION ev
                JOIN `EMPLEADO-EVALUACION` ee ON ev.id_evaluacion = ee.id_evaluacion
                JOIN EMPLEADO e ON ee.id_empleado = e.id_empleado
                ORDER BY ev.fecha_evaluacion DESC;
            """)
            rep_evaluaciones = cursor.fetchall()

        if tipo == 'capacitaciones' or tipo == 'todos':
            cursor.execute("""
                SELECT 
                    e.nombre_completo,
                    c.nombre AS capacitacion,
                    c.proveedor,
                    c.fecha_inicio,
                    c.fecha_fin,
                    ec.resultado,
                    ec.comentarios
                FROM CAPACITACION c
                JOIN `EMPLEADO-CAPACITACION` ec ON c.id_capacitacion = ec.id_capacitacion
                JOIN EMPLEADO e ON ec.id_empleado = e.id_empleado
                ORDER BY c.fecha_inicio DESC;
            """)
            rep_capacitaciones = cursor.fetchall()

        if tipo == 'proyectos' or tipo == 'todos':
            cursor.execute("""
                SELECT 
                    e.nombre_completo,
                    p.nombre AS proyecto,
                    ep.horas_asignadas,
                    ep.fecha_asignacion,
                    ep.fecha_entrega
                FROM `EMPLEADO-PROYECTO` ep
                JOIN EMPLEADO e ON ep.id_empleado = e.id_empleado
                JOIN PROYECTO p ON ep.id_proyecto = p.id_proyecto
                ORDER BY ep.fecha_asignacion DESC;
            """)
            rep_proyectos = cursor.fetchall()

        if tipo == 'presupuestos' or tipo == 'todos':
            cursor.execute("""
                SELECT 
                    d.nombre AS departamento,
                    p.fecha_inicio,
                    p.fecha_fin,
                    p.monto_asignado,
                    p.monto_utilizado,
                    (p.monto_asignado - p.monto_utilizado) AS restante
                FROM PRESUPUESTO p
                JOIN DEPARTAMENTO d ON p.id_departamento = d.id_departamento
                ORDER BY p.id_presupuesto DESC;
            """)
            rep_presupuestos = cursor.fetchall()

        return render_template(
            "reportes.html",
            rep_nomina=rep_nomina,
            rep_ausencias=rep_ausencias,
            rep_evaluaciones=rep_evaluaciones,
            rep_capacitaciones=rep_capacitaciones,
            rep_proyectos=rep_proyectos,
            rep_presupuestos=rep_presupuestos,
            tipo=tipo,
            error=None
        )

    except Exception as e:
        logging.error("⚠ ERROR EN REPORTES:", exc_info=True)
        return render_template(
            "reportes.html",
            rep_nomina=[],
            rep_ausencias=[],
            rep_evaluaciones=[],
            rep_capacitaciones=[],
            rep_proyectos=[],
            rep_presupuestos=[],
            error=f"❌ Ocurrió un error al cargar los reportes. Detalle: {str(e)}"
        )

    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if cnx:
            try:
                cnx.close()
            except Exception:
                pass
