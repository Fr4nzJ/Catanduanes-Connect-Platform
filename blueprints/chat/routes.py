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
    recipient_id = request.args.get('recipient_id')
    recipient = None
    
    if recipient_id:
        db = get_neo4j_db()
        with db.session() as session:
            recipient_data = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN u
            """, {'user_id': recipient_id})
            
            if recipient_data:
                recipient = _node_to_dict(recipient_data[0]['u'])
            else:
                # Log error for debugging
                logger.warning(f"Recipient not found: {recipient_id}")
    
    return render_template('chat/user_chat.html', recipient=recipient, recipient_id=recipient_id)

# Chatbot is registered at app level

@chat_bp.route('/')
def chatbot_view():
    """Chatbot interface"""
    return render_template('chat/chatbot.html')

# Note: Chatbot message handling is now handled by the chatbot blueprint

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

# ===== User-to-User Chat Routes =====

@chat_bp.route('/api/send-message', methods=['POST'])
@login_required
def send_user_message():
    """Send a message to another user"""
    try:
        data = request.get_json()
        recipient_id = data.get('recipient_id')
        message_text = data.get('message', '').strip()
        
        logger.debug(f"Send message - Recipient: {recipient_id}, Message length: {len(message_text)}")
        
        if not recipient_id or not message_text:
            return jsonify({'error': 'Recipient ID and message are required', 'success': False}), 400
        
        db = get_neo4j_db()
        with db.session() as session:
            # Verify recipient exists
            recipient = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN u
            """, {'user_id': recipient_id})
            
            if not recipient:
                logger.warning(f"Recipient not found: {recipient_id}")
                return jsonify({'error': 'Recipient not found', 'success': False}), 404
            
            # Create message
            message_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()
            
            safe_run(session, """
                MATCH (sender:User {id: $sender_id}), (recipient:User {id: $recipient_id})
                CREATE (m:UserMessage {
                    id: $message_id,
                    sender_id: $sender_id,
                    recipient_id: $recipient_id,
                    text: $text,
                    timestamp: $timestamp,
                    read: false
                })
                CREATE (sender)-[:SENT]->(m)
                CREATE (m)-[:SENT_TO]->(recipient)
            """, {
                'sender_id': current_user.id,
                'recipient_id': recipient_id,
                'message_id': message_id,
                'text': message_text,
                'timestamp': timestamp
            })
        
        logger.debug(f"Message sent successfully: {message_id}")
        return jsonify({
            'success': True,
            'message_id': message_id,
            'timestamp': timestamp
        })
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@chat_bp.route('/api/conversation/<recipient_id>')
@login_required
def get_conversation(recipient_id):
    """Get conversation history with a user"""
    db = get_neo4j_db()
    with db.session() as session:
        # Get all messages between current user and recipient
        messages = safe_run(session, """
            MATCH (m:UserMessage)
            WHERE (m.sender_id = $user_id AND m.recipient_id = $recipient_id)
               OR (m.sender_id = $recipient_id AND m.recipient_id = $user_id)
            RETURN m
            ORDER BY m.timestamp ASC
        """, {
            'user_id': current_user.id,
            'recipient_id': recipient_id
        })
        
        message_list = [_node_to_dict(record['m']) for record in messages]
        
        # Mark messages as read if they were sent to current user
        safe_run(session, """
            MATCH (m:UserMessage)
            WHERE m.recipient_id = $user_id AND m.sender_id = $recipient_id
            SET m.read = true
        """, {
            'user_id': current_user.id,
            'recipient_id': recipient_id
        })
    
    return jsonify({'messages': message_list})

@chat_bp.route('/api/conversations-list')
@login_required
def get_conversations_list():
    """Get list of all conversations for current user"""
    db = get_neo4j_db()
    with db.session() as session:
        # Get unique users that current user has messaged with
        conversations = safe_run(session, """
            MATCH (m:UserMessage)
            WHERE m.sender_id = $user_id OR m.recipient_id = $user_id
            WITH CASE 
                WHEN m.sender_id = $user_id THEN m.recipient_id 
                ELSE m.sender_id 
            END as other_user_id, max(m.timestamp) as last_timestamp
            MATCH (u:User {id: other_user_id})
            RETURN u, last_timestamp
            ORDER BY last_timestamp DESC
        """, {'user_id': current_user.id})
        
        conversation_list = []
        for record in conversations:
            user_data = _node_to_dict(record['u'])
            
            # Count unread messages
            unread = safe_run(session, """
                MATCH (m:UserMessage)
                WHERE m.sender_id = $other_user_id AND m.recipient_id = $user_id AND m.read = false
                RETURN count(m) as unread_count
            """, {
                'other_user_id': user_data['id'],
                'user_id': current_user.id
            })
            
            conversation_list.append({
                'user': user_data,
                'last_message': record['last_timestamp'],
                'unread_count': unread[0]['unread_count'] if unread else 0
            })
        
        return jsonify({'conversations': conversation_list})

@chat_bp.route('/api/mark-as-read/<recipient_id>', methods=['POST'])
@login_required
def mark_as_read(recipient_id):
    """Mark all messages from a user as read"""
    db = get_neo4j_db()
    with db.session() as session:
        safe_run(session, """
            MATCH (m:UserMessage)
            WHERE m.sender_id = $sender_id AND m.recipient_id = $recipient_id
            SET m.read = true
        """, {
            'sender_id': recipient_id,
            'recipient_id': current_user.id
        })
    
    return jsonify({'success': True})

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

# ===== Contextual Chat Routes (with topic/context) =====

@chat_bp.route('/contextual')
@login_required
def contextual_chat_view():
    """Chat interface with a specific context/topic"""
    recipient_id = request.args.get('recipient_id')
    context_type = request.args.get('context_type')  # e.g., 'application', 'job_inquiry'
    context_id = request.args.get('context_id')  # e.g., application ID, job ID
    context_title = request.args.get('context_title', '')  # e.g., job title or application date
    
    recipient = None
    
    if recipient_id:
        db = get_neo4j_db()
        with db.session() as session:
            recipient_data = safe_run(session, """
                MATCH (u:User {id: $user_id})
                RETURN u
            """, {'user_id': recipient_id})
            
            if recipient_data:
                recipient = _node_to_dict(recipient_data[0]['u'])
            else:
                logger.warning(f"Recipient not found: {recipient_id}")
    
    return render_template('chat/contextual_chat.html', 
                         recipient=recipient, 
                         recipient_id=recipient_id,
                         context_type=context_type,
                         context_id=context_id,
                         context_title=context_title)