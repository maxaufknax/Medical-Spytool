/**
 * Set up global keyboard shortcuts for faster navigation
 * These shortcuts are designed to work consistently across the application
 */
function setupGlobalShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Don't trigger shortcuts when typing in form fields
        if (document.activeElement.tagName === 'INPUT' || 
            document.activeElement.tagName === 'TEXTAREA' || 
            document.activeElement.tagName === 'SELECT') {
            return;
        }
        
        // Alt+? shows keyboard shortcut help
        if (e.altKey && e.key === '?') {
            e.preventDefault();
            showKeyboardShortcutHelp();
            return;
        }
          // Navigation shortcuts
        if (e.altKey) {
            const shortcuts = {
                'h': '/',                   // Home
                's': '/search',             // Search
                'r': '/results',            // Results
                'a': '/analysis',           // Analysis
                'p': '/persons',            // Persons
                'l': '/log',                // Log
                'u': '/settings',           // Settings (u for user settings)
                'd': '/docs',               // Documentation
                'i': '/info',               // Information/About
                'n': '/new',                // New record/entry
                'e': '/export',             // Export
                'c': '/contact',            // Contact
            };
            
            if (shortcuts[e.key.toLowerCase()]) {
                e.preventDefault();
                // Find link with this href or navigate directly
                const link = document.querySelector(`a[href="${shortcuts[e.key.toLowerCase()]}"]`);
                if (link) {
                    link.click();
                } else {
                    window.location.href = shortcuts[e.key.toLowerCase()];
                }
            }
        }
        
        // Function key shortcuts (F1-F12)
        switch (e.key) {
            case 'F1':
                e.preventDefault();
                showKeyboardShortcutHelp();
                break;
        }
    });
}

/**
 * Display a modal with keyboard shortcuts help
 */
function showKeyboardShortcutHelp() {
    // Create modal if it doesn't exist
    let helpModal = document.getElementById('keyboard-shortcuts-help');
    
    if (!helpModal) {
        // Create the modal
        helpModal = document.createElement('div');
        helpModal.id = 'keyboard-shortcuts-help';
        helpModal.className = 'modal fade';
        helpModal.setAttribute('tabindex', '-1');
        helpModal.setAttribute('role', 'dialog');
        helpModal.setAttribute('aria-labelledby', 'keyboard-shortcuts-title');
        
        helpModal.innerHTML = `
            <div class="modal-dialog modal-lg" role="document">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="keyboard-shortcuts-title">Tastaturkürzel</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Schließen"></button>
                    </div>
                    <div class="modal-body">
                        <h6>Navigation</h6>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Tastenkombination</th>
                                    <th>Funktion</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>H</kbd></td>
                                    <td>Zur Startseite</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>S</kbd></td>
                                    <td>Zur Suche</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>R</kbd></td>
                                    <td>Zu den Ergebnissen</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>A</kbd></td>
                                    <td>Zur Analyse</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>P</kbd></td>
                                    <td>Zur Personenverwaltung</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>U</kbd></td>
                                    <td>Zu den Einstellungen</td>
                                </tr>                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>L</kbd></td>
                                    <td>Zum Protokoll</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>D</kbd></td>
                                    <td>Zur Dokumentation</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>I</kbd></td>
                                    <td>Zur Info/Über-Seite</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>N</kbd></td>
                                    <td>Neuer Eintrag erstellen</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>E</kbd></td>
                                    <td>Zum Export</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>C</kbd></td>
                                    <td>Zum Kontakt</td>
                                </tr>
                                <tr>
                                    <td><kbd>Alt</kbd> + <kbd>?</kbd> oder <kbd>F1</kbd></td>
                                    <td>Diese Hilfe anzeigen</td>
                                </tr>
                            </tbody>
                        </table>
                        
                        <h6>Tabellen-Navigation</h6>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Tastenkombination</th>
                                    <th>Funktion</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><kbd>Pfeil hoch</kbd> / <kbd>Pfeil runter</kbd></td>
                                    <td>Zeile auf/ab</td>
                                </tr>
                                <tr>
                                    <td><kbd>Tab</kbd></td>
                                    <td>Zur nächsten interaktiven Zelle</td>
                                </tr>
                                <tr>
                                    <td><kbd>Eingabe</kbd></td>
                                    <td>Element aktivieren/auswählen</td>
                                </tr>
                                <tr>
                                    <td><kbd>Strg</kbd> + <kbd>Home</kbd></td>
                                    <td>Zum Tabellenanfang</td>
                                </tr>
                                <tr>
                                    <td><kbd>Strg</kbd> + <kbd>End</kbd></td>
                                    <td>Zum Tabellenende</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Schließen</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(helpModal);
    }
    
    // Show the modal
    const modal = new bootstrap.Modal(helpModal);
    modal.show();
}
