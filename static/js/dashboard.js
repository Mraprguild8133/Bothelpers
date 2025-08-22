// Dashboard JavaScript functionality

// Global functions for dashboard interactions
window.dashboard = {
    // Utility functions
    showLoading: function(element) {
        element.classList.add('loading');
    },
    
    hideLoading: function(element) {
        element.classList.remove('loading');
    },
    
    showAlert: function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    },
    
    // API interaction functions
    fetchStats: function() {
        return fetch('/api/stats')
            .then(response => response.json())
            .catch(error => {
                console.error('Error fetching stats:', error);
                return {};
            });
    },
    
    updateGroupSettings: function(groupId, settings) {
        return fetch(`/api/group/${groupId}/settings`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({settings: settings})
        })
        .then(response => response.json());
    }
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Telegram Bot Dashboard loaded');
    
    // Add smooth scrolling to all anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Auto-refresh functionality for stats
    if (window.location.pathname === '/') {
        setInterval(function() {
            dashboard.fetchStats().then(stats => {
                // Update stats on dashboard if elements exist
                updateStatsDisplay(stats);
            });
        }, 30000); // Refresh every 30 seconds
    }
});

// Update stats display on dashboard
function updateStatsDisplay(stats) {
    const statElements = {
        'total_groups': document.querySelector('[data-stat="total_groups"]'),
        'active_groups': document.querySelector('[data-stat="active_groups"]'),
        'spam_messages_blocked': document.querySelector('[data-stat="spam_blocked"]'),
        'total_users': document.querySelector('[data-stat="total_users"]')
    };
    
    Object.keys(statElements).forEach(key => {
        const element = statElements[key];
        if (element && stats[key] !== undefined) {
            element.textContent = stats[key];
        }
    });
}

// Form validation utilities
function validateForm(formElement) {
    const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Network status indicator
function updateNetworkStatus() {
    const statusElement = document.querySelector('.navbar-text');
    if (statusElement) {
        if (navigator.onLine) {
            statusElement.innerHTML = '<i class="fas fa-circle text-success me-1"></i>Bot Online';
        } else {
            statusElement.innerHTML = '<i class="fas fa-circle text-danger me-1"></i>Offline';
        }
    }
}

// Listen for network status changes
window.addEventListener('online', updateNetworkStatus);
window.addEventListener('offline', updateNetworkStatus);

// Initialize network status
updateNetworkStatus();
