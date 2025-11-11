from flask import Flask
from flask_cors import CORS
#from routes.empleados import empleados_bp
#from routes.finanzas import finanzas_bp

app = Flask(__name__)
CORS(app)

# Registrar Blueprints
#app.register_blueprint(empleados_bp)
#app.register_blueprint(finanzas_bp)

@app.route('/')
def index():
    return {"mensaje": "API de Empresa funcionando correctamente"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
