/**
 * MedicalSpy - Search module
 * This file contains functions for search functionality.
 */

// Show or hide additional search options
function toggleAdvancedOptions() {
    const advancedOptions = document.getElementById('advancedOptions');
    if (advancedOptions) {
        advancedOptions.classList.toggle('d-none');
    }
}

// Enable or disable search button based on query input
function validateSearchForm() {
    const searchQuery = document.getElementById('searchQuery');
    const searchButton = document.getElementById('searchButton');
    
    if (searchQuery && searchButton) {
        searchButton.disabled = !searchQuery.value.trim();
    }
}

// Show loading state during search
function setLoadingState(isLoading) {
    const searchForm = document.getElementById('searchForm');
    const searchButton = document.getElementById('searchButton');
    const searchSpinner = document.getElementById('searchSpinner');
    
    if (searchForm && searchButton && searchSpinner) {
        if (isLoading) {
            searchForm.classList.add('loading');
            searchButton.disabled = true;
            searchSpinner.classList.remove('d-none');
        } else {
            searchForm.classList.remove('loading');
            searchButton.disabled = false;
            searchSpinner.classList.add('d-none');
        }
    }
}

// Handle search form submission
function handleSearchSubmit(event) {
    // Set loading state
    setLoadingState(true);
    
    // Let the form submit normally
    return true;
}

// Save a search query
function saveSearchQuery() {
    const queryName = document.getElementById('queryName').value;
    const searchQuery = document.getElementById('searchQuery').value;
    const database = document.getElementById('database').value;
    const additionalTerms = document.getElementById('additionalTerms').value;
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const personName = document.getElementById('personSelect').value;
    
    // Validate input
    if (!queryName || !searchQuery) {
        showToast('Error', 'Query name and search query are required.', 'error');
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
        person_name: personName
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
            showToast('Success', 'Query saved successfully.', 'success');
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('saveQueryModal'));
            if (modal) {
                modal.hide();
            }
            
            // Reload the page to show the new query
            window.location.reload();
        } else {
            showToast('Error', data.message || 'Failed to save query.', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving query:', error);
        showToast('Error', 'Failed to save query. See console for details.', 'error');
    });
}

// Delete a saved query
function deleteQuery(queryIndex) {
    if (confirm('Are you sure you want to delete this query?')) {
        fetch(`/api/delete_query/${queryIndex}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Success', 'Query deleted successfully.', 'success');
                
                // Reload the page to update the list
                window.location.reload();
            } else {
                showToast('Error', data.message || 'Failed to delete query.', 'error');
            }
        })
        .catch(error => {
            console.error('Error deleting query:', error);
            showToast('Error', 'Failed to delete query. See console for details.', 'error');
        });
    }
}

// Load a saved query into the search form
function loadQuery(query) {
    document.getElementById('searchQuery').value = query.query;
    document.getElementById('database').value = query.database;
    
    if (query.additional_terms) {
        document.getElementById('additionalTerms').value = query.additional_terms;
    }
    
    if (query.start_date && query.end_date) {
        document.getElementById('startDate').value = query.start_date;
        document.getElementById('endDate').value = query.end_date;
        
        // Show advanced options
        document.getElementById('advancedOptions').classList.remove('d-none');
    }
    
    if (query.person_name) {
        document.getElementById('personSelect').value = query.person_name;
    }
    
    // Enable the search button
    validateSearchForm();
    
    // Show a toast
    showToast('Query Loaded', 'The search query has been loaded.', 'info');
}

// Show a toast notification
function showToast(title, message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
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
        showToast('Error', 'All fields are required.', 'error');
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
            showToast('Success', 'Person added successfully.', 'success');
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addPersonModal'));
            if (modal) {
                modal.hide();
            }
            
            // Reload the page to show the new person
            window.location.reload();
        } else {
            showToast('Error', data.message || 'Failed to add person.', 'error');
        }
    })
    .catch(error => {
        console.error('Error adding person:', error);
        showToast('Error', 'Failed to add person. See console for details.', 'error');
    });
}

// Initialize the search page
document.addEventListener('DOMContentLoaded', function() {
    // Initialize event listeners
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchSubmit);
    }
    
    const searchQuery = document.getElementById('searchQuery');
    if (searchQuery) {
        searchQuery.addEventListener('input', validateSearchForm);
        // Initial validation
        validateSearchForm();
    }
    
    const advancedOptionsToggle = document.getElementById('advancedOptionsToggle');
    if (advancedOptionsToggle) {
        advancedOptionsToggle.addEventListener('click', toggleAdvancedOptions);
    }
    
    const saveQueryButton = document.getElementById('saveQueryButton');
    if (saveQueryButton) {
        saveQueryButton.addEventListener('click', saveSearchQuery);
    }
    
    const addPersonButton = document.getElementById('addPersonButton');
    if (addPersonButton) {
        addPersonButton.addEventListener('click', addPerson);
    }
});
