// Person Search Module
class PersonSearch {
    constructor() {
        this.persons = [];
        this.selectedPersons = new Set();
        this.initializeFromWindow();
        this.setupEventListeners();
    }

    initializeFromWindow() {
        console.log('Initializing PersonSearch from window.allPersons');
        if (window.allPersons && Array.isArray(window.allPersons)) {
            this.persons = window.allPersons;
            console.log('Loaded persons:', this.persons);
        } else {
            console.warn('No persons data found in window.allPersons');
        }
    }

    setupEventListeners() {
        // Setup person search input listeners
        const personSearchInput = document.getElementById('personSearchInput');
        const advancedPersonSearchInput = document.getElementById('advancedPersonSearchInput');

        if (personSearchInput) {
            personSearchInput.addEventListener('input', (e) => this.handleSearch(e, false));
        }

        if (advancedPersonSearchInput) {
            advancedPersonSearchInput.addEventListener('input', (e) => this.handleSearch(e, true));
        }

        // Close suggestions on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.person-suggestions') && !e.target.closest('input')) {
                this.hideSuggestions();
            }
        });
    }

    handleSearch(event, isAdvanced = false) {
        const input = event.target;
        const query = input.value.toLowerCase().trim();
        const resultsContainerId = isAdvanced ? 'advancedPersonSearchResults' : 'personSearchResults';
        const resultsContainer = document.getElementById(resultsContainerId);

        console.log('Handling search:', {
            query: query,
            isAdvanced: isAdvanced,
            containerId: resultsContainerId,
            containerExists: !!resultsContainer
        });

        if (!query || !resultsContainer) {
            if (resultsContainer) {
                resultsContainer.style.display = 'none';
            }
            return;
        }

        // Filter persons
        const matches = this.persons.filter(person => 
            person.name.toLowerCase().includes(query) ||
            (person.first_name && person.first_name.toLowerCase().includes(query)) ||
            (person.last_name && person.last_name.toLowerCase().includes(query))
        );

        console.log('Found matches:', matches.length);

        this.showSuggestions(matches, input, resultsContainer, isAdvanced);
    }

    showSuggestions(matches, input, container, isAdvanced) {
        // Clear previous suggestions
        container.innerHTML = '';

        if (matches.length === 0) {
            container.innerHTML = `
                <div class="list-group-item text-muted">
                    <i class="fas fa-info-circle me-2"></i>Keine Personen gefunden
                </div>`;
            container.style.display = 'block';
            return;
        }

        // Create suggestions
        matches.forEach(person => {
            const item = document.createElement('div');
            item.className = 'list-group-item list-group-item-action';
            item.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="fas fa-user me-2 text-primary"></i>
                    <div>
                        <div class="fw-bold">${person.name}</div>
                        <small class="text-muted">${person.first_name} ${person.last_name}</small>
                    </div>
                </div>`;

            item.addEventListener('click', () => {
                this.selectPerson(person, input, isAdvanced);
                container.style.display = 'none';
            });

            container.appendChild(item);
        });

        // Show suggestions
        container.style.display = 'block';
    }

    selectPerson(person, input, isAdvanced) {
        const container = document.getElementById(isAdvanced ? 'advancedSelectedPersonsContainer' : 'selectedPersonsContainer');
        const hiddenInput = document.getElementById(isAdvanced ? 'advancedSelectedPersonIds' : 'selectedPersonIds');
        const noPersonsAlert = document.getElementById(isAdvanced ? 'advancedNoPersonsSelectedAlert' : 'noPersonsSelectedAlert');

        if (!container || !hiddenInput) return;

        // Add to selected persons
        this.selectedPersons.add(person.id);

        // Update hidden input
        hiddenInput.value = Array.from(this.selectedPersons).join(',');

        // Create person tag
        const tag = document.createElement('span');
        tag.className = 'badge bg-primary me-2 mb-2';
        tag.innerHTML = `
            ${person.name}
            <button type="button" class="btn-close btn-close-white ms-2" aria-label="Remove"
                data-id="${person.id}" style="font-size: 0.5rem;"></button>
        `;

        // Add remove button listener
        tag.querySelector('.btn-close').addEventListener('click', (e) => {
            this.removePerson(person.id, isAdvanced);
            e.stopPropagation();
        });

        // Hide no persons alert if present
        if (noPersonsAlert) {
            noPersonsAlert.style.display = 'none';
        }

        // Add tag to container
        container.insertBefore(tag, noPersonsAlert || null);

        // Clear input
        input.value = '';
    }

    removePerson(personId, isAdvanced) {
        const container = document.getElementById(isAdvanced ? 'advancedSelectedPersonsContainer' : 'selectedPersonsContainer');
        const hiddenInput = document.getElementById(isAdvanced ? 'advancedSelectedPersonIds' : 'selectedPersonIds');
        const noPersonsAlert = document.getElementById(isAdvanced ? 'advancedNoPersonsSelectedAlert' : 'noPersonsSelectedAlert');

        if (!container || !hiddenInput) return;

        // Remove from selected persons
        this.selectedPersons.delete(personId);

        // Update hidden input
        hiddenInput.value = Array.from(this.selectedPersons).join(',');

        // Remove tag
        const tag = container.querySelector(`[data-id="${personId}"]`).closest('.badge');
        if (tag) {
            tag.remove();
        }

        // Show no persons alert if no persons selected
        if (noPersonsAlert && this.selectedPersons.size === 0) {
            noPersonsAlert.style.display = 'block';
        }
    }

    hideSuggestions() {
        const containers = [
            document.getElementById('personSearchResults'),
            document.getElementById('advancedPersonSearchResults')
        ];

        containers.forEach(container => {
            if (container) {
                container.style.display = 'none';
            }
        });
    }
}

// Initialize person search when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing PersonSearch module');
    window.personSearch = new PersonSearch();
});
