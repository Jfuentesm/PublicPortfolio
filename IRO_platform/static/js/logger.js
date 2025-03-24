// static/js/logger.js

/**
 * Frontend logging utility that captures console logs and sends them to backend
 */
class FrontendLogger {
    constructor() {
        this.logQueue = [];
        this.logEndpoint = '/api/logs/frontend/';
        this.flushInterval = 5000; // Send logs every 5 seconds
        this.maxQueueSize = 100;
        this.enabled = true;
        this.levels = {
            DEBUG: 0,
            INFO: 1,
            WARNING: 2,
            ERROR: 3,
            CRITICAL: 4
        };
        this.currentLevel = this.levels.INFO;
        
        this.setup();
    }
    
    setup() {
        // Start periodic flush of logs
        this.flushIntervalId = setInterval(() => {
            this.flush();
        }, this.flushInterval);
        
        // Override console methods
        this.overrideConsole();
        
        // Set up global error handler
        this.setupErrorHandlers();
    }
    
    overrideConsole() {
        // Store original console methods
        const originalConsole = {
            log: console.log,
            info: console.info,
            warn: console.warn,
            error: console.error
        };
        
        // Override console.log
        console.log = (...args) => {
            originalConsole.log.apply(console, args);
            this.debug(args.map(arg => this.stringify(arg)).join(' '));
        };
        
        // Override console.info
        console.info = (...args) => {
            originalConsole.info.apply(console, args);
            this.info(args.map(arg => this.stringify(arg)).join(' '));
        };
        
        // Override console.warn
        console.warn = (...args) => {
            originalConsole.warn.apply(console, args);
            this.warn(args.map(arg => this.stringify(arg)).join(' '));
        };
        
        // Override console.error
        console.error = (...args) => {
            originalConsole.error.apply(console, args);
            this.error(args.map(arg => this.stringify(arg)).join(' '));
        };
    }
    
    setupErrorHandlers() {
        // Global error handler
        window.addEventListener('error', (event) => {
            this.critical(`Uncaught error: ${event.message} at ${event.filename}:${event.lineno}:${event.colno}`, {
                stack: event.error?.stack,
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
            return false;
        });
        
        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            this.critical(`Unhandled promise rejection: ${this.stringify(event.reason)}`, {
                reason: this.stringify(event.reason),
                stack: event.reason?.stack
            });
        });
    }
    
    stringify(obj) {
        // Convert object to string for logging
        if (obj === null) return 'null';
        if (obj === undefined) return 'undefined';
        if (typeof obj === 'string') return obj;
        
        try {
            return JSON.stringify(obj);
        } catch (e) {
            return String(obj);
        }
    }
    
    shouldLog(level) {
        // Check if this log level should be recorded
        return this.enabled && this.levels[level] >= this.currentLevel;
    }
    
    /**
     * Add a log entry to the queue
     */
    log(level, message, context = {}) {
        if (!this.shouldLog(level)) return;
        
        // Get session/user info
        const sessionId = document.cookie
            .split('; ')
            .find(row => row.startsWith('sessionid='))
            ?.split('=')[1] || 'no-session';
        
        // Add log entry to queue
        this.logQueue.push({
            timestamp: new Date().toISOString(),
            level,
            message,
            url: window.location.href,
            userAgent: navigator.userAgent,
            sessionId,
            context
        });
        
        // Flush immediately if queue is large or this is a higher severity log
        if (this.logQueue.length >= this.maxQueueSize || 
            this.levels[level] >= this.levels.ERROR) {
            this.flush();
        }
    }
    
    /**
     * Log levels
     */
    debug(message, context = {}) {
        this.log('DEBUG', message, context);
    }
    
    info(message, context = {}) {
        this.log('INFO', message, context);
    }
    
    warn(message, context = {}) {
        this.log('WARNING', message, context);
    }
    
    error(message, context = {}) {
        this.log('ERROR', message, context);
    }
    
    critical(message, context = {}) {
        this.log('CRITICAL', message, context);
    }
    
    /**
     * Send logs to backend
     */
    flush() {
        if (!this.logQueue.length) return;
        
        // Get logs to send
        const logs = [...this.logQueue];
        this.logQueue = [];
        
        // Get CSRF token
        const csrfToken = document.querySelector('meta[name="csrftoken"]')?.getAttribute('content') ||
            document.cookie
                .split('; ')
                .find(row => row.startsWith('csrftoken='))
                ?.split('=')[1] || '';
        
        // Send logs to backend
        fetch(this.logEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ logs })
        }).catch(error => {
            // Failed to send logs - add them back to queue
            this.logQueue = [...logs, ...this.logQueue].slice(0, this.maxQueueSize);
        });
    }
    
    /**
     * Set the minimum log level
     */
    setLevel(level) {
        if (this.levels[level] !== undefined) {
            this.currentLevel = this.levels[level];
        }
    }
    
    /**
     * Enable or disable logging
     */
    setEnabled(enabled) {
        this.enabled = enabled;
    }
    
    /**
     * Clean up when no longer needed
     */
    destroy() {
        // Flush remaining logs
        this.flush();
        
        // Clear flush interval
        if (this.flushIntervalId) {
            clearInterval(this.flushIntervalId);
        }
    }
}

// Initialize the logger
window.logger = new FrontendLogger();