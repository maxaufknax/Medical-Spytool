/**
 * Advanced filtering functionality for search results 
 * This script enhances the basic filtering with more advanced options
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeAdvancedFilters();
});

/**
 * Initialize all advanced filtering functions
 */
function initializeAdvancedFilters() {
    // Basic text filter (enhancing existing functionality)
    setupBasicFilter();
    
    // Advanced filters
    setupDateRangeFilter();
    setupDatabaseFilter();
    setupPublicationTypeFilter();
    setupAuthorFilter();
    setupYearFilter();
    
    // Filter persistence
    restoreFilterState();
    setupFilterPersistence();
    
    // Reset all filters button
    setupResetFilters();
}

/**
 * Set up the basic text filter with enhanced capabilities
 */
function setupBasicFilter() {
    const filterInput = document.getElementById('resultFilterInput');
    const clearFilterButton = document.getElementById('clearFilterButton');
    const resultsTable = document.getElementById('resultsTable');
    
    if (filterInput && resultsTable) {
        // Enhanced filter that searches in specific fields with better accuracy
        filterInput.addEventListener('input', function() {
            applyFilters();
        });
        
        // Clear filter button
        if (clearFilterButton) {
            clearFilterButton.addEventListener('click', function() {
                filterInput.value = '';
                applyFilters();
            });
        }
    }
}

/**
 * Set up the publication year range filter
 */
function setupYearFilter() {
    const yearFilterContainer = document.getElementById('yearFilterContainer');
    if (!yearFilterContainer) return;
    
    // Create filter elements if they don't exist
    if (!document.getElementById('yearFilterMin') || !document.getElementById('yearFilterMax')) {
        // Extract all years from the table
        const years = extractYearsFromTable();
        if (years.length === 0) return;
        
        const minYear = Math.min(...years);
        const maxYear = Math.max(...years);
        
        // Create year filter inputs
        const filterHTML = `
            <div class="input-group input-group-sm mb-2">
                <span class="input-group-text">Jahr von</span>
                <input type="number" class="form-control" id="yearFilterMin" min="${minYear}" max="${maxYear}" value="${minYear}">
                <span class="input-group-text">bis</span>
                <input type="number" class="form-control" id="yearFilterMax" min="${minYear}" max="${maxYear}" value="${maxYear}">
            </div>
        `;
        
        yearFilterContainer.innerHTML = filterHTML;
        
        // Add event listeners
        const yearFilterMin = document.getElementById('yearFilterMin');
        const yearFilterMax = document.getElementById('yearFilterMax');
        
        yearFilterMin.addEventListener('change', applyFilters);
        yearFilterMax.addEventListener('change', applyFilters);
    }
}

/**
 * Set up the database filter
 */
function setupDatabaseFilter() {
    const databaseFilterContainer = document.getElementById('databaseFilterContainer');
    if (!databaseFilterContainer) return;
    
    // Create filter elements if they don't exist
    if (!document.getElementById('databaseFilterSelect')) {
        // Extract all databases from the table
        const databases = extractDatabasesFromTable();
        if (databases.length === 0) return;
        
        // Create database filter select
        let filterHTML = `
            <select class="form-select form-select-sm" id="databaseFilterSelect">
                <option value="">Alle Datenbanken</option>
        `;
        
        databases.forEach(database => {
            filterHTML += `<option value="${database}">${database}</option>`;
        });
        
        filterHTML += `</select>`;
        
        databaseFilterContainer.innerHTML = filterHTML;
        
        // Add event listener
        const databaseFilterSelect = document.getElementById('databaseFilterSelect');
        databaseFilterSelect.addEventListener('change', applyFilters);
    }
}

/**
 * Set up the publication type filter
 */
function setupPublicationTypeFilter() {
    const pubTypeFilterContainer = document.getElementById('pubTypeFilterContainer');
    if (!pubTypeFilterContainer) return;
    
    // Create filter elements if they don't exist
    if (!document.getElementById('pubTypeFilterSelect')) {
        // Extract all publication types from the table
        const pubTypes = extractPublicationTypesFromTable();
        if (pubTypes.length === 0) return;
        
        // Create publication type filter select
        let filterHTML = `
            <select class="form-select form-select-sm" id="pubTypeFilterSelect">
                <option value="">Alle Publikationstypen</option>
        `;
        
        pubTypes.forEach(pubType => {
            if (pubType && pubType !== '--') {
                filterHTML += `<option value="${pubType}">${pubType}</option>`;
            }
        });
        
        filterHTML += `</select>`;
        
        pubTypeFilterContainer.innerHTML = filterHTML;
        
        // Add event listener
        const pubTypeFilterSelect = document.getElementById('pubTypeFilterSelect');
        pubTypeFilterSelect.addEventListener('change', applyFilters);
    }
}

/**
 * Set up the author filter
 */
