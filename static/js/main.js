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
document.addEventListener('DOMContentLoaded', () => {
    // Update properties periodically
    updateProperties();
    setInterval(updateProperties, 60000); // Update every minute
    
    // Add form submit handler
    const searchForm = document.getElementById('search-criteria-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearchCriteriaSubmit);
    }
});
