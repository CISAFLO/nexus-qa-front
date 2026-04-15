from flask import Flask, render_template, request, jsonify
import openai, time, paramiko, json
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configuración de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_thread', methods=['GET'])
def create_thread():
    try:
        thread = openai.beta.threads.create()
        return jsonify({"thread_id": thread.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_openai():
    data = request.json
    thread_id = data.get('thread_id')
    user_input = data.get('input')
    user_files = data.get('file_ids')
    
    if not user_input and not user_files:
        return jsonify("No input provided"), 400
    if thread_id == 'None':
        return jsonify("No thread provided"), 400
        
    try:
        openai.beta.threads.messages.create(
            thread_id,
            role="user",
            content=user_input,
            file_ids=user_files if user_files else []
        )
        
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=os.environ.get('OPENAI_ASSISTANT_ID')
        )
        
        while run.status != 'completed':
            run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run.status == 'requires_action':
                # ... (aquí va tu lógica de tool_calls que ya tienes)
                pass 
            time.sleep(.5)
            
        msgs = openai.beta.threads.messages.list(thread_id)
        return jsonify(msgs.data[0].content[0].text.value)
    except Exception as e:
        return jsonify(str(e)), 500

# --- Rutas adicionales (get_thread_messages, upload_file, etc.) mantén las que necesites ---

# BLOQUE CRÍTICO PARA RENDER
if __name__ == '__main__':
    # Render usa la variable de entorno PORT
    port = int(os.environ.get("PORT", 10000))
    # '0.0.0.0' es obligatorio para que el tráfico externo llegue a la app
    app.run(host='0.0.0.0', port=port, debug=False)