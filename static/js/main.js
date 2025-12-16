// Main JavaScript file for Catanduanes Connect

// Global variables
let currentUser = null;
let notifications = [];

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Load current user if authenticated
    loadCurrentUser();
    
    // Load notifications
    loadNotifications();
    
    // Auto-refresh notifications every 30 seconds
    setInterval(loadNotifications, 30000);
    
    // Initialize tooltips and popovers
    initializeTooltips();
    
    // Initialize smooth scrolling
    initializeSmoothScrolling();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize file uploads
    initializeFileUploads();
}

// User management
function loadCurrentUser() {
    fetch('/api/current-user')
        .then(response => response.json())
        .then(data => {
            if (data.user) {
                currentUser = data.user;
                updateUserInterface();
            }
        })
        .catch(error => console.error('Failed to load current user:', error));
}

function updateUserInterface() {
    // Update user-specific UI elements
    const userElements = document.querySelectorAll('[data-user-id]');
    userElements.forEach(element => {
        if (currentUser && element.dataset.userId === currentUser.id) {
            element.classList.add('current-user');
        }
    });
}

// Notifications
function loadNotifications() {
    if (!currentUser) return;
    
    fetch('/api/notifications')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                notifications = data.notifications || [];
                updateNotificationUI();
            }
        })
        .catch(error => console.error('Failed to load notifications:', error));
}

function updateNotificationUI() {
    const notificationCount = document.getElementById('notification-count');
    const notificationsList = document.getElementById('notifications-list');
    
    if (notificationCount) {
        const unreadCount = notifications.filter(n => !n.is_read).length;
        if (unreadCount > 0) {
            notificationCount.textContent = unreadCount;
            notificationCount.classList.remove('hidden');
        } else {
            notificationCount.classList.add('hidden');
        }
    }
    
    if (notificationsList) {
        if (notifications.length === 0) {
            notificationsList.innerHTML = `
                <div class="p-8 text-center text-gray-500">
                    <i class="fas fa-inbox text-4xl mb-3 block opacity-30"></i>
                    <p class="font-medium">No notifications</p>
                    <p class="text-sm">You're all caught up!</p>
                </div>
            `;
        } else {
            notificationsList.innerHTML = notifications.map(notification => `
                <div class="notification-item p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${!notification.is_read ? 'bg-blue-50' : ''}" 
                     onclick="markNotificationAsRead('${notification.id}')">
                    <div class="flex items-start gap-3">
                        <div class="flex-1">
                            <div class="flex items-center gap-2">
                                <p class="text-sm font-semibold text-gray-900">${escapeHtml(notification.title)}</p>
                                ${!notification.is_read ? '<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">New</span>' : ''}
                            </div>
                            <p class="text-sm text-gray-600 mt-1">${escapeHtml(notification.message)}</p>
                            <p class="text-xs text-gray-400 mt-2">
                                <i class="fas fa-clock mr-1"></i>${formatTimeAgo(notification.created_at)}
                            </p>
                        </div>
                        <div class="flex-shrink-0">
                            ${!notification.is_read ? '<div class="w-2.5 h-2.5 bg-blue-600 rounded-full mt-2"></div>' : ''}
                        </div>
                    </div>
                </div>
            `).join('');
        }
    }
}

function markNotificationAsRead(notificationId) {
    fetch(`/api/notifications/${notificationId}/read`, {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const notification = notifications.find(n => n.id === notificationId);
                if (notification) {
                    notification.is_read = true;
                    updateNotificationUI();
                }
            }
        })
        .catch(error => console.error('Failed to mark notification as read:', error));
}

function markAllNotificationsAsRead() {
    fetch('/api/notifications/mark-all-read', {
        method: 'POST'
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                notifications.forEach(n => n.is_read = true);
                updateNotificationUI();
            }
        })
        .catch(error => console.error('Failed to mark all notifications as read:', error));
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

// Utility functions
function formatTimeAgo(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return `${Math.floor(diffInSeconds / 2592000)}mo ago`;
}

function formatCurrency(amount, currency = 'PHP') {
    return new Intl.NumberFormat('en-PH', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

// Tooltips and popovers
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', showTooltip);
        element.addEventListener('mouseleave', hideTooltip);
    });
}

function showTooltip(event) {
    const element = event.target;
    const tooltipText = element.dataset.tooltip;
    
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip absolute bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg z-50';
    tooltip.textContent = tooltipText;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
    
    element.tooltip = tooltip;
}

function hideTooltip(event) {
    const element = event.target;
    if (element.tooltip) {
        element.tooltip.remove();
        delete element.tooltip;
    }
}

// Smooth scrolling
function initializeSmoothScrolling() {
    const smoothScrollLinks = document.querySelectorAll('a[href^="#"]');
    smoothScrollLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', validateForm);
    });
}

function validateForm(event) {
    const form = event.target;
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    if (!isValid) {
        event.preventDefault();
    }
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error text-red-600 text-sm mt-1';
    errorElement.textContent = message;
    
    field.parentNode.appendChild(errorElement);
    field.classList.add('border-red-500');
}

function clearFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    field.classList.remove('border-red-500');
}

// File uploads
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', handleFileSelect);
    });
}

function handleFileSelect(event) {
    const input = event.target;
    const files = input.files;
    
    if (files.length > 0) {
        const fileInfo = document.createElement('div');
        fileInfo.className = 'file-info text-sm text-gray-600 mt-1';
        fileInfo.innerHTML = `
            <i class="fas fa-file mr-1"></i>
            ${files[0].name} (${formatFileSize(files[0].size)})
        `;
        
        // Remove existing file info
        const existingInfo = input.parentNode.querySelector('.file-info');
        if (existingInfo) {
            existingInfo.remove();
        }
        
        input.parentNode.appendChild(fileInfo);
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Modal management
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }
}

// Confirmation dialogs
function showConfirmDialog(message, onConfirm, onCancel = null) {
    const dialog = document.createElement('div');
    dialog.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    dialog.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md mx-4">
            <h3 class="text-lg font-semibold mb-4">Confirm Action</h3>
            <p class="text-gray-600 mb-6">${message}</p>
            <div class="flex space-x-3">
                <button id="confirm-yes" class="flex-1 bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700">
                    Yes, Continue
                </button>
                <button id="confirm-no" class="flex-1 bg-gray-200 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-300">
                    Cancel
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(dialog);
    
    document.getElementById('confirm-yes').addEventListener('click', () => {
        document.body.removeChild(dialog);
        onConfirm();
    });
    
    document.getElementById('confirm-no').addEventListener('click', () => {
        document.body.removeChild(dialog);
        if (onCancel) onCancel();
    });
}

// Loading states
function showLoading(element) {
    element.disabled = true;
    element.classList.add('opacity-50');
    
    const originalText = element.innerHTML;
    element.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Loading...';
    element.dataset.originalText = originalText;
}

function hideLoading(element) {
    element.disabled = false;
    element.classList.remove('opacity-50');
    
    if (element.dataset.originalText) {
        element.innerHTML = element.dataset.originalText;
        delete element.dataset.originalText;
    }
}

// Search functionality
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in other scripts
window.CatanduanesConnect = {
    formatTimeAgo,
    formatCurrency,
    truncateText,
    openModal,
    closeModal,
    showConfirmDialog,
    showLoading,
    hideLoading,
    debounce
};