/**
 * Search functionality handler for MedicalSpyTool
 */
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    
    // Event Listener für das Datumsfilter-Kontrollkästchen
    const dateFilterCheckbox = document.getElementById('use_date_filter');
    const dateFilterSection = document.getElementById('dateFilterSection');
    
    if (dateFilterCheckbox && dateFilterSection) {
        dateFilterCheckbox.addEventListener('change', function() {
            if (this.checked) {
                dateFilterSection.style.display = 'flex';
            } else {
                dateFilterSection.style.display = 'none';
            }
        });
    }
});

let searchProgress = {
    currentProgress: 0,
    isSearching: false,
    currentDatabase: '',
    searchLog: []
};

function initializeSearch() {
    const searchForms = document.querySelectorAll('form[data-search-form]');
    let activeSearchForm = null;
    
    // Suchformular-Handler
    searchForms.forEach(form => {
        const initialState = new FormData(form);
        
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            activeSearchForm = this;
            
            // Validiere Formulardaten
            if (!validateSearchForm(this)) {
                return;
            }
            
            try {
                // Zeige Ladezustand
                showLoadingState();
                startSearchProgress();
                
                // Sende Formular
                const formData = new FormData(this);
                const response = await fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const data = await response.json();
                    if (data.error) {
                        throw new Error(data.error);
                    }
                    // Erfolgreich - zur Ergebnisseite weiterleiten
                    window.location.href = '/results';
                } else {
                    const html = await response.text();
                    if (html.includes('error-message') || html.includes('alert-danger')) {
                        // Fehler in der Antwort
                        document.documentElement.innerHTML = html;
                        restoreFormState(initialState);
                    } else {
                        // Erfolg - Seiteninhalt ersetzen
                        document.documentElement.innerHTML = html;
                    }
                }
            } catch (error) {
                console.error('Search error:', error);
                showError(error.message || 'Ein Fehler ist bei der Suche aufgetreten');
                restoreFormState(initialState);
            } finally {
                hideLoadingState();
                stopSearchProgress();
            }
        });
        
        // Datenbankauswahl-Handler
        const databaseSelect = form.querySelector('select[name="database"]');
        if (databaseSelect) {
            databaseSelect.addEventListener('change', function() {
                updateSearchFields(this.value, form);
            });
            updateSearchFields(databaseSelect.value, form);
        }
    });
    
    // Tab-Wechsel-Handler
    const searchTabs = document.querySelectorAll('button[data-bs-toggle="tab"]');
    searchTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(e) {
            hideError();
            sessionStorage.setItem('activeSearchTab', e.target.id);
        });
    });
    
    // Aktiven Tab wiederherstellen
    const activeTab = sessionStorage.getItem('activeSearchTab');
    if (activeTab) {
        const tab = document.getElementById(activeTab);
        if (tab) {
            const bsTab = new bootstrap.Tab(tab);
            bsTab.show();
        }
    }
}

function validateSearchForm(form) {
    const searchTerm = form.querySelector('[name="search_term"]')?.value.trim();
    const personNames = form.querySelector('[name="person_names"]')?.value.trim();
    const database = form.querySelector('[name="database"]')?.value;
    
    // For Combined search (Einfache Suche), only search term is required
    if (database === 'Combined') {
        if (!searchTerm) {
            showError('Bitte geben Sie einen Suchbegriff ein.');
            return false;
        }
    } else {
        // For other searches, require either search term or person names
        if (!searchTerm && !personNames) {
            showError('Bitte geben Sie mindestens einen Suchbegriff oder eine Person ein.');
            return false;
        }
    }
    
    if (!database) {
        showError('Bitte wählen Sie eine Datenbank aus.');
        return false;
    }
    
    const maxResults = parseInt(form.querySelector('[name="max_results"]')?.value);
    if (isNaN(maxResults) || maxResults < 1 || maxResults > 10000) {
        showError('Bitte geben Sie eine gültige Anzahl von Ergebnissen an (1-10000).');
        return false;
    }
    
    return true;
}

