from datetime import datetime
import logging
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from decorators import json_response
from chatbot_core import chatbot
from flask_wtf.csrf import CSRFProtect
from flask import current_app   


logger = logging.getLogger(__name__)
chatbot_bp = Blueprint('chatbot', __name__, url_prefix='/chatbot')
csrf = CSRFProtect()
@chatbot_bp.route('/')
@login_required
def chat_page():
    """Render the chatbot interface"""
    return render_template('chatbot/chatbot.html')

@chatbot_bp.route('/message', methods=['POST'])
@login_required
@json_response
@csrf.exempt 
def send_message():
    """Process a message sent to the chatbot"""
    current_app.extensions['csrf'].exempt(send_message)
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return {'error': 'Message is required'}, 400
        
    # Initialize chat history if not exists
    if 'chat_history' not in session:
        session['chat_history'] = []
    
    # Process the message through the chatbot
    try:
        response = chatbot.send_message(message)
        
        # Update chat history
        session['chat_history'].append({
            'user': message,
            'bot': response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return {
            'response': response,
            'success': True
        }
    except Exception as e:
        logger.error(f"Error processing chatbot message: {e}")
        return {
            'error': 'An error occurred processing your message',
            'success': False
        }, 500
