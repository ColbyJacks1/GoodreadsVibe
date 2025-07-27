// Global variables
let goodreadsData = [];
let charts = {};

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const resultsSection = document.getElementById('resultsSection');
const loading = document.getElementById('loading');
const analysisContent = document.getElementById('analysisContent');

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    setupFileUpload();
    setupDragAndDrop();
});

function setupFileUpload() {
    fileInput.addEventListener('change', handleFileSelect);
}

function setupDragAndDrop() {
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    if (!file.name.toLowerCase().endsWith('.csv')) {
        alert('Please upload a CSV file');
        return;
    }

    fileName.textContent = file.name;
    fileInfo.style.display = 'flex';
    
    const reader = new FileReader();
    reader.onload = function(e) {
        const csvData = e.target.result;
        parseCSV(csvData);
    };
    reader.readAsText(file);
}

function removeFile() {
    fileInput.value = '';
    fileInfo.style.display = 'none';
    resultsSection.style.display = 'none';
    goodreadsData = [];
    if (charts) {
        Object.values(charts).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });
        charts = {};
    }
}

function parseCSV(csvData) {
    const lines = csvData.split('\n');
    const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
    
    goodreadsData = [];
    
    for (let i = 1; i < lines.length; i++) {
        if (lines[i].trim() === '') continue;
        
        const values = parseCSVLine(lines[i]);
        const book = {};
        
        headers.forEach((header, index) => {
            if (values[index]) {
                book[header] = values[index].trim().replace(/"/g, '');
            }
        });
        
        if (book.Title) {
            goodreadsData.push(book);
        }
    }
    
    if (goodreadsData.length > 0) {
        analyzeData();
    } else {
        alert('No valid data found in the CSV file');
    }
}

function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        
        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            result.push(current);
            current = '';
        } else {
            current += char;
        }
    }
    
    result.push(current);
    return result;
}

function analyzeData() {
    resultsSection.style.display = 'block';
    loading.style.display = 'block';
    analysisContent.style.display = 'none';
    
    setTimeout(() => {
        const analysis = performAnalysis();
        displayResults(analysis);
        
        loading.style.display = 'none';
        analysisContent.style.display = 'block';
    }, 1000);
}

function performAnalysis() {
    const analysis = {
        totalBooks: goodreadsData.length,
        averageRating: 0,
        topGenre: '',
        readingYears: 0,
        genreDistribution: {},
        ratingDistribution: {},
        authorDistribution: {},
        readingTimeline: {},
        insights: [],
        recommendations: []
    };
    
    // Calculate basic stats
    let totalRating = 0;
    let ratedBooks = 0;
    const genres = {};
    const authors = {};
    const years = new Set();
    
    goodreadsData.forEach(book => {
        // Rating analysis
        if (book['My Rating'] && book['My Rating'] !== '0') {
            const rating = parseFloat(book['My Rating']);
            if (!isNaN(rating)) {
                totalRating += rating;
                ratedBooks++;
                
                // Rating distribution
                const ratingKey = Math.floor(rating);
                analysis.ratingDistribution[ratingKey] = (analysis.ratingDistribution[ratingKey] || 0) + 1;
            }
        }
        
        // Genre analysis
        if (book['Additional Authors'] || book['Author']) {
            const genre = extractGenre(book);
            if (genre) {
                genres[genre] = (genres[genre] || 0) + 1;
            }
        }
        
        // Author analysis
        if (book['Author']) {
            const author = book['Author'].split(',')[0].trim();
            authors[author] = (authors[author] || 0) + 1;
        }
        
        // Timeline analysis
        if (book['Date Read']) {
            const year = extractYear(book['Date Read']);
            if (year) {
                years.add(year);
                analysis.readingTimeline[year] = (analysis.readingTimeline[year] || 0) + 1;
            }
        }
    });
    
    // Calculate averages and find top items
    analysis.averageRating = ratedBooks > 0 ? (totalRating / ratedBooks).toFixed(1) : '0.0';
    analysis.readingYears = years.size;
    
    // Find top genre
    const sortedGenres = Object.entries(genres).sort((a, b) => b[1] - a[1]);
    analysis.topGenre = sortedGenres.length > 0 ? sortedGenres[0][0] : '-';
    analysis.genreDistribution = genres;
    
    // Find top authors
    const sortedAuthors = Object.entries(authors).sort((a, b) => b[1] - a[1]);
    analysis.authorDistribution = Object.fromEntries(sortedAuthors.slice(0, 10));
    
    // Generate insights
    analysis.insights = generateInsights(analysis);
    
    // Generate recommendations
    analysis.recommendations = generateRecommendations(analysis);
    
    return analysis;
}

