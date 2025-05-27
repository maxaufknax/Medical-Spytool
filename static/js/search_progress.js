/**
 * Search Progress Tracking Module
 */
class SearchProgressTracker {
    constructor() {
        this.progress = 0;
        this.isSearching = false;
        this.currentDatabase = '';
        this.logEntries = [];
        this.progressBar = document.getElementById('searchProgressBar');
        this.statusElement = document.getElementById('currentDatabaseStatus');
        this.logElement = document.getElementById('searchLog');
        this.cancelButton = document.getElementById('cancelSearch');
        
        // Event-Listener für Statusaktualisierungen
        window.addEventListener('search-progress', (e) => this.updateProgress(e.detail));
        window.addEventListener('search-status', (e) => this.updateStatus(e.detail));
        window.addEventListener('search-complete', () => this.completeSearch());
        window.addEventListener('search-error', (e) => this.handleError(e.detail));
    }
    
    start() {
        this.isSearching = true;
        this.progress = 0;
        this.logEntries = [];
        this.updateProgressBar(0);
        
        if (this.cancelButton) {
            this.cancelButton.addEventListener('click', () => this.cancelSearch());
        }
        
        // Initialisiere UI-Elemente
        this.initializeUI();
        
        // Starte Fortschrittsanimation
        this.animateProgress();
    }
    
    stop() {
        this.isSearching = false;
        this.updateProgressBar(100);
        
        if (this.cancelButton) {
            this.cancelButton.removeEventListener('click', () => this.cancelSearch());
        }
    }
    
    updateProgress(progress) {
        if (!this.isSearching) return;
        
        this.progress = Math.min(progress, 90); // Maximal 90% bis zum kompletten Abschluss
        this.updateProgressBar(this.progress);
    }
    
    updateStatus(status) {
        const { database, message } = status;
        
        if (this.statusElement && database) {
            this.statusElement.textContent = `Durchsuche ${database}...`;
        }
        
        if (this.logElement && message) {
            this.addLogEntry(message);
        }
    }
    
    addLogEntry(message) {
        const entry = {
            timestamp: new Date().toLocaleTimeString(),
            message: message
        };
        
        this.logEntries.push(entry);
        
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `
            <span class="text-muted">[${entry.timestamp}]</span>
            <span class="ms-2">${entry.message}</span>
        `;
        
        this.logElement.appendChild(logEntry);
        this.logElement.scrollTop = this.logElement.scrollHeight;
    }
    
    updateProgressBar(progress) {
        if (this.progressBar) {
            this.progressBar.style.width = `${progress}%`;
            this.progressBar.setAttribute('aria-valuenow', progress);
            this.progressBar.textContent = `${Math.round(progress)}%`;
        }
    }
    
    animateProgress() {
        if (!this.isSearching) return;
        
        // Simuliere Fortschritt basierend auf aktuellem Stand
        const increment = Math.random() * 15;
        const newProgress = Math.min(this.progress + increment, 90);
        this.progress = newProgress;
        
        this.updateProgressBar(newProgress);
        
        // Fortschrittsanimation fortsetzen
        if (this.isSearching) {
            setTimeout(() => this.animateProgress(), 500 + Math.random() * 1000);
        }
    }
    
    completeSearch() {
        this.isSearching = false;
        this.updateProgressBar(100);
        
        if (this.statusElement) {
            this.statusElement.textContent = 'Suche abgeschlossen';
        }
        
        this.addLogEntry('Suche erfolgreich beendet');
    }
    
    handleError(error) {
        this.isSearching = false;
        this.updateProgressBar(0);
        
        if (this.statusElement) {
            this.statusElement.textContent = 'Fehler bei der Suche';
        }
        
        this.addLogEntry(`Fehler: ${error.message || 'Unbekannter Fehler'}`);
    }
    
    async cancelSearch() {
        try {
            const response = await fetch('/cancel_search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                throw new Error('Fehler beim Abbrechen der Suche');
            }
            
            this.stop();
            this.addLogEntry('Suche wurde abgebrochen');
            
            // Benachrichtigung an das Haupt-Suchmodul
            window.dispatchEvent(new CustomEvent('search-cancelled'));
        } catch (error) {
            console.error('Error canceling search:', error);
            this.handleError({message: 'Fehler beim Abbrechen der Suche'});
        }
    }
    
    initializeUI() {
        const detailsPanel = document.getElementById('searchDetailsPanel');
        const toggleBtn = document.getElementById('toggleSearchDetails');
        
        if (toggleBtn && detailsPanel) {
            toggleBtn.addEventListener('click', () => {
                const collapse = new bootstrap.Collapse(detailsPanel);
                const icon = toggleBtn.querySelector('i');
                if (icon) {
                    icon.classList.toggle('fa-chevron-down');
                    icon.classList.toggle('fa-chevron-up');
                }
            });
        }
    }
}

// Erstelle eine globale Instanz des Progress Trackers
window.searchProgressTracker = new SearchProgressTracker();