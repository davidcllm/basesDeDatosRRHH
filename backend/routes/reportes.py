from flask import Blueprint, render_template, request, make_response
from dp import get_connection
import pymysql
import logging
import io
import csv
from datetime import datetime

reportes_bp = Blueprint("reportes", __name__)


@reportes_bp.route('/reportes/descargar')
def descargar_reporte():
    """Descarga un reporte en formato CSV. Parámetros: tipo, formato (csv)."""
    tipo = request.args.get('tipo', 'todos')
    formato = request.args.get('formato', 'csv')

    cnx = None
    cursor = None
    try:
        cnx = get_connection()
        cursor = cnx.cursor(pymysql.cursors.DictCursor)

        # Diccionario para almacenar reportes sin sobrescritura
        reports = {
            'nomina': {'headers': [], 'data': []},
            'ausencias': {'headers': [], 'data': []},
            'evaluaciones': {'headers': [], 'data': []},
            'capacitaciones': {'headers': [], 'data': []},
            'proyectos': {'headers': [], 'data': []},
            'presupuestos': {'headers': [], 'data': []}
        }

        # Ejecutar consultas según tipo
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
            reports['nomina']['headers'] = ['id_nomina','nombre_completo','salario_base','deducciones','percepciones','total_pagar']
            reports['nomina']['data'] = cursor.fetchall()

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
            reports['ausencias']['headers'] = ['nombre_completo','tipo','fecha_inicio','fecha_fin','motivo']
            reports['ausencias']['data'] = cursor.fetchall()

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
            reports['evaluaciones']['headers'] = ['nombre_completo','fecha_evaluacion','tipo','resultado','observaciones']
            reports['evaluaciones']['data'] = cursor.fetchall()

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
            reports['capacitaciones']['headers'] = ['nombre_completo','capacitacion','proveedor','fecha_inicio','fecha_fin','resultado','comentarios']
            reports['capacitaciones']['data'] = cursor.fetchall()

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
            reports['proyectos']['headers'] = ['nombre_completo','proyecto','horas_asignadas','fecha_asignacion','fecha_entrega']
            reports['proyectos']['data'] = cursor.fetchall()

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
            reports['presupuestos']['headers'] = ['departamento','fecha_inicio','fecha_fin','monto_asignado','monto_utilizado','restante']
            reports['presupuestos']['data'] = cursor.fetchall()

        # Preparar datos para CSV
        si = io.StringIO()
        writer = csv.writer(si)
        
        if tipo == 'todos':
            # Combinar todos los reportes en un CSV
            has_data = False
            for report_type, report_content in reports.items():
                if report_content['data']:
                    has_data = True
                    # Encabezado de sección
                    writer.writerow([report_type.upper()])
                    writer.writerow(report_content['headers'])
                    for row in report_content['data']:
                        writer.writerow([row.get(h, '') for h in report_content['headers']])
                    writer.writerow([])  # Línea en blanco entre secciones
            
            if not has_data:
                return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], tipo=tipo, error='No hay datos para descargar')
            
            filename_base = f"reportes_completos_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            # Reporte individual - validar que el tipo sea válido
            if tipo not in reports:
                return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], tipo=tipo, error='Tipo de reporte no válido')
            
            if not reports[tipo]['data']:
                return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], tipo=tipo, error='No hay datos para descargar')
            
            writer.writerow(reports[tipo]['headers'])
            for row in reports[tipo]['data']:
                writer.writerow([row.get(h, '') for h in reports[tipo]['headers']])
            
            filename_base = f"{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if formato != 'csv':
            return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], tipo=tipo, error='Solo se soporta formato CSV')
        
        output = make_response(si.getvalue())
        output.headers['Content-Disposition'] = f"attachment; filename={filename_base}.csv"
        output.headers['Content-type'] = 'text/csv; charset=utf-8'
        return output

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