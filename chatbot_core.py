from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required
from datetime import datetime
import logging
import os
from gemini_client import GeminiChat

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Gemini chat client
try:
    logger.info("Initializing Gemini chat client...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY environment variable not set")
        raise ValueError("GEMINI_API_KEY environment variable not set")

    chatbot = GeminiChat(api_key=api_key)
    logger.info("Successfully initialized Gemini chat client")
except Exception as e:
    logger.error(f"Failed to initialize Gemini chat client: {str(e)}", exc_info=True)
    chatbot = None

# Error constants
ERROR_PROCESSING = 'error_processing'
ERROR_EMPTY_INPUT = 'error_empty_input'
ERROR_UNAUTHORIZED = 'error_unauthorized'

bp = Blueprint('chatbot', __name__)

@bp.route('/chat')
def chat():
    """Render the chat interface."""
    return render_template('chatbot/chat.html')

@bp.route('/message', methods=['POST'])
@login_required
def chat_api():
    """
    Handle chat API requests.
    Expects JSON: {"message": "user message"}
    """
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({
                'status': 'error',
                'error': ERROR_EMPTY_INPUT,
                'message': 'No message provided'
            }), 400

        user_message = data['message'].strip()
        if not user_message:
            return jsonify({
                'status': 'error',
                'error': ERROR_EMPTY_INPUT,
                'message': 'Message cannot be empty'
            }), 400

        # Check if chatbot is available
        if chatbot is None:
            return jsonify({
                'status': 'error',
                'error': ERROR_PROCESSING,
                'message': 'Chatbot service is not available'
            }), 503

        # Retrieve chat history from session
        chat_history = session.get('chat_history', [])

        # Try to get context (if method exists)
        context = None
        if hasattr(chatbot, '_get_relevant_data'):
            try:
                context = chatbot._get_relevant_data(user_message)
            except Exception as e:
                logger.warning(f"Context retrieval failed: {e}")

        formatted_context = context if context else "No specific context available."

        # Send message to chatbot
        try:
            response = chatbot.send_message(
                message=user_message,
                context=formatted_context,
                history=chat_history
            )

            formatted_response = response.strip().replace("**", "").replace("*", "• ")

            # Update chat history
            chat_history.append({"role": "user", "content": user_message})
            chat_history.append({"role": "assistant", "content": formatted_response})

            # Keep only last 10 messages
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]

            session['chat_history'] = chat_history
            session.modified = True

            return jsonify({
                'status': 'success',
                'message': formatted_response,
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"Error generating chatbot response: {str(e)}", exc_info=True)
            return jsonify({
                'status': 'error',
                'error': ERROR_PROCESSING,
                'message': 'Error while generating response'
            }), 500

    except Exception as e:
        logger.error(f"Error in chat API: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': ERROR_PROCESSING,
            'message': 'An error occurred while processing your message'
        }), 500


@bp.route('/history')
@login_required
def get_chat_history():
    """Get the current user's chat history."""
    try:
        chat_history = session.get('chat_history', [])
        return jsonify({
            'status': 'success',
            'history': chat_history
        })
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': ERROR_PROCESSING,
            'message': 'Could not retrieve chat history'
        }), 500


@bp.route('/clear-session', methods=['DELETE'])
@login_required
def clear_chat_history():
    """Clear the current user's chat history."""
    try:
        session['chat_history'] = []
        session.modified = True
        return jsonify({
            'status': 'success',
            'message': 'Chat history cleared'
        })
    except Exception as e:
        logger.error(f"Error clearing chat history: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': ERROR_PROCESSING,
            'message': 'Could not clear chat history'
        }), 500
