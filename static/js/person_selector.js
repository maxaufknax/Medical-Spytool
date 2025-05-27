/**
 * Person-Selector für das Medical Spytool
 */
document.addEventListener('DOMContentLoaded', function() {
    initializePersonSelector();
});

const PersonState = {
    selectedPersons: new Map(),
    
    add(prefix, person) {
        if (!this.selectedPersons.has(prefix)) {
            this.selectedPersons.set(prefix, new Set());
        }
        this.selectedPersons.get(prefix).add(person);
        this.updateUI(prefix);
    },
    
    remove(prefix, personName) {
        const persons = this.selectedPersons.get(prefix);
        if (persons) {
            persons.delete(personName);
            this.updateUI(prefix);
        }
    },
    
    get(prefix) {
        return Array.from(this.selectedPersons.get(prefix) || []);
    },
    
    updateUI(prefix) {
        const container = document.getElementById(`${prefix}_selected_persons`);
        const hiddenInput = document.getElementById(`${prefix}_persons_names`);
        if (!container || !hiddenInput) return;
        
        // Container leeren
        container.innerHTML = '';
        
        // Aktuelle Auswahl abrufen
        const selectedPersons = this.get(prefix);
        
        if (selectedPersons.length === 0) {
            // Wenn keine Auswahl, zeige Nachricht
            container.innerHTML = '<div class="text-muted small fst-italic">Keine Personen ausgewählt</div>';
        } else {
            // Füge für jede Person ein Badge hinzu
            selectedPersons.forEach(person => {
                const badge = createPersonBadge(person, () => this.remove(prefix, person.name));
                container.appendChild(badge);
            });
        }
        
        // Hidden Input aktualisieren
        hiddenInput.value = selectedPersons.map(p => p.name).join(',');
    },
    
    clear(prefix) {
        this.selectedPersons.set(prefix, new Set());
        this.updateUI(prefix);
    }
};

function initializePersonSelector() {
    const personInputs = document.querySelectorAll('.person-autocomplete');
    if (!personInputs.length) return;
    
    personInputs.forEach(input => {
        initializeSinglePersonSelector(input);
    });
}

function initializeSinglePersonSelector(input) {
    if (!input) return;
    
    const prefix = input.id.split('_')[0];
    const container = input.parentElement;
    if (!container) return;
    
    // Vorschläge-Container erstellen
    const suggestionsContainer = container.querySelector('.person-autocomplete-items') || 
                               createSuggestionsContainer(input);
    
    // Debounced Fetch Funktion für Vorschläge
    const debouncedFetch = debounce(fetchPersonSuggestions, 300);
    
    // Input Handler
    input.addEventListener('input', async function() {
        if (!this.value.trim()) {
            hideSuggestions(suggestionsContainer);
            return;
        }
        
        try {
            const persons = await debouncedFetch(this.value);
            updateSuggestions(persons, suggestionsContainer, prefix);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
        }
    });
    
    // Klick außerhalb schließt Vorschläge
    document.addEventListener('click', function(event) {
        if (!container.contains(event.target)) {
            hideSuggestions(suggestionsContainer);
        }
    });
    
    // Tastatur-Navigation
    input.addEventListener('keydown', function(e) {
        handleKeyboardNavigation(e, suggestionsContainer, prefix);
    });
}

function createSuggestionsContainer(input) {
    const container = document.createElement('div');
    container.className = 'person-autocomplete-items';
    input.parentNode.appendChild(container);
    return container;
}

function createPersonBadge(person, onRemove) {
    const badge = document.createElement('span');
    badge.className = 'selected-person-badge';
    badge.innerHTML = `
        ${person.name}
        <button type="button" class="btn-close btn-close-white ms-2" aria-label="Entfernen"></button>
    `;
    
    const removeBtn = badge.querySelector('.btn-close');
    removeBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        onRemove();
    });
    
    return badge;
}

async function fetchPersonSuggestions(searchTerm) {
    try {
        const response = await fetch(`/api/persons?query=${encodeURIComponent(searchTerm)}`);
        if (!response.ok) throw new Error('Netzwerkfehler bei der Personensuche');
        return await response.json();
    } catch (error) {
        console.error('Fehler beim Laden der Personenvorschläge:', error);
        return [];
    }
}

function updateSuggestions(persons, container, prefix) {
    container.innerHTML = '';
    
    if (!persons.length) {
        const noResults = document.createElement('div');
        noResults.className = 'p-2 text-muted';
        noResults.textContent = 'Keine Personen gefunden';
        container.appendChild(noResults);
        return;
    }
    
    persons.forEach((person, index) => {
        const div = document.createElement('div');
        div.className = 'person-suggestion p-2';
        if (index === currentFocus) div.classList.add('person-autocomplete-active');
        
        const nameEl = document.createElement('div');
        nameEl.className = 'person-name';
        nameEl.textContent = person.Name;
        
        const detailsEl = document.createElement('div');
        detailsEl.className = 'person-details small text-muted';
        detailsEl.textContent = `${person['Search Term'] || ''} ${person['Additional Terms'] || ''}`.trim();
        
        div.appendChild(nameEl);
        if (detailsEl.textContent) div.appendChild(detailsEl);
        
        div.addEventListener('click', () => {
            PersonState.add(prefix, {
                name: person.Name,
                searchTerm: person['Search Term'],
                additionalTerms: person['Additional Terms']
            });
            container.style.display = 'none';
        });
        
        container.appendChild(div);
    });
    
    container.style.display = 'block';
}

function hideSuggestions(container) {
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
    }
    currentFocus = -1;
}

function handleKeyboardNavigation(event, container, prefix) {
    const suggestions = container.getElementsByClassName('person-suggestion');
    if (!suggestions.length) return;
    
    switch (event.key) {
        case 'ArrowDown':
            currentFocus++;
            addActive(suggestions);
            break;
            
        case 'ArrowUp':
            currentFocus--;
            addActive(suggestions);
            break;
            
        case 'Enter':
            event.preventDefault();
            if (currentFocus > -1 && suggestions[currentFocus]) {
                suggestions[currentFocus].click();
            }
            break;
            
        case 'Escape':
            hideSuggestions(container);
            break;
    }
}

function addActive(suggestions) {
    if (!suggestions) return false;
    
    removeActive(suggestions);
    
    if (currentFocus >= suggestions.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = suggestions.length - 1;
    
    suggestions[currentFocus].classList.add('person-autocomplete-active');
}

function removeActive(suggestions) {
    Array.from(suggestions).forEach(suggestion => {
        suggestion.classList.remove('person-autocomplete-active');
    });
}

let currentFocus = -1;

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}