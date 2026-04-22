from waitress import serve
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import http.client
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
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        #objeto_mensaje = value['messages']
        objeto_mensaje = value.get('messages', None)

        if objeto_mensaje:
            messages = objeto_mensaje[0]

            if "type" in messages:
                tipo = messages["type"]

                if tipo == "interactive":
                    return 0
                
                if "text" in messages:
                    text = messages["text"]["body"]
                    numero = messages["from"]

                    enviar_mensajes_whatsapp(text, numero)

        if objeto_mensaje is None:
            print("No se recibio el JSON valido", flush=True)
            return jsonify({'error': 'JSON invalido'}), 400
        
        print("JSON recibido:", json.dumps(objeto_mensaje, ensure_ascii=False, indent=2), flush=True)
        

        return jsonify({'message':'EVENT_RECEIVED'}), 200
    except Exception as e:
        print(f"Error en webhook POST: {str(e)}", flush=True)
        return jsonify({'error': str(e)}), 500


def enviar_mensajes_whatsapp(texto, number):
    texto = texto.lower()

    if "hola" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, ¿Cómo estás? Bienvenido."
            }
        }
    elif "1" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."
            }
        }
    elif "2" in texto:
        data = {
            "messaging_product": "whatsapp",
            "to": number,
            "type": "location",
            "location": {
                "latitude": "-12.067158831865067",
                "longitude": "-77.03377940839486",
                "name": "Estadio Nacional del Perú",
                "address": "Cercado de Lima"
            }
        }
    elif "3" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "document",
            "document": {
                    "link": "https://www.turnerlibros.com/wp-content/uploads/2021/02/ejemplo.pdf",
                    "caption": "Temario del Curso #001"
                }
            }
    elif "4" in texto:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "audio",
            "audio": {
                "link": "https://filesamples.com/samples/audio/mp3/sample1.mp3"
            }
        }
    else:
        data={
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, visita mi web buenos-programadores para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información del Curso. ❔\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando curso. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con AnderCode. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
            }
        }

    #Convertir el diccionario a formato JSON
    data=json.dumps(data)

    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer EAAXM8qivU6sBRQzSI6uOmY8oWjs6w1Gixja0N6ifpy4cdvkhltAdR40ci6UT14Q48ohNToFTivO7e4kRPeZC2cZBCZC2FonY31ldVNJfOL6UPBZAR4PSp6BhdJwiaB5Hnta6SrqxRMJ1Hwikn8UL57arnbO6oNu2dwJIOZBRgHj2cVJ2CegPgVAco73YZA2h4TNY1wHDfZA6nGLWpdm0cUWrG0iV5uoxoZB1JAeL1nCp7d463LQ0fczEafUuL3MH2YHZAhZAwqBXDHrlrG5MWXN5dJ2wmU"
    }

    connection = http.client.HTTPSConnection("graph.facebook.com")

    try:
        connection.request("POST","/v25.0/1036918562843642/messages", data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)
    except Exception as e:
        agregar_mensajes_log(json.dumps(e))
    finally:
        connection.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)
    #serve(app, host='0.0.0.0', port=80)