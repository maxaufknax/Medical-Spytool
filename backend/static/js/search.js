/**
 * MedicalSpy - Search module
 * This file contains functions for search functionality.
 */

// Global variable to store all persons
let allPersons = [];

// Show loading state during search
function setLoadingState(isLoading, buttonId = 'simpleSearchButton') {
    const searchForm = document.getElementById('searchForm');
    const searchButton = document.getElementById(buttonId);
    
    if (searchForm && searchButton) {
        if (isLoading) {
            searchForm.classList.add('loading');
            searchButton.disabled = true;
            searchButton.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Suche...';
        } else {
            searchForm.classList.remove('loading');
            searchButton.disabled = false;
            searchButton.innerHTML = '<i class="fas fa-search me-1"></i> Suchen';
        }
    }
}

// Handle search form submission
function handleSearchSubmit(event) {
    // Get the active search mode
    const activeTab = document.querySelector('#searchModeTabs .nav-link.active');
    if (!activeTab) return true;
    
    // Update the search mode hidden field
    const searchModeField = document.getElementById('searchMode');
    if (searchModeField) {
        const tabId = activeTab.id;
        if (tabId === 'simple-search-tab') {
            searchModeField.value = 'simple';
            
            // Validate simple search
            const simpleQuery = document.getElementById('simpleSearchQuery').value.trim();
            if (!simpleQuery) {
                event.preventDefault();
                showToast('Fehler', 'Bitte geben Sie einen Suchbegriff ein.', 'error');
                return false;
            }
        } else if (tabId === 'database-search-tab') {
            searchModeField.value = 'database';
            
            // Validate database search
            const dbQuery = document.getElementById('databaseSearchQuery').value.trim();
            if (!dbQuery) {
                event.preventDefault();
                showToast('Fehler', 'Bitte geben Sie einen Suchbegriff ein.', 'error');
                return false;
            }
        } else if (tabId === 'person-search-tab') {
            searchModeField.value = 'person';
            
            // Validate person search
            const selectedPersonIds = document.getElementById('selectedPersonIds').value;
            if (!selectedPersonIds) {
                event.preventDefault();
                showToast('Fehler', 'Bitte wählen Sie mindestens eine Person aus.', 'error');
                return false;
            }
        }
    }
    
    // Set loading state based on active tab
    const buttonMap = {
        'simple-search-tab': 'simpleSearchButton',
        'database-search-tab': 'databaseSearchButton',
        'person-search-tab': 'personSearchSubmitButton'
    };
    setLoadingState(true, buttonMap[activeTab.id]);
    
    // Let the form submit normally
    return true;
}

// Save a search query
function saveSearchQuery() {
    const queryName = document.getElementById('queryName').value;
    
    // Determine which search mode is active
    const activeTab = document.querySelector('#searchModeTabs .nav-link.active');
    if (!activeTab) {
        showToast('Fehler', 'Keine aktive Suchansicht gefunden.', 'error');
        return;
    }
    
    let searchQuery, database, additionalTerms, startDate, endDate, personName;
    
    // Get values based on active tab
    if (activeTab.id === 'simple-search-tab') {
        searchQuery = document.getElementById('simpleSearchQuery').value;
        database = document.getElementById('simpleDatabase').value;
        additionalTerms = '';
        startDate = '';
        endDate = '';
        personName = '';
    } else if (activeTab.id === 'database-search-tab') {
        searchQuery = document.getElementById('databaseSearchQuery').value;
        database = document.getElementById('databaseSelect').value;
        additionalTerms = document.getElementById('dbAdditionalTerms').value;
        startDate = document.getElementById('dbStartDate').value;
        endDate = document.getElementById('dbEndDate').value;
        personName = document.getElementById('dbPersonSelect').value;
    } else if (activeTab.id === 'person-search-tab') {
        // For person search, combine selected person names into query
        searchQuery = '';  // Will be built from selected persons on the server
        database = document.getElementById('personDatabase').value;
        additionalTerms = document.getElementById('personAdditionalTerms').value;
        startDate = document.getElementById('personStartDate').value;
        endDate = document.getElementById('personEndDate').value;
        personName = document.getElementById('selectedPersonIds').value;
    }
    
    // Validate input
    if (!queryName) {
        showToast('Fehler', 'Bitte geben Sie einen Namen für diese Suche ein.', 'error');
        return;
    }
    
    // Create request data
    const data = {
        query_name: queryName,
        search_query: searchQuery,
        database: database,
        additional_terms: additionalTerms,
        start_date: startDate,
        end_date: endDate,
        person_name: personName,
        search_mode: document.getElementById('searchMode').value
    };
    
    // Send the request
    fetch('/api/save_query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showToast('Erfolg', 'Suche erfolgreich gespeichert.', 'success');
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('saveQueryModal'));
            if (modal) {
                modal.hide();
            }
            
            // Reload the page to show the new query
            window.location.reload();
        } else {
            showToast('Fehler', data.message || 'Fehler beim Speichern der Suche.', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving query:', error);
        showToast('Fehler', 'Fehler beim Speichern der Suche. Siehe Konsole für Details.', 'error');
    });
}

