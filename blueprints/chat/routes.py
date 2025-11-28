import uuid
import logging
from datetime import datetime
from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user

from . import chat_bp
from database import get_neo4j_db, safe_run, _node_to_dict
from decorators import json_response, rate_limit_by_user
from blueprints.chatbot import chatbot_bp

logger = logging.getLogger(__name__)

@chat_bp.route('/user')
@login_required
def user_chat_view():
    """User-to-user chat interface"""
    return render_template('chat/user_chat.html')

# Chatbot is registered at app level

@chat_bp.route('/')
def chatbot_view():
    """Chatbot interface"""
    return render_template('chat/chatbot.html')

# Note: Chatbot message handling is now handled by the chatbot blueprint
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
        
    if not chatbot:
        return jsonify({
            'error': 'The chatbot service is currently unavailable. Please try again later.'
        }), 503
    
    try:
        # Get response from chatbot
        response = chatbot.get_response(message)
        
        return jsonify({
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
        # Save conversation to database
        db = get_neo4j_db()
        with db.session() as session:
            conversation_id = str(uuid.uuid4())
            
            # Create conversation record
            user_id = current_user.id if not current_user.is_anonymous else None
            safe_run(session, """
                CREATE (c:ChatConversation {
                    id: $conversation_id,
                    session_id: $session_id,
                    user_id: $user_id,
                    message: $message,
                    response: $response,
                    timestamp: $timestamp
                })
            """, {
                'conversation_id': conversation_id,
                'session_id': session_id,
                'user_id': current_user.id if current_user.is_authenticated else None,
                'message': message,
                'response': response,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        return jsonify({
            'error': 'Sorry, I encountered an error processing your message. Please try again.'
        }), 500

@chat_bp.route('/api/history')
@login_required
def get_chat_history():
    """Get user's chat history"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    skip = (page - 1) * per_page
    
    db = get_neo4j_db()
    with db.session() as session:
        conversations = safe_run(session, """
            MATCH (c:ChatConversation)
            WHERE c.user_id = $user_id
            RETURN c
            ORDER BY c.timestamp DESC
            SKIP $skip LIMIT $limit
        """, {
            'user_id': current_user.id,
            'skip': skip,
            'limit': per_page
        })
        
        conversation_list = [_node_to_dict(record['c']) for record in conversations]
    
    return jsonify({
        'conversations': conversation_list,
        'page': page,
        'per_page': per_page
    })

@chat_bp.route('/api/sessions')
@login_required
def get_chat_sessions():
    """Get user's chat sessions"""
    db = get_neo4j_db()
    with db.session() as session:
        sessions = safe_run(session, """
            MATCH (c:ChatConversation)
            WHERE c.user_id = $user_id
            RETURN DISTINCT c.session_id as session_id,
                   max(c.timestamp) as last_message
            ORDER BY last_message DESC
        """, {'user_id': current_user.id})
        
        session_list = []
        for record in sessions:
            session_list.append({
                'session_id': record['session_id'],
                'last_message': record['last_message']
            })
    
    return jsonify({'sessions': session_list})

@chat_bp.route('/api/session/<session_id>')
@login_required
def get_session_messages(session_id):
    """Get messages from a specific session"""
    db = get_neo4j_db()
    with db.session() as session:
        messages = safe_run(session, """
            MATCH (c:ChatConversation)
            WHERE c.session_id = $session_id 
            AND c.user_id = $user_id
            RETURN c
            ORDER BY c.timestamp ASC
        """, {
            'session_id': session_id,
            'user_id': current_user.id
        })
        
        message_list = [_node_to_dict(record['c']) for record in messages]
    
    return jsonify({'messages': message_list})

@chat_bp.route('/api/clear-session/<session_id>', methods=['DELETE'])
@login_required
def clear_session(session_id):
    """Clear a chat session"""
    db = get_neo4j_db()
    with db.session() as session:
        safe_run(session, """
            MATCH (c:ChatConversation)
            WHERE c.session_id = $session_id 
            AND c.user_id = $user_id
            DELETE c
        """, {
            'session_id': session_id,
            'user_id': current_user.id
        })
    
    return jsonify({'message': 'Session cleared successfully'})

@chat_bp.route('/api/analytics')
@login_required
def get_analytics():
    """Get chat analytics (admin only)"""
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_neo4j_db()
    with db.session() as session:
        # Total conversations
        total_conversations = safe_run(session, """
            MATCH (c:ChatConversation)
            RETURN count(c) as total
        """)[0]['total']
        
        # Conversations by day (last 30 days)
        daily_stats = safe_run(session, """
            MATCH (c:ChatConversation)
            WHERE c.timestamp >= datetime() - duration('P30D')
            RETURN date(c.timestamp) as date, count(c) as count
            ORDER BY date DESC
            LIMIT 30
        """)
        
        # Most common queries
        common_queries = safe_run(session, """
            MATCH (c:ChatConversation)
            RETURN c.message as query, count(*) as frequency
            ORDER BY frequency DESC
            LIMIT 20
        """)
        
        analytics = {
            'total_conversations': total_conversations,
            'daily_stats': [{**record} for record in daily_stats],
            'common_queries': [{**record} for record in common_queries]
        }
    
    return jsonify(analytics)