function updateSearchFields(database, form) {
    const searchFieldSelect = form.querySelector('select[name="search_field"]');
    if (!searchFieldSelect) return;
    
    searchFieldSelect.innerHTML = '';
    addOption(searchFieldSelect, 'Alle Felder', 'Alle Felder');
    
    const fields = getDatabaseFields(database);
    fields.forEach(field => {
        addOption(searchFieldSelect, field, field);
    });
    
    updateDatabaseSpecificElements(database, form);
}

function getDatabaseFields(database) {
    const fieldMap = {
        'PubMed': [
            'Titel', 'Autor', 'Abstract', 'Journal', 'DOI', 'PMID', 'Affiliation'
        ],
        'DNB': [
            'Titel', 'Autor', 'Schlagwort', 'ISBN', 'Verlag', 'Erscheinungsort'
        ],
        'Scopus': [
            'Titel', 'Autor', 'Abstract', 'Keywords', 'DOI', 'ISSN'
        ],
        'WoS': [
            'Titel', 'Autor', 'Topic', 'Publication Name', 'DOI'
        ],
        'GEPRIS': [
            'Projekttitel', 'Institution', 'Person', 'Fach'
        ]
    };
    
    return fieldMap[database] || [];
}

function updateDatabaseSpecificElements(database, form) {
    const pubTypeSelect = form.querySelector('select[name="pub_type"]');
    const languageSelect = form.querySelector('select[name="language"]');
    
    if (pubTypeSelect) {
        pubTypeSelect.innerHTML = '';
        addOption(pubTypeSelect, 'Alle Typen', '');
        
        const types = getDatabasePubTypes(database);
        types.forEach(type => {
            addOption(pubTypeSelect, type.text, type.value);
        });
    }
    
    if (languageSelect) {
        updateLanguageOptions(database, languageSelect);
    }
}

function getDatabasePubTypes(database) {
    const typeMap = {
        'PubMed': [
            {value: 'Journal Article', text: 'Journalartikel'},
            {value: 'Review', text: 'Review'},
            {value: 'Clinical Trial', text: 'Klinische Studie'},
            {value: 'Meta-Analysis', text: 'Meta-Analyse'},
            {value: 'Practice Guideline', text: 'Praxisleitlinie'}
        ],
        'DNB': [
            {value: 'Book', text: 'Buch'},
            {value: 'Article', text: 'Artikel'},
            {value: 'Thesis', text: 'Dissertation'},
            {value: 'Conference', text: 'Konferenzband'}
        ],
        'Scopus': [
            {value: 'Article', text: 'Artikel'},
            {value: 'Review', text: 'Review'},
            {value: 'Conference Paper', text: 'Konferenzbeitrag'},
            {value: 'Book Chapter', text: 'Buchkapitel'}
        ],
        'WoS': [
            {value: 'Article', text: 'Artikel'},
            {value: 'Review', text: 'Review'},
            {value: 'Proceedings Paper', text: 'Konferenzbeitrag'},
            {value: 'Book Chapter', text: 'Buchkapitel'}
        ],
        'GEPRIS': [
            {value: 'Project', text: 'Projekt'},
            {value: 'Institution', text: 'Institution'},
            {value: 'Person', text: 'Person'}
        ]
    };
    
    return typeMap[database] || [];
}

function updateLanguageOptions(database, select) {
    select.innerHTML = '';
    addOption(select, 'Alle Sprachen', '');
    
    const languages = [
        {value: 'German', text: 'Deutsch'},
        {value: 'English', text: 'Englisch'},
        {value: 'French', text: 'Französisch'},
        {value: 'Spanish', text: 'Spanisch'}
    ];
    
    if (database === 'DNB') {
        languages.push(
            {value: 'Italian', text: 'Italienisch'},
            {value: 'Latin', text: 'Latein'}
        );
    }
    
    languages.forEach(lang => {
        addOption(select, lang.text, lang.value);
    });
}