function setupAuthorFilter() {
    const authorFilterContainer = document.getElementById('authorFilterContainer');
    if (!authorFilterContainer) return;
    
    // Create filter element if it doesn't exist
    if (!document.getElementById('authorFilterInput')) {
        const filterHTML = `
            <div class="input-group input-group-sm">
                <span class="input-group-text">Autor</span>
                <input type="text" class="form-control" id="authorFilterInput" placeholder="Autorname eingeben...">
            </div>
        `;
        
        authorFilterContainer.innerHTML = filterHTML;
        
        // Add event listener
        const authorFilterInput = document.getElementById('authorFilterInput');
        authorFilterInput.addEventListener('input', applyFilters);
    }
}

/**
 * Set up the date range filter
 */
function setupDateRangeFilter() {
    // This would be similar to the year filter but with more precise date selection
    // For now, we'll focus on the year filter as publications typically are filtered by year
}

/**
 * Set up the reset filters button
 */
function setupResetFilters() {
    const resetFiltersButton = document.getElementById('resetFiltersButton');
    if (resetFiltersButton) {
        resetFiltersButton.addEventListener('click', function() {
            // Reset all filter inputs
            const filterInputs = document.querySelectorAll('.filter-input');
            filterInputs.forEach(input => {
                if (input.tagName === 'SELECT') {
                    input.selectedIndex = 0;
                } else if (input.type === 'text' || input.type === 'number') {
                    input.value = '';
                } else if (input.type === 'checkbox') {
                    input.checked = false;
                }
            });
            
            // Reset year filters to their min/max values
            const yearFilterMin = document.getElementById('yearFilterMin');
            const yearFilterMax = document.getElementById('yearFilterMax');
            if (yearFilterMin && yearFilterMax) {
                yearFilterMin.value = yearFilterMin.min;
                yearFilterMax.value = yearFilterMax.max;
            }
            
            // Reset basic filter
            const basicFilter = document.getElementById('resultFilterInput');
            if (basicFilter) {
                basicFilter.value = '';
            }
            
            // Apply reset filters
            applyFilters();
            
            // Clear saved filters
            clearSavedFilters();
        });
    }
}

/**
 * Extract all years from the results table
 */
function extractYearsFromTable() {
    const resultsTable = document.getElementById('resultsTable');
    if (!resultsTable) return [];
    
    const years = [];
    const rows = resultsTable.querySelectorAll('tbody tr.result-row');
    
    rows.forEach(row => {
        const yearCell = row.querySelector('td:nth-child(4)'); // Assuming year is in the 4th column
        if (yearCell && yearCell.textContent) {
            const year = parseInt(yearCell.textContent.trim());
            if (!isNaN(year) && year > 0) {
                years.push(year);
            }
        }
    });
    
    return [...new Set(years)].sort();
}

/**
 * Extract all databases from the results table
 */
function extractDatabasesFromTable() {
    const resultsTable = document.getElementById('resultsTable');
    if (!resultsTable) return [];
    
    const databases = [];
    const rows = resultsTable.querySelectorAll('tbody tr.result-row');
    
    rows.forEach(row => {
        const databaseCell = row.querySelector('td:nth-child(1)'); // Assuming database is in the 1st column
        if (databaseCell && databaseCell.textContent) {
            const database = databaseCell.textContent.trim();
            if (database) {
                databases.push(database);
            }
        }
    });
    
    return [...new Set(databases)].sort();
}

/**
 * Extract all publication types from the results table
 */
function extractPublicationTypesFromTable() {
    const resultsTable = document.getElementById('resultsTable');
    if (!resultsTable) return [];
    
    const pubTypes = [];
    const rows = resultsTable.querySelectorAll('tbody tr.result-row');
    
    rows.forEach(row => {
        const pubTypeCell = row.querySelector('td.column-type'); // Using the class for pub type column
        if (pubTypeCell && pubTypeCell.textContent) {
            const pubType = pubTypeCell.textContent.trim();
            if (pubType) {
                pubTypes.push(pubType);
            }
        }
    });
    
    return [...new Set(pubTypes)].sort();
}

/**
 * Apply all filters to the results table
 */
