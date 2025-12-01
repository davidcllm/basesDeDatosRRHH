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

        # Obtener el tipo de reporte a mostrar
        tipo = request.args.get('tipo', 'todos')
        
        # Validar tipo de reporte
        tipos_validos = ['todos', 'nomina', 'ausencias', 'evaluaciones', 'capacitaciones', 'proyectos', 'presupuestos']
        if tipo not in tipos_validos:
            tipo = 'todos'

        # Inicializar todos los reportes como vacíos
        rep_nomina = []
        rep_ausencias = []
        rep_evaluaciones = []
        rep_capacitaciones = []
        rep_proyectos = []
        rep_presupuestos = []

        if tipo == 'nomina' or tipo == 'todos':
            try:
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
            except Exception as e:
                logging.warning(f"Error al obtener nómina: {e}")
                rep_nomina = []

        if tipo == 'ausencias' or tipo == 'todos':
            try:
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
            except Exception as e:
                logging.warning(f"Error al obtener ausencias: {e}")
                rep_ausencias = []

        if tipo == 'evaluaciones' or tipo == 'todos':
            try:
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
            except Exception as e:
                logging.warning(f"Error al obtener evaluaciones: {e}")
                rep_evaluaciones = []

        if tipo == 'capacitaciones' or tipo == 'todos':
            try:
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
            except Exception as e:
                logging.warning(f"Error al obtener capacitaciones: {e}")
                rep_capacitaciones = []

        if tipo == 'proyectos' or tipo == 'todos':
            try:
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
            except Exception as e:
                logging.warning(f"Error al obtener proyectos: {e}")
                rep_proyectos = []

        if tipo == 'presupuestos' or tipo == 'todos':
            try:
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
            except Exception as e:
                logging.warning(f"Error al obtener presupuestos: {e}")
                rep_presupuestos = []

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


@reportes_bp.route('/reportes/descargar')
def descargar_reporte():
    """Descarga un reporte en formato CSV o PDF. Parámetros: tipo, formato (csv|pdf)."""
    tipo = request.args.get('tipo', 'todos')
    formato = request.args.get('formato', 'csv')
    
    # Validar parámetros
    tipos_validos = ['todos', 'nomina', 'ausencias', 'evaluaciones', 'capacitaciones', 'proyectos', 'presupuestos']
    formatos_validos = ['csv']
    
    if tipo not in tipos_validos:
        return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], 
                             rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], 
                             tipo='todos', error='Tipo de reporte no válido')
    
    if formato not in formatos_validos:
        return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], 
                             rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], 
                             tipo=tipo, error='Formato no soportado. Solo se admite CSV.')

    cnx = None
    cursor = None
    try:
        cnx = get_connection()
        if not cnx:
            return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], 
                                 rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], 
                                 tipo=tipo, error='❌ No se pudo establecer conexión con la base de datos')
        
        cursor = cnx.cursor(pymysql.cursors.DictCursor)

        # Nombre del archivo según el tipo
        if tipo == 'todos':
            filename_base = f"reporte_completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            filename_base = f"{tipo}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Si es "todos", descargar todas las tablas en un solo CSV
        if tipo == 'todos':
            tablas = [
                {
                    'title': 'Resumen de Nómina',
                    'query': """
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
                    """,
                    'headers': ['id_nomina','nombre_completo','salario_base','deducciones','percepciones','total_pagar']
                },
                {
                    'title': 'Ausencias del Personal',
                    'query': """
                        SELECT 
                            e.nombre_completo,
                            a.tipo,
                            a.fecha_inicio,
                            a.fecha_fin,
                            a.motivo
                        FROM AUSENCIA a
                        JOIN EMPLEADO e ON a.id_empleado = e.id_empleado
                        ORDER BY a.fecha_inicio DESC;
                    """,
                    'headers': ['nombre_completo','tipo','fecha_inicio','fecha_fin','motivo']
                },
                {
                    'title': 'Evaluaciones de Desempeño',
                    'query': """
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
                    """,
                    'headers': ['nombre_completo','fecha_evaluacion','tipo','resultado','observaciones']
                },
                {
                    'title': 'Capacitaciones por Empleado',
                    'query': """
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
                    """,
                    'headers': ['nombre_completo','capacitacion','proveedor','fecha_inicio','fecha_fin','resultado','comentarios']
                },
                {
                    'title': 'Participación en Proyectos',
                    'query': """
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
                    """,
                    'headers': ['nombre_completo','proyecto','horas_asignadas','fecha_asignacion','fecha_entrega']
                },
                {
                    'title': 'Presupuestos por Departamento',
                    'query': """
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
                    """,
                    'headers': ['departamento','fecha_inicio','fecha_fin','monto_asignado','monto_utilizado','restante']
                },
            ]
            
            si = io.StringIO()
            writer = csv.writer(si)
            hay_datos = False
            
            for tabla in tablas:
                try:
                    cursor.execute(tabla['query'])
                    rows = cursor.fetchall()
                    if rows:
                        hay_datos = True
                        writer.writerow([tabla['title']])
                        writer.writerow(tabla['headers'])
                        for row in rows:
                            writer.writerow([row.get(h, '') for h in tabla['headers']])
                        writer.writerow([])  # Línea vacía entre tablas
                except Exception as e:
                    logging.warning(f"Error al obtener datos de {tabla['title']}: {e}")
                    continue
            
            if not hay_datos:
                return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], tipo=tipo, error='No hay datos para descargar')
            
            # Validar tamaño del archivo (máximo 50MB)
            csv_size = len(si.getvalue())
            if csv_size > 50 * 1024 * 1024:  # 50MB
                return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], 
                                     rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], 
                                     tipo=tipo, error='El archivo es demasiado grande. Intenta filtrar los datos.')
            
            # Agregar BOM UTF-8 para que Excel reconozca los acentos
            csv_size = len(si.getvalue())
            if csv_size > 50 * 1024 * 1024:  # 50MB
                return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], 
                                     rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], 
                                     tipo=tipo, error='El archivo es demasiado grande. Intenta filtrar los datos.')
            
            # Agregar BOM UTF-8 para que Excel reconozca los acentos
            csv_content = '\ufeff' + si.getvalue()
            output = make_response(csv_content)
            output.headers['Content-Disposition'] = f"attachment; filename={filename_base}.csv"
            output.headers['Content-type'] = 'text/csv; charset=utf-8-sig'
            return output

        # Para reportes individuales
        data = []
        headers = []
        title = tipo

        if tipo == 'nomina':
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

        elif tipo == 'ausencias':
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

        elif tipo == 'evaluaciones':
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

        elif tipo == 'capacitaciones':
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

        elif tipo == 'proyectos':
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

        elif tipo == 'presupuestos':
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
        
        else:
            # Tipo no reconocido (no debería llegar aquí por la validación previa)
            return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], 
                                 rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], 
                                 tipo='todos', error='Tipo de reporte no válido')

        # Si no hay datos
        if not data:
            return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], tipo=tipo, error='No hay datos para descargar')

        if formato == 'csv':
            si = io.StringIO()
            writer = csv.writer(si)
            writer.writerow(headers)
            for row in data:
                writer.writerow([row.get(h, '') for h in headers])
            
            # Agregar BOM UTF-8 para que Excel reconozca los acentos
            csv_content = '\ufeff' + si.getvalue()
            output = make_response(csv_content)
            output.headers['Content-Disposition'] = f"attachment; filename={filename_base}.csv"
            output.headers['Content-type'] = 'text/csv; charset=utf-8-sig'
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