/**
 * MedicalSpy - Analysis module
 * This file contains functions for data analysis and visualization.
 */

// Initialize charts on page load using ChartUtils
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('analysisPage')) {
        console.log("Analysis page detected, initializing charts via analysis.js");
        fetchYearDistribution();
        fetchDatabaseDistribution(); // This will be updated to use API
        fetchTopAuthors();
        fetchTopCitedPublications();
    }

    // Theme change listener should be in charts.js or theme-manager.js
    // For now, ensure it's not duplicated if charts.js handles it.
    // If theme-manager.js calls ChartUtils.updateAllChartThemes(), this is not needed here.
    // window.addEventListener('themeChanged', function(event) {
    //     if (window.ChartUtils && event.detail && typeof event.detail.isDarkMode !== 'undefined') {
    //          console.log('Theme changed event received by analysis.js, calling ChartUtils.updateAllChartThemes.');
    //         window.ChartUtils.updateAllChartThemes(event.detail.isDarkMode);
    //     }
    // });
});

// Helper to get common chart options with theme awareness
function getCommonChartOptions(titleText, xAxisLabel, yAxisLabel, isDark = null) {
    const themeColors = ChartUtils.getThemeColors(isDark);
    const options = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                grid: { color: themeColors.gridColor },
                ticks: { color: themeColors.mutedTextColor, precision: 0 },
                title: { display: !!yAxisLabel, text: yAxisLabel, color: themeColors.textColor }
            },
            x: {
                grid: { color: themeColors.gridColor },
                ticks: { color: themeColors.mutedTextColor },
                title: { display: !!xAxisLabel, text: xAxisLabel, color: themeColors.textColor }
            }
        },
        plugins: {
            legend: { labels: { color: themeColors.textColor } },
            title: { display: true, text: titleText, color: themeColors.textColor }
        }
    };
    return options;
}


// Fetch and render year distribution chart
function fetchYearDistribution() {
    const searchId = document.getElementById('analysisPage')?.dataset.searchId;
    if (!searchId) { ChartUtils.showChartError('yearChart'); return; }

    fetch(`/api/analysis/years?search_id=${searchId}`)
        .then(response => response.ok ? response.json() : Promise.reject(`Network error: ${response.statusText}`))
        .then(apiResponse => {
            if (apiResponse.status === 'success' && apiResponse.data && apiResponse.data.years) {
                const yearData = apiResponse.data.years;
                const labels = Object.keys(yearData).sort();
                const data = labels.map(year => yearData[year]);
                const themeColors = ChartUtils.getThemeColors();

                ChartUtils.createChart('yearChart', 'bar', 
                    {
                        labels: labels,
                        datasets: [{
                            label: 'Publications',
                            data: data,
                            backgroundColor: themeColors.datasetColors[0].background,
                            borderColor: themeColors.datasetColors[0].border,
                            borderWidth: 1
                        }]
                    },
                    getCommonChartOptions('Publications by Year', 'Year', 'Number of Publications')
                );
            } else {
                ChartUtils.showChartError('yearChart', apiResponse.message);
            }
        })
        .catch(error => {
            console.error('Error fetching year distribution:', error);
            ChartUtils.showChartError('yearChart');
        });
}

// Fetch and render database distribution chart (Updated to use API)
function fetchDatabaseDistribution() {
    const searchId = document.getElementById('analysisPage')?.dataset.searchId;
    if (!searchId) { 
        ChartUtils.showChartError('databaseChart', 'Search ID not found.'); // More specific error
        return; 
    }

    fetch(`/api/analysis/database_distribution?search_id=${searchId}`)
        .then(response => response.ok ? response.json() : Promise.reject(`Network error: ${response.statusText}`))
        .then(apiResponse => {
            if (apiResponse.status === 'success' && apiResponse.data && apiResponse.data.labels && apiResponse.data.data) {
                const themeColors = ChartUtils.getThemeColors();
                // Cycle through datasetColors if there are more databases than predefined colors
                const backgroundColors = apiResponse.data.labels.map((label, index) => 
                    themeColors.datasetColors[index % themeColors.datasetColors.length].background
                );
                const borderColors = apiResponse.data.labels.map((label, index) => 
                    themeColors.datasetColors[index % themeColors.datasetColors.length].border
                );

                ChartUtils.createChart('databaseChart', 'pie',
                    {
                        labels: apiResponse.data.labels,
                        datasets: [{
                            data: apiResponse.data.data,
                            backgroundColor: backgroundColors,
                            borderColor: borderColors,
                            borderWidth: 1
                        }]
                    },
                    { 
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { 
                                position: 'right', 
                                labels: { color: themeColors.textColor } 
                            },
                            title: { 
                                display: true, 
                                text: 'Publications by Database', 
                                color: themeColors.textColor 
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        let label = context.label || '';
                                        if (label) {
                                            label += ': ';
                                        }
                                        if (context.parsed !== null) {
                                            label += context.parsed;
                                            // Calculate percentage
                                            const total = context.dataset.data.reduce((sum, value) => sum + value, 0);
                                            if (total > 0) {
                                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                                label += ` (${percentage}%)`;
                                            }
                                        }
                                        return label;
                                    }
                                }
                            }
                        }
                    }
                );
            } else {
                ChartUtils.showChartError('databaseChart', apiResponse.message || 'Failed to load database distribution data.');
            }
        })
        .catch(error => {
            console.error('Error fetching database distribution:', error);
            ChartUtils.showChartError('databaseChart');
        });
}


