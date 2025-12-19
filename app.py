

from flask import Flask, render_template, request, jsonify, session
import os
from datetime import datetime
import uuid
from chatbot_engine import get_chatbot
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size
app.config['JSON_SORT_KEYS'] = False

# Initialize chatbot (singleton pattern)
try:
    chatbot = get_chatbot()
    logger.info("Chatbot initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize chatbot: {str(e)}")
    chatbot = None

# Store conversation history in memory (use Redis or DB in production)
conversations = {}


@app.route('/')
def index():
    """Render the main chatbot interface"""
    # Create a new session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        conversations[session['session_id']] = []
        logger.info(f"New session created: {session['session_id']}")
    
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages from the user"""
    if not chatbot:
        return jsonify({
            'error': 'Chatbot service is currently unavailable. Please try again later.'
        }), 503
    
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'error': 'Message cannot be empty'
            }), 400
        
        # Limit message length
        if len(user_message) > 1000:
            return jsonify({
                'error': 'Message is too long. Please keep it under 1000 characters.'
            }), 400
        
        # Get or create session
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        
        if session_id not in conversations:
            conversations[session_id] = []
        
        logger.info(f"Processing message from session {session_id}: {user_message[:50]}...")
        
        # Add user message to history
        conversations[session_id].append({
            'role': 'user',
            'message': user_message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get response from chatbot
        bot_response = chatbot.get_response(user_message)
        
        # Add bot response to history
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
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'An error occurred while processing your request. Please try again.'
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get conversation history for the current session"""
    session_id = session.get('session_id')
    
    if not session_id or session_id not in conversations:
        return jsonify({'history': []})
    
    return jsonify({
        'history': conversations[session_id]
    })


@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear conversation history for the current session"""
    session_id = session.get('session_id')
    
    if session_id and session_id in conversations:
        conversations[session_id] = []
        logger.info(f"Cleared history for session {session_id}")
    
    return jsonify({
        'status': 'success',
        'message': 'Conversation history cleared'
    })


@app.route('/api/sources', methods=['POST'])
def get_sources():
    """Get relevant sources for a query"""
    if not chatbot:
        return jsonify({
            'error': 'Chatbot service is currently unavailable'
        }), 503
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'error': 'Query cannot be empty'
            }), 400
        
        sources = chatbot.get_relevant_sources(query, k=3)
        return jsonify({
            'sources': sources
        })
        
    except Exception as e:
        logger.error(f"Error retrieving sources: {str(e)}")
        return jsonify({
            'error': 'Failed to retrieve sources'
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy' if chatbot else 'unhealthy',
        'timestamp': datetime.now().isoformat(),
        'chatbot_status': 'initialized' if chatbot else 'not_initialized'
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Resource not found'
        }), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Internal server error'
        }), 500
    return render_template('500.html'), 500


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Method not allowed'
        }), 405
    return jsonify({
        'error': 'Method not allowed'
    }), 405


