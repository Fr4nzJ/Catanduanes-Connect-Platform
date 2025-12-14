// Chat functionality for Catanduanes Connect
let isChatOpen = false;

document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-messages');
    const messageInput = document.getElementById('chat-input');

    // Add typing indicator styles
    const style = document.createElement('style');
    style.textContent = `
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 4px 8px;
        }
        
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: rgba(100, 100, 100, 0.6);
            border-radius: 50%;
            animation: typing 1s infinite ease-in-out;
        }
        
        .typing-indicator span:nth-child(1) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(2) { animation-delay: 0.3s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        
        @keyframes typing {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
        }
    `;
    document.head.appendChild(style);

    // Setup event handlers
    setupChatHandlers();
});

function setupChatHandlers() {
    // Handle chat input submission
    document.addEventListener('keypress', function(e) {
        if (e.target.id === 'chat-input' && e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendChatMessage();
        }
    });
}

function toggleChat() {
    const chatModal = document.getElementById('chat-modal');
    if (chatModal.classList.contains('hidden')) {
        openChat();
    } else {
        closeChat();
    }
}

function sendChatMessage() {
    const messageInput = document.getElementById('chat-input');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Clear input
    messageInput.value = '';
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send message to server
    fetch('/api/chatbot/message', {
        method: 'POST',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        // Hide typing indicator
        hideTypingIndicator();
        
        if (data.status === 'error') {
            addMessageToChat('error', data.message || 'Sorry, something went wrong. Please try again.');
        } else {
            addMessageToChat('bot', data.message || data.response);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideTypingIndicator();
        addMessageToChat('error', 'Sorry, something went wrong. Please try again.');
    });
}

function addMessageToChat(type, message) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'mb-4 ' + (type === 'user' ? 'text-right' : 'text-left');
    
    const messageContent = document.createElement('div');
    messageContent.className = type === 'user' 
        ? 'inline-block bg-blue-600 text-white px-4 py-2 rounded-lg max-w-[80%]'
        : 'inline-block bg-gray-200 text-gray-800 px-4 py-2 rounded-lg max-w-[80%]';
    
    messageContent.textContent = message;
    messageDiv.appendChild(messageContent);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const chatMessages = document.getElementById('chat-messages');
    const indicator = document.createElement('div');
    indicator.id = 'typing-indicator';
    indicator.className = 'typing-indicator mb-4';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) {
        indicator.remove();
    }
}

function openChat() {
    const chatModal = document.getElementById('chat-modal');
    chatModal.classList.remove('hidden');
    isChatOpen = true;
    
    // Focus on input
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.focus();
    }
    
    // Mark messages as read
    if (currentUser) {
        markChatMessagesAsRead();
    }
}

function closeChat() {
    const chatModal = document.getElementById('chat-modal');
    chatModal.classList.add('hidden');
    isChatOpen = false;
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    }
}

