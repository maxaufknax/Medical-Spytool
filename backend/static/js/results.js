/**
 * MedicalSpy - Results module
 * This file contains functions for managing search results.
 */

// Filter results in the table
function filterResults() {
    const filterInput = document.getElementById('resultFilter');
    const tableRows = document.querySelectorAll('#resultsTable tbody tr');
    const cardItems = document.querySelectorAll('#cardView .result-card');
    
    if (!filterInput) return;
    
    const filterText = filterInput.value.toLowerCase();
    
    // Filter table rows
    if (tableRows.length) {
        tableRows.forEach(row => {
            let rowText = '';
            row.querySelectorAll('td').forEach(cell => {
                rowText += cell.textContent + ' ';
            });
            
            rowText = rowText.toLowerCase();
            
            if (rowText.includes(filterText)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        
        // Update count of visible results
        updateVisibleResultsCount(tableRows);
    }
    
    // Filter card items
    if (cardItems.length) {
        cardItems.forEach(card => {
            let cardText = card.textContent.toLowerCase();
            
            if (cardText.includes(filterText)) {
                card.closest('.col-lg-6').style.display = '';
            } else {
                card.closest('.col-lg-6').style.display = 'none';
            }
        });
        
        // If in card view, update count based on visible cards
        if (document.getElementById('cardView') && !document.getElementById('cardView').classList.contains('d-none')) {
            const visibleCards = Array.from(cardItems).filter(card => card.closest('.col-lg-6').style.display !== 'none');
            document.getElementById('resultCount').textContent = `${visibleCards.length} von ${cardItems.length}`;
        }
    }
}

// Update the count of visible results
function updateVisibleResultsCount(tableRows) {
    const resultCount = document.getElementById('resultCount');
    if (!resultCount) return;
    
    let visibleCount = 0;
    tableRows.forEach(row => {
        if (row.style.display !== 'none') {
            visibleCount++;
        }
    });
    
    resultCount.textContent = `Showing ${visibleCount} of ${tableRows.length} results`;
}

// Export results
function exportResults(format) {
    // Set the export format
    document.getElementById('exportFormat').value = format;
    
    // Validate if at least one column is selected
    const checkedColumns = document.querySelectorAll('.column-checkbox:checked');
    if (checkedColumns.length === 0) {
        // Show alert if no columns selected
        alert('Bitte wählen Sie mindestens eine Spalte für den Export aus.');
        return;
    }
    
    // Show loading state
    const exportBtn = document.querySelector(`#export${format.charAt(0).toUpperCase() + format.slice(1)}Btn`);
    if (exportBtn) {
        const originalText = exportBtn.innerHTML;
        exportBtn.disabled = true;
        exportBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exportiere...`;
        
        // Submit the form and reset button after a short delay
        document.getElementById('exportConfigForm').submit();
        
        // Reset button state after submission (since the page will reload on success)
        setTimeout(() => {
            exportBtn.disabled = false;
            exportBtn.innerHTML = originalText;
        }, 5000); // Safety timeout in case the form submission fails
    } else {
        // Fallback if button not found
        document.getElementById('exportConfigForm').submit();
    }
}

// Sort the results table by a column
function sortResultsTable(columnIndex, dataType) {
    const table = document.getElementById('resultsTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Determine sort direction
    const sortDirectionElement = table.querySelector('.sort-direction');
    let ascending = true;
    
    if (sortDirectionElement) {
        // If we're already sorting by this column, toggle direction
        if (sortDirectionElement.dataset.columnIndex == columnIndex) {
            ascending = sortDirectionElement.dataset.direction === 'asc' ? false : true;
        }
        
        // Remove existing sort indicators
        const headers = table.querySelectorAll('th');
        headers.forEach(header => {
            header.classList.remove('sorting-asc', 'sorting-desc');
        });
    }
    
    // Sort the rows
    rows.sort((a, b) => {
        const aCellValue = a.cells[columnIndex].textContent.trim();
        const bCellValue = b.cells[columnIndex].textContent.trim();
        
        let comparison = 0;
        
        if (dataType === 'number') {
            // Numeric sorting
            const aNum = parseFloat(aCellValue) || 0;
            const bNum = parseFloat(bCellValue) || 0;
            comparison = aNum - bNum;
        } else if (dataType === 'date') {
            // Date sorting
            const aDate = new Date(aCellValue) || new Date(0);
            const bDate = new Date(bCellValue) || new Date(0);
            comparison = aDate - bDate;
        } else {
            // Default to string sorting
            comparison = aCellValue.localeCompare(bCellValue);
        }
        
        return ascending ? comparison : -comparison;
    });
    
    // Update the table with sorted rows
    rows.forEach(row => {
        tbody.appendChild(row);
    });
    
    // Update sort direction indicator
    const headerCell = table.querySelector(`th:nth-child(${columnIndex + 1})`);
    headerCell.classList.add(ascending ? 'sorting-asc' : 'sorting-desc');
    
    // Store sort direction for next click
    if (sortDirectionElement) {
        sortDirectionElement.dataset.columnIndex = columnIndex;
        sortDirectionElement.dataset.direction = ascending ? 'asc' : 'desc';
    } else {
        // Create a new element if it doesn't exist
        const newSortDirection = document.createElement('span');
        newSortDirection.className = 'sort-direction';
        newSortDirection.dataset.columnIndex = columnIndex;
        newSortDirection.dataset.direction = ascending ? 'asc' : 'desc';
        newSortDirection.style.display = 'none';
        table.appendChild(newSortDirection);
    }
}

// Toggle between list and grid view for results
function toggleResultsView(viewType) {
    const listView = document.getElementById('listView');
    const cardView = document.getElementById('cardView');
    
    if (!listView || !cardView) return;
    
    if (viewType === 'cards') {
        listView.classList.add('d-none');
        cardView.classList.remove('d-none');
        document.getElementById('cardViewBtn').classList.add('active');
        document.getElementById('listViewBtn').classList.remove('active');
    } else {
        listView.classList.remove('d-none');
        cardView.classList.add('d-none');
        document.getElementById('listViewBtn').classList.add('active');
        document.getElementById('cardViewBtn').classList.remove('active');
    }
    
    // Save preference in localStorage
    localStorage.setItem('resultsViewPreference', viewType);
}

// Initialize results page
document.addEventListener('DOMContentLoaded', function() {
    // Initialize filter functionality
    const filterInput = document.getElementById('resultFilter');
    if (filterInput) {
        filterInput.addEventListener('input', filterResults);
        
        // Add clear button for filter
        const filterContainer = filterInput.parentElement;
        if (filterContainer) {
            const clearButton = document.createElement('button');
            clearButton.className = 'btn btn-sm btn-outline-secondary position-absolute';
            clearButton.style.right = '5px';
            clearButton.style.top = '5px';
            clearButton.innerHTML = '<i class="fas fa-times"></i>';
            clearButton.addEventListener('click', () => {
                filterInput.value = '';
                filterResults();
                filterInput.focus();
            });
            filterContainer.style.position = 'relative';
            filterContainer.appendChild(clearButton);
        }
    }
    
    // Initialize tooltips for action buttons
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(tooltipTriggerEl => {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize export buttons in the main interface
    const exportCsv = document.getElementById('exportCsv');
    const exportExcel = document.getElementById('exportExcel');
    if (exportCsv && exportExcel) {
        // Show export config modal when buttons are clicked
        exportCsv.addEventListener('click', () => {
            const exportConfigModal = new bootstrap.Modal(document.getElementById('exportConfigModal'));
            exportConfigModal.show();
        });
        exportExcel.addEventListener('click', () => {
            const exportConfigModal = new bootstrap.Modal(document.getElementById('exportConfigModal'));
            exportConfigModal.show();
        });
    }
    
    // Initialize export buttons in the modal
    const exportCsvBtn = document.getElementById('exportCsvBtn');
    if (exportCsvBtn) {
        exportCsvBtn.addEventListener('click', () => exportResults('csv'));
    }
    
    const exportExcelBtn = document.getElementById('exportExcelBtn');
    if (exportExcelBtn) {
        exportExcelBtn.addEventListener('click', () => exportResults('excel'));
    }
    
    const exportBibtexBtn = document.getElementById('exportBibtexBtn');
    if (exportBibtexBtn) {
        exportBibtexBtn.addEventListener('click', () => exportResults('bibtex'));
    }
    
    // Handle select all columns checkbox
    const selectAllCheckbox = document.getElementById('select-all-columns');
    const columnCheckboxes = document.querySelectorAll('.column-checkbox');
    
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            columnCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
        
        // Check if all column checkboxes are already checked
        const updateSelectAllState = () => {
            selectAllCheckbox.checked = Array.from(columnCheckboxes).every(checkbox => checkbox.checked);
            selectAllCheckbox.indeterminate = Array.from(columnCheckboxes).some(checkbox => checkbox.checked) && 
                                             !Array.from(columnCheckboxes).every(checkbox => checkbox.checked);
        };
        
        // Set initial state
        updateSelectAllState();
        
        // Update when individual checkboxes change
        columnCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateSelectAllState);
        });
    }
    
    // Initialize view toggling
    const listViewBtn = document.getElementById('listViewBtn');
    if (listViewBtn) {
        listViewBtn.addEventListener('click', () => toggleResultsView('list'));
    }
    
    const cardViewBtn = document.getElementById('cardViewBtn');
    if (cardViewBtn) {
        cardViewBtn.addEventListener('click', () => toggleResultsView('cards'));
    }
    
    // Set the initial view based on saved preference or default to list
    const savedView = localStorage.getItem('resultsViewPreference') || 'list';
    toggleResultsView(savedView);
    
    // Initialize table with initial count
    const tableRows = document.querySelectorAll('#resultsTable tbody tr');
    if (tableRows.length) {
        updateVisibleResultsCount(tableRows);
    }
    
    // Set up table sorting
    const sortableHeaders = document.querySelectorAll('th[data-sortable]');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const columnIndex = Array.from(header.parentElement.children).indexOf(header);
            const dataType = header.dataset.type || 'text';
            sortResultsTable(columnIndex, dataType);
        });
    });
});
