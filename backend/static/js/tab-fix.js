/**
 * Tab-Fix für MedicalSpy
 * 
 * Dieses Skript stellt sicher, dass die Bootstrap-Tabs korrekt funktionieren,
 * selbst wenn es Probleme mit der Bootstrap-Tab-Initialisierung geben sollte.
 */

// Warten, bis das DOM vollständig geladen ist
document.addEventListener('DOMContentLoaded', function() {
    console.log('Tab-Fix wird initialisiert...');
    
    // Manuelles Handling der Tab-Funktionalität
    function setupTabHandling() {
        const searchModeTabs = document.querySelectorAll('#searchModeTabs .nav-link');
        
        // Für jeden Tab einen Click-Handler registrieren
        searchModeTabs.forEach(tab => {
            tab.addEventListener('click', function(event) {
                event.preventDefault();
                
                console.log('Tab geklickt:', this.id, 'target:', this.getAttribute('href'));
                
                // Alle Tabs deaktivieren
                searchModeTabs.forEach(t => {
                    t.classList.remove('active');
                });
                
                // Diesen Tab aktivieren
                this.classList.add('active');
                
                // Alle Tab-Inhalte ausblenden
                document.querySelectorAll('.tab-content > .tab-pane').forEach(pane => {
                    pane.classList.remove('active');
                    pane.classList.remove('show');
                });
                
                // Ziel-Tab-Inhalt anzeigen
                const targetId = this.getAttribute('href').substring(1);
                const targetPane = document.getElementById(targetId);
                
                if (targetPane) {
                    targetPane.classList.add('active');
                    targetPane.classList.add('show');
                    console.log('Tab-Inhalt aktiviert:', targetId);
                    
                    // Update hidden field
                    const searchModeField = document.getElementById('searchMode');
                    if (searchModeField) {
                        if (this.id === 'simple-search-tab') {
                            searchModeField.value = 'simple';
                        } else if (this.id === 'person-search-tab') {
                            searchModeField.value = 'person';
                        } else if (this.id === 'advanced-search-tab') {
                            searchModeField.value = 'advanced';
                        } else if (this.id === 'saved-queries-tab') {
                            searchModeField.value = 'saved';
                        }
                    }
                } else {
                    console.error('Tab-Inhalt nicht gefunden:', targetId);
                }
            });
        });
        
        console.log('Tab-Handling wurde manuell initialisiert');
    }
    
    // Initialisierung mit kurzer Verzögerung, um sicherzustellen, dass
    // alle DOM-Elemente vollständig geladen sind
    setTimeout(setupTabHandling, 100);
});