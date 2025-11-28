// Admin Interface JavaScript
class AdminInterface {
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
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                const tabName = e.currentTarget.dataset.tab;
                this.switchTab(tabName);
            });
        });

        // Search functionality
        const searchToggle = document.getElementById('searchToggle');
        const searchOverlay = document.getElementById('searchOverlay');
        const searchClose = document.getElementById('searchClose');
        const searchInput = document.getElementById('searchInput');

        searchToggle.addEventListener('click', () => this.toggleSearch());
        searchClose.addEventListener('click', () => this.closeSearch());
        searchInput.addEventListener('input', (e) => this.performSearch(e.target.value));
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeSearch();
        });

        // Theme toggle
        const themeToggle = document.getElementById('themeToggle');
        themeToggle.addEventListener('click', () => this.toggleTheme());

        // Form interactions
        document.querySelectorAll('.form-input, .form-toggle input, .form-checkbox input').forEach(input => {
            input.addEventListener('change', (e) => this.handleSettingChange(e));
            input.addEventListener('focus', (e) => this.handleInputFocus(e));
            input.addEventListener('blur', (e) => this.handleInputBlur(e));
        });

        // Range slider
        document.getElementById('flag-threshold').addEventListener('input', (e) => {
            this.updateRangeLabel(e.target);
        });

        // Click outside search overlay
        searchOverlay.addEventListener('click', (e) => {
            if (e.target === searchOverlay) this.closeSearch();
        });

        // Save settings on Ctrl+S
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveSettings();
            }
        });
    }

    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Tab navigation with arrow keys
            if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
                const activeTab = document.querySelector('.nav-tab.active');
                if (document.activeElement === activeTab || activeTab.contains(document.activeElement)) {
                    e.preventDefault();
                    const tabs = Array.from(document.querySelectorAll('.nav-tab'));
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

        document.querySelectorAll('.settings-card').forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
            observer.observe(card);
        });

        // Animate overview cards
        document.querySelectorAll('.overview-card').forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
        });
    }

    switchTab(tabName) {
        if (this.currentTab === tabName) return;

        // Update tab buttons
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update sections
        document.querySelectorAll('.settings-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`settings-${tabName}`).classList.add('active');

        // Animate section change
        const activeSection = document.getElementById(`settings-${tabName}`);
        activeSection.style.opacity = '0';
        activeSection.style.transform = 'translateX(20px)';
        
        setTimeout(() => {
            activeSection.style.opacity = '1';
            activeSection.style.transform = 'translateX(0)';
        }, 50);

        this.currentTab = tabName;
        
        // Store in localStorage
        localStorage.setItem('adminLastTab', tabName);
        
        // Update URL hash
        window.history.replaceState(null, null, `#${tabName}`);
    }

    toggleSearch() {
        const searchOverlay = document.getElementById('searchOverlay');
        const searchInput = document.getElementById('searchInput');
        
        searchOverlay.classList.add('active');
        searchInput.focus();
        
        // Animate overlay
        anime({
            targets: searchOverlay,
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutQuart'
        });
    }

    closeSearch() {
        const searchOverlay = document.getElementById('searchOverlay');
        const searchInput = document.getElementById('searchInput');
        const searchResults = document.getElementById('searchResults');
        
        anime({
            targets: searchOverlay,
            opacity: [1, 0],
            duration: 200,
            easing: 'easeInQuart',
            complete: () => {
                searchOverlay.classList.remove('active');
                searchInput.value = '';
                searchResults.innerHTML = '';
            }
        });
    }

    performSearch(query) {
        const searchResults = document.getElementById('searchResults');
        
        if (!query.trim()) {
            searchResults.innerHTML = '';
            return;
        }

        const results = this.searchIndex.filter(item => 
            item.title.toLowerCase().includes(query.toLowerCase()) ||
            item.description.toLowerCase().includes(query.toLowerCase()) ||
            item.keywords.some(keyword => keyword.toLowerCase().includes(query.toLowerCase()))
        );

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="search-no-results">No results found</div>';
            return;
        }

        searchResults.innerHTML = results.map(result => `
            <div class="search-result-item" onclick="adminInterface.navigateToSetting('${result.tab}', '${result.elementId}')">
                <div class="search-result-title">${result.title}</div>
                <div class="search-result-description">${result.description}</div>
            </div>
        `).join('');
    }

    navigateToSetting(tab, elementId) {
        this.switchTab(tab);
        this.closeSearch();
        
        setTimeout(() => {
            const element = document.getElementById(elementId);
            if (element) {
                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                element.focus();
                
                // Highlight element
                element.style.transition = 'background-color 0.3s ease';
                element.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
                setTimeout(() => {
                    element.style.backgroundColor = '';
                }, 2000);
            }
        }, 300);
    }

    buildSearchIndex() {
        this.searchIndex = [
            // General Settings
            {
                title: 'Platform Name',
                description: 'The name of your platform as it appears to users',
                keywords: ['platform', 'name', 'brand', 'title'],
                tab: 'general',
                elementId: 'platform-name'
            },
            {
                title: 'Platform Description',
                description: 'Brief description of your platform\'s purpose',
                keywords: ['description', 'about', 'purpose', 'mission'],
                tab: 'general',
                elementId: 'platform-description'
            },
            {
                title: 'Platform URL',
                description: 'The main URL where your platform is accessible',
                keywords: ['url', 'domain', 'website', 'link'],
                tab: 'general',
                elementId: 'platform-url'
            },
            {
                title: 'User Registration',
                description: 'Allow new users to register on the platform',
                keywords: ['registration', 'signup', 'users', 'access'],
                tab: 'general',
                elementId: 'registration-enabled'
            },
            {
                title: 'Email Verification',
                description: 'Users must verify their email address before accessing the platform',
                keywords: ['email', 'verification', 'confirm', 'validate'],
                tab: 'general',
                elementId: 'email-verification'
            },
            {
                title: 'Manual Approval',
                description: 'New user registrations require admin approval before activation',
                keywords: ['approval', 'moderation', 'review', 'manual'],
                tab: 'general',
                elementId: 'manual-approval'
            },
            {
                title: 'Content Moderation',
                description: 'Default status for new content submissions',
                keywords: ['moderation', 'content', 'approval', 'status'],
                tab: 'general',
                elementId: 'default-content-status'
            },
            {
                title: 'Auto-Flagging',
                description: 'Automatically flag potentially inappropriate content for review',
                keywords: ['flagging', 'auto', 'content', 'review'],
                tab: 'general',
                elementId: 'auto-flag-enabled'
            },
            {
                title: 'Flag Threshold',
                description: 'Sensitivity level for automatic content flagging',
                keywords: ['threshold', 'sensitivity', 'flag', 'level'],
                tab: 'general',
                elementId: 'flag-threshold'
            },
            
            // Email Settings
            {
                title: 'SMTP Host',
                description: 'Your SMTP server hostname',
                keywords: ['smtp', 'host', 'server', 'email'],
                tab: 'email',
                elementId: 'smtp-host'
            },
            {
                title: 'SMTP Port',
                description: 'SMTP server port (usually 587 for TLS, 465 for SSL)',
                keywords: ['port', 'smtp', 'tls', 'ssl'],
                tab: 'email',
                elementId: 'smtp-port'
            },
            {
                title: 'SMTP Username',
                description: 'Username for SMTP authentication',
                keywords: ['username', 'smtp', 'login', 'email'],
                tab: 'email',
                elementId: 'smtp-username'
            },
            {
                title: 'SMTP Password',
                description: 'Password for SMTP authentication',
                keywords: ['password', 'smtp', 'authentication', 'email'],
                tab: 'email',
                elementId: 'smtp-password'
            },
            {
                title: 'TLS Encryption',
                description: 'Use TLS encryption for email sending',
                keywords: ['tls', 'encryption', 'security', 'email'],
                tab: 'email',
                elementId: 'smtp-tls'
            },
            {
                title: 'From Name',
                description: 'Name that appears in the "From" field of emails',
                keywords: ['from', 'name', 'sender', 'email'],
                tab: 'email',
                elementId: 'email-from-name'
            },
            {
                title: 'From Email',
                description: 'Email address that appears in the "From" field',
                keywords: ['from', 'email', 'sender', 'address'],
                tab: 'email',
                elementId: 'email-from-email'
            },
            {
                title: 'Email Footer',
                description: 'Footer text that appears at the bottom of all emails',
                keywords: ['footer', 'email', 'signature', 'text'],
                tab: 'email',
                elementId: 'email-footer'
            },
            
            // Security Settings
            {
                title: 'Two-Factor Authentication',
                description: 'Require users to use 2FA for additional security',
                keywords: ['2fa', 'two-factor', 'authentication', 'security'],
                tab: 'security',
                elementId: 'two-factor-auth'
            },
            {
                title: 'Session Timeout',
                description: 'How long before user sessions expire due to inactivity',
                keywords: ['session', 'timeout', 'inactive', 'duration'],
                tab: 'security',
                elementId: 'session-timeout'
            },
            {
                title: 'Maximum Login Attempts',
                description: 'Number of failed login attempts before temporary lockout',
                keywords: ['login', 'attempts', 'failed', 'lockout'],
                tab: 'security',
                elementId: 'max-login-attempts'
            },
            {
                title: 'Lockout Duration',
                description: 'How long users are locked out after exceeding login attempts',
                keywords: ['lockout', 'duration', 'timeout', 'security'],
                tab: 'security',
                elementId: 'lockout-duration'
            },
            {
                title: 'Minimum Password Length',
                description: 'Minimum number of characters required for passwords',
                keywords: ['password', 'length', 'minimum', 'characters'],
                tab: 'security',
                elementId: 'min-password-length'
            },
            {
                title: 'Require Uppercase Letters',
                description: 'Passwords must contain uppercase letters',
                keywords: ['uppercase', 'password', 'letters', 'requirement'],
                tab: 'security',
                elementId: 'require-uppercase'
            },
            {
                title: 'Require Lowercase Letters',
                description: 'Passwords must contain lowercase letters',
                keywords: ['lowercase', 'password', 'letters', 'requirement'],
                tab: 'security',
                elementId: 'require-lowercase'
            },
            {
                title: 'Require Numbers',
                description: 'Passwords must contain numbers',
                keywords: ['numbers', 'password', 'digits', 'requirement'],
                tab: 'security',
                elementId: 'require-numbers'
            },
            {
                title: 'Require Special Characters',
                description: 'Passwords must contain special characters',
                keywords: ['special', 'characters', 'password', 'symbols'],
                tab: 'security',
                elementId: 'require-symbols'
            },
            {
                title: 'API Rate Limiting',
                description: 'Limit the number of API requests per user to prevent abuse',
                keywords: ['api', 'rate', 'limiting', 'requests'],
                tab: 'security',
                elementId: 'api-rate-limiting'
            },
            {
                title: 'API Rate Limit',
                description: 'Maximum number of API requests allowed per minute per user',
                keywords: ['api', 'rate', 'limit', 'maximum'],
                tab: 'security',
                elementId: 'api-rate-limit'
            },
            {
                title: 'CORS Protection',
                description: 'Restrict API access to authorized domains only',
                keywords: ['cors', 'protection', 'api', 'domains'],
                tab: 'security',
                elementId: 'cors-protection'
            },
            
            // Notification Settings
            {
                title: 'New User Registration',
                description: 'Send email when a new user registers',
                keywords: ['new', 'user', 'registration', 'email'],
                tab: 'notifications',
                elementId: 'email-new-user'
            },
            {
                title: 'New Job Posting',
                description: 'Send email when a new job is posted',
                keywords: ['new', 'job', 'posting', 'email'],
                tab: 'notifications',
                elementId: 'email-new-job'
            },
            {
                title: 'New Business Listing',
                description: 'Send email when a new business is listed',
                keywords: ['new', 'business', 'listing', 'email'],
                tab: 'notifications',
                elementId: 'email-new-business'
            },
            {
                title: 'Verification Request',
                description: 'Send email when users submit verification documents',
                keywords: ['verification', 'request', 'documents', 'email'],
                tab: 'notifications',
                elementId: 'email-verification-request'
            },
            {
                title: 'Content Flagged',
                description: 'Send email when content is flagged for review',
                keywords: ['content', 'flagged', 'review', 'email'],
                tab: 'notifications',
                elementId: 'email-report-flagged'
            },
            {
                title: 'Admin Email Address',
                description: 'Email address where admin notifications should be sent',
                keywords: ['admin', 'email', 'address', 'notifications'],
                tab: 'notifications',
                elementId: 'admin-email'
            },
            {
                title: 'Daily Summary Report',
                description: 'Receive daily summary of platform activity',
                keywords: ['daily', 'summary', 'report', 'activity'],
                tab: 'notifications',
                elementId: 'daily-summary'
            },
            {
                title: 'Security Alerts',
                description: 'Receive alerts for security-related events',
                keywords: ['security', 'alerts', 'events', 'notifications'],
                tab: 'notifications',
                elementId: 'security-alerts'
            },
            
            // Integration Settings
            {
                title: 'Payment Processing',
                description: 'Allow users to make payments through the platform',
                keywords: ['payment', 'processing', 'transactions', 'payments'],
                tab: 'integrations',
                elementId: 'payments-enabled'
            },
            {
                title: 'Payment Gateway',
                description: 'Choose your preferred payment gateway provider',
                keywords: ['payment', 'gateway', 'provider', 'stripe'],
                tab: 'integrations',
                elementId: 'payment-gateway'
            },
            {
                title: 'Payment API Key',
                description: 'API key for your payment gateway integration',
                keywords: ['api', 'key', 'payment', 'integration'],
                tab: 'integrations',
                elementId: 'payment-api-key'
            },
            {
                title: 'Analytics Integration',
                description: 'Track user behavior and platform performance',
                keywords: ['analytics', 'tracking', 'performance', 'statistics'],
                tab: 'integrations',
                elementId: 'analytics-enabled'
            },
            {
                title: 'Analytics Provider',
                description: 'Choose your analytics tracking provider',
                keywords: ['analytics', 'provider', 'google', 'mixpanel'],
                tab: 'integrations',
                elementId: 'analytics-provider'
            },
            {
                title: 'Tracking ID',
                description: 'Your analytics tracking ID or measurement ID',
                keywords: ['tracking', 'id', 'analytics', 'measurement'],
                tab: 'integrations',
                elementId: 'analytics-tracking-id'
            },
            {
                title: 'Social Login',
                description: 'Allow users to login using social media accounts',
                keywords: ['social', 'login', 'facebook', 'google'],
                tab: 'integrations',
                elementId: 'social-login-enabled'
            },
            {
                title: 'Facebook App ID',
                description: 'Facebook application ID for social login integration',
                keywords: ['facebook', 'app', 'id', 'social'],
                tab: 'integrations',
                elementId: 'facebook-app-id'
            },
            {
                title: 'Google Client ID',
                description: 'Google client ID for social login integration',
                keywords: ['google', 'client', 'id', 'social'],
                tab: 'integrations',
                elementId: 'google-client-id'
            }
        ];
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
        const labels = element.parentElement.querySelector('.range-labels');
        const labelsArray = Array.from(labels.children);
        
        // Update visual feedback
        labelsArray.forEach((label, index) => {
            label.style.fontWeight = index === Math.floor((value - 1) / 3) ? '600' : '400';
            label.style.color = index === Math.floor((value - 1) / 3) ? 'var(--primary-light)' : 'var(--text-secondary)';
        });
    }

    updateOverviewCards() {
        const pendingChanges = Object.keys(this.settings).length;
        const pendingCard = document.querySelector('.overview-card .card-content h3');
        
        if (pendingCard && pendingCard.textContent.includes('Pending Changes')) {
            pendingCard.textContent = `${pendingChanges} Pending Changes`;
            
            const cardIcon = pendingCard.closest('.overview-card').querySelector('.card-icon');
            if (pendingChanges > 0) {
                cardIcon.className = 'card-icon warning';
                cardIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
            } else {
                cardIcon.className = 'card-icon success';
                cardIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
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
            name: document.getElementById('platform-name').value,
            description: document.getElementById('platform-description').value,
            url: document.getElementById('platform-url').value,
            registrationEnabled: document.getElementById('registration-enabled').checked,
            emailVerification: document.getElementById('email-verification').checked,
            manualApproval: document.getElementById('manual-approval').checked,
            defaultContentStatus: document.getElementById('default-content-status').value,
            autoFlagEnabled: document.getElementById('auto-flag-enabled').checked,
            flagThreshold: document.getElementById('flag-threshold').value
        };
        
        // Email settings
        settings.email = {
            smtpHost: document.getElementById('smtp-host').value,
            smtpPort: document.getElementById('smtp-port').value,
            smtpUsername: document.getElementById('smtp-username').value,
            smtpPassword: document.getElementById('smtp-password').value,
            smtpTls: document.getElementById('smtp-tls').checked,
            fromName: document.getElementById('email-from-name').value,
            fromEmail: document.getElementById('email-from-email').value,
            footer: document.getElementById('email-footer').value
        };
        
        // Security settings
        settings.security = {
            twoFactorAuth: document.getElementById('two-factor-auth').checked,
            sessionTimeout: document.getElementById('session-timeout').value,
            maxLoginAttempts: document.getElementById('max-login-attempts').value,
            lockoutDuration: document.getElementById('lockout-duration').value,
            minPasswordLength: document.getElementById('min-password-length').value,
            requireUppercase: document.getElementById('require-uppercase').checked,
            requireLowercase: document.getElementById('require-lowercase').checked,
            requireNumbers: document.getElementById('require-numbers').checked,
            requireSymbols: document.getElementById('require-symbols').checked,
            apiRateLimiting: document.getElementById('api-rate-limiting').checked,
            apiRateLimit: document.getElementById('api-rate-limit').value,
            corsProtection: document.getElementById('cors-protection').checked
        };
        
        // Notification settings
        settings.notifications = {
            emailNewUser: document.getElementById('email-new-user').checked,
            emailNewJob: document.getElementById('email-new-job').checked,
            emailNewBusiness: document.getElementById('email-new-business').checked,
            emailVerificationRequest: document.getElementById('email-verification-request').checked,
            emailReportFlagged: document.getElementById('email-report-flagged').checked,
            adminEmail: document.getElementById('admin-email').value,
            dailySummary: document.getElementById('daily-summary').checked,
            securityAlerts: document.getElementById('security-alerts').checked
        };
        
        // Integration settings
        settings.integrations = {
            paymentsEnabled: document.getElementById('payments-enabled').checked,
            paymentGateway: document.getElementById('payment-gateway').value,
            paymentApiKey: document.getElementById('payment-api-key').value,
            analyticsEnabled: document.getElementById('analytics-enabled').checked,
            analyticsProvider: document.getElementById('analytics-provider').value,
            analyticsTrackingId: document.getElementById('analytics-tracking-id').value,
            socialLoginEnabled: document.getElementById('social-login-enabled').checked,
            facebookAppId: document.getElementById('facebook-app-id').value,
            googleClientId: document.getElementById('google-client-id').value
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
            document.querySelectorAll('.form-input, .form-range').forEach(input => {
                input.value = input.defaultValue || '';
            });
            
            document.querySelectorAll('.form-toggle input[type="checkbox"], .form-checkbox input[type="checkbox"]').forEach(checkbox => {
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

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update icon
        const themeIcon = document.querySelector('#themeToggle i');
        themeIcon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        
        this.showToast('info', 'Theme Changed', `Switched to ${newTheme} mode`);
    }

    showLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.classList.add('active');
        
        anime({
            targets: loadingOverlay,
            opacity: [0, 1],
            duration: 300,
            easing: 'easeOutQuart'
        });
    }

    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        
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

    showToast(type, title, message) {
        const toastContainer = document.getElementById('toastContainer');
        const toastId = 'toast-' + Date.now();
        
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div class="toast-icon">
                <i class="fas ${this.getToastIcon(type)}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close" onclick="adminInterface.closeToast('${toastId}')">
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
}

// Initialize the admin interface
const adminInterface = new AdminInterface();

// Make functions globally available
window.saveSettings = () => adminInterface.saveSettings();
window.resetSettings = () => adminInterface.resetSettings();
window.switchSettingsTab = (tab) => adminInterface.switchTab(tab);

// Initialize theme from localStorage
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    const themeIcon = document.querySelector('#themeToggle i');
    themeIcon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
});

// Handle URL hash changes
window.addEventListener('hashchange', () => {
    const hash = window.location.hash.slice(1);
    if (hash && hash !== adminInterface.currentTab) {
        adminInterface.switchTab(hash);
    }
});