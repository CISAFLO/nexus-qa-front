from flask import Flask, render_template, request, jsonify
from openai import OpenAI
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración del Cliente de OpenAI (Sintaxis moderna v1.0+)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_thread', methods=['GET'])
def create_thread():
    try:
        thread = client.beta.threads.create()
        return jsonify({"thread_id": thread.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_openai():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('input')
    user_files = data.get('file_ids') # Lista de IDs de archivos previamente subidos
    
    if not user_input and not user_files:
        return jsonify("No input provided"), 400
    if not thread_id or thread_id == 'None':
        return jsonify("No thread provided"), 400
        
    try:
        # CORRECCIÓN DEL ERROR 'file_ids':
        # En la API moderna, los archivos se pasan como 'attachments'
        attachments = []
        if user_files:
            for f_id in user_files:
                attachments.append({
                    "file_id": f_id,
                    "tools": [{"type": "file_search"}]
                })

        # Crear el mensaje en el hilo
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_input,
            attachments=attachments if attachments else None
        )
        
        # Crear el Run para procesar la respuesta
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        # Esperar la respuesta (Polling)
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1) # Un segundo es más saludable para la tasa de transferencia (rate limits)
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            
            if run.status == 'failed':
                return jsonify(f"Error en el asistente: {run.last_error}"), 500
            
            if run.status == 'requires_action':
                # Aquí iría tu lógica de funciones si Nexus QA necesita ejecutar código
                pass 
            
        # Recuperar los mensajes y devolver el último
        msgs = client.beta.threads.messages.list(thread_id=thread_id)
        # Accedemos al contenido de la respuesta del asistente
        response_text = msgs.data[0].content[0].text.value
        return jsonify(response_text)

    except Exception as e:
        print(f"Error detectado: {e}") # Para que lo veas en la terminal de VS Code
        return jsonify(str(e)), 500

# BLOQUE PARA DESPLIEGUE (Render/Railway)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)