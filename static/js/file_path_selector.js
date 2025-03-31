/**
 * Datei-/Verzeichnisauswahl für das Medical Spytool
 * 
 * Dieses Skript ermöglicht die Auswahl von Dateien und Verzeichnissen
 * mithilfe des nativen Datei-Explorers des Betriebssystems.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialisiere Ordner-Auswahl-Buttons für die Eingabefelder
    initializeFolderSelectors();
});

/**
 * Initialisiert die Ordner-Auswahl für die Pfad-Eingabefelder
 */
function initializeFolderSelectors() {
    // Füge Ordner-Auswahl-Buttons zu den Pfad-Feldern hinzu
    addFolderSelectorToField('output_path', 'Ausgabepfad auswählen');
    addFolderSelectorToField('person_list_path', 'Personenlisten-Pfad auswählen');
}

/**
 * Fügt einen Ordner-Auswahl-Button zu einem Eingabefeld hinzu
 * 
 * @param {string} fieldId - Die ID des Eingabefeldes
 * @param {string} buttonText - Der Text für den Button
 */
function addFolderSelectorToField(fieldId, buttonText) {
    const inputField = document.getElementById(fieldId);
    if (!inputField) return;
    
    // Erstelle Container für Eingabefeld und Button
    const container = document.createElement('div');
    container.className = 'input-group';
    
    // Nimm das Eingabefeld aus dem DOM und füge es dem Container hinzu
    const parent = inputField.parentNode;
    inputField.parentNode.removeChild(inputField);
    container.appendChild(inputField);
    
    // Erstelle und füge den Button hinzu
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn btn-outline-secondary';
    button.innerHTML = '<i class="fas fa-folder-open"></i>';
    button.title = buttonText;
    
    // Event-Listener für den Button
    button.addEventListener('click', function() {
        openFolderDialog(fieldId);
    });
    
    container.appendChild(button);
    
    // Füge den Container an die ursprüngliche Position des Eingabefeldes ein
    parent.appendChild(container);
    
    // Füge auch einen Click-Listener zum Eingabefeld hinzu
    inputField.addEventListener('click', function() {
        openFolderDialog(fieldId);
    });
}

/**
 * Öffnet einen Datei-/Ordner-Dialog über das Backend
 * 
 * @param {string} targetFieldId - Die ID des Ziel-Eingabefeldes
 */
function openFolderDialog(targetFieldId) {
    // Sende eine Anfrage an das Backend, um den Datei-/Ordner-Dialog zu öffnen
    fetch('/select_folder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            field_id: targetFieldId,
            current_path: document.getElementById(targetFieldId).value
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.selected_path) {
            // Aktualisiere das Eingabefeld mit dem ausgewählten Pfad
            document.getElementById(targetFieldId).value = data.selected_path;
        } else if (data.error) {
            console.error('Fehler bei der Ordnerauswahl:', data.error);
        }
    })
    .catch(error => {
        console.error('Fehler bei der Anfrage:', error);
    });
}