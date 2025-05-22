/**
 * MedicalSpy - Search module - Fixed version
 * This file contains functions for search functionality.
 */

// Global variables to store persons data and selected persons
let allPersons = [];
let selectedPersons = new Set();
let lastSearchQuery = '';
let searchStatusIntervalId = null;
let searchTimeout = null;
const MAX_SEARCH_DURATION = 45000; // 45 seconds maximum search time

// Helper function to get a cookie by name
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Function to synchronize CSRF token from cookie to form
function syncCsrfToken() {
    const tokenFromCookie = getCookie('csrf_token');
    const tokenInput = document.querySelector('input[name="csrf_token"]');
    
    if (tokenFromCookie && tokenInput) {
        // Update form token if it differs from cookie token
        if (tokenInput.value !== tokenFromCookie) {
            console.log('Synchronizing CSRF token from cookie to form');
            tokenInput.value = tokenFromCookie;
        }
        return tokenInput.value;
    } else if (tokenInput && !tokenInput.value && tokenFromCookie) {
        console.log('Form token empty but cookie token available - synchronizing');
        tokenInput.value = tokenFromCookie;
        return tokenInput.value;
    } else if (!tokenFromCookie) {
        console.error('No CSRF token available in cookie');
    } else if (!tokenInput) {
        console.error('No CSRF token input field found in form');
    }
    return null;
}

// Function to show a toast message
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast show position-fixed top-0 end-0 m-3 bg-${type}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">Medical Spytool</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">${message}</div>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

// Function to update the UI based on search status
function updateSearchUI(status, message) {
    const searchButton = document.querySelector('button[type="submit"]');
    const loadingOverlay = document.querySelector('.loading-overlay');
    
    if (searchButton) {
        switch (status) {
            case 'searching':
                searchButton.disabled = true;
                searchButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Suche läuft...';
                break;
            case 'completed':
            case 'no_results':
            case 'error':
            case 'timeout':
                searchButton.disabled = false;
                searchButton.innerHTML = '<i class="fas fa-search me-2"></i>Suchen';
                break;
            default:
                searchButton.disabled = false;
                searchButton.innerHTML = '<i class="fas fa-search me-2"></i>Suchen';
        }
    }
    
    // Update or remove loading overlay
    if (status === 'searching') {
        if (!loadingOverlay) {
            const overlay = document.createElement('div');
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-content">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <h5>Suche läuft...</h5>
                    <p class="text-muted">Bitte warten Sie, während die ausgewählten Datenbanken durchsucht werden.</p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
    } else {
        if (loadingOverlay) {
            loadingOverlay.remove();
        }
    }
    
    // Show message if provided
    if (message) {
        showToast(message, status === 'error' ? 'danger' : 'info');
    }
}

// Function to check search status
function checkSearchStatus() {
    fetch('/search/status?' + new Date().getTime(), {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        console.log('Search status:', data);
        
        switch (data.status) {
            case 'searching':
                updateSearchUI('searching', data.message);
                break;
                
            case 'completed':
                stopSearchStatusPolling();
                updateSearchUI('completed', 'Suche abgeschlossen.');
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
                break;
                
            case 'no_results':
                stopSearchStatusPolling();
                updateSearchUI('no_results', 'Keine Ergebnisse gefunden.');
                break;
                
            case 'error':
                stopSearchStatusPolling();
                updateSearchUI('error', data.message || 'Ein Fehler ist aufgetreten.');
                break;
                
            case 'timeout':
                stopSearchStatusPolling();
                updateSearchUI('timeout', 'Die Suche hat zu lange gedauert. Bitte versuchen Sie es später erneut.');
                break;
                
            default:
                console.warn('Unknown search status:', data.status);
        }
        
        // Handle any errors from the search
        if (data.errors && data.errors.length > 0) {
            data.errors.forEach(error => {
                showToast(`Fehler in ${error.database}: ${error.error}`, 'warning');
            });
        }
    })
    .catch(error => {
        console.error('Error checking search status:', error);
        stopSearchStatusPolling();
        updateSearchUI('error', 'Fehler beim Prüfen des Suchstatus.');
    });
}

// Function to start search status polling
function startSearchStatusPolling() {
    if (searchStatusIntervalId) {
        stopSearchStatusPolling();
    }
    
    // Initial check
    checkSearchStatus();
    
    // Start polling every 2 seconds
    searchStatusIntervalId = setInterval(checkSearchStatus, 2000);
    
    // Set a maximum search duration timeout
    searchTimeout = setTimeout(() => {
        stopSearchStatusPolling();
        updateSearchUI('timeout', 'Die Suche wurde nach 45 Sekunden automatisch abgebrochen.');
    }, MAX_SEARCH_DURATION);
}

// Function to stop search status polling
function stopSearchStatusPolling() {
    if (searchStatusIntervalId) {
        clearInterval(searchStatusIntervalId);
        searchStatusIntervalId = null;
    }
    
    if (searchTimeout) {
        clearTimeout(searchTimeout);
        searchTimeout = null;
    }
}

// Initialize search functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded - initializing search functionality');

    // Initialize CSRF token handling first
    // Ensure CSRF token is available in the meta tag
    const csrfMetaTag = document.querySelector('meta[name="csrf-token"]');
    if (!csrfMetaTag || !csrfMetaTag.getAttribute('content')) {
        console.error('CSRF meta tag or its content is missing!');
        // Optionally, display an error to the user or try to fetch it if applicable
    } else {
        console.log('CSRF meta tag found with content.');
    }

    const initialToken = syncCsrfToken(); // This will also set the cookie if the meta tag is present
    console.log('Initial CSRF token sync: ' + (initialToken ? 'successful' : 'failed or not needed'));

    // Set up an interval to periodically check and refresh the CSRF token
    const tokenInterval = setInterval(function() {
        const refreshedToken = syncCsrfToken();
        console.log('CSRF token refresh: ' + (refreshedToken ? 'synchronized' : 'failed'));
    }, 30000); // Check every 30 seconds
    
    // Ensure CSRF token is synced right before any forms are submitted
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Synchronize right before submission
            const lastToken = syncCsrfToken();
            console.log('CSRF token check before submission: ' + (lastToken ? 'valid' : 'missing'));
        }, true); // Use capturing phase to run before other handlers
    });
    
    // Then initialize the search form
    initializeSearchForm();
    initializePersonsData();
    
    console.log('Search functionality initialization complete');
});

