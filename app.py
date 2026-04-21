from waitress import serve
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json
import os

app = Flask(__name__)

#Configuracion de la BD SQLITE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Modelo de la tabla Log
class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_y_hora = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    texto = db.Column(db.Text, nullable=False)

#Crear la tabla si no existe
with app.app_context():
    db.create_all()

#Funcion para ordenar los registros por fecha y hora
def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora, reverse=True)

@app.route('/')
def index():
    #Obtener todos los registros de ls BD
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html', registros=registros_ordenados)

mensajes_log = []

#Funcion para agregar mensajes y guardar en la BD
def agregar_mensajes_log(data):
    try:
        #Convertir el JSON/dict a String
        texto_json = json.dumps(data, ensure_ascii=False, indent=2)
        mensajes_log.append(texto_json)

        #Guardar el mensaje en la BD
        nuevo_registro = Log(texto=texto_json)
        db.session.add(nuevo_registro)
        db.session.commit()

        print("Registro guardado correctamente en la BD", flush=True)
    
    except Exception as e:
        db.session.rollback()
        print(f"Error guardando en BD: {str(e)}", flush=True)
        raise

#Token de verificacion para la configuracion
TOKEN_BRYAN = "BRYANASCANOA"

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    if request.method == 'GET':
        return verificar_token(request)
        
    elif request.method == 'POST':
        return recibir_mensajes(request)


def verificar_token(req):
    mode = req.args.get('hub.mode')
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if mode == 'subscribe' and token == TOKEN_BRYAN:
        print('WEBHOOK VERIFICADO', flush=True)
        return challenge, 200
    else:
        return jsonify({'error':'Token Invalido'}),401


def recibir_mensajes(req):
    try:
        data = req.get_json(silent=True)

        if data is None:
            print("No se recibio el JSON valido", flush=True)
            return jsonify({'error': 'JSON invalido'}), 400
        
        print("JSON recibido:", json.dumps(data, ensure_ascii=False, indent=2), flush=True)
        agregar_mensajes_log(data)

        return jsonify({'message':'EVENT_RECEIVED'}), 200
    except Exception as e:
        print(f"Error en webhook POST: {str(e)}", flush=True)
        jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=80, debug=True)
    #serve(app, host='0.0.0.0', port=80)