// Fetch and render top authors chart
function fetchTopAuthors() {
    const searchId = document.getElementById('analysisPage')?.dataset.searchId;
    if (!searchId) { ChartUtils.showChartError('authorsChart'); return; }

    fetch(`/api/analysis/authors?search_id=${searchId}&limit=10`)
        .then(response => response.ok ? response.json() : Promise.reject(`Network error: ${response.statusText}`))
        .then(apiResponse => {
            if (apiResponse.status === 'success' && apiResponse.data && apiResponse.data.authors) {
                const authorsData = apiResponse.data.authors;
                const labels = authorsData.map(item => item.name);
                const data = authorsData.map(item => item.count);
                const themeColors = ChartUtils.getThemeColors();
                
                let options = getCommonChartOptions('Top Contributing Authors', 'Number of Publications', null /* Y-axis label not needed for horizontal */);
                options.indexAxis = 'y'; // Make it horizontal
                options.plugins.legend.display = false; // Typically hide legend for single dataset horizontal bar

                ChartUtils.createChart('authorsChart', 'bar',
                    {
                        labels: labels,
                        datasets: [{
                            label: 'Publications',
                            data: data,
                            backgroundColor: themeColors.datasetColors[1].background,
                            borderColor: themeColors.datasetColors[1].border,
                            borderWidth: 1
                        }]
                    },
                    options
                );
            } else {
                ChartUtils.showChartError('authorsChart', apiResponse.message);
            }
        })
        .catch(error => {
            console.error('Error fetching top authors:', error);
            ChartUtils.showChartError('authorsChart');
        });
}


// Fetch and render top cited publications chart
function fetchTopCitedPublications() {
    const searchId = document.getElementById('analysisPage')?.dataset.searchId;
    if (!searchId) { ChartUtils.showChartError('citationChart'); return; }
    
    fetch(`/api/analysis/top_cited?search_id=${searchId}&limit=10`)
        .then(response => response.ok ? response.json() : Promise.reject(`Network error: ${response.statusText}`))
        .then(apiResponse => {
            if (apiResponse.status === 'success' && apiResponse.data && apiResponse.data.publications) {
                const publicationData = apiResponse.data.publications;
                const labels = publicationData.map(item => {
                    let title = item.title || 'Untitled';
                    return title.length > 50 ? title.substring(0, 47) + '...' : title;
                });
                const data = publicationData.map(item => item.citations);
                const themeColors = ChartUtils.getThemeColors();

                let options = getCommonChartOptions('Top Cited Publications', 'Number of Citations', null);
                options.indexAxis = 'y';
                options.plugins.legend.display = false;
                options.plugins.tooltip = { // Custom tooltip for full title
                     callbacks: {
                        title: function(tooltipItems) {
                            const originalIndex = tooltipItems[0].dataIndex;
                            return publicationData[originalIndex].title || 'Untitled';
                        },
                        label: function(tooltipItem) {
                            return `Citations: ${tooltipItem.raw}`;
                        }
                    }
                };


                ChartUtils.createChart('citationChart', 'bar', 
                    {
                        labels: labels,
                        datasets: [{
                            label: 'Citations',
                            data: data,
                            backgroundColor: themeColors.datasetColors[3].background, // Using a different color
                            borderColor: themeColors.datasetColors[3].border,
                            borderWidth: 1
                        }]
                    },
                    options
                );
            } else {
                ChartUtils.showChartError('citationChart', apiResponse.message);
            }
        })
        .catch(error => {
            console.error('Error fetching top cited publications:', error);
            ChartUtils.showChartError('citationChart');
        });
}

// Remove local showChartError as it's now in ChartUtils
// Remove local updateAllCharts as it's now in ChartUtils (and called by event listeners in charts.js)
