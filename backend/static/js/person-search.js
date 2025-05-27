// Person Search Module
class PersonSearch {
    constructor() {
        this.persons = [];
        this.selectedPersons = new Set();
        this.initializeFromWindow();
        this.setupEventListeners();
        this.focusedSuggestionIndex = -1; // For keyboard navigation
        this.currentMatches = []; // To store current suggestion matches
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

        input.setAttribute('aria-expanded', 'false'); // Reset aria-expanded

        if (!query || !resultsContainer) {
            if (resultsContainer) this.hideSuggestions(resultsContainer, input);
            this.currentMatches = [];
            this.focusedSuggestionIndex = -1;
            return;
        }

        this.currentMatches = this.persons.filter(person => 
            person.name.toLowerCase().includes(query) ||
            (person.first_name && person.first_name.toLowerCase().includes(query)) ||
            (person.last_name && person.last_name.toLowerCase().includes(query))
        );

        this.showSuggestions(this.currentMatches, input, resultsContainer, isAdvanced);
    }

    showSuggestions(matches, input, container, isAdvanced) {
        container.innerHTML = '';
        this.focusedSuggestionIndex = -1; // Reset focus index
        input.removeAttribute('aria-activedescendant');


        if (matches.length === 0) {
            container.innerHTML = `<div class="list-group-item text-muted" role="option"><i class="fas fa-info-circle me-2"></i>Keine Personen gefunden</div>`;
            container.style.display = 'block';
            input.setAttribute('aria-expanded', 'true');
            return;
        }

        matches.forEach((person, index) => {
            const item = document.createElement('div');
            item.className = 'list-group-item list-group-item-action person-suggestion-item';
            item.id = `${container.id}-item-${index}`;
            item.setAttribute('role', 'option');
            // Store person data directly on the element for easier access
            item.dataset.person = JSON.stringify(person); 

            item.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="fas fa-user me-2 text-primary" aria-hidden="true"></i>
                    <div>
                        <div class="fw-bold">${person.name}</div>
                        <small class="text-muted">${person.first_name || ''} ${person.last_name || ''}</small>
                    </div>
                </div>`;

            item.addEventListener('click', () => {
                this.selectPerson(person, input, isAdvanced);
                this.hideSuggestions(container, input);
            });
            
            item.addEventListener('mouseover', () => {
                if (this.focusedSuggestionIndex !== -1 && container.children[this.focusedSuggestionIndex]) {
                     container.children[this.focusedSuggestionIndex].classList.remove('suggestion-focused');
                }
                this.focusedSuggestionIndex = index;
                item.classList.add('suggestion-focused');
                input.setAttribute('aria-activedescendant', item.id);
            });

            container.appendChild(item);
        });

        container.style.display = 'block';
        input.setAttribute('aria-expanded', 'true');
    }
    
    updateFocusedSuggestion(container, input) {
        Array.from(container.children).forEach((child, idx) => {
            if (idx === this.focusedSuggestionIndex) {
                child.classList.add('suggestion-focused');
                input.setAttribute('aria-activedescendant', child.id);
                child.scrollIntoView({ block: 'nearest' });
            } else {
                child.classList.remove('suggestion-focused');
            }
        });
    }


    selectPerson(person, input, isAdvanced) {
        const containerIdSuffix = isAdvanced ? 'advanced' : '';
        const container = document.getElementById(`${containerIdSuffix}SelectedPersonsContainer`);
        const hiddenInput = document.getElementById(`${containerIdSuffix}SelectedPersonIds`);
        const noPersonsAlert = document.getElementById(`${containerIdSuffix}NoPersonsSelectedAlert`);

        if (!container || !hiddenInput) {
            console.error("Required elements for selecting person not found:", {container, hiddenInput});
            return;
        }
        
        // Ensure person.id is a number before adding to Set for consistency, though Set handles mixed types.
        const personIdNum = Number(person.id);
        if (isNaN(personIdNum)) {
            console.error("Invalid person ID:", person.id);
            return;
        }

        this.selectedPersons.add(personIdNum);
        hiddenInput.value = Array.from(this.selectedPersons).join(',');

        const tag = document.createElement('span');
        tag.className = 'badge bg-primary me-2 mb-2 selected-person-tag';
        tag.setAttribute('role', 'listitem');
        tag.innerHTML = `
            ${person.name}
            <button type="button" class="btn-close btn-close-white ms-2" 
                    aria-label="Remove ${person.name}" data-id="${personIdNum}" 
                    style="font-size: 0.65em;"></button>
        `;

        tag.querySelector('.btn-close').addEventListener('click', (e) => {
            this.removePerson(personIdNum, isAdvanced);
            e.stopPropagation(); // Prevent tag click event if any
        });

        if (noPersonsAlert) noPersonsAlert.style.display = 'none';
        container.insertBefore(tag, noPersonsAlert || container.firstChild); // Insert before alert or as first child

        input.value = ''; // Clear input
        this.currentMatches = []; // Clear matches
        this.focusedSuggestionIndex = -1; // Reset focus
        input.focus(); // Return focus to the input field
    }

    removePerson(personId, isAdvanced) { // personId is expected to be a number here
        const container = document.getElementById(isAdvanced ? 'advancedSelectedPersonsContainer' : 'selectedPersonsContainer');
        const containerIdSuffix = isAdvanced ? 'advanced' : '';
        const container = document.getElementById(`${containerIdSuffix}SelectedPersonsContainer`);
        const hiddenInput = document.getElementById(`${containerIdSuffix}SelectedPersonIds`);
        const noPersonsAlert = document.getElementById(`${containerIdSuffix}NoPersonsSelectedAlert`);

        if (!container || !hiddenInput) return;

        this.selectedPersons.delete(personId); // personId should be a number
        hiddenInput.value = Array.from(this.selectedPersons).join(',');

        const tag = container.querySelector(`.selected-person-tag button[data-id="${personId}"]`)?.closest('.selected-person-tag');
        if (tag) tag.remove();

        if (noPersonsAlert && this.selectedPersons.size === 0) {
            noPersonsAlert.style.display = 'flex'; // Assuming it's a flex container
        }
    }

    hideSuggestions(containerElement, inputElement) {
        if (containerElement) containerElement.style.display = 'none';
        if (inputElement) {
             inputElement.removeAttribute('aria-activedescendant');
             inputElement.setAttribute('aria-expanded', 'false');
        }
        this.focusedSuggestionIndex = -1;
        this.currentMatches = [];
    }

    setupEventListeners() {
        const inputs = [
            { el: document.getElementById('personSearchInput'), advanced: false, containerId: 'personSearchResults' },
            { el: document.getElementById('advancedPersonSearchInput'), advanced: true, containerId: 'advancedPersonSearchResults' }
        ];

        inputs.forEach(obj => {
            if (obj.el) {
                obj.el.addEventListener('input', (e) => this.handleSearch(e, obj.advanced));
                obj.el.addEventListener('keydown', (e) => {
                    const container = document.getElementById(obj.containerId);
                    if (!container || container.style.display === 'none' || this.currentMatches.length === 0) return;

                    if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        this.focusedSuggestionIndex = (this.focusedSuggestionIndex + 1) % this.currentMatches.length;
                        this.updateFocusedSuggestion(container, obj.el);
                    } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        this.focusedSuggestionIndex = (this.focusedSuggestionIndex - 1 + this.currentMatches.length) % this.currentMatches.length;
                        this.updateFocusedSuggestion(container, obj.el);
                    } else if (e.key === 'Enter') {
                        e.preventDefault();
                        if (this.focusedSuggestionIndex !== -1 && container.children[this.focusedSuggestionIndex]) {
                            const selectedPersonData = JSON.parse(container.children[this.focusedSuggestionIndex].dataset.person);
                            this.selectPerson(selectedPersonData, obj.el, obj.advanced);
                            this.hideSuggestions(container, obj.el);
                        }
                    } else if (e.key === 'Escape') {
                        e.preventDefault();
                        this.hideSuggestions(container, obj.el);
                    }
                });
            }
        });

        document.addEventListener('click', (e) => {
            inputs.forEach(obj => {
                const inputEl = obj.el;
                const containerEl = document.getElementById(obj.containerId);
                if (inputEl && containerEl && !inputEl.contains(e.target) && !containerEl.contains(e.target)) {
                    this.hideSuggestions(containerEl, inputEl);
                }
            });
        });
    }
}

// Initialize person search when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('personSearchInput') || document.getElementById('advancedPersonSearchInput')) {
        console.log('Initializing PersonSearch module');
        window.personSearchInstance = new PersonSearch(); // Ensure it's assigned to a unique global var or managed within scope
    }
});
