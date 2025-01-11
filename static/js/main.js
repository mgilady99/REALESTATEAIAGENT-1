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

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get buttons
    const scrapeClassifiedBtn = document.getElementById('scrapeClassified');
    const scrapeNewsBtn = document.getElementById('scrapeNews');

    // Add click event listeners
    if (scrapeClassifiedBtn) {
        scrapeClassifiedBtn.addEventListener('click', async function() {
            try {
                scrapeClassifiedBtn.disabled = true;
                scrapeClassifiedBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping...';
                
                const response = await fetch('/scrape', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showAlert('success', 'Property scraping started successfully!');
                    setTimeout(updateProperties, 5000); // Update properties after 5 seconds
                } else {
                    throw new Error(data.message || 'Failed to start property scraping');
                }
            } catch (error) {
                showAlert('error', 'Error: ' + error.message);
            } finally {
                scrapeClassifiedBtn.disabled = false;
                scrapeClassifiedBtn.innerHTML = '<i class="fas fa-search"></i> Scrape Property Ads';
            }
        });
    }

    if (scrapeNewsBtn) {
        scrapeNewsBtn.addEventListener('click', async function() {
            try {
                scrapeNewsBtn.disabled = true;
                scrapeNewsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping...';
                
                const response = await fetch('/scrape/news', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showAlert('success', 'News scraping started successfully!');
                    setTimeout(updateNews, 5000); // Update news after 5 seconds
                } else {
                    throw new Error(data.message || 'Failed to start news scraping');
                }
            } catch (error) {
                showAlert('error', 'Error: ' + error.message);
            } finally {
                scrapeNewsBtn.disabled = false;
                scrapeNewsBtn.innerHTML = '<i class="fas fa-newspaper"></i> Scrape News';
            }
        });
    }

    // Function to update properties list
    async function updateProperties() {
        try {
            const response = await fetch('/api/properties');
            const data = await response.json();
            
            if (response.ok) {
                const propertiesList = document.getElementById('propertiesList');
                if (propertiesList && data.properties && data.properties.length > 0) {
                    propertiesList.innerHTML = data.properties.map(property => `
                        <div class="col-md-6 col-lg-4 mb-4">
                            <div class="card h-100">
                                ${property.image_url ? `<img src="${property.image_url}" class="card-img-top" alt="Property Image">` : ''}
                                <div class="card-body">
                                    <h5 class="card-title">${property.title}</h5>
                                    <p class="card-text">${property.description ? property.description.substring(0, 200) + '...' : ''}</p>
                                    <p class="card-text">
                                        <strong>Price:</strong> ${property.price}<br>
                                        <strong>Location:</strong> ${property.location}<br>
                                        <strong>Source:</strong> ${property.source}
                                    </p>
                                    ${property.url ? `<a href="${property.url}" class="btn btn-primary" target="_blank">View Details</a>` : ''}
                                </div>
                                <div class="card-footer text-muted">
                                    Added: ${new Date(property.created_at).toLocaleString()}
                                </div>
                            </div>
                        </div>
                    `).join('');
                }
            }
        } catch (error) {
            console.error('Error updating properties:', error);
        }
    }

    // Function to update news list
    async function updateNews() {
        try {
            const response = await fetch('/api/news');
            const data = await response.json();
            
            if (response.ok) {
                const newsList = document.getElementById('newsList');
                if (newsList && data.news_items && data.news_items.length > 0) {
                    newsList.innerHTML = data.news_items.map(news => `
                        <div class="col-md-6 mb-4">
                            <div class="card h-100">
                                <div class="card-body">
                                    <h5 class="card-title">${news.title}</h5>
                                    <p class="card-text">${news.summary ? news.summary.substring(0, 200) + '...' : ''}</p>
                                    <a href="${news.url}" class="btn btn-info text-white" target="_blank">Read More</a>
                                </div>
                                <div class="card-footer text-muted">
                                    Published: ${new Date(news.published_at).toLocaleString()}
                                </div>
                            </div>
                        </div>
                    `).join('');
                }
            }
        } catch (error) {
            console.error('Error updating news:', error);
        }
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
    updateNews();
});
