// export_page.js - Funktionen für die Export-Seite

document.addEventListener('DOMContentLoaded', function() {
    // Dateipfad-Auswahl für Export-Pfad
    const chooseOutputPathBtn = document.getElementById('choose_output_path');
    const outputPathInput = document.getElementById('output_path');
    
    if (chooseOutputPathBtn && outputPathInput) {
        chooseOutputPathBtn.addEventListener('click', function() {
            // Ein Dateiauswahl-Dialog kann in einer Web-Anwendung nicht direkt 
            // auf das Dateisystem des Servers zugreifen, daher simulieren wir 
            // dies mit einem Modal-Dialog
            showFolderSelectionDialog(outputPathInput.value, function(selectedPath) {
                outputPathInput.value = selectedPath;
            });
        });
    }
    
    // Prüfen, ob alle/keine Spalten ausgewählt werden sollen
    const selectAllColumnsBtn = document.getElementById('select_all_columns');
    const clearAllColumnsBtn = document.getElementById('clear_all_columns');
    const columnCheckboxes = document.querySelectorAll('input[name="output_columns"]');
    
    if (selectAllColumnsBtn) {
        selectAllColumnsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            columnCheckboxes.forEach(checkbox => checkbox.checked = true);
        });
    }
    
    if (clearAllColumnsBtn) {
        clearAllColumnsBtn.addEventListener('click', function(e) {
            e.preventDefault();
            columnCheckboxes.forEach(checkbox => checkbox.checked = false);
        });
    }
});

// Simulierte Funktion für Ordnerauswahl (da wir in einer Web-Anwendung keinen direkten Zugriff auf das Dateisystem haben)
function showFolderSelectionDialog(currentPath, callback) {
    // Erstelle das Modal dynamisch
    const modalId = 'folderSelectionModal';
    let modal = document.getElementById(modalId);
    
    if (!modal) {
        const modalHTML = `
            <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="${modalId}Label" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="${modalId}Label">Ordner auswählen</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Schließen"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <label for="folder_path" class="form-label">Pfad eingeben</label>
                                <input type="text" class="form-control" id="folder_path" value="">
                                <small class="form-text">Geben Sie einen absoluten oder relativen Pfad ein.</small>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Häufige Verzeichnisse</label>
                                <div class="list-group">
                                    <button type="button" class="list-group-item list-group-item-action" data-path="./output">./output (Standard)</button>
                                    <button type="button" class="list-group-item list-group-item-action" data-path="./exports">./exports</button>
                                    <button type="button" class="list-group-item list-group-item-action" data-path="./downloads">./downloads</button>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Abbrechen</button>
                            <button type="button" class="btn btn-primary" id="select_folder_btn">Auswählen</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Füge das Modal zum Body hinzu
        const div = document.createElement('div');
        div.innerHTML = modalHTML;
        document.body.appendChild(div.firstChild);
        
        modal = document.getElementById(modalId);
        
        // Event-Listener für die Standardpfade
        const pathButtons = modal.querySelectorAll('.list-group-item');
        pathButtons.forEach(button => {
            button.addEventListener('click', function() {
                document.getElementById('folder_path').value = this.getAttribute('data-path');
            });
        });
    }
    
    // Setze den aktuellen Pfad
    document.getElementById('folder_path').value = currentPath;
    
    // Bootstrap Modal erstellen
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Event-Listener für den Auswahl-Button
    const selectBtn = document.getElementById('select_folder_btn');
    selectBtn.onclick = function() {
        const selectedPath = document.getElementById('folder_path').value;
        bsModal.hide();
        if (callback) callback(selectedPath);
    };
}