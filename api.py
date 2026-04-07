# api.py
import sys
import os
import atexit
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from flask import Flask, request, jsonify, session
from src.conversational_agent import TheaterAgent
import logging
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Session için gizli anahtar
logging.basicConfig(level=logging.INFO)

# Aktif agent'ları tutacak sözlük (session_id -> TheaterAgent)
agents = {}

@app.route('/chat', methods=['POST'], strict_slashes=False)

def chat():
    # Session ID al (yoksa oluştur)
    session_id = request.json.get('session_id') if request.json else None
    if not session_id:
        session_id = str(uuid.uuid4())
    
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Mesaj alanı gerekli'}), 400
    
    user_message = data['message'].strip()
    if not user_message:
        return jsonify({'error': 'Mesaj boş olamaz'}), 400
    
    # Bu session_id için daha önce agent oluşturulmuş mu?
    if session_id not in agents:
        agents[session_id] = TheaterAgent()
        # Agent kapatmayı session sonunda yapmak için (isteğe bağlı)
    
    agent = agents[session_id]
    
    try:
        response_text = agent.chat(user_message)
        return jsonify({'reply': response_text, 'session_id': session_id})
    except Exception as e:
        logging.error(f"Agent hatası: {e}", exc_info=True)
        return jsonify({'error': f'Bir hata oluştu: {str(e)}'}), 500

# Uygulama kapanırken tüm agent'ları temizle
@atexit.register
def cleanup():
    for agent in agents.values():
        agent.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)