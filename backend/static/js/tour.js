/**
 * MedicalSpy Interactive Tour
 * 
 * Diese Datei implementiert ein interaktives Tour-Feature mit einem
 * animierten Maskottchen als Guide durch die Anwendung.
 */

class MedicalSpyTour {
    constructor() {
        this.currentStep = 0;
        this.tourActive = false;
        this.mascotPosition = { x: 20, y: 20 };
        this.tourSteps = [
            {
                target: 'navbar',
                title: 'Willkommen bei MedicalSpy!',
                content: 'Ich bin Ihr virtueller Assistent und werde Sie durch die verschiedenen Funktionen führen. Klicken Sie auf "Weiter", um fortzufahren.',
                placement: 'bottom',
                mascotPosition: { x: 50, y: 70 }
            },
            {
                target: '.nav-link[href*="search"]',
                title: 'Suchfunktion',
                content: 'Hier können Sie nach medizinischen Publikationen suchen. Es gibt drei verschiedene Suchmodi: Einfache Suche, Personensuche und Erweiterte Suche.',
                placement: 'bottom',
                mascotPosition: { x: 200, y: 70 }
            },
            {
                target: '#database-selection',
                title: 'Datenbankauswahl',
                content: 'Wählen Sie eine oder mehrere Datenbanken für Ihre Suche aus. Sie können in PubMed und der Deutschen Nationalbibliothek gleichzeitig suchen.',
                placement: 'right',
                mascotPosition: { x: 100, y: 150 }
            },
            {
                target: '#persons-tab-panel, #persons-tab',
                title: 'Personensuche',
                content: 'Hier können Sie Personen auswählen, nach deren Publikationen Sie suchen möchten. Die Suche funktioniert auch ohne zusätzliche Suchbegriffe.',
                placement: 'top',
                mascotPosition: { x: 300, y: 250 }
            },
            {
                target: '#saved-queries-tab-panel, #saved-queries-tab',
                title: 'Gespeicherte Suchanfragen',
                content: 'Hier finden Sie Ihre gespeicherten Suchanfragen. Sie können diese laden, um frühere Suchen zu wiederholen.',
                placement: 'left',
                mascotPosition: { x: 500, y: 250 }
            },
            {
                target: '.nav-link[href*="results"]',
                title: 'Ergebnisse',
                content: 'Hier werden die Suchergebnisse angezeigt. Sie können sie nach verschiedenen Kriterien filtern und sortieren.',
                placement: 'bottom',
                mascotPosition: { x: 300, y: 70 }
            },
            {
                target: '.nav-link[href*="analysis"]',
                title: 'Analyse',
                content: 'Hier können Sie Ihre Suchergebnisse analysieren und visualisieren, z.B. nach Erscheinungsjahr oder Autor.',
                placement: 'bottom',
                mascotPosition: { x: 400, y: 70 }
            },
            {
                target: '.nav-link[href*="persons"]',
                title: 'Personenverwaltung',
                content: 'Hier können Sie Personen hinzufügen, bearbeiten oder löschen, nach deren Publikationen Sie suchen möchten.',
                placement: 'bottom',
                mascotPosition: { x: 500, y: 70 }
            },
            {
                target: '.nav-link[href*="settings"]',
                title: 'Einstellungen',
                content: 'Hier können Sie API-Schlüssel konfigurieren und andere Einstellungen vornehmen.',
                placement: 'bottom',
                mascotPosition: { x: 600, y: 70 }
            },
            {
                target: '.nav-link[href*="log"]',
                title: 'Protokoll',
                content: 'Hier finden Sie ein Protokoll aller durchgeführten Aktionen und Suchanfragen.',
                placement: 'bottom',
                mascotPosition: { x: 700, y: 70 }
            },
            {
                target: 'body',
                title: 'Tour beendet!',
                content: 'Sie haben nun einen Überblick über die wichtigsten Funktionen von MedicalSpy. Wenn Sie weitere Fragen haben, starten Sie die Tour jederzeit erneut über das Hilfe-Menü.',
                placement: 'center',
                mascotPosition: { x: 400, y: 300 }
            }
        ];
        
        this.createMascot();
        this.createTourPopup();
        this.createTourControls();
    }
    
