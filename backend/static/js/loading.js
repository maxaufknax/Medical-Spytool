/**
 * Loading spinner and async request handling for Medical Spytool
 * Provides functionality for showing loading indicators during async operations
 */

// Create loading overlay element
function createLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <div class="loading-message">Bitte warten...</div>
        </div>
    `;
    document.body.appendChild(overlay);
    return overlay;
}

// Get or create loading overlay
function getLoadingOverlay() {
    let overlay = document.querySelector('.loading-overlay');
    if (!overlay) {
        overlay = createLoadingOverlay();
    }
    return overlay;
}

// Show loading indicator
function showLoading(message = 'Bitte warten...') {
    const overlay = getLoadingOverlay();
    const messageEl = overlay.querySelector('.loading-message');
    
    if (messageEl) {
        messageEl.textContent = message;
    }
    
    overlay.classList.add('active');
    document.body.classList.add('loading');
    
    // Announce to screen readers
    const announcer = document.getElementById('loading-announcer') || document.createElement('div');
    announcer.id = 'loading-announcer';
    announcer.className = 'sr-only';
    announcer.setAttribute('aria-live', 'assertive');
    announcer.textContent = message;
    
    if (!document.getElementById('loading-announcer')) {
        document.body.appendChild(announcer);
    }
}

// Hide loading indicator
function hideLoading() {
    const overlay = getLoadingOverlay();
    overlay.classList.remove('active');
    document.body.classList.remove('loading');
    
    // Update screen reader announcement
    const announcer = document.getElementById('loading-announcer');
    if (announcer) {
        announcer.textContent = 'Laden abgeschlossen';
    }
}

// Helper function for AJAX requests with loading indicator
async function fetchWithLoading(url, options = {}, loadingMessage = 'Daten werden geladen...') {
    showLoading(loadingMessage);
    
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    } finally {
        hideLoading();
    }
}

// Initialize loading indicators for forms and links with data attributes
document.addEventListener('DOMContentLoaded', function() {
    // Handle forms with data-show-loading attribute
    document.querySelectorAll('form[data-show-loading]').forEach(form => {
        form.addEventListener('submit', function(e) {
            const message = this.getAttribute('data-loading-message') || 'Formular wird verarbeitet...';
            showLoading(message);
        });
    });
    
    // Handle links with data-show-loading attribute
    document.querySelectorAll('a[data-show-loading]').forEach(link => {
        link.addEventListener('click', function(e) {
            // Don't show loading for links that open in new tabs/windows
            if (this.target === '_blank') return;
            
            const message = this.getAttribute('data-loading-message') || 'Seite wird geladen...';
            showLoading(message);
        });
    });
    
    // Handle buttons with data-show-loading attribute
    document.querySelectorAll('button[data-show-loading]').forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.type !== 'submit' || !this.closest('form')) {
                const message = this.getAttribute('data-loading-message') || 'Wird geladen...';
                showLoading(message);
            }
        });
    });
});
