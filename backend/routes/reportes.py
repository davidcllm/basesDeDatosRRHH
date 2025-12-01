from flask import Blueprint, render_template, request, make_response
from dp import get_connection
import pymysql
import logging
import io
import csv
from datetime import datetime

reportes_bp = Blueprint("reportes", __name__)


def _parse_date_param(raw_value, label):
    if not raw_value:
        return None
    value = raw_value.strip()
    if not value:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return value
    except ValueError:
        logging.warning("Fecha inválida recibida para %s: %s", label, raw_value)
        return None


def _build_date_clause(fecha_inicio, fecha_fin, *, start_field=None, end_field=None, single_field=None):
    clauses = []
    params = []
    if single_field:
        if fecha_inicio and fecha_fin:
            clauses.append(f"{single_field} BETWEEN %s AND %s")
            params.extend([fecha_inicio, fecha_fin])
        elif fecha_inicio:
            clauses.append(f"{single_field} >= %s")
            params.append(fecha_inicio)
        elif fecha_fin:
            clauses.append(f"{single_field} <= %s")
            params.append(fecha_fin)
    elif start_field and end_field:
        if fecha_inicio and fecha_fin:
            clauses.append(f"{start_field} >= %s AND {end_field} <= %s")
            params.extend([fecha_inicio, fecha_fin])
        elif fecha_inicio:
            clauses.append(f"{start_field} >= %s")
            params.append(fecha_inicio)
        elif fecha_fin:
            clauses.append(f"{end_field} <= %s")
            params.append(fecha_fin)

    if not clauses:
        return "", []

    return " WHERE " + " AND ".join(clauses), params


def _build_query_config(tipo, fecha_inicio=None, fecha_fin=None):
    if tipo == 'nomina':
        query = """
            SELECT 
                n.id_nomina,
                e.nombre_completo,
                n.salario_base,
                n.deducciones,
                n.percepciones,
                n.total_pagar
            FROM NOMINA n
            JOIN EMPLEADO e ON n.id_empleado = e.id_empleado
            ORDER BY n.id_nomina DESC
        """
        headers = ['id_nomina','nombre_completo','salario_base','deducciones','percepciones','total_pagar']
        title = 'Resumen de Nómina'
        params = []
    elif tipo == 'ausencias':
        base_query = """
            SELECT 
                e.nombre_completo,
                a.tipo,
                a.fecha_inicio,
                a.fecha_fin,
                a.motivo
            FROM AUSENCIA a
            JOIN EMPLEADO e ON a.id_empleado = e.id_empleado
        """
        clause, params = _build_date_clause(
            fecha_inicio,
            fecha_fin,
            start_field='a.fecha_inicio',
            end_field='a.fecha_fin'
        )
        query = base_query + clause + " ORDER BY a.fecha_inicio DESC"
        headers = ['nombre_completo','tipo','fecha_inicio','fecha_fin','motivo']
        title = 'Ausencias del Personal'
    elif tipo == 'evaluaciones':
        base_query = """
            SELECT 
                e.nombre_completo,
                ev.fecha_evaluacion,
                ev.tipo,
                ev.resultado,
                ev.observaciones
            FROM EVALUACION ev
            JOIN `EMPLEADO-EVALUACION` ee ON ev.id_evaluacion = ee.id_evaluacion
            JOIN EMPLEADO e ON ee.id_empleado = e.id_empleado
        """
        clause, params = _build_date_clause(
            fecha_inicio,
            fecha_fin,
            single_field='ev.fecha_evaluacion'
        )
        query = base_query + clause + " ORDER BY ev.fecha_evaluacion DESC"
        headers = ['nombre_completo','fecha_evaluacion','tipo','resultado','observaciones']
        title = 'Evaluaciones de Desempeño'
    elif tipo == 'capacitaciones':
        base_query = """
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
        """
        clause, params = _build_date_clause(
            fecha_inicio,
            fecha_fin,
            start_field='c.fecha_inicio',
            end_field='c.fecha_fin'
        )
        query = base_query + clause + " ORDER BY c.fecha_inicio DESC"
        headers = ['nombre_completo','capacitacion','proveedor','fecha_inicio','fecha_fin','resultado','comentarios']
        title = 'Capacitaciones por Empleado'
    elif tipo == 'proyectos':
        base_query = """
            SELECT 
                e.nombre_completo,
                p.nombre AS proyecto,
                ep.horas_asignadas,
                ep.fecha_asignacion,
                ep.fecha_entrega
            FROM `EMPLEADO-PROYECTO` ep
            JOIN EMPLEADO e ON ep.id_empleado = e.id_empleado
            JOIN PROYECTO p ON ep.id_proyecto = p.id_proyecto
        """
        clause, params = _build_date_clause(
            fecha_inicio,
            fecha_fin,
            start_field='ep.fecha_asignacion',
            end_field='ep.fecha_entrega'
        )
        query = base_query + clause + " ORDER BY ep.fecha_asignacion DESC"
        headers = ['nombre_completo','proyecto','horas_asignadas','fecha_asignacion','fecha_entrega']
        title = 'Participación en Proyectos'
    elif tipo == 'presupuestos':
        base_query = """
            SELECT 
                d.nombre AS departamento,
                p.fecha_inicio,
                p.fecha_fin,
                p.monto_asignado,
                p.monto_utilizado,
                (p.monto_asignado - p.monto_utilizado) AS restante
            FROM PRESUPUESTO p
            JOIN DEPARTAMENTO d ON p.id_departamento = d.id_departamento
        """
        clause, params = _build_date_clause(
            fecha_inicio,
            fecha_fin,
            start_field='p.fecha_inicio',
            end_field='p.fecha_fin'
        )
        query = base_query + clause + " ORDER BY p.id_presupuesto DESC"
        headers = ['departamento','fecha_inicio','fecha_fin','monto_asignado','monto_utilizado','restante']
        title = 'Presupuestos por Departamento'
    else:
        return None

    return {
        'query': query,
        'params': tuple(params),
        'headers': headers,
        'title': title
    }

