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
    // let activeSearchForm = null; // activeSearchForm is not used

    // Suchformular-Handler
    searchForms.forEach(form => {
        // const initialState = new FormData(form); // initialState is not used effectively for restore

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            // activeSearchForm = this; // Not used

            if (!validateSearchForm(this)) {
                // Use global error display from base.html if available, otherwise local
                if (window.showError) window.showError(form.dataset.lastError || 'Formularvalidierung fehlgeschlagen.');
                else console.error(form.dataset.lastError || 'Formularvalidierung fehlgeschlagen.');
                return;
            }
            
            if (window.searchProgressTracker && typeof window.searchProgressTracker.start === 'function') {
                window.searchProgressTracker.start();
            }
            showLoadingState(); // Shows the #detailedSearchProgressContainer

            try {
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
                if (contentType && contentType.includes('application/json')) { // Should be HTML for search results
                    const data = await response.json(); // This path might be an error from backend
                    if (data.error) {
                        throw new Error(data.error);
                    }
                     // If backend returns JSON with a redirect URL:
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                         // Fallback or handle other JSON responses if necessary
                        document.getElementById('detailedSearchProgressContainer').innerHTML = '<div class="alert alert-info">Suche abgeschlossen, verarbeite Ergebnisse...</div>';
                        // Potentially update parts of the page with JSON data if that's the design
                    }
                } else { // Expecting HTML response
                    const html = await response.text();
                    // Check if the response is the results page or an error page
                    if (response.url.includes("/results") || !html.match(/class="alert alert-danger"|class="error-message"/i)) {
                        document.open();
                        document.write(html);
                        document.close();
                        // Force reload or re-init JS if needed after writing to document
                        // This is a full page replacement, so scripts in new page should run.
                    } else {
                        // It's likely an error page or search page with error messages
                        // Display the error within the current page structure if possible
                        // For simplicity now, still replacing content, but could be improved
                        // to inject into a specific div.
                        document.open();
                        document.write(html);
                        document.close();
                    }
                }
                if (window.searchProgressTracker && typeof window.searchProgressTracker.completeSearch === 'function') {
                    window.searchProgressTracker.completeSearch();
                }
            } catch (error) {
                console.error('Search error:', error);
                if (window.showError) window.showError(error.message || 'Ein Fehler ist bei der Suche aufgetreten');
                else alert(error.message || 'Ein Fehler ist bei der Suche aufgetreten');

                if (window.searchProgressTracker && typeof window.searchProgressTracker.handleError === 'function') {
                    window.searchProgressTracker.handleError(error);
                }
            } finally {
                // hideLoadingState() might be called too soon if page navigates.
                // searchProgressTracker.stop() is better handled by completeSearch/handleError.
            }
        });
        
        // Datenbankauswahl-Handler for specific search tab
        const specificDbSelect = document.querySelector('#specific select[name="database"]');
        if (specificDbSelect) {
            specificDbSelect.addEventListener('change', function() {
                fetchAndUpdateDynamicOptions(this.value, this.form);
            });
            // Initial population if a database is pre-selected
            if (specificDbSelect.value) {
                fetchAndUpdateDynamicOptions(specificDbSelect.value, specificDbSelect.form);
            }
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
    // Store error message in a data attribute to be picked up by caller
    form.dataset.lastError = '';
    const searchTermInput = form.querySelector('[name="search_term"]');
    const searchTerm = searchTermInput ? searchTermInput.value.trim() : '';

    const personNamesInput = form.querySelector('[name="person_names"]');
    const personNames = personNamesInput ? personNamesInput.value.trim() : '';

    const database = form.querySelector('[name="database"]')?.value;
    
    if (database === 'Combined') {
        if (!searchTerm && !personNames) { // Allow person names in combined search too
            form.dataset.lastError = 'Für die einfache Suche geben Sie bitte einen Suchbegriff oder eine Person ein.';
            return false;
        }
    } else if (database !== 'Person') { // For specific DB, not person tab
        if (!searchTerm && !personNames) {
            form.dataset.lastError = 'Bitte geben Sie mindestens einen Suchbegriff oder eine Person ein.';
            return false;
        }
    } else if (database === 'Person') { // For person tab
        const personSelector = form.querySelector('#person_selector');
        if (!personSelector || !personSelector.value) {
            form.dataset.lastError = 'Bitte wählen Sie eine Person für die personenspezifische Suche aus.';
            return false;
        }
    }
    
    if (!database) {
        form.dataset.lastError = 'Bitte wählen Sie eine Datenbank aus.';
        return false;
    }
    
    const maxResultsInput = form.querySelector('[name="max_results"]');
    if (maxResultsInput) { // Max results is not on Person tab form
        const maxResults = parseInt(maxResultsInput.value);
        if (isNaN(maxResults) || maxResults < 1 || maxResults > 10000) {
            form.dataset.lastError = 'Bitte geben Sie eine gültige Anzahl von Ergebnissen an (1-10000).';
            return false;
        }
    }
    
    return true;
}

