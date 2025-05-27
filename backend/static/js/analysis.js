/**
 * MedicalSpy - Analysis module
 * This file contains functions for data analysis and visualization.
 */

// Initialize charts on page load
document.addEventListener('DOMContentLoaded', function() {
    // Load year distribution data
    fetchYearDistribution();
    
    // Load database distribution data
    fetchDatabaseDistribution();
    
    // Load top authors data
    fetchTopAuthors();
    
    // Register charts for theme updates - verwendet das zentrale Theme-Management
    window.addEventListener('themeChanged', function(event) {
        const { isDarkMode } = event.detail;
        updateAllCharts(isDarkMode);
    });
    
    // Fallback für direkte DOM-Änderungen (für Rückwärtskompatibilität)
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.attributeName === 'data-bs-theme') {
                // Verwende das zentrale Theme-Management, falls verfügbar
                if (!window.medicalSpyThemeManager || !window.medicalSpyThemeManager.isChanging) {
                    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
                    updateAllCharts(isDark);
                }
            }
        });
    });
    
    observer.observe(document.documentElement, { attributes: true });
});

// Fetch year distribution data
function fetchYearDistribution() {
    const searchId = document.getElementById('analysisPage')?.dataset.searchId;
    if (!searchId) return;
    
    fetch(`/api/analysis/years?search_id=${searchId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                renderYearChart(data.data.years);
            } else {
                showChartError('yearChart');
            }
        })
        .catch(error => {
            console.error('Error fetching year distribution:', error);
            showChartError('yearChart');
        });
}

// Fetch database distribution data
function fetchDatabaseDistribution() {
    const searchId = document.getElementById('analysisPage')?.dataset.searchId;
    if (!searchId) return;
    
    // This is a simple example that would use the results directly from the page
    // In a real API implementation, you would fetch this data from an endpoint
    const databases = {};
    const results = JSON.parse(document.getElementById('analysisPage').dataset.results || '[]');
    
    results.forEach(result => {
        const database = result.Datenbank || result.Database || 'Unknown';
        databases[database] = (databases[database] || 0) + 1;
    });
    
    renderDatabaseChart(databases);
}

// Fetch top authors data
function fetchTopAuthors() {
    const searchId = document.getElementById('analysisPage')?.dataset.searchId;
    if (!searchId) return;
    
    fetch(`/api/analysis/authors?search_id=${searchId}&limit=10`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                renderTopAuthorsChart(data.data.authors);
            } else {
                showChartError('authorsChart');
            }
        })
        .catch(error => {
            console.error('Error fetching top authors:', error);
            showChartError('authorsChart');
        });
}

// Render year distribution chart
function renderYearChart(yearData) {
    const ctx = document.getElementById('yearChart');
    if (!ctx) return;
    
    // Convert the object to arrays for Chart.js
    const years = Object.keys(yearData).sort();
    const counts = years.map(year => yearData[year]);
    
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const textColor = isDark ? '#f8f9fa' : '#343a40';
    
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: years,
            datasets: [{
                label: 'Publications',
                data: counts,
                backgroundColor: 'rgba(73, 160, 217, 0.7)',
                borderColor: 'rgba(44, 107, 160, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        color: textColor,
                        precision: 0
                    },
                    title: {
                        display: true,
                        text: 'Number of Publications',
                        color: textColor
                    }
                },
                x: {
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        color: textColor
                    },
                    title: {
                        display: true,
                        text: 'Year',
                        color: textColor
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: textColor
                    }
                },
                title: {
                    display: true,
                    text: 'Publications by Year',
                    color: textColor
                }
            }
        }
    });
    
    // Register chart for dark mode updates
    window.charts.push({ id: 'yearChart', instance: chart });
}

// Render database distribution chart
function renderDatabaseChart(databaseData) {
    const ctx = document.getElementById('databaseChart');
    if (!ctx) return;
    
    // Convert the object to arrays for Chart.js
    const databases = Object.keys(databaseData);
    const counts = databases.map(db => databaseData[db]);
    
    // Generate colors
    const backgroundColors = [
        'rgba(73, 160, 217, 0.7)',
        'rgba(46, 204, 113, 0.7)',
        'rgba(243, 156, 18, 0.7)',
        'rgba(231, 76, 60, 0.7)',
        'rgba(155, 89, 182, 0.7)',
        'rgba(52, 152, 219, 0.7)',
        'rgba(243, 104, 224, 0.7)',
        'rgba(250, 130, 49, 0.7)',
        'rgba(39, 174, 96, 0.7)',
        'rgba(41, 128, 185, 0.7)'
    ];
    
    const borderColors = [
        'rgba(44, 107, 160, 1)',
        'rgba(39, 174, 96, 1)',
        'rgba(211, 84, 0, 1)',
        'rgba(192, 57, 43, 1)',
        'rgba(142, 68, 173, 1)',
        'rgba(41, 128, 185, 1)',
        'rgba(155, 89, 182, 1)',
        'rgba(230, 126, 34, 1)',
        'rgba(22, 160, 133, 1)',
        'rgba(40, 116, 166, 1)'
    ];
    
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const textColor = isDark ? '#f8f9fa' : '#343a40';
    
    const chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: databases,
            datasets: [{
                data: counts,
                backgroundColor: backgroundColors.slice(0, databases.length),
                borderColor: borderColors.slice(0, databases.length),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: textColor
                    }
                },
                title: {
                    display: true,
                    text: 'Publications by Database',
                    color: textColor
                }
            }
        }
    });
    
    // Register chart for dark mode updates
    window.charts.push({ id: 'databaseChart', instance: chart });
}

// Render top authors chart
function renderTopAuthorsChart(authorsData) {
    const ctx = document.getElementById('authorsChart');
    if (!ctx) return;
    
    // Process the data
    const authors = authorsData.map(item => item.name);
    const counts = authorsData.map(item => item.count);
    
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const textColor = isDark ? '#f8f9fa' : '#343a40';
    
    const chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: authors,
            datasets: [{
                label: 'Publications',
                data: counts,
                backgroundColor: 'rgba(46, 204, 113, 0.7)',
                borderColor: 'rgba(39, 174, 96, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        color: textColor,
                        precision: 0
                    },
                    title: {
                        display: true,
                        text: 'Number of Publications',
                        color: textColor
                    }
                },
                y: {
                    grid: {
                        color: gridColor
                    },
                    ticks: {
                        color: textColor
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Top Contributing Authors',
                    color: textColor
                }
            }
        }
    });
    
    // Register chart for dark mode updates
    window.charts.push({ id: 'authorsChart', instance: chart });
}

// Show error message when chart data cannot be loaded
function showChartError(chartId) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    
    const container = canvas.parentNode;
    
    // Create error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-warning text-center my-3';
    errorDiv.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Daten konnten nicht geladen werden.';
    
    // Replace canvas with error message
    container.replaceChild(errorDiv, canvas);
}

// Update all charts for dark/light mode - verwendet zentrales Theme-Management
function updateAllCharts(isDark = null) {
    // Verwende das zentrale Theme-Management, wenn verfügbar
    if (window.medicalSpyThemeManager) {
        window.medicalSpyThemeManager.updateChartTheme();
        return;
    }
    
    // Fallback für direktes Update
    if (isDark === null) {
        isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    }
    
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const textColor = isDark ? '#f8f9fa' : '#343a40';
    
    if (window.charts && window.charts.length) {
        window.charts.forEach(chart => {
            if (chart.instance) {
                // Update scales if they exist
                if (chart.instance.options.scales) {
                    Object.keys(chart.instance.options.scales).forEach(axisKey => {
                        const axis = chart.instance.options.scales[axisKey];
                        if (axis.grid) axis.grid.color = gridColor;
                        if (axis.ticks) axis.ticks.color = textColor;
                        if (axis.title) axis.title.color = textColor;
                    });
                }
                
                // Update legend
                if (chart.instance.options.plugins.legend) {
                    chart.instance.options.plugins.legend.labels.color = textColor;
                }
                
                // Update title
                if (chart.instance.options.plugins.title) {
                    chart.instance.options.plugins.title.color = textColor;
                }
                
                chart.instance.update();
            }
        });
    }
}
