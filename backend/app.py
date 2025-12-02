# Este archivo fue creado con ayuda de la Inteligencia Artificial de OpenAI. 
# OpenAI. (2025). ChatGPT [Modelo de lenguaje de gran tamaño]. https://chat.openai.com/chat

from flask import Flask, render_template, redirect, url_for, session, flash
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

app.config['JSON_AS_ASCII'] = False

app.config["SECRET_KEY"] = "1b16d3f2c5897a0e5b9f4d6c8e3a2b10d7e4f9c0a6b5d4e3c2b1a0f9e8d7c6b5"
app.config["JWT_SECRET_KEY"] = "abc2c97e4dc1b1d3b48491098d7dfe6f"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)

# Habilitar lectura de token desde cookies (y headers opcional)
app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
# Para desarrollo local (HTTP) permitir cookies no seguras
app.config["JWT_COOKIE_SECURE"] = False
# Si no quieres manejar CSRF por ahora (solo para dev), desactívalo
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

jwt = JWTManager(app)

# Manejador de errores JWT: redirigir a login si falta token
@jwt.unauthorized_loader
def missing_token_callback(error):
    flash("Intentaste ingresar a una ruta protegida sin credenciales.", "error")
    return redirect(url_for('auth.login'))

# Manejador de errores JWT: redirigir a login si el token es inválido o expiró
@jwt.invalid_token_loader
def invalid_token_callback(error):
    flash("Token inválido o expirado. Por favor, inicia sesión nuevamente.", "error")
    return redirect(url_for('auth.login'))

# Manejador de errores JWT: redirigir a login si el token expiró
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    flash("Tu sesión ha expirado. Por favor, inicia sesión nuevamente.", "error")
    return redirect(url_for('auth.login'))

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
