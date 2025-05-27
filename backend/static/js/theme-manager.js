/**
 * Central Theme Manager für MedicalSpy
 * Verhindert unkontrollierte Theme-Wechsel und stellt konsistentes Verhalten sicher
 */

(function() {
    'use strict';
    
    // Verhindere mehrfache Initialisierung
    if (window.medicalSpyThemeManager) {
        return;
    }
    
    const THEME_STORAGE_KEY = 'medicalspy-theme';
    const THEME_ATTRIBUTE = 'data-bs-theme';
    
    class ThemeManager {
        constructor() {
            this.isChanging = false;
            this.initialized = false;
            this.htmlElement = document.documentElement;
            this.observers = [];
            
            // Sofortige Theme-Anwendung ohne Flackern
            this.applyStoredThemeImmediately();
            
            // Warte auf DOM-Load für vollständige Initialisierung
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.initialize());
            } else {
                this.initialize();
            }
        }
        
        applyStoredThemeImmediately() {
            const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
            const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
            
            let theme = 'light';
            if (savedTheme === 'dark' || (savedTheme === null && prefersDarkMode)) {
                theme = 'dark';
            }
            
            // Sofortige Anwendung ohne Transition
            this.htmlElement.classList.add('no-transition');
            this.htmlElement.setAttribute(THEME_ATTRIBUTE, theme);
            
            // Entferne no-transition nach kurzer Zeit
            setTimeout(() => {
                this.htmlElement.classList.remove('no-transition');
            }, 50);
        }
        
        initialize() {
            if (this.initialized) return;
            this.initialized = true;
            
            console.log('MedicalSpy Theme Manager initialisiert');
            
            // Setup Theme Toggle Event
            this.setupThemeToggle();
            
            // Setup System Theme Change Listener
            this.setupSystemThemeListener();
            
            // Setup Chart Theme Updates
            this.setupChartThemeUpdates();
            
            // Update initial UI state
            this.updateUIState();
        }
        
        setupThemeToggle() {
            const themeToggle = document.getElementById('theme-toggle');
            if (themeToggle) {
                // Entferne vorherige Event Listener
                themeToggle.removeEventListener('change', this.handleThemeToggle);
                
                // Füge neuen Event Listener hinzu
                this.handleThemeToggle = (event) => {
                    const isDarkMode = event.target.checked;
                    this.setTheme(isDarkMode ? 'dark' : 'light');
                };
                
                themeToggle.addEventListener('change', this.handleThemeToggle);
                
                // Setze korrekten Toggle-Status
                const currentTheme = this.getCurrentTheme();
                themeToggle.checked = currentTheme === 'dark';
            }
        }
        
        setupSystemThemeListener() {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            const handleSystemThemeChange = (e) => {
                // Nur anwenden, wenn keine explizite Benutzereinstellung vorhanden
                if (!localStorage.getItem(THEME_STORAGE_KEY)) {
                    this.setTheme(e.matches ? 'dark' : 'light', false);
                }
            };
            
            mediaQuery.addEventListener('change', handleSystemThemeChange);
        }
        
        setupChartThemeUpdates() {
            // MutationObserver für Chart-Updates nur wenn nötig
            if (typeof Chart !== 'undefined') {
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.type === 'attributes' && 
                            mutation.attributeName === THEME_ATTRIBUTE && 
                            !this.isChanging) {
                            this.updateChartTheme();
                        }
                    });
                });
                
                observer.observe(this.htmlElement, { attributes: true });
                this.observers.push(observer);
            }
        }
        
        getCurrentTheme() {
            return this.htmlElement.getAttribute(THEME_ATTRIBUTE) || 'light';
        }
        
        setTheme(theme, saveToStorage = true) {
            if (this.isChanging) return;
            
            this.isChanging = true;
            const newTheme = theme === 'dark' ? 'dark' : 'light';
            const isDarkMode = newTheme === 'dark';
            
            try {
                // Update HTML attribute
                this.htmlElement.setAttribute(THEME_ATTRIBUTE, newTheme);
                
                // Update toggle state
                const themeToggle = document.getElementById('theme-toggle');
                if (themeToggle) {
                    themeToggle.checked = isDarkMode;
                }
                
                // Save to localStorage
                if (saveToStorage) {
                    localStorage.setItem(THEME_STORAGE_KEY, newTheme);
                }
                
                // Update UI elements
                this.updateUIState();
                
                // Update charts
                this.updateChartTheme();
                
                console.log(`Theme gewechselt zu: ${newTheme}`);
                
            } catch (error) {
                console.error('Fehler beim Theme-Wechsel:', error);
            } finally {
                this.isChanging = false;
            }
        }
        
        updateUIState() {
            const isDarkMode = this.getCurrentTheme() === 'dark';
            
            // Update theme text if present
            const themeText = document.getElementById('theme-mode-text');
            if (themeText) {
                themeText.textContent = isDarkMode ? 'Dark' : 'Light';
            }
            
            // Trigger custom event for other components
            window.dispatchEvent(new CustomEvent('themeChanged', {
                detail: { theme: this.getCurrentTheme(), isDarkMode }
            }));
        }
        
        updateChartTheme() {
            if (typeof Chart === 'undefined' || !window.charts) return;
            
            const isDarkMode = this.getCurrentTheme() === 'dark';
            
            // Update Chart.js defaults
            Chart.defaults.color = isDarkMode ? '#f8f9fa' : '#343a40';
            Chart.defaults.borderColor = isDarkMode ? '#495057' : '#dee2e6';
            
            // Update existing charts
            if (window.charts && Array.isArray(window.charts)) {
                window.charts.forEach(chart => {
                    if (chart && chart.instance) {
                        this.updateSingleChart(chart.instance, isDarkMode);
                    } else if (chart && chart.update) {
                        // Direct chart instance
                        this.updateSingleChart(chart, isDarkMode);
                    }
                });
            }
        }
        
        updateSingleChart(chartInstance, isDarkMode) {
            try {
                const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
                const textColor = isDarkMode ? '#f8f9fa' : '#343a40';
                const mutedTextColor = isDarkMode ? '#adb5bd' : '#6c757d';
                
                // Update scales
                if (chartInstance.options.scales) {
                    Object.keys(chartInstance.options.scales).forEach(axisKey => {
                        const axis = chartInstance.options.scales[axisKey];
                        if (axis.grid) axis.grid.color = gridColor;
                        if (axis.ticks) axis.ticks.color = mutedTextColor;
                        if (axis.title) axis.title.color = textColor;
                    });
                }
                
                // Update legend
                if (chartInstance.options.plugins && chartInstance.options.plugins.legend) {
                    chartInstance.options.plugins.legend.labels.color = textColor;
                }
                
                // Update title
                if (chartInstance.options.plugins && chartInstance.options.plugins.title) {
                    chartInstance.options.plugins.title.color = textColor;
                }
                
                chartInstance.update('none');
            } catch (error) {
                console.warn('Fehler beim Update eines Charts:', error);
            }
        }
        
        destroy() {
            this.observers.forEach(observer => observer.disconnect());
            this.observers = [];
            
            const themeToggle = document.getElementById('theme-toggle');
            if (themeToggle && this.handleThemeToggle) {
                themeToggle.removeEventListener('change', this.handleThemeToggle);
            }
        }
    }
    
    // Globale Instanz erstellen
    window.medicalSpyThemeManager = new ThemeManager();
    
    // Legacy-Support für bestehenden Code
    window.themeManager = window.medicalSpyThemeManager;
    
})();
