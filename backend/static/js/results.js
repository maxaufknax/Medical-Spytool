/**
 * MedicalSpy - Results module
 * This file contains functions for managing search results.
 */

// Filter results in the table or cards
function filterResults() {
    const filterInput = document.getElementById('resultFilter');
    const tableRows = document.querySelectorAll('#resultsTable tbody tr');
    const cardItems = document.querySelectorAll('#cardView .result-card'); // These are the cards themselves
    
    if (!filterInput) return;
    
    const filterText = filterInput.value.toLowerCase();
    
    // Determine current view
    const isListView = document.getElementById('listView') && !document.getElementById('listView').classList.contains('d-none');
    const isCardView = document.getElementById('cardView') && !document.getElementById('cardView').classList.contains('d-none');

    if (isListView && tableRows.length) {
        tableRows.forEach(row => {
            let rowText = '';
            row.querySelectorAll('td').forEach(cell => {
                rowText += cell.textContent + ' ';
            });
            rowText = rowText.toLowerCase();
            row.style.display = rowText.includes(filterText) ? '' : 'none';
        });
        updateVisibleResultsCount(tableRows);
    }
    
    if (isCardView && cardItems.length) {
        cardItems.forEach(card => {
            let cardText = card.textContent.toLowerCase();
            // Cards are wrapped in a column div that needs to be hidden/shown
            const cardWrapper = card.closest('.col-lg-6'); 
            if (cardWrapper) {
                cardWrapper.style.display = cardText.includes(filterText) ? '' : 'none';
            }
        });
        // For card view, pass the direct card elements to updateVisibleResultsCount
        updateVisibleResultsCount(cardItems); 
    }
}

// Update the count of visible results (specifically for the current page)
function updateVisibleResultsCount(itemsOnPage) { // itemsOnPage can be tableRows or cardItems
    const currentPageResultCountSpan = document.getElementById('currentPageResultCount');
    if (!currentPageResultCountSpan) return;
    
    let visibleCount = 0;
    itemsOnPage.forEach(item => { 
        // For table rows, display is directly on the row.
        // For cards, display is on the parent '.col-lg-6' element.
        const elementToCheck = item.matches('tr') ? item : item.closest('.col-lg-6');
        if (elementToCheck && elementToCheck.style.display !== 'none') {
            visibleCount++;
        }
    });
    
    currentPageResultCountSpan.textContent = visibleCount;
}

