@reportes_bp.route("/reportes/exportar_csv/<string:tipo>")
def exportar_csv(tipo):
    """
    Exportar datos a CSV según el tipo solicitado:
      - nomina
      - ausencias
      - evaluaciones
      - capacitaciones
      - proyectos
      - presupuestos
    """

    cnx = get_connection()
    cursor = cnx.cursor(pymysql.cursors.DictCursor)

    consultas = {
        "nomina": """
            SELECT e.nombre_completo AS empleado, n.salario_base, n.deducciones, 
                   n.percepciones, n.total_pagar
            FROM EMPLEADO e
            JOIN `EMPLEADO-NOMINA` en ON e.id_empleado = en.id_empleado
            JOIN NOMINA n ON en.id_nomina = n.id_nomina
        """,
        "ausencias": """
            SELECT e.nombre_completo AS empleado, a.tipo, a.fecha_inicio, a.fecha_fin, a.motivo
            FROM EMPLEADO e
            JOIN AUSENCIA a ON e.id_empleado = a.id_empleado
        """,
        "evaluaciones": """
            SELECT e.nombre_completo AS empleado, ev.fecha_evaluacion, ev.tipo, ev.resultado
            FROM EMPLEADO e
            JOIN `EMPLEADO-EVALUACION` ee ON e.id_empleado = ee.id_empleado
            JOIN EVALUACION ev ON ee.id_evaluacion = ev.id_evaluacion
        """,
        "capacitaciones": """
            SELECT e.nombre_completo AS empleado, c.nombre AS capacitacion,
                   c.proveedor, c.fecha_inicio, c.fecha_fin
            FROM EMPLEADO e
            JOIN `EMPLEADO-CAPACITACION` ec ON e.id_empleado = ec.id_empleado
            JOIN CAPACITACION c ON ec.id_capacitacion = c.id_capacitacion
        """,
        "proyectos": """
            SELECT e.nombre_completo AS empleado, p.nombre AS proyecto,
                   ep.horas_asignadas
            FROM EMPLEADO e
            JOIN `EMPLEADO-PROYECTO` ep ON e.id_empleado = ep.id_empleado
            JOIN PROYECTO p ON ep.id_proyecto = p.id_proyecto
        """,
        "presupuestos": """
            SELECT d.nombre AS departamento, p.periodo,
                   p.monto_asignado, p.monto_utilizado,
                   (p.monto_asignado - p.monto_utilizado) AS restante
            FROM PRESUPUESTO p
            JOIN DEPARTAMENTO d ON p.id_departamento = d.id_departamento
        """
    }

    if tipo not in consultas:
        return "Tipo de reporte inválido", 400

    cursor.execute(consultas[tipo])
    datos = cursor.fetchall()
    cursor.close()
    cnx.close()

    # Convertir a CSV
    import csv
    from io import StringIO
    si = StringIO()
    writer = csv.DictWriter(si, fieldnames=datos[0].keys())
    writer.writeheader()
    writer.writerows(datos)

    # Respuesta como archivo
    from flask import Response
    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={tipo}_reporte.csv"
        }
    )
