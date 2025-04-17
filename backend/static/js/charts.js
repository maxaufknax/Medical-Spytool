/**
 * MedicalSpy - Charts module
 * This file contains functions for creating and updating charts.
 */

// Create a year distribution chart
function createYearChart(chartData) {
    // Get the canvas
    const ctx = document.getElementById('yearChart').getContext('2d');
    
    // Extract years and counts
    const years = Object.keys(chartData).sort();
    const counts = years.map(year => chartData[year]);
    
    // Create chart
    const yearChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: years,
            datasets: [{
                label: 'Publications per Year',
                data: counts,
                backgroundColor: 'rgba(13, 110, 253, 0.7)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        title: (tooltipItems) => {
                            return `Year: ${tooltipItems[0].label}`;
                        },
                        label: (tooltipItem) => {
                            return `Publications: ${tooltipItem.raw}`;
                        }
                    }
                }
            }
        }
    });
    
    return yearChart;
}

// Create an author distribution chart
function createAuthorChart(chartData) {
    // Get the canvas
    const ctx = document.getElementById('authorChart').getContext('2d');
    
    // Extract authors and counts
    const authors = Object.keys(chartData);
    const counts = authors.map(author => chartData[author]);
    
    // Create chart
    const authorChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: authors,
            datasets: [{
                label: 'Publications per Author',
                data: counts,
                backgroundColor: 'rgba(40, 167, 69, 0.7)',
                borderColor: 'rgba(40, 167, 69, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',  // Horizontal bar chart
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        title: (tooltipItems) => {
                            return `Author: ${tooltipItems[0].label}`;
                        },
                        label: (tooltipItem) => {
                            return `Publications: ${tooltipItem.raw}`;
                        }
                    }
                }
            }
        }
    });
    
    return authorChart;
}

// Create a database distribution chart
function createDatabaseChart(results) {
    // Get the canvas
    const ctx = document.getElementById('databaseChart').getContext('2d');
    
    // Count results by database
    const databaseCounts = {};
    results.forEach(result => {
        const database = result.Datenbank || 'Unknown';
        databaseCounts[database] = (databaseCounts[database] || 0) + 1;
    });
    
    // Extract databases and counts
    const databases = Object.keys(databaseCounts);
    const counts = databases.map(db => databaseCounts[db]);
    
    // Define colors for databases
    const colors = {
        'PubMed': 'rgba(13, 110, 253, 0.7)',
        'Deutsche Nationalbibliothek': 'rgba(255, 193, 7, 0.7)',
        'Unknown': 'rgba(108, 117, 125, 0.7)'
    };
    
    // Create chart colors array
    const backgroundColor = databases.map(db => colors[db] || 'rgba(108, 117, 125, 0.7)');
    const borderColor = databases.map(db => {
        const bgColor = colors[db] || 'rgba(108, 117, 125, 0.7)';
        return bgColor.replace('0.7', '1');
    });
    
    // Create chart
    const databaseChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: databases,
            datasets: [{
                data: counts,
                backgroundColor: backgroundColor,
                borderColor: borderColor,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: (tooltipItem) => {
                            const database = tooltipItem.label;
                            const count = tooltipItem.raw;
                            const percentage = ((count / results.length) * 100).toFixed(1);
                            return `${database}: ${count} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    return databaseChart;
}

// Create a citation distribution chart
function createCitationChart(results) {
    // Get the canvas
    const ctx = document.getElementById('citationChart').getContext('2d');
    
    // Filter results to only include those with citation counts
    const resultsWithCitations = results.filter(result => {
        const citationCount = result.Zitationsanzahl;
        return citationCount !== undefined && 
               citationCount !== null && 
               citationCount !== "N/A" && 
               !isNaN(parseInt(citationCount));
    });
    
    // Extract titles and citation counts
    const titles = resultsWithCitations.map(result => {
        // Truncate long titles
        let title = result.Titel || 'Untitled';
        return title.length > 30 ? title.substring(0, 27) + '...' : title;
    });
    
    const citationCounts = resultsWithCitations.map(result => parseInt(result.Zitationsanzahl));
    
    // Sort by citation count (descending)
    const combined = titles.map((title, i) => ({ title, count: citationCounts[i] }));
    combined.sort((a, b) => b.count - a.count);
    
    // Take only top 10
    const top10 = combined.slice(0, 10);
    
    // Create chart
    const citationChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(item => item.title),
            datasets: [{
                label: 'Citation Count',
                data: top10.map(item => item.count),
                backgroundColor: 'rgba(220, 53, 69, 0.7)',
                borderColor: 'rgba(220, 53, 69, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',  // Horizontal bar chart
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        title: (tooltipItems) => {
                            return tooltipItems[0].label;
                        },
                        label: (tooltipItem) => {
                            return `Citations: ${tooltipItem.raw}`;
                        }
                    }
                }
            }
        }
    });
    
    return citationChart;
}

// Initialize all charts on the analysis page
function initializeCharts() {
    // Get the results data
    const resultsData = document.getElementById('resultsData');
    if (!resultsData) return;
    
    const results = JSON.parse(resultsData.textContent || '[]');
    if (results.length === 0) return;
    
    // Get analysis data
    const analysisDataElem = document.getElementById('analysisData');
    if (!analysisDataElem) return;
    
    const analysisData = JSON.parse(analysisDataElem.textContent || '{}');
    
    // Create charts if data exists
    if (analysisData.year_counts) {
        createYearChart(analysisData.year_counts);
    }
    
    if (analysisData.top_authors) {
        createAuthorChart(analysisData.top_authors);
    }
    
    // Create database distribution chart
    createDatabaseChart(results);
    
    // Create citation chart if results have citation counts
    createCitationChart(results);
}

// Initialize charts when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize charts if we're on the analysis page
    if (document.getElementById('analysisPage')) {
        initializeCharts();
    }
});
