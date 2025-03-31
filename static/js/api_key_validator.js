/**
 * API-Key-Validator für Medical Spytool
 * 
 * Dieses Script validiert API-Keys für verschiedene Datenbanken 
 * und zeigt visuelles Feedback an.
 */

document.addEventListener('DOMContentLoaded', function() {
    // API-Key Eingabefelder
    const apiKeyFields = {
        'pubmed': document.getElementById('pubmed_api_key'),
        'dnb': document.getElementById('dnb_api_key'),
        'scopus': document.getElementById('scopus_api_key'),
        'wos': document.getElementById('wos_api_key'),
        'gepris': document.getElementById('gepris_api_key')
    };
    
    // Event-Listener für Validierungen hinzufügen
    Object.keys(apiKeyFields).forEach(database => {
        const field = apiKeyFields[database];
        if (field) {
            // Verzögertes Validieren beim Tippen (Debounce)
            let debounceTimer;
            field.addEventListener('input', function() {
                clearTimeout(debounceTimer);
                
                // Entferne frühere Validierungsklassen
                field.classList.remove('api-key-valid', 'api-key-invalid');
                field.classList.add('api-key-validating');
                
                // Starte verzögerte Validierung, wenn Input gestoppt hat
                debounceTimer = setTimeout(() => {
                    validateApiKey(database, field.value);
                }, 800);
            });
            
            // Initiale Validierung, wenn bereits ein Wert vorhanden ist
            if (field.value.trim() !== '') {
                validateApiKey(database, field.value);
            }
        }
    });
    
    /**
     * Validiert einen API-Key für die angegebene Datenbank.
     * 
     * @param {string} database - Name der Datenbank (pubmed, dnb, etc.)
     * @param {string} apiKey - Der zu validierende API-Key
     */
    function validateApiKey(database, apiKey) {
        // Leer-Check
        if (!apiKey || apiKey.trim() === '') {
            updateValidationStatus(database, 'empty');
            return;
        }
        
        // Validierungs-URL endpunkte
        const endpoints = {
            'pubmed': '/validate_api_key/pubmed',
            'dnb': '/validate_api_key/dnb',
            'scopus': '/validate_api_key/scopus',
            'wos': '/validate_api_key/wos',
            'gepris': '/validate_api_key/gepris'
        };
        
        // Sende Validierungsanfrage an den Server
        fetch(endpoints[database], {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ api_key: apiKey })
        })
        .then(response => response.json())
        .then(data => {
            // Aktualisiere UI basierend auf Validierungsergebnis
            updateValidationStatus(database, data.valid ? 'valid' : 'invalid', data.message);
        })
        .catch(error => {
            // Fehlerbehandlung
            console.error('API key validation error:', error);
            updateValidationStatus(database, 'error', 'Validierungsfehler, bitte versuchen Sie es später erneut.');
        });
    }
    
    /**
     * Aktualisiert die Anzeige des Validierungsstatus im UI.
     * 
     * @param {string} database - Name der Datenbank
     * @param {string} status - Status der Validierung: 'valid', 'invalid', 'empty', 'error'
     * @param {string} message - Optionale Nachricht zur Anzeige
     */
    function updateValidationStatus(database, status, message = '') {
        const field = apiKeyFields[database];
        if (!field) return;
        
        // Entferne Validierungsklassen
        field.classList.remove('api-key-validating', 'api-key-valid', 'api-key-invalid');
        
        // Finde den zugehörigen Statuscontainer
        const statusContainer = field.closest('.card-body').querySelector('.api-key-status');
        if (statusContainer) {
            statusContainer.innerHTML = '';
            statusContainer.classList.remove('valid', 'invalid');
        }
        
        // Finde den Meldungscontainer
        const messageContainer = field.closest('.card-body').querySelector('.error-message');
        if (messageContainer) {
            messageContainer.textContent = message;
            messageContainer.classList.remove('visible');
        }
        
        // Status-spezifische UI-Updates
        switch (status) {
            case 'valid':
                field.classList.add('api-key-valid');
                if (statusContainer) {
                    statusContainer.innerHTML = '<i class="fas fa-check-circle"></i>';
                    statusContainer.classList.add('valid');
                }
                break;
                
            case 'invalid':
                field.classList.add('api-key-invalid');
                if (statusContainer) {
                    statusContainer.innerHTML = '<i class="fas fa-exclamation-circle"></i>';
                    statusContainer.classList.add('invalid');
                }
                if (messageContainer && message) {
                    messageContainer.classList.add('visible');
                }
                break;
                
            case 'error':
                field.classList.add('api-key-invalid');
                if (statusContainer) {
                    statusContainer.innerHTML = '<i class="fas fa-times-circle"></i>';
                    statusContainer.classList.add('invalid');
                }
                if (messageContainer && message) {
                    messageContainer.classList.add('visible');
                }
                break;
                
            case 'empty':
                // Neutraler Zustand, keine visuellen Änderungen
                break;
        }
    }
});