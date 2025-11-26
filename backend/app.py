from flask import Flask, render_template, redirect, url_for, session
from flask_jwt_extended import JWTManager
from datetime import timedelta

from routes.auth import auth_bp
from routes.empleados import empleados_bp
from routes.nomina import nomina_bp
from routes.asistencias import asistencias_bp
from routes.evaluacion import evaluacion_bp
from routes.proyectos import proyectos_bp
from routes.cuentas import cuentas_bp
from routes.presupuestos import presupuestos_bp
from routes.reportes import reportes_bp
from routes.seguridad import seguridad_bp

from jinja2 import Environment, FileSystemLoader


app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

app.config["SECRET_KEY"] = "1b16d3f2c5897a0e5b9f4d6c8e3a2b10d7e4f9c0a6b5d4e3c2b1a0f9e8d7c6b5" 

# --- Configuración de JWT ---
app.config["JWT_SECRET_KEY"] = "abc2c97e4dc1b1d3b48491098d7dfe6f"  
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)

@app.template_filter('currency')
def format_currency(value):
    if value is None:
        return "0.00"
    try:
        return "${:,.2f}".format(float(value))
    except (TypeError, ValueError):
        return "0.00"

    
app.jinja_env.filters['currency'] = format_currency


# Registrar blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(empleados_bp)
app.register_blueprint(nomina_bp)
app.register_blueprint(asistencias_bp)
app.register_blueprint(evaluacion_bp)
app.register_blueprint(proyectos_bp)
app.register_blueprint(cuentas_bp)
app.register_blueprint(presupuestos_bp)
app.register_blueprint(reportes_bp)
app.register_blueprint(seguridad_bp)

# Context processor para inyectar el rol actual en todas las plantillas
@app.context_processor
def inject_role():
    return {"current_role": session.get("role")}

@app.route("/")
def home():
    # Si ya hay sesión iniciada, enviar a la vista de empleados
    if session.get("role"):
        return redirect(url_for("empleados.empleados"))
    return render_template("login.html")  # Página principal 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
