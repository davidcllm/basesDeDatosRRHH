from flask import Blueprint, render_template, make_response, send_file
from dp import get_connection
import pymysql
import csv
import io
import zipfile
import datetime

reportes_bp = Blueprint("reportes", __name__)


# ======================================================
#   📌 FUNCIÓN PARA EXPORTAR CUALQUIER REPORTE A CSV
# ======================================================
def export_to_csv(filename, query, headers):
    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    cnx.close()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(headers)

    for row in data:
        writer.writerow(list(row.values()))

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output


# ======================================================
# 📌 CSV Individuales
# ======================================================

@reportes_bp.route("/reportes/csv/nomina")
def csv_nomina():
    return export_to_csv(
        "nomina.csv",
        """
        SELECT e.nombre_completo, n.salario_base, n.deducciones,
        n.percepciones, n.total_pagar, en.fecha_inicio, en.fecha_fin
        FROM EMPLEADO e
        JOIN `EMPLEADO-NOMINA` en ON e.id_empleado = en.id_empleado
        JOIN NOMINA n ON en.id_nomina = n.id_nomina
        """,
        ["Empleado", "Salario Base", "Deducciones", "Percepciones", "Total Pagar", "Inicio", "Fin"]
    )


@reportes_bp.route("/reportes/csv/ausencias")
def csv_ausencias():
    return export_to_csv(
        "ausencias.csv",
        """
        SELECT e.nombre_completo, a.tipo, a.fecha_inicio, a.fecha_fin, a.motivo
        FROM EMPLEADO e
        JOIN AUSENCIA a ON e.id_empleado = a.id_empleado
        """,
        ["Empleado", "Tipo", "Inicio", "Fin", "Motivo"]
    )


@reportes_bp.route("/reportes/csv/evaluaciones")
def csv_evaluaciones():
    return export_to_csv(
        "evaluaciones.csv",
        """
        SELECT e.nombre_completo, ev.fecha_evaluacion, ev.tipo, ev.resultado, ev.observaciones
        FROM EMPLEADO e
        JOIN `EMPLEADO-EVALUACION` ee ON e.id_empleado = ee.id_empleado
        JOIN EVALUACION ev ON ee.id_evaluacion = ev.id_evaluacion
        """,
        ["Empleado", "Fecha Evaluación", "Tipo", "Resultado", "Observaciones"]
    )


@reportes_bp.route("/reportes/csv/capacitaciones")
def csv_capacitaciones():
    return export_to_csv(
        "capacitaciones.csv",
        """
        SELECT e.nombre_completo, c.nombre AS capacitacion, c.proveedor,
        c.fecha_inicio, c.fecha_fin, ec.resultado, ec.comentarios
        FROM EMPLEADO e
        JOIN `EMPLEADO-CAPACITACION` ec ON e.id_empleado = ec.id_empleado
        JOIN CAPACITACION c ON ec.id_capacitacion = c.id_capacitacion
        """,
        ["Empleado", "Capacitación", "Proveedor", "Inicio", "Fin", "Resultado", "Comentarios"]
    )


@reportes_bp.route("/reportes/csv/proyectos")
def csv_proyectos():
    return export_to_csv(
        "proyectos.csv",
        """
        SELECT e.nombre_completo, p.nombre AS proyecto, ep.horas_asignadas,
        ep.fecha_asignacion, ep.fecha_entrega
        FROM EMPLEADO e
        JOIN `EMPLEADO-PROYECTO` ep ON e.id_empleado = ep.id_empleado
        JOIN PROYECTO p ON ep.id_proyecto = p.id_proyecto
        """,
        ["Empleado", "Proyecto", "Horas", "Asignación", "Entrega"]
    )


@reportes_bp.route("/reportes/csv/presupuestos")
def csv_presupuestos():
    return export_to_csv(
        "presupuestos.csv",
        """
        SELECT d.nombre AS departamento, p.periodo,
        p.monto_asignado, p.monto_utilizado,
        (p.monto_asignado - p.monto_utilizado) AS restante
        FROM PRESUPUESTO p
        JOIN DEPARTAMENTO d ON p.id_departamento = d.id_departamento
        """,
        ["Departamento", "Periodo", "Asignado", "Utilizado", "Restante"]
    )


# ======================================================
# 📌 ZIP con TODOS los reportes
# ======================================================
@reportes_bp.route("/reportes/zip")
def zip_reportes():
    files = {
        "nomina.csv": "/reportes/csv/nomina",
        "ausencias.csv": "/reportes/csv/ausencias",
        "evaluaciones.csv": "/reportes/csv/evaluaciones",
        "capacitaciones.csv": "/reportes/csv/capacitaciones",
        "proyectos.csv": "/reportes/csv/proyectos",
        "presupuestos.csv": "/reportes/csv/presupuestos",
    }

    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, "w") as zf:
        for filename, path in files.items():
            with reportes_bp.test_request_context(path):
                data = reportes_bp.view_functions[path[1:].replace("/", ".")]()
                zf.writestr(filename, data.response[0])

    mem_zip.seek(0)
    return send_file(
        mem_zip,
        mimetype='application/zip',
        as_attachment=True,
        download_name="reportes_completos.zip"
    )
