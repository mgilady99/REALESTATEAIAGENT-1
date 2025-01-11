// Global variables for URLs
let propertyUrls = [];
let newsUrls = [];

// Function to fetch and update properties
async function updateProperties() {
    try {
        const response = await fetch('/api/properties');
        const data = await response.json();
        
        const tableBody = document.getElementById('properties-table');
        if (!tableBody) return;
        
        tableBody.innerHTML = data.properties.map(property => `
            <tr>
                <td>${property.title || ''}</td>
                <td>${property.price || ''}</td>
                <td>${property.location || ''}</td>
                <td>${property.date_listed ? new Date(property.date_listed).toLocaleDateString() : ''}</td>
                <td>
                    <a href="${property.url}" target="_blank" class="btn btn-sm btn-primary">View</a>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error fetching properties:', error);
    }
}

// Function to handle search criteria form submission
async function handleSearchCriteriaSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    try {
        const response = await fetch('/search-criteria', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            alert('Search criteria saved successfully!');
            location.reload();
        } else {
            alert('Error saving search criteria');
        }
    } catch (error) {
        console.error('Error submitting search criteria:', error);
        alert('Error saving search criteria');
    }
}

// Load URLs when the page loads
document.addEventListener('DOMContentLoaded', function() {
    loadUrls();
    setupScrapeButtons();
});

// Setup scrape buttons
function setupScrapeButtons() {
    document.getElementById('scrapeClassified').addEventListener('click', async function() {
        const button = this;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping...';
        
        try {
            const response = await fetch('/scrape', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                displayProperties(data.properties);
            } else {
                alert('Error: ' + data.message);
            }
        } catch (error) {
            alert('Error during scraping: ' + error.message);
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-search"></i> Scrape Property Ads';
        }
    });

    document.getElementById('scrapeNews').addEventListener('click', async function() {
        const button = this;
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping News...';
        
        try {
            const response = await fetch('/scrape/news', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                displayNews(data.news);
            } else {
                alert('Error: ' + data.message);
            }
        } catch (error) {
            alert('Error during news scraping: ' + error.message);
        } finally {
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-newspaper"></i> Scrape News';
        }
    });
}

// URL Management Functions
async function loadUrls() {
    try {
        const response = await fetch('/api/urls');
        const data = await response.json();
        propertyUrls = data.property_urls || [];
        newsUrls = data.news_urls || [];
        updateUrlLists();
    } catch (error) {
        console.error('Error loading URLs:', error);
    }
}

function updateUrlLists() {
    const propertyList = document.getElementById('propertyUrlsList');
    const newsList = document.getElementById('newsUrlsList');
    
    propertyList.innerHTML = propertyUrls.map((url, index) => createUrlListItem(url, index, 'property')).join('');
    newsList.innerHTML = newsUrls.map((url, index) => createUrlListItem(url, index, 'news')).join('');
}

function createUrlListItem(url, index, type) {
    return `
        <div class="url-item">
            <span class="url-text">${url}</span>
            <div class="url-actions">
                <button class="btn btn-sm btn-danger" onclick="removeUrl('${type}', ${index})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `;
}

function addPropertyUrl() {
    const input = document.getElementById('newPropertyUrl');
    const url = input.value.trim();
    if (url && !propertyUrls.includes(url)) {
        propertyUrls.push(url);
        updateUrlLists();
        input.value = '';
    }
}

function addNewsUrl() {
    const input = document.getElementById('newNewsUrl');
    const url = input.value.trim();
    if (url && !newsUrls.includes(url)) {
        newsUrls.push(url);
        updateUrlLists();
        input.value = '';
    }
}

function removeUrl(type, index) {
    if (type === 'property') {
        propertyUrls.splice(index, 1);
    } else {
        newsUrls.splice(index, 1);
    }
    updateUrlLists();
}

async function saveUrls() {
    try {
        const response = await fetch('/api/urls', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                property_urls: propertyUrls,
                news_urls: newsUrls
            })
        });
        
        const data = await response.json();
        if (data.success) {
            alert('URLs saved successfully!');
            document.getElementById('urlManagerModal').querySelector('.btn-close').click();
        } else {
            alert('Error saving URLs: ' + data.message);
        }
    } catch (error) {
        alert('Error saving URLs: ' + error.message);
    }
}

// Display Functions
function displayProperties(properties) {
    const container = document.getElementById('propertiesList');
    if (!properties || properties.length === 0) {
        container.innerHTML = '<div class="col-12"><p class="text-center">No properties found.</p></div>';
        return;
    }

    container.innerHTML = properties.map(property => `
        <div class="col-md-4 mb-4">
            <div class="card h-100">
                ${property.image_url ? 
                    `<img src="${property.image_url}" class="card-img-top" alt="${property.title}" style="height: 200px; object-fit: cover;">` :
                    '<div class="card-img-top bg-light d-flex align-items-center justify-content-center" style="height: 200px;">No Image</div>'
                }
                <div class="card-body">
                    <h5 class="card-title">${property.title}</h5>
                    <p class="card-text">
                        <strong>Price:</strong> ${property.price ? `₪${property.price.toLocaleString()}` : 'N/A'}<br>
                        <strong>Location:</strong> ${property.location || 'N/A'}
                    </p>
                    ${property.url ? 
                        `<a href="${property.url}" target="_blank" class="btn btn-primary">View Details</a>` :
                        '<button class="btn btn-primary" disabled>No Link Available</button>'
                    }
                </div>
            </div>
        </div>
    `).join('');
}

function displayNews(news) {
    const container = document.getElementById('newsList');
    if (!news || news.length === 0) {
        container.innerHTML = '<div class="col-12"><p class="text-center">No news articles found.</p></div>';
        return;
    }

    container.innerHTML = news.map(article => `
        <div class="col-md-4 mb-4">
            <div class="card h-100">
                ${article.image_url ? 
                    `<img src="${article.image_url}" class="card-img-top" alt="${article.title}" style="height: 200px; object-fit: cover;">` :
                    '<div class="card-img-top bg-light d-flex align-items-center justify-content-center" style="height: 200px;">No Image</div>'
                }
                <div class="card-body">
                    <h5 class="card-title">${article.title}</h5>
                    <p class="card-text">${article.description || 'No description available.'}</p>
                    <p class="card-text"><small class="text-muted">Source: ${article.source}</small></p>
                    ${article.url ? 
                        `<a href="${article.url}" target="_blank" class="btn btn-primary">Read More</a>` :
                        '<button class="btn btn-primary" disabled>No Link Available</button>'
                    }
                </div>
            </div>
        </div>
    `).join('');
}

// Function to show alerts
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '1050';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    
    // Remove alert after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Initial load of properties and news
updateProperties();
