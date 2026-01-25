/**
 * Tangled Graph Explorer - Main JavaScript
 * 
 * Common utilities and initialization.
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

// Notification helper
function showNotification(message, type = 'info') {
    // TODO: Implement notification UI
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('Tangled Graph Explorer loaded');
});
