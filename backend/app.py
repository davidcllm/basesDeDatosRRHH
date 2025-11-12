from flask import Flask, render_template
from routes.empleados import empleados_bp
from routes.nomina import nomina_bp
from routes.asistencias import asistencias_bp
from routes.evaluacion import evaluacion_bp
from routes.proyectos import proyectos_bp
from routes.cuentas import cuentas_bp
from routes.presupuestos import presupuestos_bp
from routes.reportes import reportes_bp
from routes.seguridad import seguridad_bp

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

# Registrar blueprints
app.register_blueprint(empleados_bp)
app.register_blueprint(nomina_bp)
app.register_blueprint(asistencias_bp)
app.register_blueprint(evaluacion_bp)
app.register_blueprint(proyectos_bp)
app.register_blueprint(cuentas_bp)
app.register_blueprint(presupuestos_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(seguridad_bp)

@app.route("/")
def home():
    return render_template("empleados.html")  # Página principal 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
