from flask import Blueprint, render_template
from dp import get_connection
import pymysql

reportes_bp = Blueprint("reportes", __name__)

@reportes_bp.route("/reportes")
def reportes():
    """
    Módulo: Reportes y Estadísticas
    """

    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    # 1) RESUMEN DE NÓMINA - CORREGIDO
    cursor.execute("""
        SELECT 
            e.id_empleado,
            e.nombre_completo,
            n.id_nomina,
            n.salario_base,
            n.deducciones,
            n.percepciones,
            n.total_pagar
        FROM EMPLEADO e
        JOIN NOMINA n ON e.id_empleado = n.id_empleado
        ORDER BY e.nombre_completo ASC;
    """)
    rep_nomina = cursor.fetchall()

    # 2) AUSENCIAS DEL PERSONAL
    cursor.execute("""
        SELECT 
            e.id_empleado,
            e.nombre_completo,
            a.id_ausencia,
            a.tipo,
            a.fecha_inicio,
            a.fecha_fin,
            a.motivo
        FROM EMPLEADO e
        JOIN AUSENCIA a ON e.id_empleado = a.id_empleado
        ORDER BY a.fecha_inicio DESC;
    """)
    rep_ausencias = cursor.fetchall()

    # 3) EVALUACIONES POR EMPLEADO
    cursor.execute("""
        SELECT 
            e.id_empleado,
            e.nombre_completo,
            ev.id_evaluacion,
            ev.fecha_evaluacion,
            ev.tipo,
            ev.resultado,
            ev.observaciones
        FROM EMPLEADO e
        JOIN `EMPLEADO-EVALUACION` ee ON e.id_empleado = ee.id_empleado
        JOIN EVALUACION ev ON ee.id_evaluacion = ev.id_evaluacion
        ORDER BY ev.fecha_evaluacion DESC;
    """)
    rep_evaluaciones = cursor.fetchall()

    # 4) CAPACITACIONES POR EMPLEADO
    cursor.execute("""
        SELECT 
            e.id_empleado,
            e.nombre_completo,
            c.id_capacitacion,
            c.nombre AS capacitacion,
            c.fecha_inicio,
            c.fecha_fin,
            c.proveedor,
            ec.resultado,
            ec.comentarios
        FROM EMPLEADO e
        JOIN `EMPLEADO-CAPACITACION` ec ON e.id_empleado = ec.id_empleado
        JOIN CAPACITACION c ON ec.id_capacitacion = c.id_capacitacion
        ORDER BY c.fecha_inicio DESC;
    """)
    rep_capacitaciones = cursor.fetchall()

    # 5) PARTICIPACIÓN EN PROYECTOS
    cursor.execute("""
        SELECT 
            e.id_empleado,
            e.nombre_completo,
            p.id_proyecto,
            p.nombre AS proyecto,
            ep.horas_asignadas,
            ep.fecha_asignacion,
            ep.fecha_entrega
        FROM EMPLEADO e
        JOIN `EMPLEADO-PROYECTO` ep ON e.id_empleado = ep.id_empleado
        JOIN PROYECTO p ON ep.id_proyecto = p.id_proyecto
        ORDER BY p.nombre ASC, e.nombre_completo ASC;
    """)
    rep_proyectos = cursor.fetchall()

    # 6) PRESUPUESTOS POR DEPARTAMENTO - CORREGIDO
    cursor.execute("""
        SELECT 
            d.nombre AS departamento,
            p.fecha_inicio AS periodo_inicio,
            p.fecha_fin AS periodo_fin,
            p.monto_asignado,
            p.monto_utilizado,
            (p.monto_asignado - p.monto_utilizado) AS restante
        FROM PRESUPUESTO p
        JOIN DEPARTAMENTO d ON p.id_departamento = d.id_departamento
        ORDER BY d.nombre ASC, p.fecha_inicio DESC;
    """)
    rep_presupuestos = cursor.fetchall()

    cursor.close()
    cnx.close()

    return render_template(
        "reportes.html",
        rep_nomina=rep_nomina,
        rep_ausencias=rep_ausencias,
        rep_evaluaciones=rep_evaluaciones,
        rep_capacitaciones=rep_capacitaciones,
        rep_proyectos=rep_proyectos,
        rep_presupuestos=rep_presupuestos
    )
