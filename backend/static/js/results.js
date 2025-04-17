/**
 * MedicalSpy - Results module
 * This file contains functions for managing search results.
 */

// Filter results in the table
function filterResults() {
    const filterInput = document.getElementById('resultFilter');
    const tableRows = document.querySelectorAll('#resultsTable tbody tr');
    
    if (!filterInput || !tableRows.length) return;
    
    const filterText = filterInput.value.toLowerCase();
    
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
    // Create form
    const form = document.createElement('form');
    form.method = 'post';
    form.action = '/api/export_results';
    
    // Add format input
    const formatInput = document.createElement('input');
    formatInput.type = 'hidden';
    formatInput.name = 'format';
    formatInput.value = format;
    form.appendChild(formatInput);
    
    // Add the form to the document and submit it
    document.body.appendChild(form);
    form.submit();
    
    // Clean up
    document.body.removeChild(form);
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
    }
    
    // Initialize export buttons
    const exportCsvButton = document.getElementById('exportCsv');
    if (exportCsvButton) {
        exportCsvButton.addEventListener('click', () => exportResults('csv'));
    }
    
    const exportExcelButton = document.getElementById('exportExcel');
    if (exportExcelButton) {
        exportExcelButton.addEventListener('click', () => exportResults('excel'));
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