function sendChatMessage() {
    const messageInput = document.getElementById('chat-input');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Clear input
    messageInput.value = '';
    
    // Add user message to chat
    addMessageToChat('user', message);
    
    // Show typing indicator
    showTypingIndicator();
    
    // Send message to server
    fetch('/chatbot/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        // Hide typing indicator
        hideTypingIndicator();
        
        if (data.error) {
            addMessageToChat('error', 'Sorry, something went wrong. Please try again.');
        } else {
            addMessageToChat('bot', data.response);
            
            // Save to chat history if user is logged in
            if (typeof currentUser !== 'undefined' && currentUser) {
                saveChatMessage(message, data.response);
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        hideTypingIndicator();
        addMessageToChat('error', 'Sorry, something went wrong. Please try again.');
    });
}

function addChatMessage(message, sender, isError = false) {
    const chatMessages = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    if (sender === 'user') {
        messageElement.className = 'flex justify-end mb-3';
        messageElement.innerHTML = `
            <div class="bg-blue-600 text-white px-4 py-2 rounded-lg max-w-xs">
                <p class="text-sm">${escapeHtml(message)}</p>
                <p class="text-xs text-blue-200 mt-1">${timestamp}</p>
            </div>
        `;
    } else {
        messageElement.className = 'flex justify-start mb-3';
        const bgColor = isError ? 'bg-red-100 border border-red-200' : 'bg-gray-100';
        const textColor = isError ? 'text-red-800' : 'text-gray-800';
        
        messageElement.innerHTML = `
            <div class="flex items-start">
                <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-2 flex-shrink-0">
                    <i class="fas fa-robot text-blue-600 text-sm"></i>
                </div>
                <div class="${bgColor} ${textColor} px-4 py-2 rounded-lg max-w-xs">
                    <p class="text-sm">${escapeHtml(message)}</p>
                    <p class="text-xs text-gray-500 mt-1">${timestamp}</p>
                </div>
            </div>
        `;
    }
    
    chatMessages.appendChild(messageElement);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Add to local messages array
    chatMessages.push({
        message: message,
        sender: sender,
        timestamp: new Date().toISOString()
    });
}

// Loading indicator is handled by showTypingIndicator() and hideTypingIndicator()


function loadChatHistory() {
    if (!currentUser) return;
    
    fetch('/chat/api/history')
        .then(response => response.json())
        .then(data => {
            if (data.conversations && data.conversations.length > 0) {
                // Add welcome message
                addChatMessage('Welcome back! Here to help you with any questions.', 'bot');
                
                // Optionally load recent history
                // loadRecentChatHistory();
            } else {
                // First time user
                addChatMessage('Hello! I\'m here to help you with jobs, businesses, and services in Catanduanes. What can I assist you with today?', 'bot');
            }
        })
        .catch(error => {
            console.error('Failed to load chat history:', error);
            addChatMessage('Hello! I\'m here to help you with jobs, businesses, and services in Catanduanes. What can I assist you with today?', 'bot');
        });
}

function saveChatMessage(userMessage, botResponse) {
    // This would typically save to a database
    // For now, we'll just log it
    console.log('Chat message saved:', {
        user: userMessage,
        bot: botResponse,
        session: chatSessionId,
        userId: currentUser ? currentUser.id : null
    });
}

function loadRecentChatHistory() {
    fetch('/chat/api/session/' + chatSessionId)
        .then(response => response.json())
        .then(data => {
            if (data.messages && data.messages.length > 0) {
                // Clear existing messages except welcome
                const chatMessages = document.getElementById('chat-messages');
                chatMessages.innerHTML = '';
                
                // Load recent messages (last 10)
                const recentMessages = data.messages.slice(-10);
                recentMessages.forEach(msg => {
                    addChatMessage(msg.message, msg.user_id ? 'user' : 'bot');
                });
            }
        })
        .catch(error => console.error('Failed to load session history:', error));
}

function markChatMessagesAsRead() {
    // Mark chat-related notifications as read
    const chatNotifications = notifications.filter(n => 
        n.type === 'chat_message' && !n.is_read
    );
    
    chatNotifications.forEach(notification => {
        markNotificationAsRead(notification.id);
    });
}

function clearChatSession() {
    if (!confirm('Are you sure you want to clear this chat session?')) {
        return;
    }
    
    fetch('/chat/api/clear-session/' + chatSessionId, {
        method: 'DELETE',
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').getAttribute('content')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            // Clear chat messages
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = '';
            chatMessages = [];
            
            // Add welcome message
            addChatMessage('Chat cleared. How can I help you today?', 'bot');
        }
    })
    .catch(error => {
        console.error('Failed to clear chat session:', error);
        alert('Failed to clear chat session. Please try again.');
    });
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Quick chat actions
function sendQuickMessage(message) {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.value = message;
        sendChatMessage();
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl/Cmd + Shift + C to toggle chat
    if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'C') {
        event.preventDefault();
        toggleChat();
    }
    
    // Escape to close chat
    if (event.key === 'Escape' && isChatOpen) {
        closeChat();
    }
});

// Export functions
window.Chat = {
    toggleChat,
    openChat,
    closeChat,
    sendChatMessage,
    handleChatKeyPress,
    sendQuickMessage,
    clearChatSession
};