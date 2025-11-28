// Enhanced Admin Interface JavaScript
// Author: AI Assistant | Version: 2.0 | Date: 2024

class EnhancedAdminInterface {
    constructor() {
        this.currentTab = 'general';
        this.settings = {};
        this.originalSettings = {};
        this.searchIndex = [];
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSettings();
        this.buildSearchIndex();
        this.initializeAnimations();
        this.setupKeyboardNavigation();
        this.initializeTheme();
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.admin-nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Form interactions
        document.querySelectorAll('.admin-form-input, .admin-form-toggle input, .admin-form-checkbox input').forEach(input => {
            input.addEventListener('change', (e) => this.handleSettingChange(e));
            input.addEventListener('focus', (e) => this.handleInputFocus(e));
            input.addEventListener('blur', (e) => this.handleInputBlur(e));
        });

        // Range slider
        document.getElementById('flag-threshold')?.addEventListener('input', (e) => {
            this.updateRangeLabel(e.target);
        });

        // Save settings on Ctrl+S
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveSettings();
            }
        });

        // Save and Reset buttons
        const saveBtn = document.querySelector('[onclick="saveSettings()"]');
        const resetBtn = document.querySelector('[onclick="resetSettings()"]');
        
        if (saveBtn) {
            saveBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.saveSettings();
            });
        }
        
        if (resetBtn) {
            resetBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.resetSettings();
            });
        }
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Tab navigation with arrow keys
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                const activeTab = document.querySelector('.admin-nav-tab.active');
                if (document.activeElement === activeTab || activeTab.contains(document.activeElement)) {
                    e.preventDefault();
                    const tabs = Array.from(document.querySelectorAll('.admin-nav-tab'));
                    const currentIndex = tabs.indexOf(activeTab);
                    let newIndex;
                    
                    if (e.key === 'ArrowLeft') {
                        newIndex = currentIndex > 0 ? currentIndex - 1 : tabs.length - 1;
                    } else {
                        newIndex = currentIndex < tabs.length - 1 ? currentIndex + 1 : 0;
                    }
                    
                    tabs[newIndex].focus();
                    tabs[newIndex].click();
                }
            }
        });
    }

    initializeAnimations() {
        // Animate cards on scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        document.querySelectorAll('.admin-settings-card').forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
            observer.observe(card);
        });

        // Animate overview cards
        document.querySelectorAll('.admin-overview-card').forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });
    }

    switchTab(tabName) {
        if (this.currentTab === tabName) return;

        // Update tab buttons
        document.querySelectorAll('.admin-nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');

        // Update sections
        document.querySelectorAll('.admin-settings-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`settings-${tabName}`)?.classList.add('active');

        // Animate section change
        const activeSection = document.getElementById(`settings-${tabName}`);
        if (activeSection) {
            activeSection.style.opacity = '0';
            activeSection.style.transform = 'translateX(20px)';
            
            setTimeout(() => {
                activeSection.style.opacity = '1';
                activeSection.style.transform = 'translateX(0)';
            }, 50);
        }

        this.currentTab = tabName;
        
        // Store in localStorage
        localStorage.setItem('adminLastTab', tabName);
        
        // Update URL hash
        window.history.replaceState(null, null, `#${tabName}`);
    }

    handleSettingChange(e) {
        const element = e.target;
        const settingId = element.id;
        const value = element.type === 'checkbox' ? element.checked : element.value;
        
        // Store the change
        this.settings[settingId] = value;
        
        // Show visual feedback
        this.showSettingChanged(element);
        
        // Update overview cards
        this.updateOverviewCards();
        
        // Validate if needed
        this.validateSetting(element);
    }

    handleInputFocus(e) {
        e.target.parentElement.classList.add('focused');
    }

    handleInputBlur(e) {
        e.target.parentElement.classList.remove('focused');
    }

    showSettingChanged(element) {
        // Add visual indicator
        element.style.borderColor = '#10b981';
        element.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.1)';
        
        // Remove after 2 seconds
        setTimeout(() => {
            element.style.borderColor = '';
            element.style.boxShadow = '';
        }, 2000);
    }

    validateSetting(element) {
        const value = element.value;
        let isValid = true;
        let message = '';

        switch (element.type) {
            case 'email':
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                isValid = emailRegex.test(value);
                message = 'Please enter a valid email address';
                break;
            case 'url':
                try {
                    new URL(value);
                    isValid = true;
                } catch {
                    isValid = false;
                    message = 'Please enter a valid URL';
                }
                break;
            case 'number':
                const min = parseFloat(element.min);
                const max = parseFloat(element.max);
                const numValue = parseFloat(value);
                
                if (min && numValue < min) {
                    isValid = false;
                    message = `Value must be at least ${min}`;
                } else if (max && numValue > max) {
                    isValid = false;
                    message = `Value must be at most ${max}`;
                }
                break;
        }

        if (!isValid) {
            element.style.borderColor = '#ef4444';
            this.showToast('error', 'Validation Error', message);
        }

        return isValid;
    }

    updateRangeLabel(element) {
        const value = element.value;
        const labels = element.parentElement.querySelector('.admin-range-labels');
        if (labels) {
            const labelsArray = Array.from(labels.children);
            
            // Update visual feedback
            labelsArray.forEach((label, index) => {
                label.style.fontWeight = index === Math.floor((value - 1) / 3) ? '600' : '400';
                label.style.color = index === Math.floor((value - 1) / 3) ? 'var(--admin-primary-light)' : 'var(--admin-text-secondary)';
            });
        }
    }

    updateOverviewCards() {
        const pendingChanges = Object.keys(this.settings).length;
        const pendingCard = document.querySelector('.admin-overview-card .admin-card-content h3');
        
        if (pendingCard && pendingCard.textContent.includes('Pending Changes')) {
            pendingCard.textContent = `${pendingChanges} Pending Changes`;
            
            const cardIcon = pendingCard.closest('.admin-overview-card').querySelector('.admin-card-icon');
            if (cardIcon) {
                if (pendingChanges > 0) {
                    cardIcon.className = 'admin-card-icon warning';
                    cardIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                } else {
                    cardIcon.className = 'admin-card-icon success';
                    cardIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
                }
            }
        }
    }

    loadSettings() {
        // Load from localStorage or use defaults
        const savedSettings = localStorage.getItem('adminSettings');
        const savedTab = localStorage.getItem('adminLastTab');
        
        if (savedSettings) {
            this.settings = JSON.parse(savedSettings);
            this.applySettings();
        }
        
        if (savedTab && savedTab !== this.currentTab) {
            this.switchTab(savedTab);
        }
        
        // Load from URL hash
        const hash = window.location.hash.slice(1);
        if (hash && hash !== this.currentTab) {
            this.switchTab(hash);
        }
        
        this.originalSettings = { ...this.settings };
    }

    applySettings() {
        Object.entries(this.settings).forEach(([key, value]) => {
            const element = document.getElementById(key);
            if (element) {
                if (element.type === 'checkbox') {
                    element.checked = value;
                } else {
                    element.value = value;
                }
            }
        });
    }

    collectSettings() {
        const settings = {};
        
        // General settings
        settings.platform = {
            name: document.getElementById('platform-name')?.value || '',
            description: document.getElementById('platform-description')?.value || '',
            url: document.getElementById('platform-url')?.value || '',
            registrationEnabled: document.getElementById('registration-enabled')?.checked || false,
            emailVerification: document.getElementById('email-verification')?.checked || false,
            manualApproval: document.getElementById('manual-approval')?.checked || false,
            defaultContentStatus: document.getElementById('default-content-status')?.value || 'active',
            autoFlagEnabled: document.getElementById('auto-flag-enabled')?.checked || false,
            flagThreshold: document.getElementById('flag-threshold')?.value || '3'
        };
        
        // Email settings
        settings.email = {
            smtpHost: document.getElementById('smtp-host')?.value || '',
            smtpPort: document.getElementById('smtp-port')?.value || '',
            smtpUsername: document.getElementById('smtp-username')?.value || '',
            smtpPassword: document.getElementById('smtp-password')?.value || '',
            smtpTls: document.getElementById('smtp-tls')?.checked || false,
            fromName: document.getElementById('email-from-name')?.value || '',
            fromEmail: document.getElementById('email-from-email')?.value || '',
            footer: document.getElementById('email-footer')?.value || ''
        };
        
        // Security settings
        settings.security = {
            twoFactorAuth: document.getElementById('two-factor-auth')?.checked || false,
            sessionTimeout: document.getElementById('session-timeout')?.value || '30',
            maxLoginAttempts: document.getElementById('max-login-attempts')?.value || '5',
            lockoutDuration: document.getElementById('lockout-duration')?.value || '15',
            minPasswordLength: document.getElementById('min-password-length')?.value || '8',
            requireUppercase: document.getElementById('require-uppercase')?.checked || false,
            requireLowercase: document.getElementById('require-lowercase')?.checked || false,
            requireNumbers: document.getElementById('require-numbers')?.checked || false,
            requireSymbols: document.getElementById('require-symbols')?.checked || false,
            apiRateLimiting: document.getElementById('api-rate-limiting')?.checked || false,
            apiRateLimit: document.getElementById('api-rate-limit')?.value || '60',
            corsProtection: document.getElementById('cors-protection')?.checked || false
        };
        
        // Notification settings
        settings.notifications = {
            emailNewUser: document.getElementById('email-new-user')?.checked || false,
            emailNewJob: document.getElementById('email-new-job')?.checked || false,
            emailNewBusiness: document.getElementById('email-new-business')?.checked || false,
            emailVerificationRequest: document.getElementById('email-verification-request')?.checked || false,
            emailReportFlagged: document.getElementById('email-report-flagged')?.checked || false,
            adminEmail: document.getElementById('admin-email')?.value || '',
            dailySummary: document.getElementById('daily-summary')?.checked || false,
            securityAlerts: document.getElementById('security-alerts')?.checked || false
        };
        
        // Integration settings
        settings.integrations = {
            paymentsEnabled: document.getElementById('payments-enabled')?.checked || false,
            paymentGateway: document.getElementById('payment-gateway')?.value || '',
            paymentApiKey: document.getElementById('payment-api-key')?.value || '',
            analyticsEnabled: document.getElementById('analytics-enabled')?.checked || false,
            analyticsProvider: document.getElementById('analytics-provider')?.value || 'google',
            analyticsTrackingId: document.getElementById('analytics-tracking-id')?.value || '',
            socialLoginEnabled: document.getElementById('social-login-enabled')?.checked || false,
            facebookAppId: document.getElementById('facebook-app-id')?.value || '',
            googleClientId: document.getElementById('google-client-id')?.value || ''
        };
        
        return settings;
    }

    saveSettings() {
        const settings = this.collectSettings();
        
        // Show loading
        this.showLoading();
        
        // Simulate API call
        setTimeout(() => {
            // Save to localStorage
            localStorage.setItem('adminSettings', JSON.stringify(settings));
            
            // Reset settings tracking
            this.settings = {};
            this.originalSettings = { ...settings };
            
            // Update UI
            this.updateOverviewCards();
            this.hideLoading();
            
            // Show success message
            this.showToast('success', 'Settings Saved', 'Your settings have been saved successfully');
            
            console.log('Settings saved:', settings);
        }, 1500);
    }

    resetSettings() {
        if (confirm('Are you sure you want to reset all settings to their default values? This action cannot be undone.')) {
            // Reset all form fields
            document.querySelectorAll('.admin-form-input, .admin-form-range').forEach(input => {
                input.value = input.defaultValue || '';
            });
            
            document.querySelectorAll('.admin-form-toggle input[type="checkbox"], .admin-form-checkbox input[type="checkbox"]').forEach(checkbox => {
                checkbox.checked = checkbox.defaultChecked;
            });
            
            // Clear saved settings
            localStorage.removeItem('adminSettings');
            this.settings = {};
            this.originalSettings = {};
            
            // Update UI
            this.updateOverviewCards();
            
            // Show success message
            this.showToast('info', 'Settings Reset', 'Settings have been reset to defaults');
        }
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update icon if theme toggle exists
        const themeIcon = document.querySelector('#themeToggle i');
        if (themeIcon) {
            themeIcon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
        
        this.showToast('info', 'Theme Changed', `Switched to ${newTheme} mode`);
    }

    showLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay') || 
                              document.querySelector('.admin-loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.classList.add('active');
            
            anime({
                targets: loadingOverlay,
                opacity: [0, 1],
                duration: 300,
                easing: 'easeOutQuart'
            });
        }
    }

    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay') || 
                              document.querySelector('.admin-loading-overlay');
        if (loadingOverlay) {
            anime({
                targets: loadingOverlay,
                opacity: [1, 0],
                duration: 300,
                easing: 'easeInQuart',
                complete: () => {
                    loadingOverlay.classList.remove('active');
                }
            });
        }
    }

    showToast(type, title, message) {
        const toastContainer = document.getElementById('toastContainer') || 
                              document.querySelector('.admin-toast-container');
        if (!toastContainer) return;
        
        const toastId = 'toast-' + Date.now();
        
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `admin-toast ${type}`;
        toast.innerHTML = `
            <div class="admin-toast-icon">
                <i class="fas ${this.getToastIcon(type)}"></i>
            </div>
            <div class="admin-toast-content">
                <div class="admin-toast-title">${title}</div>
                <div class="admin-toast-message">${message}</div>
            </div>
            <button class="admin-toast-close" onclick="enhancedAdminInterface.closeToast('${toastId}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Animate in
        anime({
            targets: toast,
            translateX: [300, 0],
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutQuart'
        });
        
        // Auto remove
        setTimeout(() => {
            this.closeToast(toastId);
        }, 5000);
    }

    closeToast(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) {
            anime({
                targets: toast,
                translateX: [0, 300],
                opacity: [1, 0],
                duration: 300,
                easing: 'easeInQuart',
                complete: () => {
                    toast.remove();
                }
            });
        }
    }

    getToastIcon(type) {
        switch (type) {
            case 'success': return 'fa-check-circle';
            case 'error': return 'fa-exclamation-circle';
            case 'warning': return 'fa-exclamation-triangle';
            case 'info': return 'fa-info-circle';
            default: return 'fa-info-circle';
        }
    }

    buildSearchIndex() {
        // This would be populated with actual search data
        this.searchIndex = [
            // Example search entries - in real implementation, this would be generated from the actual form elements
            {
                title: 'Platform Name',
                description: 'The name of your platform as it appears to users',
                keywords: ['platform', 'name', 'brand', 'title'],
                tab: 'general',
                elementId: 'platform-name'
            }
            // ... more search entries
        ];
    }
}

// Initialize the enhanced admin interface
const enhancedAdminInterface = new EnhancedAdminInterface();

// Make functions globally available for backward compatibility
window.saveSettings = () => enhancedAdminInterface.saveSettings();
window.resetSettings = () => enhancedAdminInterface.resetSettings();
window.switchSettingsTab = (tab) => enhancedAdminInterface.switchTab(tab);

// Handle URL hash changes
window.addEventListener('hashchange', () => {
    const hash = window.location.hash.slice(1);
    if (hash && hash !== enhancedAdminInterface.currentTab) {
        enhancedAdminInterface.switchTab(hash);
    }
});

// Add CSS classes for enhanced styling
document.addEventListener('DOMContentLoaded', () => {
    // Add admin container class to the main container
    const container = document.querySelector('.admin-container');
    if (container) {
        container.classList.add('admin-container');
    }
    
    // Add background effects
    if (!document.querySelector('.admin-bg-effects')) {
        const bgEffects = document.createElement('div');
        bgEffects.className = 'admin-bg-effects';
        bgEffects.innerHTML = `
            <div class="admin-gradient-bg"></div>
            <div class="admin-floating-shapes">
                <div class="admin-shape admin-shape-1"></div>
                <div class="admin-shape admin-shape-2"></div>
                <div class="admin-shape admin-shape-3"></div>
            </div>
        `;
        document.body.appendChild(bgEffects);
    }
    
    // Add loading overlay
    if (!document.getElementById('loadingOverlay')) {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.id = 'loadingOverlay';
        loadingOverlay.className = 'admin-loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="admin-loading-spinner">
                <div class="admin-spinner"></div>
                <p>Saving settings...</p>
            </div>
        `;
        document.body.appendChild(loadingOverlay);
    }
    
    // Add toast container
    if (!document.getElementById('toastContainer')) {
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'admin-toast-container';
        document.body.appendChild(toastContainer);
    }
});

