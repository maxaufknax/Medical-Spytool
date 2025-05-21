/**
 * MedicalSpy - Search module - Fixed version
 * This file contains functions for search functionality.
 */

// Global variables to store persons data and selected persons
let allPersons = [];
let selectedPersons = new Set();
let lastSearchQuery = '';

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

// Initialize search functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOMContentLoaded - initializing search functionality');
    
    // Initialize CSRF token handling first
    const initialToken = syncCsrfToken();
    console.log('Initial CSRF token: ' + (initialToken ? 'found' : 'missing'));
    
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
            switch(activeTab) {
                case 'simple-search-tab':
                    searchModeInput.value = 'simple';
                    break;
                case 'person-search-tab':
                    searchModeInput.value = 'person';
                    break;
                case 'advanced-search-tab':
                    searchModeInput.value = 'advanced';
                    break;
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
            alert('Sicherheitstoken fehlt. Bitte laden Sie die Seite neu.');
            return false;
        } else {
            console.log('CSRF token valid: ' + csrfToken.substring(0, 5) + '...');
        }
        
        // Get active tab to determine which search mode is active
        const activeTab = document.querySelector('#searchModeTabs .nav-link.active');
        if (!activeTab) {
            console.warn('No active tab found');
        } else {
            const tabId = activeTab.id;
            console.log('Active tab: ' + tabId);
            
            if (tabId === 'simple-search-tab') {
                // Check simple search fields
                const simpleQuery = document.querySelector('#simple-search input[name="simple_query_content"]');
                if (simpleQuery && !simpleQuery.value.trim()) {
                    event.preventDefault();
                    alert('Bitte geben Sie einen Suchbegriff ein.');
                    return false;
                }
            }
        }
        
        // Validate database selection
        const databases = Array.from(document.querySelectorAll('input[name="databases"]:checked'));
        if (databases.length === 0) {
            event.preventDefault();
            alert('Bitte mindestens eine Datenbank auswählen.');
            return false;
        }
        console.log('Selected databases: ' + databases.map(db => db.value).join(', '));
        
        // Show loading indicator
        const searchButton = document.querySelector('button[type="submit"]');
        if (searchButton) {
            searchButton.disabled = true;
            searchButton.innerHTML = '<span class="spinner-border spinner-border-sm mr-2"></span> Suche läuft...';
            console.log('Search button set to loading state');
        }
        
        // Double-check if the form has the CSRF token before submission
        const formCsrfToken = document.querySelector('input[name="csrf_token"]');
        if (!formCsrfToken || !formCsrfToken.value) {
            event.preventDefault();
            console.error('Form is missing CSRF token at final check');
            alert('Formular fehlt das Sicherheitstoken. Bitte Seite neu laden.');
            return false;
        }
        
        console.log('Form validation passed - submitting form');
        // Let the form submit naturally
        return true;
    });
}

// Initialize persons data
function initializePersonsData() {
    if (window.allPersons && Array.isArray(window.allPersons)) {
        allPersons = window.allPersons;
        console.log('Persons data initialized:', allPersons.length + ' persons loaded');
    }
}
