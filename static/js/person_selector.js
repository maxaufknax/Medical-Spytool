/**
 * Person-Selector für das Medical Spytool
 * 
 * Dieses Skript implementiert eine Autocomplete-Funktion für die Personenauswahl
 * und verwaltet die Liste der ausgewählten Personen als Tags.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialisiere Personenauswahl auf allen relevanten Seiten
    initializePersonSelector();
});

/**
 * Initialisiert die Personenauswahl mit Autocomplete-Funktion
 */
function initializePersonSelector() {
    // Wir suchen nach verschiedenen möglichen Eingabefeldern für die Personensuche
    const personInputs = document.querySelectorAll('.person-autocomplete');
    if (personInputs.length === 0) return;
    
    // Initialisiere jedes Personenauswahlfeld
    personInputs.forEach(personInput => {
        initializeSinglePersonSelector(personInput);
    });
}

/**
 * Initialisiert ein einzelnes Personenauswahlfeld
 */
function initializeSinglePersonSelector(personInput) {
    if (!personInput) return;
    
    // Bestimme den ID-Präfix basierend auf der Eingabefeld-ID
    const prefix = personInput.id.split('_')[0];
    
    // Container für ausgewählte Personen
    const selectedPersonsContainer = document.getElementById(`${prefix}_selected_persons`);
    if (!selectedPersonsContainer) {
        console.error(`Kein Container mit ID "${prefix}_selected_persons" gefunden`);
        return;
    }
    
    // Verstecktes Eingabefeld für die ausgewählten Personen (wird an das Backend übermittelt)
    const selectedPersonsHiddenInput = document.getElementById(`${prefix}_persons_names`);
    if (!selectedPersonsHiddenInput) {
        console.error(`Kein Hidden-Input mit ID "${prefix}_persons_names" gefunden`);
        return;
    }
    
    // Vorschläge-Container
    const suggestionsContainer = document.createElement('div');
    suggestionsContainer.className = 'person-suggestions';
    suggestionsContainer.style.position = 'absolute';
    suggestionsContainer.style.width = personInput.offsetWidth + 'px';
    suggestionsContainer.style.maxHeight = '200px';
    suggestionsContainer.style.overflowY = 'auto';
    suggestionsContainer.style.display = 'none';
    suggestionsContainer.style.zIndex = '1000';
    suggestionsContainer.style.border = '1px solid #dee2e6';
    suggestionsContainer.style.borderRadius = '0.25rem';
    suggestionsContainer.style.backgroundColor = 'var(--bs-body-bg)';
    suggestionsContainer.style.boxShadow = '0 0.5rem 1rem rgba(0, 0, 0, 0.15)';
    personInput.parentNode.appendChild(suggestionsContainer);
    
    // Array für ausgewählte Personen
    let selectedPersons = [];
    
    // Event-Listener für Eingabefeld
    personInput.addEventListener('input', function() {
        const searchTerm = this.value.trim();
        
        if (searchTerm.length < 2) {
            suggestionsContainer.style.display = 'none';
            return;
        }
        
        // Anfrage an Backend für Personenvorschläge
        fetch(`/api/persons?query=${encodeURIComponent(searchTerm)}`)
            .then(response => response.json())
            .then(data => {
                suggestionsContainer.innerHTML = '';
                
                if (data.length === 0) {
                    suggestionsContainer.style.display = 'none';
                    return;
                }
                
                // Vorschläge anzeigen
                data.forEach(person => {
                    // Prüfen, ob die Person bereits ausgewählt ist
                    if (selectedPersons.includes(person.name)) {
                        return;
                    }
                    
                    const div = document.createElement('div');
                    div.className = 'person-suggestion p-2';
                    div.textContent = person.name;
                    div.style.cursor = 'pointer';
                    div.style.borderBottom = '1px solid #dee2e6';
                    div.style.transition = 'background-color 0.15s ease-in-out';
                    
                    div.addEventListener('mouseenter', function() {
                        this.style.backgroundColor = 'var(--bs-primary-bg-subtle)';
                    });
                    
                    div.addEventListener('mouseleave', function() {
                        this.style.backgroundColor = '';
                    });
                    
                    div.addEventListener('click', function() {
                        // Person zur Liste hinzufügen
                        addPerson(person);
                        
                        // Eingabefeld leeren und Vorschläge ausblenden
                        personInput.value = '';
                        suggestionsContainer.style.display = 'none';
                    });
                    
                    suggestionsContainer.appendChild(div);
                });
                
                // Vorschläge-Container anzeigen
                suggestionsContainer.style.display = 'block';
            })
            .catch(error => {
                console.error('Fehler beim Abrufen der Personenvorschläge:', error);
            });
    });
    
    // Klick außerhalb schließt die Vorschläge
    document.addEventListener('click', function(event) {
        if (!personInput.contains(event.target) && !suggestionsContainer.contains(event.target)) {
            suggestionsContainer.style.display = 'none';
        }
    });
    
    /**
     * Fügt eine Person zur Liste der ausgewählten Personen hinzu
     */
    function addPerson(person) {
        // Prüfen, ob die Person bereits ausgewählt ist
        if (selectedPersons.includes(person.name)) {
            return;
        }
        
        // Person zum Array hinzufügen
        selectedPersons.push(person.name);
        
        // Badge erstellen
        const badge = document.createElement('span');
        badge.className = 'badge bg-primary me-2 mb-2';
        badge.style.fontSize = '100%';
        badge.style.display = 'inline-flex';
        badge.style.alignItems = 'center';
        
        // Person-Name
        const nameSpan = document.createElement('span');
        nameSpan.textContent = person.name;
        badge.appendChild(nameSpan);
        
        // Entfernen-Button
        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.className = 'btn-close ms-2';
        removeButton.style.fontSize = '0.65em';
        removeButton.style.marginLeft = '5px';
        removeButton.setAttribute('aria-label', 'Entfernen');
        
        removeButton.addEventListener('click', function() {
            // Person aus dem Array entfernen
            selectedPersons = selectedPersons.filter(p => p !== person.name);
            
            // Badge entfernen
            badge.remove();
            
            // Verstecktes Eingabefeld aktualisieren
            updateHiddenInput();
        });
        
        badge.appendChild(removeButton);
        
        // Badge zum Container hinzufügen
        selectedPersonsContainer.appendChild(badge);
        
        // Verstecktes Eingabefeld aktualisieren
        updateHiddenInput();
    }
    
    /**
     * Aktualisiert das versteckte Eingabefeld mit den ausgewählten Personen
     */
    function updateHiddenInput() {
        selectedPersonsHiddenInput.value = JSON.stringify(selectedPersons);
        
        // Aktualisiere den Platzhaltertext
        const placeholderText = selectedPersonsContainer.querySelector('.text-muted.small.fst-italic');
        if (placeholderText) {
            if (selectedPersons.length > 0) {
                placeholderText.style.display = 'none';
            } else {
                placeholderText.style.display = 'block';
            }
        }
    }
    
    // Initialisiere bereits vorhandene Personen (z.B. nach Formular-Submit)
    if (selectedPersonsHiddenInput.value) {
        try {
            const savedPersons = JSON.parse(selectedPersonsHiddenInput.value);
            
            if (Array.isArray(savedPersons)) {
                savedPersons.forEach(personName => {
                    if (personName) {
                        addPerson({ name: personName });
                    }
                });
            }
        } catch (e) {
            console.error('Fehler beim Parsieren der gespeicherten Personen:', e);
        }
    }
}