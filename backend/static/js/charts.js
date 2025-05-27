 * MedicalSpy - Charts module (Refactored)
 * This file contains generic utility functions for creating and updating charts
 * using Chart.js, and managing theme responsiveness for charts.
 */

// Global store for active chart instances
window.medicalSpyCharts = window.medicalSpyCharts || {};

const ChartUtils = {
    // Store for chart instances for easy access and updates
    instances: window.medicalSpyCharts,

    // Default theme-aware colors
    getThemeColors: function(isDark = null) {
        if (isDark === null) {
            isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        }
        return {
            gridColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
            textColor: isDark ? '#f8f9fa' : '#343a40',
            mutedTextColor: isDark ? '#adb5bd' : '#6c757d',
            // Define a palette for chart datasets
            datasetColors: [
                { background: 'rgba(73, 160, 217, 0.7)', border: 'rgba(44, 107, 160, 1)' }, // Blue
                { background: 'rgba(46, 204, 113, 0.7)', border: 'rgba(39, 174, 96, 1)' },  // Green
                { background: 'rgba(243, 156, 18, 0.7)', border: 'rgba(211, 84, 0, 1)' },   // Orange
                { background: 'rgba(231, 76, 60, 0.7)', border: 'rgba(192, 57, 43, 1)' },  // Red
                { background: 'rgba(155, 89, 182, 0.7)', border: 'rgba(142, 68, 173, 1)' }, // Purple
                { background: 'rgba(52, 152, 219, 0.7)', border: 'rgba(41, 128, 185, 1)' }  // Light Blue
            ]
        };
    },

    // Generic chart creation function
    createChart: function(canvasId, type, data, options) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element with ID '${canvasId}' not found.`);
            return null;
        }

        // Destroy existing chart on this canvas, if any
        if (this.instances[canvasId]) {
            this.instances[canvasId].destroy();
        }

        const chart = new Chart(ctx, { type, data, options });
        this.instances[canvasId] = chart;
        
        // Add to global window.charts for theme manager compatibility (if still used by theme-manager.js)
        // Consider removing window.charts if theme-manager.js can directly call ChartUtils.updateAllChartThemes()
        if (window.charts && Array.isArray(window.charts)) {
            const existingChartIndex = window.charts.findIndex(c => c.id === canvasId);
            if (existingChartIndex > -1) {
                window.charts[existingChartIndex].instance = chart;
            } else {
                window.charts.push({ id: canvasId, instance: chart });
            }
        }
        return chart;
    },

    // Update themes for all managed charts
    updateAllChartThemes: function(isDark = null) {
        if (typeof Chart === 'undefined') return;

        const themeColors = this.getThemeColors(isDark);

        // Update Chart.js defaults
        Chart.defaults.color = themeColors.textColor;
        Chart.defaults.borderColor = themeColors.gridColor; // Default border for elements like legend box

        for (const chartId in this.instances) {
            if (Object.hasOwnProperty.call(this.instances, chartId)) {
                const chart = this.instances[chartId];
                if (chart && chart.options) {
                    // Update scales
                    if (chart.options.scales) {
                        Object.keys(chart.options.scales).forEach(axisKey => {
                            const axis = chart.options.scales[axisKey];
                            if (axis.grid) axis.grid.color = themeColors.gridColor;
                            if (axis.ticks) axis.ticks.color = themeColors.mutedTextColor;
                            if (axis.title) axis.title.color = themeColors.textColor;
                        });
                    }
                    // Update legend
                    if (chart.options.plugins && chart.options.plugins.legend) {
                        chart.options.plugins.legend.labels.color = themeColors.textColor;
                    }
                    // Update title
                    if (chart.options.plugins && chart.options.plugins.title) {
                        chart.options.plugins.title.color = themeColors.textColor;
                    }
                    chart.update('none'); // 'none' for no animation
                }
            }
        }
        console.log("Chart themes updated for: ", Object.keys(this.instances));
    },

    // Helper to show an error message in place of a chart
    showChartError: function(canvasId, message = 'Daten konnten nicht geladen werden.') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const container = canvas.parentNode;
        if (!container) return;

        // Destroy existing chart instance if it exists
        if (this.instances[canvasId]) {
            this.instances[canvasId].destroy();
            delete this.instances[canvasId];
        }
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-warning text-center my-3 chart-error-message';
        errorDiv.innerHTML = `<i class="fas fa-exclamation-triangle me-2"></i>${message}`;
        
        // Replace canvas with error message or append if canvas not there
        if (canvas.parentNode === container) {
            container.replaceChild(errorDiv, canvas);
        } else {
            // If canvas was already removed or never there, just append the error.
            // Clear previous error messages for this container
            const existingError = container.querySelector('.chart-error-message');
            if (existingError) existingError.remove();
            container.appendChild(errorDiv);
        }
    }
};

// Expose ChartUtils globally, e.g., for analysis.js to use
window.ChartUtils = ChartUtils;

// Event listener for theme changes to update charts
// This assumes theme-manager.js dispatches a 'themeChanged' event
window.addEventListener('themeChanged', function(event) {
    if (window.ChartUtils && event.detail && typeof event.detail.isDarkMode !== 'undefined') {
        console.log('Theme changed event received by charts.js, updating chart themes.');
        window.ChartUtils.updateAllChartThemes(event.detail.isDarkMode);
    } else if (window.ChartUtils) { // Fallback if event.detail is not as expected
        console.log('Theme changed event received by charts.js (no detail), updating chart themes based on current attribute.');
        window.ChartUtils.updateAllChartThemes();
    }
});

// Fallback for direct DOM attribute changes (e.g. by theme-manager.js initial load)
// This might be redundant if theme-manager.js reliably dispatches 'themeChanged'
// or directly calls ChartUtils.updateAllChartThemes().
if (window.MutationObserver && document.documentElement) {
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.attributeName === 'data-bs-theme') {
                // Prevent double updates if medicalSpyThemeManager is handling it
                if (window.medicalSpyThemeManager && window.medicalSpyThemeManager.isChanging) return;
                
                if (window.ChartUtils) {
                     console.log('data-bs-theme attribute changed, updating chart themes via MutationObserver.');
                    window.ChartUtils.updateAllChartThemes();
                }
            }
        });
    });
    observer.observe(document.documentElement, { attributes: true });
} else {
    console.warn("MutationObserver not available or documentElement not ready for chart theme observing.");
}

console.log('charts.js loaded and ChartUtils initialized.');
