// Main JavaScript file for dashboard functionality

// Utility function for API calls
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (data) {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(endpoint, options);
        return await response.json();
    } catch (error) {
        console.error('API call error:', error);
        throw error;
    }
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Agent Connector Dashboard loaded');
});