// Add CSS for enhanced admin interface
const adminStyles = `
/* Enhanced Admin Interface Styles */
.admin-container {
    position: relative;
    z-index: 1;
}

.admin-bg-effects {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: -1;
    pointer-events: none;
    overflow: hidden;
}

.admin-gradient-bg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, 
        rgba(30, 58, 138, 0.03) 0%, 
        rgba(16, 185, 129, 0.03) 50%, 
        rgba(71, 85, 105, 0.03) 100%);
    animation: adminGradientShift 20s ease-in-out infinite;
}

@keyframes adminGradientShift {
    0%, 100% { transform: translateX(0) translateY(0); }
    25% { transform: translateX(-10px) translateY(-5px); }
    50% { transform: translateX(5px) translateY(-10px); }
    75% { transform: translateX(-5px) translateY(5px); }
}

.admin-floating-shapes {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}

.admin-shape {
    position: absolute;
    border-radius: 9999px;
    background: linear-gradient(45deg, #3b82f6, #10b981);
    opacity: 0.1;
    animation: adminFloat 15s ease-in-out infinite;
}

.admin-shape-1 {
    width: 100px;
    height: 100px;
    top: 20%;
    left: 10%;
    animation-delay: 0s;
}

.admin-shape-2 {
    width: 60px;
    height: 60px;
    top: 60%;
    right: 15%;
    animation-delay: 5s;
}

.admin-shape-3 {
    width: 80px;
    height: 80px;
    bottom: 30%;
    left: 20%;
    animation-delay: 10s;
}

@keyframes adminFloat {
    0%, 100% { transform: translateY(0) rotate(0deg); }
    33% { transform: translateY(-20px) rotate(120deg); }
    66% { transform: translateY(10px) rotate(240deg); }
}

/* Toast Styles */
.admin-toast-container {
    position: fixed;
    top: 2rem;
    right: 2rem;
    z-index: 1000;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    max-width: 400px;
}

.admin-toast {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem 1.5rem;
    background: white;
    border-radius: 0.75rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    border: 1px solid #e5e7eb;
    min-width: 300px;
    position: relative;
    overflow: hidden;
}

.admin-toast::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: #3b82f6;
}

.admin-toast.success::before {
    background: #10b981;
}

.admin-toast.error::before {
    background: #ef4444;
}

.admin-toast.warning::before {
    background: #f59e0b;
}

.admin-toast.info::before {
    background: #3b82f6;
}

.admin-toast-icon {
    font-size: 1.25rem;
    flex-shrink: 0;
    margin-top: 2px;
}

.admin-toast.success .admin-toast-icon {
    color: #10b981;
}

.admin-toast.error .admin-toast-icon {
    color: #ef4444;
}

.admin-toast.warning .admin-toast-icon {
    color: #f59e0b;
}

.admin-toast.info .admin-toast-icon {
    color: #3b82f6;
}

.admin-toast-content {
    flex: 1;
    min-width: 0;
}

.admin-toast-title {
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.25rem;
    font-size: 0.875rem;
}

.admin-toast-message {
    font-size: 0.875rem;
    color: #6b7280;
    line-height: 1.4;
}

.admin-toast-close {
    background: none;
    border: none;
    color: #9ca3af;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: 0.25rem;
    transition: all 0.2s ease;
    flex-shrink: 0;
}

.admin-toast-close:hover {
    background: #f3f4f6;
    color: #111827;
}

/* Loading Overlay */
.admin-loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    display: none;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(5px);
}

.admin-loading-overlay.active {
    display: flex;
}

.admin-loading-spinner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    background: white;
    padding: 3rem;
    border-radius: 0.75rem;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
    text-align: center;
}

.admin-spinner {
    width: 3rem;
    height: 3rem;
    border: 3px solid #e5e7eb;
    border-top: 3px solid #3b82f6;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

.admin-loading-spinner p {
    color: #6b7280;
    font-weight: 500;
    margin: 0;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = adminStyles;
document.head.appendChild(styleSheet);