    createMascot() {
        // Erstelle das Maskottchen-Element
        this.mascot = document.createElement('div');
        this.mascot.id = 'tour-mascot';
        this.mascot.innerHTML = `
            <svg width="80" height="80" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
                <g id="mascot-body">
                    <!-- Körper -->
                    <circle cx="40" cy="40" r="30" fill="#4a86e8" />
                    <!-- Gesicht -->
                    <circle cx="40" cy="35" r="20" fill="#ffffff" />
                    <!-- Augen -->
                    <circle cx="32" cy="30" r="4" fill="#333333" class="mascot-eye" />
                    <circle cx="48" cy="30" r="4" fill="#333333" class="mascot-eye" />
                    <!-- Mund -->
                    <path d="M30,45 Q40,55 50,45" stroke="#333333" stroke-width="2" fill="none" class="mascot-mouth" />
                    <!-- Brille -->
                    <circle cx="32" cy="30" r="6" stroke="#333333" stroke-width="1.5" fill="none" />
                    <circle cx="48" cy="30" r="6" stroke="#333333" stroke-width="1.5" fill="none" />
                    <line x1="38" y1="30" x2="42" y2="30" stroke="#333333" stroke-width="1.5" />
                    <!-- Stethoskop -->
                    <path d="M25,60 Q15,50 25,40" stroke="#cc0000" stroke-width="2" fill="none" />
                    <circle cx="25" cy="40" r="3" fill="#cc0000" />
                </g>
            </svg>
        `;
        this.mascot.style.position = 'fixed';
        this.mascot.style.zIndex = '9999';
        this.mascot.style.pointerEvents = 'none';
        this.mascot.style.transition = 'all 0.5s ease-in-out';
        this.mascot.style.opacity = '0';
        document.body.appendChild(this.mascot);
        
        // Füge CSS-Animationen für das Maskottchen hinzu
        const style = document.createElement('style');
        style.textContent = `
            @keyframes float {
                0% { transform: translateY(0px); }
                50% { transform: translateY(-10px); }
                100% { transform: translateY(0px); }
            }
            @keyframes blink {
                0% { transform: scaleY(1); }
                20% { transform: scaleY(0.1); }
                25% { transform: scaleY(1); }
                100% { transform: scaleY(1); }
            }
            @keyframes talk {
                0% { d: path('M30,45 Q40,55 50,45'); }
                25% { d: path('M30,48 Q40,55 50,48'); }
                50% { d: path('M30,45 Q40,50 50,45'); }
                75% { d: path('M30,47 Q40,52 50,47'); }
                100% { d: path('M30,45 Q40,55 50,45'); }
            }
            #tour-mascot {
                animation: float 3s infinite ease-in-out;
            }
            #tour-mascot .mascot-eye {
                animation: blink 4s infinite;
            }
            #tour-mascot.talking .mascot-mouth {
                animation: talk 1s infinite;
            }
        `;
        document.head.appendChild(style);
    }
    
