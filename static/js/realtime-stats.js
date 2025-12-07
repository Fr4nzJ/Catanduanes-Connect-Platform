/**
 * Real-time data update system
 * Automatically refreshes dashboard and homepage stats
 */

class RealtimeStatsUpdater {
    constructor(options = {}) {
        this.apiEndpoint = options.apiEndpoint || '/api/realtime/stats';
        this.refreshInterval = options.refreshInterval || 10000; // 10 seconds default
        this.statsElements = options.statsElements || {};
        this.isRunning = false;
        this.lastUpdate = null;
    }

    /**
     * Start real-time updates
     */
    start() {
        if (this.isRunning) return;
        this.isRunning = true;
        this.updateStats();
        this.intervalId = setInterval(() => this.updateStats(), this.refreshInterval);
    }

    /**
     * Stop real-time updates
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        this.isRunning = false;
    }

    /**
     * Fetch and update stats
     */
    async updateStats() {
        try {
            const response = await fetch(this.apiEndpoint);
            if (!response.ok) {
                console.error('Failed to fetch stats:', response.status);
                return;
            }

            const data = await response.json();
            this.lastUpdate = new Date();
            this.updateElements(data);
        } catch (error) {
            console.error('Error updating stats:', error);
        }
    }

    /**
     * Update DOM elements with new stats
     */
    updateElements(data) {
        Object.entries(this.statsElements).forEach(([key, elementId]) => {
            const element = document.getElementById(elementId);
            if (element && data[key] !== undefined) {
                const newValue = data[key];
                const oldValue = element.textContent;
                
                // Update value
                element.textContent = newValue;
                
                // Add animation if value changed
                if (oldValue !== newValue && oldValue !== '0') {
                    element.classList.add('stats-updated');
                    setTimeout(() => {
                        element.classList.remove('stats-updated');
                    }, 1000);
                }
            }
        });

        // Update last refresh time if element exists
        const lastRefreshEl = document.getElementById('last-refresh-time');
        if (lastRefreshEl) {
            lastRefreshEl.textContent = this.formatTime(this.lastUpdate);
        }
    }

    /**
     * Format time for display
     */
    formatTime(date) {
        if (!date) return 'Never';
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
    }

    /**
     * Update refresh interval
     */
    setInterval(milliseconds) {
        this.refreshInterval = milliseconds;
        if (this.isRunning) {
            this.stop();
            this.start();
        }
    }
}

/**
 * Homepage stats updater - special version for homepage
 */
class HomepageStatsUpdater extends RealtimeStatsUpdater {
    constructor(options = {}) {
        super({
            apiEndpoint: '/api/homepage/stats',
            refreshInterval: 15000, // 15 seconds for homepage
            ...options
        });
    }
}

/**
 * Initialize real-time updates on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if we should initialize real-time updates
    const statsConfig = window.REALTIME_STATS_CONFIG;
    if (!statsConfig) return;

    if (statsConfig.type === 'homepage') {
        window.statsUpdater = new HomepageStatsUpdater(statsConfig);
    } else {
        window.statsUpdater = new RealtimeStatsUpdater(statsConfig);
    }

    window.statsUpdater.start();

    // Stop updates when page is hidden (tab/window switch)
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            window.statsUpdater.stop();
        } else {
            window.statsUpdater.start();
            // Refresh immediately when tab becomes visible
            window.statsUpdater.updateStats();
        }
    });
});

/**
 * Utility function to add CSS styles for animations
 */
function initRealtimeStyles() {
    if (document.getElementById('realtime-styles')) return;

    const style = document.createElement('style');
    style.id = 'realtime-styles';
    style.textContent = `
        .stats-updated {
            animation: statsHighlight 0.6s ease-in-out;
        }

        @keyframes statsHighlight {
            0% {
                background-color: #fff3cd;
                transform: scale(1);
            }
            50% {
                background-color: #fff9e6;
                transform: scale(1.05);
            }
            100% {
                background-color: transparent;
                transform: scale(1);
            }
        }

        .realtime-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
            padding: 0.25rem 0.75rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 9999px;
            font-weight: 600;
        }

        .realtime-badge .pulse-dot {
            display: inline-block;
            width: 6px;
            height: 6px;
            background-color: #10b981;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% {
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7);
            }
            70% {
                box-shadow: 0 0 0 6px rgba(16, 185, 129, 0);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(16, 185, 129, 0);
            }
        }

        .last-refresh-text {
            font-size: 0.75rem;
            color: #6b7280;
            margin-top: 0.25rem;
        }
    `;
    document.head.appendChild(style);
}

// Initialize styles when script loads
initRealtimeStyles();