function applyFilters() {
    const resultsTable = document.getElementById('resultsTable');
    if (!resultsTable) return;
    
    const rows = resultsTable.querySelectorAll('tbody tr.result-row');
    let visibleCount = 0;
    
    // Get filter values
    const textFilter = document.getElementById('resultFilterInput')?.value.toLowerCase() || '';
    const yearMin = parseInt(document.getElementById('yearFilterMin')?.value) || 0;
    const yearMax = parseInt(document.getElementById('yearFilterMax')?.value) || 9999;
    const databaseFilter = document.getElementById('databaseFilterSelect')?.value || '';
    const pubTypeFilter = document.getElementById('pubTypeFilterSelect')?.value || '';
    const authorFilter = document.getElementById('authorFilterInput')?.value.toLowerCase() || '';
    
    // Save filter state
    saveFilterState();
    
    // Apply filters to each row
    rows.forEach(row => {
        // Check text filter (search in all columns)
        const rowText = row.textContent.toLowerCase();
        const passesTextFilter = !textFilter || rowText.includes(textFilter);
        
        // Check year filter
        const yearCell = row.querySelector('td:nth-child(4)');
        const year = yearCell ? parseInt(yearCell.textContent.trim()) : 0;
        const passesYearFilter = isNaN(year) || (year >= yearMin && year <= yearMax);
        
        // Check database filter
        const databaseCell = row.querySelector('td:nth-child(1)');
        const database = databaseCell ? databaseCell.textContent.trim() : '';
        const passesDatabaseFilter = !databaseFilter || database === databaseFilter;
        
        // Check publication type filter
        const pubTypeCell = row.querySelector('td.column-type');
        const pubType = pubTypeCell ? pubTypeCell.textContent.trim() : '';
        const passesPubTypeFilter = !pubTypeFilter || pubType === pubTypeFilter;
        
        // Check author filter
        const authorCell = row.querySelector('td:nth-child(3)');
        const authorText = authorCell ? authorCell.textContent.toLowerCase() : '';
        const passesAuthorFilter = !authorFilter || authorText.includes(authorFilter);
        
        // Show or hide row based on all filters
        const visible = passesTextFilter && passesYearFilter && passesDatabaseFilter && 
                        passesPubTypeFilter && passesAuthorFilter;
        
        row.style.display = visible ? '' : 'none';
        
        if (visible) visibleCount++;
    });
    
    // Update filter stats
    updateFilterStats(visibleCount, rows.length);
}

/**
 * Update filter statistics and visibility of "no matching results" message.
 */
function updateFilterStats(visibleCount, totalCount) {
    const filterStatsElement = document.getElementById('filterStats');
    const tableFooter = document.getElementById('resultsTableFooter');

    if (filterStatsElement) {
        filterStatsElement.textContent = `Angezeigt: ${visibleCount} von ${totalCount} Ergebnissen`;
        
        if (visibleCount < totalCount && visibleCount > 0) {
            filterStatsElement.classList.add('text-warning');
            filterStatsElement.classList.remove('text-muted');
        } else {
            filterStatsElement.classList.add('text-muted');
            filterStatsElement.classList.remove('text-warning');
        }
    }

    if (tableFooter) {
        if (visibleCount === 0 && totalCount > 0) { // Show message only if there were rows to filter but none matched
            tableFooter.style.display = '';
        } else {
            tableFooter.style.display = 'none';
        }
    }
}

/**
 * Save filter state to session storage
 */
function saveFilterState() {
    const filters = {
        textFilter: document.getElementById('resultFilterInput')?.value || '',
        yearMin: document.getElementById('yearFilterMin')?.value || '',
        yearMax: document.getElementById('yearFilterMax')?.value || '',
        database: document.getElementById('databaseFilterSelect')?.value || '',
        pubType: document.getElementById('pubTypeFilterSelect')?.value || '',
        author: document.getElementById('authorFilterInput')?.value || ''
    };
    
    sessionStorage.setItem('searchResultFilters', JSON.stringify(filters));
}

/**
 * Restore filter state from session storage
 */
function restoreFilterState() {
    const savedFilters = sessionStorage.getItem('searchResultFilters');
    if (!savedFilters) return;
    
    try {
        const filters = JSON.parse(savedFilters);
        
        // Apply saved filters to inputs
        if (document.getElementById('resultFilterInput')) {
            document.getElementById('resultFilterInput').value = filters.textFilter || '';
        }
        
        if (document.getElementById('yearFilterMin')) {
            document.getElementById('yearFilterMin').value = filters.yearMin || document.getElementById('yearFilterMin').min;
        }
        
        if (document.getElementById('yearFilterMax')) {
            document.getElementById('yearFilterMax').value = filters.yearMax || document.getElementById('yearFilterMax').max;
        }
        
        if (document.getElementById('databaseFilterSelect')) {
            document.getElementById('databaseFilterSelect').value = filters.database || '';
        }
        
        if (document.getElementById('pubTypeFilterSelect')) {
            document.getElementById('pubTypeFilterSelect').value = filters.pubType || '';
        }
        
        if (document.getElementById('authorFilterInput')) {
            document.getElementById('authorFilterInput').value = filters.author || '';
        }
        
        // Apply restored filters
        applyFilters();
    } catch (e) {
        console.error('Error restoring filter state:', e);
        clearSavedFilters();
    }
}

/**
 * Set up filter persistence between page visits
 */
function setupFilterPersistence() {
    // Save filters when navigating away
    window.addEventListener('beforeunload', saveFilterState);
}

/**
 * Clear saved filters from session storage
 */
function clearSavedFilters() {
    sessionStorage.removeItem('searchResultFilters');
}