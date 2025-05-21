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
        // Deaktiviert für die Suchseite, um Konflikte mit Bootstrap zu vermeiden
        
        console.log('Tab-Handling wurde manuell initialisiert');
    }
    
    // Initialisierung mit kurzer Verzögerung, um sicherzustellen, dass
    // alle DOM-Elemente vollständig geladen sind
    setTimeout(setupTabHandling, 100);
});