async function fetchAndUpdateDynamicOptions(databaseName, form) {
    if (!databaseName) {
        // Clear dependent selects if no database is chosen
        populateSelect(form.querySelector('select[name="search_field"]'), [], 'Alle Felder', 'Alle Felder');
        populateSelect(form.querySelector('select[name="pub_type"]'), [], 'Alle Typen', '');
        populateSelect(form.querySelector('select[name="language"]'), [], 'Alle Sprachen', '');
        return;
    }

    const searchFieldSelect = form.querySelector('select[name="search_field"]');
    const pubTypeSelect = form.querySelector('select[name="pub_type"]');
    const languageSelect = form.querySelector('select[name="language"]');

    // Add a simple loading indicator if desired, e.g., disable selects
    if (searchFieldSelect) searchFieldSelect.disabled = true;
    if (pubTypeSelect) pubTypeSelect.disabled = true;
    if (languageSelect) languageSelect.disabled = true;
    
    try {
        const response = await fetch(`/api/database_options/${databaseName}`);
        if (!response.ok) {
            throw new Error(`Failed to fetch options: ${response.statusText}`);
        }
        const options = await response.json();

        if (searchFieldSelect) {
            populateSelect(searchFieldSelect, options.search_fields || [], 'Alle Felder', 'Alle Felder');
        }
        if (pubTypeSelect) {
            // Convert simple list to {value: item, text: item} if needed, or expect backend to provide this
            const pubTypesForSelect = options.pub_types.map(pt => (typeof pt === 'string' ? {value: pt, text: pt} : pt));
            populateSelect(pubTypeSelect, pubTypesForSelect, 'Alle Typen', '');
        }
        if (languageSelect) {
            const languagesForSelect = options.languages.map(lang => (typeof lang === 'string' ? {value: lang, text: lang} : lang));
            populateSelect(languageSelect, languagesForSelect, 'Alle Sprachen', '');
        }

    } catch (error) {
        console.error('Error updating dynamic select fields:', error);
        if(window.showError) window.showError('Fehler beim Laden der datenbankspezifischen Optionen.');
        // Optionally clear or set to default if fetch fails
        if (searchFieldSelect) populateSelect(searchFieldSelect, [], 'Alle Felder', 'Alle Felder');
        if (pubTypeSelect) populateSelect(pubTypeSelect, [], 'Alle Typen', '');
        if (languageSelect) populateSelect(languageSelect, [], 'Alle Sprachen', '');
    } finally {
        if (searchFieldSelect) searchFieldSelect.disabled = false;
        if (pubTypeSelect) pubTypeSelect.disabled = false;
        if (languageSelect) languageSelect.disabled = false;
    }
}

function populateSelect(selectElement, optionsArray, defaultOptionText, defaultOptionValue) {
    if (!selectElement) return;
    selectElement.innerHTML = ''; // Clear existing options
    
    addOption(selectElement, defaultOptionText, defaultOptionValue); // Add the "All/Default" option
    
    optionsArray.forEach(option => {
        if (typeof option === 'string') { // Simple list of strings
            addOption(selectElement, option, option);
        } else { // Assuming {value: 'val', text: 'Display Text'}
            addOption(selectElement, option.text, option.value);
        }
    });
}

function addOption(selectElement, text, value) {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = text;
    selectElement.appendChild(option);
}

function showLoadingState() {
    // This function now primarily ensures the detailedSearchProgressContainer is visible.
    // The actual progress animation and text updates are handled by SearchProgressTracker.
    const loadingContainer = document.getElementById('detailedSearchProgressContainer');
    if (loadingContainer) {
        loadingContainer.style.removeProperty('display'); // Remove potential 'display: none !important;'
        loadingContainer.style.display = 'flex'; // Show it
    }
    
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.disabled = true;
    });
    
    // Use the global escape key handler from base.html for the global indicator,
    // search_progress.js might have its own for the detailed one if needed.
}

function hideLoadingState() {
    const loadingContainer = document.getElementById('detailedSearchProgressContainer');
    if (loadingContainer) {
        // Important to use !important if the HTML has it, or ensure it's removed.
        loadingContainer.style.setProperty('display', 'none', 'important');
    }
    
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.disabled = false;
    });
}

// Removed local showError, hideError, restoreFormState as they are less robust or handled by base.html / form reset.
// Removed local progress functions (startSearchProgress, stopSearchProgress, updateProgressBar, animateProgress, updateSearchStatus)
// as these are now the responsibility of the SearchProgressTracker class in search_progress.js

// cancelSearch is specific to the detailed search progress UI, so it can remain here or move to search_progress.js
// For now, assuming search_progress.js's cancelSearch is primary if that's where the button listener is.
// If the button is in search.html and this script adds listener, it can stay.
// The current search_progress.js has its own cancelSearch. This one can be removed if redundant.
async function localCancelSearch() { // Renamed to avoid conflict if search_progress.js also has one globally
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