function extractGenre(book) {
    // Try to extract genre from various fields
    const genreFields = ['Additional Authors', 'Author', 'Title'];
    
    for (const field of genreFields) {
        if (book[field]) {
            const text = book[field].toLowerCase();
            
            // Simple genre detection based on keywords
            if (text.includes('fiction') || text.includes('novel')) return 'Fiction';
            if (text.includes('non-fiction') || text.includes('nonfiction')) return 'Non-Fiction';
            if (text.includes('science fiction') || text.includes('sci-fi')) return 'Science Fiction';
            if (text.includes('fantasy')) return 'Fantasy';
            if (text.includes('mystery') || text.includes('thriller')) return 'Mystery/Thriller';
            if (text.includes('romance')) return 'Romance';
            if (text.includes('biography') || text.includes('memoir')) return 'Biography/Memoir';
            if (text.includes('history')) return 'History';
            if (text.includes('philosophy')) return 'Philosophy';
            if (text.includes('science') || text.includes('technology')) return 'Science/Technology';
        }
    }
    
    return 'General';
}

function extractYear(dateString) {
    const yearMatch = dateString.match(/\b(19|20)\d{2}\b/);
    return yearMatch ? yearMatch[0] : null;
}

function generateInsights(analysis) {
    const insights = [];
    
    // Reading volume insight
    if (analysis.totalBooks > 50) {
        insights.push({
            title: "📚 Avid Reader",
            content: `You've read ${analysis.totalBooks} books! You're clearly passionate about reading and have a substantial library.`
        });
    } else if (analysis.totalBooks > 20) {
        insights.push({
            title: "📖 Regular Reader",
            content: `With ${analysis.totalBooks} books, you maintain a steady reading habit.`
        });
    }
    
    // Rating insight
    const avgRating = parseFloat(analysis.averageRating);
    if (avgRating >= 4.0) {
        insights.push({
            title: "⭐ Selective Reader",
            content: `Your average rating of ${analysis.averageRating} suggests you're quite selective and know what you like.`
        });
    } else if (avgRating >= 3.0) {
        insights.push({
            title: "📊 Balanced Perspective",
            content: `Your average rating of ${analysis.averageRating} shows a balanced approach to rating books.`
        });
    }
    
    // Genre insight
    if (analysis.topGenre && analysis.topGenre !== 'General') {
        insights.push({
            title: "🎭 Genre Preference",
            content: `Your favorite genre appears to be ${analysis.topGenre}, which dominates your reading choices.`
        });
    }
    
    // Timeline insight
    const timelineYears = Object.keys(analysis.readingTimeline).sort();
    if (timelineYears.length > 1) {
        const firstYear = timelineYears[0];
        const lastYear = timelineYears[timelineYears.length - 1];
        insights.push({
            title: "📅 Reading Journey",
            content: `Your reading journey spans from ${firstYear} to ${lastYear}, showing a consistent reading habit over time.`
        });
    }
    
    return insights;
}