// Delete a saved query
function deleteQuery(queryId) {
    if (confirm('Sind Sie sicher, dass Sie diese Suche löschen möchten?')) {
        fetch(`/api/delete_query/${queryId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Erfolg', 'Suche erfolgreich gelöscht.', 'success');
                
                // Reload the page to update the list
                window.location.reload();
            } else {
                showToast('Fehler', data.message || 'Fehler beim Löschen der Suche.', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting query:', error);
            showToast('Fehler', 'Fehler beim Löschen der Suche. Siehe Konsole für Details.', 'error');
        });
    }
}

// Load a saved query into the search form
function loadQuery(query) {
    // Determine which tab to activate based on search mode
    let tabId;
    if (query.search_mode === 'simple') {
        tabId = 'simple-search-tab';
    } else if (query.search_mode === 'database') {
        tabId = 'database-search-tab';
    } else if (query.search_mode === 'person') {
        tabId = 'person-search-tab';
    } else {
        // Default to simple search if mode is not recognized
        tabId = 'simple-search-tab';
    }
    
    // Activate the appropriate tab
    const tab = document.getElementById(tabId);
    if (tab) {
        const tabInstance = new bootstrap.Tab(tab);
        tabInstance.show();
    }
    
    // Fill in the form fields based on search mode
    if (query.search_mode === 'simple') {
        if (document.getElementById('simpleSearchQuery')) {
            document.getElementById('simpleSearchQuery').value = query.query || '';
        }
        if (document.getElementById('simpleDatabase')) {
            document.getElementById('simpleDatabase').value = query.database || '';
        }
    } else if (query.search_mode === 'database') {
        if (document.getElementById('databaseSearchQuery')) {
            document.getElementById('databaseSearchQuery').value = query.query || '';
        }
        if (document.getElementById('databaseSelect')) {
            document.getElementById('databaseSelect').value = query.database || '';
        }
        if (document.getElementById('dbAdditionalTerms')) {
            document.getElementById('dbAdditionalTerms').value = query.additional_terms || '';
        }
        if (document.getElementById('dbStartDate')) {
            document.getElementById('dbStartDate').value = query.start_date || '';
        }
        if (document.getElementById('dbEndDate')) {
            document.getElementById('dbEndDate').value = query.end_date || '';
        }
        if (document.getElementById('dbPersonSelect')) {
            document.getElementById('dbPersonSelect').value = query.person_name || '';
        }
    } else if (query.search_mode === 'person') {
        if (document.getElementById('personDatabase')) {
            document.getElementById('personDatabase').value = query.database || '';
        }
        if (document.getElementById('personAdditionalTerms')) {
            document.getElementById('personAdditionalTerms').value = query.additional_terms || '';
        }
        if (document.getElementById('personStartDate')) {
            document.getElementById('personStartDate').value = query.start_date || '';
        }
        if (document.getElementById('personEndDate')) {
            document.getElementById('personEndDate').value = query.end_date || '';
        }
        
        // Handle selected persons
        if (query.person_name) {
            const personIds = query.person_name.split(',');
            document.getElementById('selectedPersonIds').value = query.person_name;
            
            // Try to load the person names and display them as tags
            updateSelectedPersonsDisplay();
        }
    }
    
    // Update the search mode hidden field
    document.getElementById('searchMode').value = query.search_mode || 'simple';
    
    // Show a toast
    showToast('Suche geladen', 'Die gespeicherte Suche wurde geladen.', 'info');
}

// Show a toast notification
function showToast(title, message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1050';
        document.body.appendChild(toastContainer);
    }
    
    // Create the toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    // Create the toast content
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong>: ${message}
            </div>
            <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add the toast to the container
    toastContainer.appendChild(toast);
    
    // Initialize and show the toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();
    
    // Remove the toast when hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// Add a new person
function addPerson() {
    const name = document.getElementById('personName').value;
    const firstName = document.getElementById('personFirstName').value;
    const lastName = document.getElementById('personLastName').value;
    
    // Validate input
    if (!name || !firstName || !lastName) {
        showToast('Fehler', 'Alle Felder sind erforderlich.', 'error');
        return;
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('action', 'add');
    formData.append('name', name);
    formData.append('first_name', firstName);
    formData.append('last_name', lastName);
    
    // Send the request
    fetch('/api/manage_persons', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            showToast('Erfolg', 'Person erfolgreich hinzugefügt.', 'success');
            
            // Add the new person to the allPersons array
            if (data.person) {
                allPersons.push(data.person);
            }
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addPersonModal'));
            if (modal) {
                modal.hide();
            }
            
            // Reload the page to show the new person
            window.location.reload();
        } else {
            showToast('Fehler', data.message || 'Fehler beim Hinzufügen der Person.', 'error');
        }
    })
    .catch(error => {
        console.error('Error adding person:', error);
        showToast('Fehler', 'Fehler beim Hinzufügen der Person. Siehe Konsole für Details.', 'error');
    });
}

// Handle person search input
function handlePersonSearch() {
    const input = document.getElementById('personSearchInput');
    const results = document.getElementById('personSearchResults');
    
    if (!input || !results) return;
    
    const searchTerm = input.value.trim().toLowerCase();
    
    // Clear previous results
    results.innerHTML = '';
    
    if (searchTerm.length < 2) {
        results.style.display = 'none';
        return;
    }
    
    // Filter persons
    const matches = allPersons.filter(person => {
        return person.name.toLowerCase().includes(searchTerm) ||
               person.first_name.toLowerCase().includes(searchTerm) ||
               person.last_name.toLowerCase().includes(searchTerm);
    });
    
    // Generate results HTML
    if (matches.length > 0) {
        matches.forEach(person => {
            const item = document.createElement('a');
            item.className = 'dropdown-item';
            item.href = '#';
            item.innerHTML = `
                <strong>${person.name}</strong>
                <small class="d-block text-muted">${person.first_name} ${person.last_name}</small>
            `;
            
            // Add person selection handler
            item.addEventListener('click', (e) => {
                e.preventDefault();
                selectPerson(person);
                input.value = '';
                results.style.display = 'none';
            });
            
            results.appendChild(item);
        });
        
        results.style.display = 'block';
    } else {
        const noResults = document.createElement('div');
        noResults.className = 'dropdown-item disabled';
        noResults.textContent = 'Keine Personen gefunden';
        results.appendChild(noResults);
        results.style.display = 'block';
    }
}

// Select a person for the search
function selectPerson(person) {
    // Get the hidden input for selected person IDs
    const selectedPersonIds = document.getElementById('selectedPersonIds');
    const selectedPersonsContainer = document.getElementById('selectedPersonsContainer');
    
    if (!selectedPersonIds || !selectedPersonsContainer) return;
    
    // Get current selected IDs
    const currentIds = selectedPersonIds.value ? selectedPersonIds.value.split(',') : [];
    
    // Add the new ID if not already selected
    if (!currentIds.includes(person.id.toString())) {
        currentIds.push(person.id.toString());
        selectedPersonIds.value = currentIds.join(',');
        
        // Update the display
        updateSelectedPersonsDisplay();
    }
}

// Update the display of selected persons
function updateSelectedPersonsDisplay() {
    const selectedPersonIds = document.getElementById('selectedPersonIds');
    const selectedPersonsContainer = document.getElementById('selectedPersonsContainer');
    const noPersonsSelectedAlert = document.getElementById('noPersonsSelectedAlert');
    
    if (!selectedPersonIds || !selectedPersonsContainer) return;
    
    // Get current selected IDs
    const currentIds = selectedPersonIds.value ? selectedPersonIds.value.split(',') : [];
    
    // Clear the container except for the alert
    const tags = selectedPersonsContainer.querySelectorAll('.badge');
    tags.forEach(tag => tag.remove());
    
    // Show or hide the "no persons" alert
    if (noPersonsSelectedAlert) {
        noPersonsSelectedAlert.style.display = currentIds.length > 0 ? 'none' : 'block';
    }
    
    // Add tags for each selected person
    currentIds.forEach(id => {
        const person = allPersons.find(p => p.id.toString() === id);
        if (person) {
            const tag = document.createElement('span');
            tag.className = 'badge bg-primary me-2 mb-2';
            tag.innerHTML = `
                ${person.name}
                <button type="button" class="btn-close btn-close-white ms-2" aria-label="Remove" 
                    onclick="removePerson(${person.id})"></button>
            `;
            
            // Insert the tag before the alert
            if (noPersonsSelectedAlert) {
                selectedPersonsContainer.insertBefore(tag, noPersonsSelectedAlert);
            } else {
                selectedPersonsContainer.appendChild(tag);
            }
        }
    });
}

// Remove a person from the selected list
function removePerson(personId) {
    // Get the hidden input for selected person IDs
    const selectedPersonIds = document.getElementById('selectedPersonIds');
    
    if (!selectedPersonIds) return;
    
    // Get current selected IDs
    const currentIds = selectedPersonIds.value ? selectedPersonIds.value.split(',') : [];
    
    // Remove the ID
    const updatedIds = currentIds.filter(id => id !== personId.toString());
    selectedPersonIds.value = updatedIds.join(',');
    
    // Update the display
    updateSelectedPersonsDisplay();
}

// Load all persons
function loadAllPersons() {
    // This function now assumes that the persons are already loaded in the HTML
    allPersons = [];
    
    // Check if persons are available in the DOM
    const personElements = document.querySelectorAll('#persons-list .list-group-item[data-id]');
    
    if (personElements.length > 0) {
        personElements.forEach(element => {
            const id = element.dataset.id;
            const name = element.dataset.name;
            const firstName = element.dataset.firstName;
            const lastName = element.dataset.lastName;
            
            allPersons.push({
                id: id,
                name: name,
                first_name: firstName,
                last_name: lastName
            });
        });
    } else {
        // Fall back to extracting from the person selection dropdown
        const personSelect = document.getElementById('dbPersonSelect');
        if (personSelect) {
            const options = personSelect.querySelectorAll('option:not([value=""])');
            options.forEach(option => {
                if (option.dataset.id) {
                    allPersons.push({
                        id: option.dataset.id,
                        name: option.textContent,
                        first_name: option.dataset.firstName || '',
                        last_name: option.dataset.lastName || ''
                    });
                }
            });
        }
    }
    
    console.log('Loaded', allPersons.length, 'persons');
}

// Handle search mode tab changes
function handleSearchModeChange(event) {
    // Update the search mode hidden field
    const searchModeField = document.getElementById('searchMode');
    if (!searchModeField) return;
    
    // Get the target tab ID
    const tabId = event.target.id;
    
    // Update the search mode
    if (tabId === 'simple-search-tab') {
        searchModeField.value = 'simple';
    } else if (tabId === 'advanced-search-tab') {
        searchModeField.value = 'advanced';
        // Show/hide database-specific filters based on selected database
        updateDatabaseSpecificFilters();
    } else if (tabId === 'person-search-tab') {
        searchModeField.value = 'person';
    }
}

// Function to update database-specific filters based on selected database
function updateDatabaseSpecificFilters() {
    const selectedDatabase = document.getElementById('advancedDatabaseSelect').value;
    const pubmedFilters = document.getElementById('pubmed-specific-filters');
    const dnbFilters = document.getElementById('dnb-specific-filters');
    
    if (selectedDatabase === 'PubMed') {
        pubmedFilters.style.display = 'block';
        dnbFilters.style.display = 'none';
    } else if (selectedDatabase === 'DNB') {
        pubmedFilters.style.display = 'none';
        dnbFilters.style.display = 'block';
    } else {
        // Hide all database-specific filters for other databases
        pubmedFilters.style.display = 'none';
        dnbFilters.style.display = 'none';
    }
}

// Initialize the search page
document.addEventListener('DOMContentLoaded', function() {
    // Load all persons
    loadAllPersons();
    
    // Initialize event listeners for search form
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }
    
    // Search mode tabs
    const searchModeTabs = document.querySelectorAll('#searchModeTabs .nav-link');
    searchModeTabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', handleSearchModeChange);
    });
    
    // Person search input
    const personSearchInput = document.getElementById('personSearchInput');
    if (personSearchInput) {
        personSearchInput.addEventListener('input', handlePersonSearch);
        
        // Hide search results when clicking outside
        document.addEventListener('click', function(event) {
            const results = document.getElementById('personSearchResults');
            if (results && !personSearchInput.contains(event.target) && !results.contains(event.target)) {
                results.style.display = 'none';
            }
        });
    }
    
    // Person search button
    const personSearchButton = document.getElementById('personSearchButton');
    if (personSearchButton) {
        personSearchButton.addEventListener('click', handlePersonSearch);
    }
    
    // Save query button
    const saveQueryButton = document.getElementById('saveQueryButton');
    if (saveQueryButton) {
        saveQueryButton.addEventListener('click', saveSearchQuery);
    }
    
    // Add person button
    const addPersonButton = document.getElementById('addPersonButton');
    if (addPersonButton) {
        addPersonButton.addEventListener('click', addPerson);
    }
    
    // Add click event to person list items
    const personsList = document.getElementById('persons-list');
    if (personsList) {
        const personItems = personsList.querySelectorAll('.list-group-item');
        personItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const personId = this.dataset.id;
                const personName = this.dataset.name;
                const personFirstName = this.dataset.firstName;
                const personLastName = this.dataset.lastName;
                
                if (personId) {
                    selectPerson({
                        id: personId,
                        name: personName,
                        first_name: personFirstName,
                        last_name: personLastName
                    });
                }
            });
        });
    }
    
    // Advanced person search input
    const advancedPersonSearchInput = document.getElementById('advancedPersonSearchInput');
    if (advancedPersonSearchInput) {
        advancedPersonSearchInput.addEventListener('input', function() {
            handleAdvancedPersonSearch();
        });
        
        // Hide search results when clicking outside
        document.addEventListener('click', function(event) {
            const results = document.getElementById('advancedPersonSearchResults');
            if (results && !advancedPersonSearchInput.contains(event.target) && !results.contains(event.target)) {
                results.style.display = 'none';
            }
        });
    }
    
    // Advanced person search button
    const advancedPersonSearchButton = document.getElementById('advancedPersonSearchButton');
    if (advancedPersonSearchButton) {
        advancedPersonSearchButton.addEventListener('click', function() {
            handleAdvancedPersonSearch();
        });
    }
    
    // Database selection change in advanced mode
    const advancedDatabaseSelect = document.getElementById('advancedDatabaseSelect');
    if (advancedDatabaseSelect) {
        advancedDatabaseSelect.addEventListener('change', updateDatabaseSpecificFilters);
        // Initialize filter visibility on page load
        updateDatabaseSpecificFilters();
    }
    
    // Initialize person selectors
    updateSelectedPersonsDisplay();
    
    // Enable tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Handle advanced person search input
function handleAdvancedPersonSearch() {
    const input = document.getElementById('advancedPersonSearchInput');
    const results = document.getElementById('advancedPersonSearchResults');
    
    if (!input || !results) return;
    
    const searchTerm = input.value.trim().toLowerCase();
    
    // Clear previous results
    results.innerHTML = '';
    
    if (searchTerm.length < 2) {
        results.style.display = 'none';
        return;
    }
    
    // Filter persons
    const matches = allPersons.filter(person => {
        return person.name.toLowerCase().includes(searchTerm) ||
            person.first_name.toLowerCase().includes(searchTerm) ||
            person.last_name.toLowerCase().includes(searchTerm);
    });
    
    if (matches.length === 0) {
        results.innerHTML = '<div class="dropdown-item text-muted">Keine Ergebnisse gefunden</div>';
    } else {
        matches.forEach(person => {
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'dropdown-item';
            item.textContent = `${person.name} (${person.first_name} ${person.last_name})`;
            
            item.addEventListener('click', function(e) {
                e.preventDefault();
                selectAdvancedPerson(person);
                input.value = '';
                results.style.display = 'none';
            });
            
            results.appendChild(item);
        });
    }
    
    results.style.display = 'block';
}

// Handle selection of a person in advanced search mode
function selectAdvancedPerson(person) {
    // Add to selected persons list if not already there
    const selectedPersons = getSelectedAdvancedPersons();
    
    // Check if already selected
    if (selectedPersons.find(p => p.id === person.id)) {
        return; // Already selected
    }
    
    // Add to list
    selectedPersons.push(person);
    
    // Update the hidden input
    document.getElementById('advancedSelectedPersonIds').value = JSON.stringify(selectedPersons.map(p => p.id));
    
    // Update display
    updateAdvancedSelectedPersonsDisplay();
}

// Get list of currently selected persons in advanced search
function getSelectedAdvancedPersons() {
    const idsField = document.getElementById('advancedSelectedPersonIds');
    
    if (idsField && idsField.value) {
        try {
            const ids = JSON.parse(idsField.value);
            return ids.map(id => {
                return allPersons.find(p => p.id == id); // Use loose equality to handle numeric/string IDs
            }).filter(p => p); // Filter out any undefined entries
        } catch (e) {
            console.error('Error parsing selected person IDs:', e);
            return [];
        }
    }
    
    return [];
}

// Update the display of selected persons in advanced search
function updateAdvancedSelectedPersonsDisplay() {
    const container = document.getElementById('advancedSelectedPersonsContainer');
    const noPersonsAlert = document.getElementById('advancedNoPersonsSelectedAlert');
    
    if (!container) return;
    
    const selectedPersons = getSelectedAdvancedPersons();
    
    // Clear existing tags (except the alert)
    Array.from(container.children).forEach(child => {
        if (child !== noPersonsAlert) {
            container.removeChild(child);
        }
    });
    
    // Show/hide the "no persons" alert
    if (noPersonsAlert) {
        noPersonsAlert.style.display = selectedPersons.length ? 'none' : 'block';
    }
    
    // Add tags for each selected person
    selectedPersons.forEach(person => {
        const tag = document.createElement('div');
        tag.className = 'badge bg-primary me-2 mb-2 p-2';
        tag.innerHTML = `
            ${person.name}
            <button type="button" class="btn-close btn-close-white ms-2" aria-label="Remove" 
                   data-id="${person.id}" style="font-size: 0.5rem;"></button>
        `;
        
        // Add event listener to remove button
        tag.querySelector('.btn-close').addEventListener('click', function() {
            removeAdvancedPerson(this.dataset.id);
        });
        
        container.appendChild(tag);
    });
}

// Remove a person from the advanced search selection
function removeAdvancedPerson(personId) {
    let selectedPersons = getSelectedAdvancedPersons();
    
    // Remove the person with matching ID
    selectedPersons = selectedPersons.filter(p => p.id != personId); // Use loose equality
    
    // Update the hidden input
    document.getElementById('advancedSelectedPersonIds').value = JSON.stringify(selectedPersons.map(p => p.id));
    
    // Update display
    updateAdvancedSelectedPersonsDisplay();
}