@reportes_bp.route("/reportes")
def reportes():
    cnx = None
    cursor = None

    try:
        cnx = get_connection()
        cursor = cnx.cursor(pymysql.cursors.DictCursor)

        # Obtener el tipo de reporte a mostrar
        tipo = request.args.get('tipo', 'todos')
        
        # Obtener parámetros de fecha
        fecha_inicio = _parse_date_param(request.args.get('fecha_inicio'), 'fecha_inicio')
        fecha_fin = _parse_date_param(request.args.get('fecha_fin'), 'fecha_fin')
        
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
                query = """
                    SELECT 
                        e.nombre_completo,
                        a.tipo,
                        a.fecha_inicio,
                        a.fecha_fin,
                        a.motivo
                    FROM AUSENCIA a
                    JOIN EMPLEADO e ON a.id_empleado = e.id_empleado
                """
                
                # Agregar filtro de fechas si se proporcionan
                if fecha_inicio and fecha_fin:
                    query += " WHERE a.fecha_inicio >= %s AND a.fecha_fin <= %s"
                    cursor.execute(query + " ORDER BY a.fecha_inicio DESC;", (fecha_inicio, fecha_fin))
                elif fecha_inicio:
                    query += " WHERE a.fecha_inicio >= %s"
                    cursor.execute(query + " ORDER BY a.fecha_inicio DESC;", (fecha_inicio,))
                elif fecha_fin:
                    query += " WHERE a.fecha_fin <= %s"
                    cursor.execute(query + " ORDER BY a.fecha_inicio DESC;", (fecha_fin,))
                else:
                    cursor.execute(query + " ORDER BY a.fecha_inicio DESC;")
                
                rep_ausencias = cursor.fetchall()
            except Exception as e:
                logging.warning(f"Error al obtener ausencias: {e}")
                rep_ausencias = []

        if tipo == 'evaluaciones' or tipo == 'todos':
            try:
                query = """
                    SELECT 
                        e.nombre_completo,
                        ev.fecha_evaluacion,
                        ev.tipo,
                        ev.resultado,
                        ev.observaciones
                    FROM EVALUACION ev
                    JOIN `EMPLEADO-EVALUACION` ee ON ev.id_evaluacion = ee.id_evaluacion
                    JOIN EMPLEADO e ON ee.id_empleado = e.id_empleado
                """
                
                # Agregar filtro de fechas si se proporcionan
                if fecha_inicio and fecha_fin:
                    query += " WHERE ev.fecha_evaluacion BETWEEN %s AND %s"
                    cursor.execute(query + " ORDER BY ev.fecha_evaluacion DESC;", (fecha_inicio, fecha_fin))
                elif fecha_inicio:
                    query += " WHERE ev.fecha_evaluacion >= %s"
                    cursor.execute(query + " ORDER BY ev.fecha_evaluacion DESC;", (fecha_inicio,))
                elif fecha_fin:
                    query += " WHERE ev.fecha_evaluacion <= %s"
                    cursor.execute(query + " ORDER BY ev.fecha_evaluacion DESC;", (fecha_fin,))
                else:
                    cursor.execute(query + " ORDER BY ev.fecha_evaluacion DESC;")
                
                rep_evaluaciones = cursor.fetchall()
            except Exception as e:
                logging.warning(f"Error al obtener evaluaciones: {e}")
                rep_evaluaciones = []

        if tipo == 'capacitaciones' or tipo == 'todos':
            try:
                query = """
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
                """
                
                # Agregar filtro de fechas si se proporcionan
                if fecha_inicio and fecha_fin:
                    query += " WHERE c.fecha_inicio >= %s AND c.fecha_fin <= %s"
                    cursor.execute(query + " ORDER BY c.fecha_inicio DESC;", (fecha_inicio, fecha_fin))
                elif fecha_inicio:
                    query += " WHERE c.fecha_inicio >= %s"
                    cursor.execute(query + " ORDER BY c.fecha_inicio DESC;", (fecha_inicio,))
                elif fecha_fin:
                    query += " WHERE c.fecha_fin <= %s"
                    cursor.execute(query + " ORDER BY c.fecha_inicio DESC;", (fecha_fin,))
                else:
                    cursor.execute(query + " ORDER BY c.fecha_inicio DESC;")
                
                rep_capacitaciones = cursor.fetchall()
            except Exception as e:
                logging.warning(f"Error al obtener capacitaciones: {e}")
                rep_capacitaciones = []

        if tipo == 'proyectos' or tipo == 'todos':
            try:
                query = """
                    SELECT 
                        e.nombre_completo,
                        p.nombre AS proyecto,
                        ep.horas_asignadas,
                        ep.fecha_asignacion,
                        ep.fecha_entrega
                    FROM `EMPLEADO-PROYECTO` ep
                    JOIN EMPLEADO e ON ep.id_empleado = e.id_empleado
                    JOIN PROYECTO p ON ep.id_proyecto = p.id_proyecto
                """
                
                # Agregar filtro de fechas si se proporcionan
                if fecha_inicio and fecha_fin:
                    query += " WHERE ep.fecha_asignacion >= %s AND ep.fecha_entrega <= %s"
                    cursor.execute(query + " ORDER BY ep.fecha_asignacion DESC;", (fecha_inicio, fecha_fin))
                elif fecha_inicio:
                    query += " WHERE ep.fecha_asignacion >= %s"
                    cursor.execute(query + " ORDER BY ep.fecha_asignacion DESC;", (fecha_inicio,))
                elif fecha_fin:
                    query += " WHERE ep.fecha_entrega <= %s"
                    cursor.execute(query + " ORDER BY ep.fecha_asignacion DESC;", (fecha_fin,))
                else:
                    cursor.execute(query + " ORDER BY ep.fecha_asignacion DESC;")
                
                rep_proyectos = cursor.fetchall()
            except Exception as e:
                logging.warning(f"Error al obtener proyectos: {e}")
                rep_proyectos = []

        if tipo == 'presupuestos' or tipo == 'todos':
            try:
                query = """
                    SELECT 
                        d.nombre AS departamento,
                        p.fecha_inicio,
                        p.fecha_fin,
                        p.monto_asignado,
                        p.monto_utilizado,
                        (p.monto_asignado - p.monto_utilizado) AS restante
                    FROM PRESUPUESTO p
                    JOIN DEPARTAMENTO d ON p.id_departamento = d.id_departamento
                """
                
                # Agregar filtro de fechas si se proporcionan
                if fecha_inicio and fecha_fin:
                    query += " WHERE p.fecha_inicio >= %s AND p.fecha_fin <= %s"
                    cursor.execute(query + " ORDER BY p.id_presupuesto DESC;", (fecha_inicio, fecha_fin))
                elif fecha_inicio:
                    query += " WHERE p.fecha_inicio >= %s"
                    cursor.execute(query + " ORDER BY p.id_presupuesto DESC;", (fecha_inicio,))
                elif fecha_fin:
                    query += " WHERE p.fecha_fin <= %s"
                    cursor.execute(query + " ORDER BY p.id_presupuesto DESC;", (fecha_fin,))
                else:
                    cursor.execute(query + " ORDER BY p.id_presupuesto DESC;")
                
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
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
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
    fecha_inicio = _parse_date_param(request.args.get('fecha_inicio'), 'fecha_inicio')
    fecha_fin = _parse_date_param(request.args.get('fecha_fin'), 'fecha_fin')
    tablas_param = request.args.get('tablas')
    
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
            filtered_tables = []
            if tablas_param:
                parts = [p.strip().lower() for p in tablas_param.split(',') if p.strip()]
                seen = set()
                for part in parts:
                    if part in tipos_validos and part != 'todos' and part not in seen:
                        filtered_tables.append(part)
                        seen.add(part)
            tablas_tipo = filtered_tables if filtered_tables else ['nomina','ausencias','evaluaciones','capacitaciones','proyectos','presupuestos']
            si = io.StringIO()
            writer = csv.writer(si)
            hay_datos = False

            for tabla_tipo in tablas_tipo:
                config = _build_query_config(tabla_tipo, fecha_inicio, fecha_fin)
                if not config:
                    continue
                try:
                    cursor.execute(config['query'], config['params'])
                    rows = cursor.fetchall()
                    if rows:
                        hay_datos = True
                        writer.writerow([config['title']])
                        writer.writerow(config['headers'])
                        for row in rows:
                            writer.writerow([row.get(h, '') for h in config['headers']])
                        writer.writerow([])
                except Exception as e:
                    logging.warning(f"Error al obtener datos de {config['title']}: {e}")
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
        config = _build_query_config(tipo, fecha_inicio, fecha_fin)
        if not config:
            return render_template('reportes.html', rep_nomina=[], rep_ausencias=[], rep_evaluaciones=[], 
                                 rep_capacitaciones=[], rep_proyectos=[], rep_presupuestos=[], 
                                 tipo='todos', error='Tipo de reporte no válido')

        cursor.execute(config['query'], config['params'])
        rows = cursor.fetchall()
        headers = config['headers']
        data = rows

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