function generateRecommendations(analysis) {
    const recommendations = [];
    
    // Based on genre preference
    if (analysis.topGenre) {
        const genreRecs = {
            'Fiction': 'Try exploring different subgenres like historical fiction or contemporary fiction.',
            'Science Fiction': 'Consider exploring cyberpunk or space opera subgenres.',
            'Fantasy': 'You might enjoy epic fantasy series or urban fantasy.',
            'Mystery/Thriller': 'Try psychological thrillers or detective novels.',
            'Non-Fiction': 'Explore different subjects like science, philosophy, or current events.',
            'Biography/Memoir': 'Consider reading about different historical figures or contemporary personalities.'
        };
        
        if (genreRecs[analysis.topGenre]) {
            recommendations.push({
                title: "🎯 Genre Exploration",
                content: genreRecs[analysis.topGenre]
            });
        }
    }
    
    // Based on rating pattern
    const avgRating = parseFloat(analysis.averageRating);
    if (avgRating >= 4.0) {
        recommendations.push({
            title: "⭐ High Standards",
            content: "Since you rate books highly, try reading books that have won major literary awards or are critically acclaimed."
        });
    }
    
    // General recommendations
    recommendations.push({
        title: "📚 Expand Your Horizons",
        content: "Consider reading books from genres you haven't explored much, or try books from different time periods or cultures."
    });
    
    recommendations.push({
        title: "🔄 Revisit Favorites",
        content: "Look back at your highest-rated books and try to find similar books by the same authors or in the same genre."
    });
    
    return recommendations;
}

function displayResults(analysis) {
    // Update stats
    document.getElementById('totalBooks').textContent = analysis.totalBooks;
    document.getElementById('avgRating').textContent = analysis.averageRating;
    document.getElementById('topGenre').textContent = analysis.topGenre;
    document.getElementById('readingYears').textContent = analysis.readingYears;
    
    // Create charts
    createReadingTimelineChart(analysis.readingTimeline);
    createGenreChart(analysis.genreDistribution);
    createRatingChart(analysis.ratingDistribution);
    createAuthorChart(analysis.authorDistribution);
    
    // Display insights
    displayInsights(analysis.insights);
    
    // Display recommendations
    displayRecommendations(analysis.recommendations);
}

function createReadingTimelineChart(timelineData) {
    const ctx = document.getElementById('readingTimeline').getContext('2d');
    const years = Object.keys(timelineData).sort();
    const counts = years.map(year => timelineData[year]);
    
    if (charts.readingTimeline) {
        charts.readingTimeline.destroy();
    }
    
    charts.readingTimeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [{
                label: 'Books Read',
                data: counts,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function createGenreChart(genreData) {
    const ctx = document.getElementById('genreChart').getContext('2d');
    const genres = Object.keys(genreData);
    const counts = Object.values(genreData);
    
    if (charts.genreChart) {
        charts.genreChart.destroy();
    }
    
    charts.genreChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: genres,
            datasets: [{
                data: counts,
                backgroundColor: [
                    '#667eea', '#764ba2', '#f093fb', '#f5576c',
                    '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function createRatingChart(ratingData) {
    const ctx = document.getElementById('ratingChart').getContext('2d');
    const ratings = Object.keys(ratingData).sort();
    const counts = ratings.map(rating => ratingData[rating]);
    
    if (charts.ratingChart) {
        charts.ratingChart.destroy();
    }
    
    charts.ratingChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ratings.map(r => `${r} stars`),
            datasets: [{
                label: 'Number of Books',
                data: counts,
                backgroundColor: '#667eea',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function createAuthorChart(authorData) {
    const ctx = document.getElementById('authorChart').getContext('2d');
    const authors = Object.keys(authorData);
    const counts = Object.values(authorData);
    
    if (charts.authorChart) {
        charts.authorChart.destroy();
    }
    
    charts.authorChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: authors,
            datasets: [{
                label: 'Books Read',
                data: counts,
                backgroundColor: '#764ba2',
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
}

function displayInsights(insights) {
    const insightsGrid = document.getElementById('insightsGrid');
    insightsGrid.innerHTML = '';
    
    insights.forEach(insight => {
        const insightCard = document.createElement('div');
        insightCard.className = 'insight-card';
        insightCard.innerHTML = `
            <h4>${insight.title}</h4>
            <p>${insight.content}</p>
        `;
        insightsGrid.appendChild(insightCard);
    });
}

function displayRecommendations(recommendations) {
    const recommendationsGrid = document.getElementById('recommendationsGrid');
    recommendationsGrid.innerHTML = '';
    
    recommendations.forEach(rec => {
        const recCard = document.createElement('div');
        recCard.className = 'recommendation-card';
        recCard.innerHTML = `
            <h4>${rec.title}</h4>
            <p>${rec.content}</p>
        `;
        recommendationsGrid.appendChild(recCard);
    });
} 