function addOption(select, text, value) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = text;
    select.appendChild(option);
}

function showLoadingState() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.removeProperty('display');
        loadingIndicator.style.display = 'flex';
    }
    
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.disabled = true;
    });
    
    document.addEventListener('keydown', handleEscapeKey);
}

function hideLoadingState() {
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.setProperty('display', 'none', 'important');
    }
    
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.disabled = false;
    });
    
    document.removeEventListener('keydown', handleEscapeKey);
}

function handleEscapeKey(event) {
    if (event.key === 'Escape') {
        hideLoadingState();
        stopSearchProgress();
    }
}

function showError(message) {
    const errorContainer = document.createElement('div');
    errorContainer.className = 'alert alert-danger alert-dismissible fade show';
    errorContainer.innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(errorContainer, container.firstChild);
    }
}

function hideError() {
    const errorAlert = document.querySelector('.alert-danger');
    if (errorAlert) {
        errorAlert.remove();
    }
}

function restoreFormState(formData) {
    if (!formData) return;
    
    const form = document.querySelector('form[data-search-form]');
    if (!form) return;
    
    for (const [key, value] of formData.entries()) {
        const input = form.querySelector(`[name="${key}"]`);
        if (input) {
            if (input.type === 'checkbox') {
                input.checked = value === 'on';
            } else {
                input.value = value;
            }
        }
    }
}

function startSearchProgress() {
    searchProgress.isSearching = true;
    searchProgress.currentProgress = 0;
    searchProgress.searchLog = [];
    updateProgressBar(0);
    
    // Initialisiere UI-Elemente
    const detailsPanel = document.getElementById('searchDetailsPanel');
    const toggleBtn = document.getElementById('toggleSearchDetails');
    const cancelBtn = document.getElementById('cancelSearch');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            const collapse = new bootstrap.Collapse(detailsPanel);
            this.querySelector('i').classList.toggle('fa-chevron-down');
            this.querySelector('i').classList.toggle('fa-chevron-up');
        });
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', cancelSearch);
    }
    
    // Starte Fortschrittsanimation
    animateProgress();
}

function stopSearchProgress() {
    searchProgress.isSearching = false;
    updateProgressBar(100);
}

function updateProgressBar(progress) {
    const progressBar = document.getElementById('searchProgressBar');
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${Math.round(progress)}%`;
    }
}

function animateProgress() {
    if (!searchProgress.isSearching) return;
    
    // Simuliere Fortschritt basierend auf aktuellem Stand
    const increment = Math.random() * 15;
    const newProgress = Math.min(searchProgress.currentProgress + increment, 90);
    searchProgress.currentProgress = newProgress;
    
    updateProgressBar(newProgress);
    
    // Fortschrittsanimation fortsetzen
    if (searchProgress.isSearching) {
        setTimeout(animateProgress, 500 + Math.random() * 1000);
    }
}

function updateSearchStatus(database, message) {
    const statusElement = document.getElementById('currentDatabaseStatus');
    const logElement = document.getElementById('searchLog');
    
    if (statusElement) {
        statusElement.textContent = `Durchsuche ${database}...`;
    }
    
    if (logElement && message) {
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <span class="text-muted">[${new Date().toLocaleTimeString()}]</span>
            <span class="ms-2">${message}</span>
        `;
        logElement.appendChild(logEntry);
        logElement.scrollTop = logElement.scrollHeight;
    }
}

async function cancelSearch() {
    try {
        const response = await fetch('/cancel_search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (!response.ok) {
            throw new Error('Fehler beim Abbrechen der Suche');
        }
        
        stopSearchProgress();
        hideLoadingState();
        showError('Suche wurde abgebrochen');
    } catch (error) {
        console.error('Error canceling search:', error);
        showError('Fehler beim Abbrechen der Suche');
    }
}