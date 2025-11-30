
from flask import Blueprint, render_template, request, make_response
from dp import get_connection
import pymysql
import logging
import io
import csv
from datetime import datetime

reportes_bp = Blueprint("reportes", __name__)

@reportes_bp.route("/reportes")
def reportes():
    cnx = None
    cursor = None

    try:
        cnx = get_connection()
        cursor = cnx.cursor(pymysql.cursors.DictCursor)

        # Obtener parámetros
        tipo = request.args.get('tipo', 'todos')
        fecha_inicio = request.args.get('fecha_inicio', '')
        fecha_fin = request.args.get('fecha_fin', '')

        # Inicializar todos los reportes como vacíos
        rep_nomina = []
        rep_ausencias = []
        rep_evaluaciones = []
        rep_capacitaciones = []
        rep_proyectos = []
        rep_presupuestos = []
        
        # Función auxiliar para construir filtro de fecha
        def agregar_filtro_fecha(query, fecha_field):
            if fecha_inicio or fecha_fin:
                if fecha_inicio and fecha_fin:
                    return f"{query} AND {fecha_field} BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"
                elif fecha_inicio:
                    return f"{query} AND {fecha_field} >= '{fecha_inicio}'"
                elif fecha_fin:
                    return f"{query} AND {fecha_field} <= '{fecha_fin}'"
            return query

        if tipo == 'nomina' or tipo == 'todos':
            cursor.execute("""
                SELECT 
                    n.id_nomina,
                    e.nombre_completo,
                    d.nombre AS departamento,
                    n.salario_base,
                    n.deducciones,
                    n.percepciones,
                    n.total_pagar
                FROM NOMINA n
                JOIN EMPLEADO e ON n.id_empleado = e.id_empleado
                LEFT JOIN DEPARTAMENTO d ON e.id_departamento = d.id_departamento
                ORDER BY n.id_nomina DESC;
            """)
            rep_nomina = cursor.fetchall()

        if tipo == 'ausencias' or tipo == 'todos':
            query = """
                SELECT 
                    e.nombre_completo,
                    d.nombre AS departamento,
                    a.tipo,
                    a.fecha_inicio,
                    a.fecha_fin,
                    a.motivo,
                    DATEDIFF(a.fecha_fin, a.fecha_inicio) + 1 AS dias_ausencia
                FROM AUSENCIA a
                JOIN EMPLEADO e ON a.id_empleado = e.id_empleado
                LEFT JOIN DEPARTAMENTO d ON e.id_departamento = d.id_departamento
                WHERE 1=1
            """
            if fecha_inicio or fecha_fin:
                if fecha_inicio and fecha_fin:
                    query += f" AND a.fecha_inicio BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"
                elif fecha_inicio:
                    query += f" AND a.fecha_inicio >= '{fecha_inicio}'"
                elif fecha_fin:
                    query += f" AND a.fecha_fin <= '{fecha_fin}'"
            query += " ORDER BY a.fecha_inicio DESC"
            cursor.execute(query)
            rep_ausencias = cursor.fetchall()

        if tipo == 'evaluaciones' or tipo == 'todos':
            query = """
                SELECT 
                    e.nombre_completo,
                    d.nombre AS departamento,
                    ev.fecha_evaluacion,
                    ev.tipo,
                    ev.resultado,
                    ev.observaciones
                FROM EVALUACION ev
                JOIN `EMPLEADO-EVALUACION` ee ON ev.id_evaluacion = ee.id_evaluacion
                JOIN EMPLEADO e ON ee.id_empleado = e.id_empleado
                LEFT JOIN DEPARTAMENTO d ON e.id_departamento = d.id_departamento
                WHERE 1=1
            """
            if fecha_inicio or fecha_fin:
                if fecha_inicio and fecha_fin:
                    query += f" AND ev.fecha_evaluacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"
                elif fecha_inicio:
                    query += f" AND ev.fecha_evaluacion >= '{fecha_inicio}'"
                elif fecha_fin:
                    query += f" AND ev.fecha_evaluacion <= '{fecha_fin}'"
            query += " ORDER BY ev.fecha_evaluacion DESC"
            cursor.execute(query)
            rep_evaluaciones = cursor.fetchall()

        if tipo == 'capacitaciones' or tipo == 'todos':
            query = """
                SELECT 
                    e.nombre_completo,
                    d.nombre AS departamento,
                    c.nombre AS capacitacion,
                    c.proveedor,
                    c.fecha_inicio,
                    c.fecha_fin,
                    ec.resultado,
                    ec.comentarios
                FROM CAPACITACION c
                JOIN `EMPLEADO-CAPACITACION` ec ON c.id_capacitacion = ec.id_capacitacion
                JOIN EMPLEADO e ON ec.id_empleado = e.id_empleado
                LEFT JOIN DEPARTAMENTO d ON e.id_departamento = d.id_departamento
                WHERE 1=1
            """
            if fecha_inicio or fecha_fin:
                if fecha_inicio and fecha_fin:
                    query += f" AND c.fecha_inicio BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"
                elif fecha_inicio:
                    query += f" AND c.fecha_inicio >= '{fecha_inicio}'"
                elif fecha_fin:
                    query += f" AND c.fecha_fin <= '{fecha_fin}'"
            query += " ORDER BY c.fecha_inicio DESC"
            cursor.execute(query)
            rep_capacitaciones = cursor.fetchall()

        if tipo == 'proyectos' or tipo == 'todos':
            query = """
                SELECT 
                    e.nombre_completo,
                    d.nombre AS departamento,
                    p.nombre AS proyecto,
                    ep.horas_asignadas,
                    ep.fecha_asignacion,
                    ep.fecha_entrega
                FROM `EMPLEADO-PROYECTO` ep
                JOIN EMPLEADO e ON ep.id_empleado = e.id_empleado
                LEFT JOIN DEPARTAMENTO d ON e.id_departamento = d.id_departamento
                JOIN PROYECTO p ON ep.id_proyecto = p.id_proyecto
                WHERE 1=1
            """
            if fecha_inicio or fecha_fin:
                if fecha_inicio and fecha_fin:
                    query += f" AND ep.fecha_asignacion BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"
                elif fecha_inicio:
                    query += f" AND ep.fecha_asignacion >= '{fecha_inicio}'"
                elif fecha_fin:
                    query += f" AND ep.fecha_entrega <= '{fecha_fin}'"
            query += " ORDER BY ep.fecha_asignacion DESC"
            cursor.execute(query)
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
        
        # Calcular estadísticas
        stats = {}
        if tipo == 'nomina' or tipo == 'todos':
            cursor.execute("SELECT SUM(total_pagar) as total, AVG(salario_base) as promedio FROM NOMINA")
            resultado = cursor.fetchone()
            stats['nomina_total'] = resultado.get('total') or 0
            stats['nomina_promedio'] = resultado.get('promedio') or 0
        
        if tipo == 'ausencias' or tipo == 'todos':
            cursor.execute("SELECT COUNT(*) as cantidad FROM AUSENCIA")
            stats['ausencias_cantidad'] = cursor.fetchone().get('cantidad') or 0
        
        if tipo == 'evaluaciones' or tipo == 'todos':
            cursor.execute("SELECT COUNT(*) as cantidad FROM EVALUACION")
            stats['evaluaciones_cantidad'] = cursor.fetchone().get('cantidad') or 0
        
        if tipo == 'capacitaciones' or tipo == 'todos':
            cursor.execute("SELECT COUNT(*) as cantidad FROM CAPACITACION")
            stats['capacitaciones_cantidad'] = cursor.fetchone().get('cantidad') or 0
        
        if tipo == 'proyectos' or tipo == 'todos':
            cursor.execute("SELECT COUNT(*) as cantidad, SUM(horas_asignadas) as horas_totales FROM `EMPLEADO-PROYECTO`")
            resultado = cursor.fetchone()
            stats['proyectos_cantidad'] = resultado.get('cantidad') or 0
            stats['proyectos_horas'] = resultado.get('horas_totales') or 0
        
        if tipo == 'presupuestos' or tipo == 'todos':
            cursor.execute("SELECT SUM(monto_asignado) as total_asignado, SUM(monto_utilizado) as total_utilizado FROM PRESUPUESTO")
            resultado = cursor.fetchone()
            stats['presupuestos_asignado'] = resultado.get('total_asignado') or 0
            stats['presupuestos_utilizado'] = resultado.get('total_utilizado') or 0

        return render_template(
            "reportes.html",
            rep_nomina=rep_nomina,
            rep_ausencias=rep_ausencias,
            rep_evaluaciones=rep_evaluaciones,
            rep_capacitaciones=rep_capacitaciones,
            rep_proyectos=rep_proyectos,
            rep_presupuestos=rep_presupuestos,
            tipo=tipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            stats=stats,
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
            stats={},
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


@reportes_bp.route('/reportes/descargar')
def descargar_reporte():
    """Descarga un reporte en formato CSV o PDF. Parámetros: tipo, formato (csv|pdf)."""
    tipo = request.args.get('tipo', 'todos')
    formato = request.args.get('formato', 'csv')

    cnx = None
    cursor = None
    try:
        cnx = get_connection()
        cursor = cnx.cursor(pymysql.cursors.DictCursor)

        # Determinar qué consulta ejecutar según 'tipo'
        data = []
        headers = []
        title = tipo

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
            rows = cursor.fetchall()
            headers = ['id_nomina','nombre_completo','salario_base','deducciones','percepciones','total_pagar']
            data = rows
            title = 'nomina'

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
            rows = cursor.fetchall()
            headers = ['nombre_completo','tipo','fecha_inicio','fecha_fin','motivo']
            data = rows
            title = 'ausencias'

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
            rows = cursor.fetchall()
            headers = ['nombre_completo','fecha_evaluacion','tipo','resultado','observaciones']
            data = rows
            title = 'evaluaciones'

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
            rows = cursor.fetchall()
            headers = ['nombre_completo','capacitacion','proveedor','fecha_inicio','fecha_fin','resultado','comentarios']
            data = rows
            title = 'capacitaciones'

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
            rows = cursor.fetchall()
            headers = ['nombre_completo','proyecto','horas_asignadas','fecha_asignacion','fecha_entrega']
            data = rows
            title = 'proyectos'

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
            rows = cursor.fetchall()
            headers = ['departamento','fecha_inicio','fecha_fin','monto_asignado','monto_utilizado','restante']
            data = rows
            title = 'presupuestos'

        # Si tipo es 'todos', necesitamos manejar múltiples reportes
        if tipo == 'todos':
            # Colectar todos los reportes
            reportes_todos = []
            
            # Nómina
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
            reportes_todos.append(('NÓMINA', ['id_nomina','nombre_completo','salario_base','deducciones','percepciones','total_pagar'], cursor.fetchall()))
            
            # Ausencias
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
            reportes_todos.append(('AUSENCIAS', ['nombre_completo','tipo','fecha_inicio','fecha_fin','motivo'], cursor.fetchall()))
            
            # Evaluaciones
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
            reportes_todos.append(('EVALUACIONES', ['nombre_completo','fecha_evaluacion','tipo','resultado','observaciones'], cursor.fetchall()))
            
            # Capacitaciones
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
            reportes_todos.append(('CAPACITACIONES', ['nombre_completo','capacitacion','proveedor','fecha_inicio','fecha_fin','resultado','comentarios'], cursor.fetchall()))
            
            # Proyectos
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
            reportes_todos.append(('PROYECTOS', ['nombre_completo','proyecto','horas_asignadas','fecha_asignacion','fecha_entrega'], cursor.fetchall()))
            
            # Presupuestos
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
            reportes_todos.append(('PRESUPUESTOS', ['departamento','fecha_inicio','fecha_fin','monto_asignado','monto_utilizado','restante'], cursor.fetchall()))
            
            if formato == 'csv':
                si = io.StringIO()
                writer = csv.writer(si)
                
                for reporte_nombre, reporte_headers, reporte_data in reportes_todos:
                    writer.writerow([reporte_nombre])
                    writer.writerow(reporte_headers)
                    for row in reporte_data:
                        writer.writerow([row.get(h, '') for h in reporte_headers])
                    writer.writerow([])
                
                filename_base = f"reportes_completos_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                output = make_response(si.getvalue())
                output.headers['Content-Disposition'] = f"attachment; filename={filename_base}.csv"
                output.headers['Content-type'] = 'text/csv; charset=utf-8'
                return output
            else:
                return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], tipo=tipo, error='Formato no soportado')
        else:
            # Si no hay datos
            if not data:
                return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], tipo=tipo, error='No hay datos para descargar')

            filename_base = f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            if formato == 'csv':
                si = io.StringIO()
                writer = csv.writer(si)
                writer.writerow(headers)
                for row in data:
                    writer.writerow([row.get(h, '') for h in headers])
                output = make_response(si.getvalue())
                output.headers['Content-Disposition'] = f"attachment; filename={filename_base}.csv"
                output.headers['Content-type'] = 'text/csv; charset=utf-8'
                return output
            else:
                return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], tipo=tipo, error='Formato no soportado')

    except Exception as e:
        logging.error('Error al generar descarga', exc_info=True)
        return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], tipo=tipo, error=f'Error al generar el archivo: {e}')

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