    createTourPopup() {
        // Erstelle das Popup für die Tour-Erklärungen
        this.popup = document.createElement('div');
        this.popup.id = 'tour-popup';
        this.popup.innerHTML = `
            <div class="tour-header">
                <h5 class="tour-title"></h5>
                <button type="button" class="btn-close" aria-label="Schließen"></button>
            </div>
            <div class="tour-body">
                <p class="tour-content"></p>
            </div>
            <div class="tour-footer">
                <button type="button" class="btn btn-sm btn-secondary tour-btn-back">Zurück</button>
                <span class="tour-progress"></span>
                <button type="button" class="btn btn-sm btn-primary tour-btn-next">Weiter</button>
            </div>
        `;
        this.popup.style.position = 'fixed';
        this.popup.style.zIndex = '9998';
        this.popup.style.background = 'var(--bs-dark-bg-subtle)';
        this.popup.style.color = 'var(--bs-body-color)';
        this.popup.style.borderRadius = '8px';
        this.popup.style.padding = '15px';
        this.popup.style.boxShadow = '0 5px 15px rgba(0,0,0,0.3)';
        this.popup.style.width = '320px';
        this.popup.style.display = 'none';
        document.body.appendChild(this.popup);
        
        // Stil für Popup-Elemente
        const style = document.createElement('style');
        style.textContent = `
            #tour-popup {
                border: 1px solid var(--bs-border-color);
            }
            #tour-popup .tour-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            #tour-popup .tour-title {
                margin: 0;
            }
            #tour-popup .tour-body {
                margin-bottom: 15px;
            }
            #tour-popup .tour-footer {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            #tour-popup .tour-progress {
                font-size: 12px;
                color: var(--bs-secondary-color);
            }
            .tour-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 9000;
                pointer-events: none;
            }
            .tour-target-highlight {
                position: absolute;
                z-index: 9001;
                box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
                pointer-events: none;
                border-radius: 4px;
                border: 2px solid #4a86e8;
            }
        `;
        document.head.appendChild(style);
        
        // Event-Listener für Popup-Buttons
        this.popup.querySelector('.btn-close').addEventListener('click', () => this.endTour());
        this.popup.querySelector('.tour-btn-next').addEventListener('click', () => this.nextStep());
        this.popup.querySelector('.tour-btn-back').addEventListener('click', () => this.prevStep());
    }
    
    createTourControls() {
        // Erstelle den Tour-Starter-Button
        const navbar = document.querySelector('nav .container');
        if (navbar) {
            const tourBtn = document.createElement('button');
            tourBtn.type = 'button';
            tourBtn.classList.add('btn', 'btn-outline-info', 'btn-sm', 'ms-auto', 'me-2');
            tourBtn.innerHTML = '<i class="fas fa-question-circle me-1"></i> Tour starten';
            tourBtn.addEventListener('click', () => this.startTour());
            
            // Füge den Button zur Navbar hinzu
            const navbarCollapse = navbar.querySelector('.collapse');
            navbar.insertBefore(tourBtn, navbarCollapse);
        }
    }
    
    startTour() {
        this.tourActive = true;
        this.currentStep = 0;
        
        // Erstelle Overlay für Tour
        this.overlay = document.createElement('div');
        this.overlay.classList.add('tour-overlay');
        document.body.appendChild(this.overlay);
        
        // Zeige Maskottchen
        this.mascot.style.opacity = '1';
        
        // Starte mit dem ersten Schritt
        this.showStep(0);
    }
    
    endTour() {
        this.tourActive = false;
        
        // Entferne Overlay und Highlight
        if (this.overlay) {
            this.overlay.remove();
        }
        const highlight = document.querySelector('.tour-target-highlight');
        if (highlight) {
            highlight.remove();
        }
        
        // Verstecke Maskottchen und Popup
        this.mascot.style.opacity = '0';
        this.popup.style.display = 'none';
        
        // Entferne "talking" Klasse vom Maskottchen
        this.mascot.classList.remove('talking');
    }
    
    nextStep() {
        if (this.currentStep < this.tourSteps.length - 1) {
            this.showStep(this.currentStep + 1);
        } else {
            this.endTour();
        }
    }
    
    prevStep() {
        if (this.currentStep > 0) {
            this.showStep(this.currentStep - 1);
        }
    }
    
