/**
 * Tangled Graph Explorer — Main JavaScript
 *
 * Common utilities, API helper, and notification system.
 */

// API helper
const api = {
    async get(url) {
        const response = await fetch(url);
        return response.json();
    },

    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        return response.json();
    }
};

// Toast notification system
function showNotification(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        console.log(`[${type.toUpperCase()}] ${message}`);
        return;
    }

    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Auto-dismiss after 3.5s
    setTimeout(() => {
        toast.classList.add('toast--exit');
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Tangled Graph Explorer loaded');
});