// Initialize form handlers
function initializeSearchForm() {
    const searchForm = document.getElementById('searchForm');
    if (!searchForm) return;

    const searchModeInput = document.getElementById('searchMode');
    const searchModeTabs = document.getElementById('searchModeTabs');
    
    // Update search mode when tabs change
    if (searchModeTabs) {
        searchModeTabs.addEventListener('show.bs.tab', function(event) {
            const activeTab = event.target.id;
            const currentSearchMode = searchModeInput.value;
            let newSearchMode = 'simple'; // Default to simple

            switch(activeTab) {
                case 'simple-search-tab':
                    newSearchMode = 'simple';
                    break;
                case 'person-search-tab':
                    newSearchMode = 'person';
                    break;
                case 'advanced-search-tab':
                    newSearchMode = 'advanced';
                    break;
                // Add cases for other tabs if they represent different search modes
            }
            
            if (currentSearchMode !== newSearchMode) {
                searchModeInput.value = newSearchMode;
                console.log('Search mode changed to: ' + newSearchMode);
            }
        });
    }
      // Handle form submission
    searchForm.addEventListener('submit', function(event) {
        console.log('Form submission started - validating');
        
        // First sync the CSRF token from cookie to form
        const csrfToken = syncCsrfToken();
        
        // Verify CSRF token exists after synchronizing
        if (!csrfToken) {
            event.preventDefault();
            console.error('Missing CSRF token even after sync attempt');
            showToast('Sicherheitstoken fehlt. Bitte laden Sie die Seite neu.', 'error');
            return false;
        }
        
        // Validate form based on active search mode
        if (!validateSearchForm()) {
            event.preventDefault();
            return false;
        }
        
        // Show loading state
        updateSearchUI('searching');
        
        // Start polling for search status after a short delay
        setTimeout(() => {
            startSearchStatusPolling();
        }, 500);
        
        // Let the form submit
        return true;
    });
}

// Helper function to validate the search form
function validateSearchForm() {
    const activeTab = document.querySelector('#searchModeTabs .nav-link.active');
    if (!activeTab) {
        console.warn('No active tab found');
        return false;
    }
    
    const tabId = activeTab.id;
    console.log('Validating tab:', tabId);
    
    // Validate based on search mode
    switch(tabId) {
        case 'simple-search-tab':
            return validateSimpleSearch();
        case 'person-search-tab':
            return validatePersonSearch();
        case 'advanced-search-tab':
            return validateAdvancedSearch();
        default:
            console.warn('Unknown search mode:', tabId);
            return false;
    }
}

// Validate simple search
function validateSimpleSearch() {
    const simpleQueryInput = document.querySelector('#simple-search input[name="simple_query_content"]');
    if (!simpleQueryInput?.value.trim()) {
        showToast('Bitte geben Sie einen Suchbegriff ein.', 'warning');
        simpleQueryInput?.classList.add('is-invalid');
        return false;
    }
    simpleQueryInput.classList.remove('is-invalid');
    return validateDatabaseSelection();
}

// Validate person search
function validatePersonSearch() {
    const selectedPersonIdsInput = document.getElementById('selectedPersonIds');
    if (!selectedPersonIdsInput?.value) {
        showToast('Bitte wählen Sie mindestens eine Person für die personenbezogene Suche aus.', 'warning');
        const noPersonsAlert = document.getElementById('noPersonsSelectedAlert');
        noPersonsAlert?.classList.add('border-danger');
        return false;
    }
    
    const noPersonsAlert = document.getElementById('noPersonsSelectedAlert');
    noPersonsAlert?.classList.remove('border-danger');
    return validateDatabaseSelection();
}

// Validate advanced search
function validateAdvancedSearch() {
    const advancedQueryInput = document.getElementById('advancedSearchQuery');
    if (!advancedQueryInput?.value.trim()) {
        showToast('Bitte geben Sie die Hauptsuchbegriffe für die erweiterte Suche ein.', 'warning');
        advancedQueryInput?.classList.add('is-invalid');
        return false;
    }
    advancedQueryInput.classList.remove('is-invalid');
    return validateDatabaseSelection();
}

// Validate database selection
function validateDatabaseSelection() {
    const databaseCheckboxes = document.querySelectorAll('input[name="databases"]:checked');
    if (databaseCheckboxes.length === 0) {
        showToast('Bitte wählen Sie mindestens eine Datenbank aus.', 'warning');
        const dbContainer = document.querySelector('.databases-container');
        dbContainer?.classList.add('border-danger');
        return false;
    }
    
    const dbContainer = document.querySelector('.databases-container');
    dbContainer?.classList.remove('border-danger');
    return true;
}

// Initialize persons data
function initializePersonsData() {
    if (window.allPersons && Array.isArray(window.allPersons)) {
        allPersons = window.allPersons;
        console.log('Persons data initialized:', allPersons.length + ' persons loaded');
    }
}
