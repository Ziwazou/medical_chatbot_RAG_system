import os
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from chatbot_engine import get_chatbot

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['JSON_SORT_KEYS'] = False

try:
    chatbot = get_chatbot()
except Exception as e:
    logger.error(f"Failed to initialize chatbot: {e}")
    chatbot = None

conversations = {}


@app.route('/')
def index():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        conversations[session['session_id']] = []
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    if not chatbot:
        return jsonify({'error': 'Chatbot service is currently unavailable.'}), 503

    try:
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'Message cannot be empty.'}), 400

        if len(user_message) > 1000:
            return jsonify({'error': 'Message exceeds the 1000 character limit.'}), 400

        session_id = session.get('session_id') or str(uuid.uuid4())
        session['session_id'] = session_id

        if session_id not in conversations:
            conversations[session_id] = []

        conversations[session_id].append({
            'role': 'user',
            'message': user_message,
            'timestamp': datetime.now().isoformat()
        })

        bot_response = chatbot.get_response(user_message)

        conversations[session_id].append({
            'role': 'assistant',
            'message': bot_response,
            'timestamp': datetime.now().isoformat()
        })

        return jsonify({
            'response': bot_response,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error handling chat request: {e}", exc_info=True)
        return jsonify({'error': 'An internal error occurred.'}), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    session_id = session.get('session_id')
    history = conversations.get(session_id, []) if session_id else []
    return jsonify({'history': history})


@app.route('/api/clear', methods=['POST'])
def clear_history():
    session_id = session.get('session_id')
    if session_id and session_id in conversations:
        conversations[session_id] = []
    return jsonify({'status': 'success', 'message': 'History cleared.'})


@app.route('/api/sources', methods=['POST'])
def get_sources():
    if not chatbot:
        return jsonify({'error': 'Chatbot service is unavailable.'}), 503

    try:
        data = request.get_json() or {}
        query = data.get('query', '').strip()
        if not query:
            return jsonify({'error': 'Query parameter is required.'}), 400

        sources = chatbot.get_relevant_sources(query, k=3)
        return jsonify({'sources': sources})
    except Exception as e:
        logger.error(f"Error retrieving sources: {e}")
        return jsonify({'error': 'Failed to retrieve sources.'}), 500


@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy' if chatbot else 'unhealthy',
        'timestamp': datetime.now().isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found.'}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error.'}), 500
    return render_template('500.html'), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