    showStep(stepIndex) {
        this.currentStep = stepIndex;
        const step = this.tourSteps[stepIndex];
        
        // Update Popup-Inhalt
        this.popup.querySelector('.tour-title').textContent = step.title;
        this.popup.querySelector('.tour-content').textContent = step.content;
        this.popup.querySelector('.tour-progress').textContent = `${stepIndex + 1}/${this.tourSteps.length}`;
        
        // Zeige/verstecke Zurück-Button
        this.popup.querySelector('.tour-btn-back').style.visibility = stepIndex > 0 ? 'visible' : 'hidden';
        
        // Update Text des Weiter-Buttons für den letzten Schritt
        const nextBtn = this.popup.querySelector('.tour-btn-next');
        nextBtn.textContent = stepIndex === this.tourSteps.length - 1 ? 'Fertig' : 'Weiter';
        
        // Finde das Ziel-Element
        let targetElement;
        if (step.target === 'body') {
            targetElement = document.body;
        } else {
            targetElement = document.querySelector(step.target);
        }
        
        if (!targetElement) {
            console.error(`Zielelement nicht gefunden: ${step.target}`);
            this.nextStep();
            return;
        }
        
        // Entferne vorhandenes Highlight
        const existingHighlight = document.querySelector('.tour-target-highlight');
        if (existingHighlight) {
            existingHighlight.remove();
        }
        
        // Erstelle Highlight für das Ziel-Element (außer für body)
        if (step.target !== 'body') {
            const rect = targetElement.getBoundingClientRect();
            const highlight = document.createElement('div');
            highlight.classList.add('tour-target-highlight');
            highlight.style.width = `${rect.width + 8}px`;
            highlight.style.height = `${rect.height + 8}px`;
            highlight.style.top = `${rect.top - 4}px`;
            highlight.style.left = `${rect.left - 4}px`;
            document.body.appendChild(highlight);
            
            // Scrolle zum Ziel, wenn nötig
            if (rect.top < 0 || rect.bottom > window.innerHeight) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }
        
        // Positioniere Maskottchen
        let mascotX = step.mascotPosition ? step.mascotPosition.x : 20;
        let mascotY = step.mascotPosition ? step.mascotPosition.y : 20;
        
        this.mascot.style.left = `${mascotX}px`;
        this.mascot.style.top = `${mascotY}px`;
        
        // Positioniere Popup relativ zum Ziel
        let popupX, popupY;
        
        if (step.target === 'body') {
            // Zentriere das Popup für den body-Target
            popupX = window.innerWidth / 2 - 160;
            popupY = window.innerHeight / 2 - 100;
        } else {
            const rect = targetElement.getBoundingClientRect();
            
            // Positioniere das Popup basierend auf dem Placement
            switch (step.placement) {
                case 'top':
                    popupX = rect.left + rect.width / 2 - 160;
                    popupY = rect.top - 200;
                    break;
                case 'bottom':
                    popupX = rect.left + rect.width / 2 - 160;
                    popupY = rect.bottom + 20;
                    break;
                case 'left':
                    popupX = rect.left - 340;
                    popupY = rect.top + rect.height / 2 - 80;
                    break;
                case 'right':
                    popupX = rect.right + 20;
                    popupY = rect.top + rect.height / 2 - 80;
                    break;
                case 'center':
                    popupX = window.innerWidth / 2 - 160;
                    popupY = window.innerHeight / 2 - 100;
                    break;
                default:
                    popupX = rect.left + rect.width / 2 - 160;
                    popupY = rect.bottom + 20;
            }
        }
        
        // Stelle sicher, dass das Popup innerhalb des Viewports bleibt
        popupX = Math.max(20, Math.min(popupX, window.innerWidth - 340));
        popupY = Math.max(20, Math.min(popupY, window.innerHeight - 200));
        
        // Zeige Popup
        this.popup.style.left = `${popupX}px`;
        this.popup.style.top = `${popupY}px`;
        this.popup.style.display = 'block';
        
        // Starte "Sprechanimation" des Maskottchens
        this.mascot.classList.add('talking');
        
        // Stoppe die Sprechanimation nach 3 Sekunden
        setTimeout(() => {
            this.mascot.classList.remove('talking');
        }, 3000);
    }
}

// Initialisiere die Tour, wenn das DOM vollständig geladen ist
document.addEventListener('DOMContentLoaded', () => {
    // Warte einen Moment, um sicherzustellen, dass andere Skripte geladen sind
    setTimeout(() => {
        window.medicalSpyTour = new MedicalSpyTour();
    }, 500);
});