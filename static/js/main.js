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
    // Update properties periodically
    updateProperties();
    setInterval(updateProperties, 60000); // Update every minute
    
    // Add form submit handler
    const searchForm = document.getElementById('search-criteria-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchCriteriaSubmit);
    }
    
    // Scraping action buttons
    const scrapeClassifiedBtn = document.getElementById('scrapeClassified');
    const scrapeNewsBtn = document.getElementById('scrapeNews');
    const scrapeFacebookBtn = document.getElementById('scrapeFacebook');
    
    // Handle classified ads scraping
    if (scrapeClassifiedBtn) {
        scrapeClassifiedBtn.addEventListener('click', async function() {
            try {
                scrapeClassifiedBtn.disabled = true;
                scrapeClassifiedBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping...';
                
                const response = await fetch('/scrape');
                const data = await response.json();
                
                if (data.status === 'success') {
                    showAlert('success', `Successfully scraped ${data.count} properties`);
                    setTimeout(() => location.reload(), 2000);
                } else {
                    showAlert('error', 'Error scraping properties');
                }
            } catch (error) {
                showAlert('error', 'Error scraping properties');
            } finally {
                scrapeClassifiedBtn.disabled = false;
                scrapeClassifiedBtn.innerHTML = '<i class="fas fa-search"></i> Scrape Classified Ads';
            }
        });
    }
    
    // Handle news scraping
    if (scrapeNewsBtn) {
        scrapeNewsBtn.addEventListener('click', async function() {
            try {
                scrapeNewsBtn.disabled = true;
                scrapeNewsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping News...';
                
                const response = await fetch('/scrape/news');
                const data = await response.json();
                
                if (data.status === 'success') {
                    showAlert('success', `Successfully scraped ${data.count} news articles`);
                    setTimeout(() => location.reload(), 2000);
                } else {
                    showAlert('error', 'Error scraping news');
                }
            } catch (error) {
                showAlert('error', 'Error scraping news');
            } finally {
                scrapeNewsBtn.disabled = false;
                scrapeNewsBtn.innerHTML = '<i class="fas fa-newspaper"></i> Scrape News';
            }
        });
    }
    
    // Handle Facebook scraping
    if (scrapeFacebookBtn) {
        scrapeFacebookBtn.addEventListener('click', async function() {
            try {
                scrapeFacebookBtn.disabled = true;
                scrapeFacebookBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping Facebook...';
                
                const response = await fetch('/scrape/facebook');
                const data = await response.json();
                
                if (data.status === 'success') {
                    showAlert('success', `Successfully scraped ${data.count} Facebook posts`);
                    setTimeout(() => location.reload(), 2000);
                } else {
                    showAlert('error', 'Error scraping Facebook posts');
                }
            } catch (error) {
                showAlert('error', 'Error scraping Facebook posts');
            } finally {
                scrapeFacebookBtn.disabled = false;
                scrapeFacebookBtn.innerHTML = '<i class="fab fa-facebook"></i> Scrape Facebook Groups';
            }
        });
    }
    
    // Helper function to show alerts
    function showAlert(type, message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.container').firstChild);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => alertDiv.remove(), 5000);
    }
});