// Export results
function exportResults(format) {
    document.getElementById('exportFormat').value = format;
    const checkedColumns = document.querySelectorAll('.column-checkbox:checked');
    if (checkedColumns.length === 0) {
        alert('Bitte wählen Sie mindestens eine Spalte für den Export aus.');
        return;
    }
    
    const exportBtn = document.querySelector(`#export${format.charAt(0).toUpperCase() + format.slice(1)}Btn`); // Corrected selector
    if (exportBtn) {
        const originalText = exportBtn.innerHTML;
        exportBtn.disabled = true;
        exportBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exportiere...`;
        
        document.getElementById('exportConfigForm').submit();
        
        setTimeout(() => {
            exportBtn.disabled = false;
            exportBtn.innerHTML = originalText;
        }, 5000); 
    } else {
        document.getElementById('exportConfigForm').submit();
    }
}

// Sort the results table by a column
function sortResultsTable(columnIndex, dataType) {
    const table = document.getElementById('resultsTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const sortDirectionElement = table.querySelector('.sort-direction') || document.createElement('span'); // Ensure element exists
    sortDirectionElement.className = 'sort-direction'; // Ensure class
    sortDirectionElement.style.display = 'none'; // Hide it
    if (!sortDirectionElement.parentNode) table.appendChild(sortDirectionElement);


    let ascending = true;
    
    if (sortDirectionElement.dataset.columnIndex == columnIndex) {
        ascending = sortDirectionElement.dataset.direction === 'desc'; // Toggle: if was desc, now asc
    }
        
    const headers = table.querySelectorAll('th');
    headers.forEach(header => {
        header.classList.remove('sorting-asc', 'sorting-desc');
    });
    
    rows.sort((a, b) => {
        const aCellValue = a.cells[columnIndex].textContent.trim();
        const bCellValue = b.cells[columnIndex].textContent.trim();
        let comparison = 0;
        
        if (dataType === 'number') {
            const aNum = parseFloat(aCellValue) || 0;
            const bNum = parseFloat(bCellValue) || 0;
            comparison = aNum - bNum;
        } else if (dataType === 'date') {
            // Basic date parsing, assuming YYYY-MM-DD or DD.MM.YYYY or similar that Date.parse can handle
            // More robust parsing might be needed for specific formats
            const aDate = Date.parse(aCellValue) || 0;
            const bDate = Date.parse(bCellValue) || 0;
            comparison = aDate - bDate;
        } else {
            comparison = aCellValue.localeCompare(bCellValue, undefined, {numeric: true, sensitivity: 'base'});
        }
        return ascending ? comparison : -comparison;
    });
    
    rows.forEach(row => {
        tbody.appendChild(row);
    });
    
    const headerCell = table.querySelector(`th:nth-child(${columnIndex + 1})`);
    if (headerCell) {
        headerCell.classList.add(ascending ? 'sorting-asc' : 'sorting-desc');
    }
    
    sortDirectionElement.dataset.columnIndex = columnIndex;
    sortDirectionElement.dataset.direction = ascending ? 'asc' : 'desc';
}

// Toggle between list and grid view for results
function toggleResultsView(viewType) {
    const listView = document.getElementById('listView');
    const cardView = document.getElementById('cardView');
    const listViewBtn = document.getElementById('listViewBtn');
    const cardViewBtn = document.getElementById('cardViewBtn');
    
    if (!listView || !cardView || !listViewBtn || !cardViewBtn) return;
    
    if (viewType === 'cards') {
        listView.classList.add('d-none');
        cardView.classList.remove('d-none');
        cardViewBtn.classList.add('active');
        listViewBtn.classList.remove('active');
    } else { // Default to list view
        listView.classList.remove('d-none');
        cardView.classList.add('d-none');
        listViewBtn.classList.add('active');
        cardViewBtn.classList.remove('active');
    }
    localStorage.setItem('resultsViewPreference', viewType);
}

// Initialize results page
document.addEventListener('DOMContentLoaded', function() {
    const filterInput = document.getElementById('resultFilter');
    if (filterInput) {
        filterInput.addEventListener('input', filterResults);
        const filterContainer = filterInput.parentElement;
        if (filterContainer && !filterContainer.querySelector('.clear-filter-btn')) { // Avoid adding multiple clear buttons
            const clearButton = document.createElement('button');
            clearButton.className = 'btn btn-sm btn-outline-secondary position-absolute clear-filter-btn';
            clearButton.innerHTML = '<i class="fas fa-times"></i>';
            clearButton.style.right = '5px'; // Adjust as per input group or direct styling
            clearButton.style.top = '50%';
            clearButton.style.transform = 'translateY(-50%)';
            clearButton.addEventListener('click', () => {
                filterInput.value = '';
                filterResults();
                filterInput.focus();
            });
            if (filterContainer.style.position !== 'relative' && filterContainer.style.position !== 'absolute' && filterContainer.style.position !== 'fixed') {
                 filterContainer.style.position = 'relative'; // Needed for absolute positioning of child
            }
            filterContainer.appendChild(clearButton);
        }
    }
    
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(tooltipTriggerEl => {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    const exportCsvMainBtn = document.getElementById('exportCsv'); // Renamed to avoid conflict
    const exportExcelMainBtn = document.getElementById('exportExcel'); // Renamed to avoid conflict
    const exportConfigModalElement = document.getElementById('exportConfigModal');
    let exportConfigModalInstance = null;
    if (exportConfigModalElement) {
         exportConfigModalInstance = new bootstrap.Modal(exportConfigModalElement);
    }

    if (exportCsvMainBtn) {
        exportCsvMainBtn.addEventListener('click', () => {
            if(exportConfigModalInstance) exportConfigModalInstance.show();
        });
    }
    if (exportExcelMainBtn) {
        exportExcelMainBtn.addEventListener('click', () => {
            if(exportConfigModalInstance) exportConfigModalInstance.show();
        });
    }
    
    const exportCsvModalBtn = document.getElementById('exportCsvBtn'); // Button inside modal
    if (exportCsvModalBtn) {
        exportCsvModalBtn.addEventListener('click', () => exportResults('csv'));
    }
    
    const exportExcelModalBtn = document.getElementById('exportExcelBtn'); // Button inside modal
    if (exportExcelModalBtn) {
        exportExcelModalBtn.addEventListener('click', () => exportResults('excel'));
    }
    
    const exportBibtexBtn = document.getElementById('exportBibtexBtn');
    if (exportBibtexBtn) {
        exportBibtexBtn.addEventListener('click', () => exportResults('bibtex'));
    }
    
    const selectAllCheckbox = document.getElementById('select-all-columns');
    const columnCheckboxes = document.querySelectorAll('.column-checkbox');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            columnCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
        const updateSelectAllState = () => {
            const allChecked = Array.from(columnCheckboxes).every(checkbox => checkbox.checked);
            const someChecked = Array.from(columnCheckboxes).some(checkbox => checkbox.checked);
            selectAllCheckbox.checked = allChecked;
            selectAllCheckbox.indeterminate = someChecked && !allChecked;
        };
        updateSelectAllState();
        columnCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateSelectAllState);
        });
    }
    
    const listViewBtn = document.getElementById('listViewBtn');
    if (listViewBtn) {
        listViewBtn.addEventListener('click', () => toggleResultsView('list'));
    }
    
    const cardViewBtn = document.getElementById('cardViewBtn');
    if (cardViewBtn) {
        cardViewBtn.addEventListener('click', () => toggleResultsView('cards'));
    }
    
    const savedView = localStorage.getItem('resultsViewPreference') || 'list';
    toggleResultsView(savedView); // This will also handle initial active states for buttons
    
    // No initial call to updateVisibleResultsCount here as Jinja already sets the correct initial count.
    // filterResults() will update it if/when filters are applied.

    const sortableHeaders = document.querySelectorAll('th[data-sortable]');
    sortableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const columnIndex = Array.from(header.parentElement.children).indexOf(header);
            const dataType = header.dataset.type || 'text';
            sortResultsTable(columnIndex, dataType);
        });
    });
});
