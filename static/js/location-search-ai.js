/**
 * Enhanced Location Search with Gemini AI
 * Provides intelligent location filtering for Jobs and Businesses pages
 */

class LocationSearchAI {
    constructor(options = {}) {
        this.apiBaseUrl = options.apiBaseUrl || '/api/location';
        this.jobsListUrl = '/jobs/list';
        this.businessesListUrl = '/businesses';
        this.cache = new Map();
    }

    /**
     * Get location suggestions with AI enhancement
     */
    async getLocationSuggestions(query) {
        if (!query || query.length < 2) {
            return [];
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/get-location-suggestions?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            return data.suggestions || [];
        } catch (error) {
            console.error('Error getting location suggestions:', error);
            return [];
        }
    }

    /**
     * Use AI to understand location query and suggest corrections
     */
    async suggestLocations(query) {
        if (!query) return null;

        // Check cache first
        if (this.cache.has(query)) {
            return this.cache.get(query);
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/ai-suggest-locations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            if (data.status === 'success') {
                this.cache.set(query, data.suggestions);
                return data.suggestions;
            }
            return null;
        } catch (error) {
            console.error('Error getting AI location suggestions:', error);
            return null;
        }
    }

    /**
     * Search jobs with AI-enhanced location understanding
     */
    async searchJobs(filters = {}) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/search-jobs-by-location`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(filters)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error searching jobs:', error);
            return { status: 'error', message: error.message };
        }
    }

    /**
     * Search businesses with AI-enhanced location understanding
     */
    async searchBusinesses(filters = {}) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/search-businesses-by-location`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(filters)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error searching businesses:', error);
            return { status: 'error', message: error.message };
        }
    }
}

// Initialize global instance
const locationSearchAI = new LocationSearchAI();

/**
 * Setup location search with autocomplete
 */
function setupLocationSearch(inputSelector, suggestionsSelector, onSearch = null) {
    const locationInput = document.querySelector(inputSelector);
    const suggestionsContainer = document.querySelector(suggestionsSelector);

    if (!locationInput) return;

    // Input event for autocomplete
    locationInput.addEventListener('input', async (e) => {
        const query = e.target.value.trim();

        if (query.length < 2) {
            if (suggestionsContainer) {
                suggestionsContainer.innerHTML = '';
            }
            return;
        }

        // Get AI suggestions
        const suggestions = await locationSearchAI.suggestLocations(query);
        
        if (suggestions && suggestionsContainer) {
            displayLocationSuggestions(suggestions, suggestionsContainer, locationInput, onSearch);
        }

        // Also get autocomplete suggestions
        const autocompleteSuggestions = await locationSearchAI.getLocationSuggestions(query);
        
        if (suggestionsContainer && autocompleteSuggestions.length > 0) {
            if (!suggestions) {
                displayLocationSuggestions(
                    { 
                        primary_location: autocompleteSuggestions[0], 
                        alternate_locations: autocompleteSuggestions.slice(1) 
                    }, 
                    suggestionsContainer, 
                    locationInput, 
                    onSearch
                );
            }
        }
    });

    // Enter key to search
    locationInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = e.target.value.trim();
            if (query && onSearch) {
                onSearch(query);
            }
        }
    });
}

/**
 * Display location suggestions in UI
 */
function displayLocationSuggestions(suggestions, container, inputElement, onSearch) {
    container.innerHTML = '';

    if (!suggestions) return;

    const primary = suggestions.primary_location;
    const alternates = suggestions.alternate_locations || [];
    const confidence = suggestions.confidence || 0;

    // Primary location
    if (primary) {
        const primaryDiv = document.createElement('div');
        primaryDiv.className = 'location-suggestion primary';
        primaryDiv.style.cssText = `
            padding: 12px;
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            cursor: pointer;
            margin-bottom: 8px;
            border-radius: 4px;
            transition: all 0.2s;
        `;
        
        const confidenceStr = confidence > 0.8 ? '✓ High match' : 
                            confidence > 0.5 ? '≈ Similar' : 
                            '? Possible match';
        
        primaryDiv.innerHTML = `
            <div style="font-weight: 600; color: #667eea;">${primary}</div>
            <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">${confidenceStr}</div>
        `;
        
        primaryDiv.addEventListener('click', () => {
            inputElement.value = primary;
            container.innerHTML = '';
            if (onSearch) onSearch(primary);
        });
        
        primaryDiv.addEventListener('mouseover', () => {
            primaryDiv.style.background = '#e0e7ff';
        });
        
        primaryDiv.addEventListener('mouseout', () => {
            primaryDiv.style.background = '#f0f4ff';
        });
        
        container.appendChild(primaryDiv);
    }

    // Alternate locations
    alternates.forEach((location, index) => {
        const altDiv = document.createElement('div');
        altDiv.className = 'location-suggestion alternate';
        altDiv.style.cssText = `
            padding: 10px 12px;
            background: #f3f4f6;
            cursor: pointer;
            margin-bottom: 4px;
            border-radius: 4px;
            font-size: 14px;
            transition: all 0.2s;
        `;
        altDiv.textContent = location;
        
        altDiv.addEventListener('click', () => {
            inputElement.value = location;
            container.innerHTML = '';
            if (onSearch) onSearch(location);
        });
        
        altDiv.addEventListener('mouseover', () => {
            altDiv.style.background = '#e5e7eb';
        });
        
        altDiv.addEventListener('mouseout', () => {
            altDiv.style.background = '#f3f4f6';
        });
        
        container.appendChild(altDiv);
    });
}

/**
 * Perform AI-enhanced location search for jobs
 */
async function performJobLocationSearch(locationQuery, filters = {}) {
    const loadingEl = document.querySelector('[data-loading]');
    if (loadingEl) loadingEl.style.display = 'block';

    try {
        const searchFilters = {
            location: locationQuery,
            ...filters,
            page: filters.page || 1,
            per_page: filters.per_page || 12
        };

        const result = await locationSearchAI.searchJobs(searchFilters);

        if (result.status === 'success') {
            updateJobsDisplay(result.jobs, result.location_data);
            updatePagination(result.page, result.total, result.per_page, 'jobs');
        } else {
            showError(result.message || 'Search failed');
        }
    } catch (error) {
        showError('An error occurred during search');
        console.error(error);
    } finally {
        if (loadingEl) loadingEl.style.display = 'none';
    }
}

/**
 * Perform AI-enhanced location search for businesses
 */
async function performBusinessLocationSearch(locationQuery, filters = {}) {
    const loadingEl = document.querySelector('[data-loading]');
    if (loadingEl) loadingEl.style.display = 'block';

    try {
        const searchFilters = {
            location: locationQuery,
            ...filters,
            page: filters.page || 1,
            per_page: filters.per_page || 12
        };

        const result = await locationSearchAI.searchBusinesses(searchFilters);

        if (result.status === 'success') {
            updateBusinessesDisplay(result.businesses, result.location_data);
            updatePagination(result.page, result.total, result.per_page, 'businesses');
        } else {
            showError(result.message || 'Search failed');
        }
    } catch (error) {
        showError('An error occurred during search');
        console.error(error);
    } finally {
        if (loadingEl) loadingEl.style.display = 'none';
    }
}

/**
 * Update jobs display
 */
function updateJobsDisplay(jobs, locationData) {
    const container = document.querySelector('[data-jobs-container]');
    if (!container) return;

    if (jobs.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #6b7280;">
                <p>No jobs found in <strong>${locationData.primary_location}</strong></p>
                <p style="font-size: 14px; margin-top: 10px;">Try searching in a different location</p>
            </div>
        `;
        return;
    }

    container.innerHTML = jobs.map(job => `
        <div class="job-card" style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; background: white;">
            <h3 style="margin: 0 0 8px 0; color: #111827; font-size: 18px; font-weight: 600;">${job.title}</h3>
            <p style="margin: 0 0 8px 0; color: #667eea; font-weight: 500;">${job.business_name}</p>
            <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px;">${job.description.substring(0, 100)}...</p>
            <div style="display: flex; gap: 16px; font-size: 14px; color: #6b7280; margin-bottom: 12px;">
                <span>📍 ${job.location}</span>
                <span>💰 ${job.salary_range}</span>
                <span>📋 ${job.type}</span>
            </div>
            <a href="/jobs/${job.id}" style="display: inline-block; background: #667eea; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: 500;">View Details</a>
        </div>
    `).join('');
}

/**
 * Update businesses display
 */
function updateBusinessesDisplay(businesses, locationData) {
    const container = document.querySelector('[data-businesses-container]');
    if (!container) return;

    if (businesses.length === 0) {
        container.innerHTML = `
            <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #6b7280;">
                <p>No businesses found in <strong>${locationData.primary_location}</strong></p>
                <p style="font-size: 14px; margin-top: 10px;">Try searching in a different location</p>
            </div>
        `;
        return;
    }

    container.innerHTML = businesses.map(business => `
        <div class="business-card" style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; background: white;">
            <h3 style="margin: 0 0 8px 0; color: #111827; font-size: 18px; font-weight: 600;">${business.name}</h3>
            <p style="margin: 0 0 8px 0; color: #667eea; font-weight: 500; font-size: 14px;">${business.category.replace('_', ' ')}</p>
            <div style="display: flex; align-items: center; margin-bottom: 8px; font-size: 14px;">
                <span style="color: #fbbf24;">★</span>
                <span style="margin-left: 4px; color: #374151;">${business.rating.toFixed(1)} (${business.review_count} reviews)</span>
            </div>
            <p style="margin: 0 0 8px 0; color: #6b7280; font-size: 14px;">${business.description.substring(0, 100)}...</p>
            <div style="display: flex; gap: 16px; font-size: 14px; color: #6b7280; margin-bottom: 12px;">
                <span>📍 ${business.address}</span>
                ${business.is_verified ? '<span style="background: #d1fae5; color: #065f46; padding: 2px 8px; border-radius: 4px;">✓ Verified</span>' : ''}
            </div>
            <a href="/businesses/${business.id}" style="display: inline-block; background: #667eea; color: white; padding: 8px 16px; border-radius: 6px; text-decoration: none; font-weight: 500;">View Profile</a>
        </div>
    `).join('');
}

/**
 * Update pagination
 */
function updatePagination(page, total, perPage, type) {
    const totalPages = Math.ceil(total / perPage);
    const paginationEl = document.querySelector('[data-pagination]');
    
    if (!paginationEl || totalPages <= 1) return;

    let paginationHTML = '';
    
    // Previous button
    if (page > 1) {
        paginationHTML += `<button onclick="goToPage(${page - 1}, '${type}')" style="padding: 8px 12px; margin: 0 4px; border: 1px solid #d1d5db; border-radius: 4px; cursor: pointer;">← Previous</button>`;
    }
    
    // Page numbers
    for (let i = Math.max(1, page - 2); i <= Math.min(totalPages, page + 2); i++) {
        const style = i === page ? 'background: #667eea; color: white;' : 'background: white; color: #667eea;';
        paginationHTML += `<button onclick="goToPage(${i}, '${type}')" style="padding: 8px 12px; margin: 0 4px; border: 1px solid #d1d5db; border-radius: 4px; cursor: pointer; ${style};">${i}</button>`;
    }
    
    // Next button
    if (page < totalPages) {
        paginationHTML += `<button onclick="goToPage(${page + 1}, '${type}')" style="padding: 8px 12px; margin: 0 4px; border: 1px solid #d1d5db; border-radius: 4px; cursor: pointer;">Next →</button>`;
    }
    
    paginationEl.innerHTML = paginationHTML;
}

/**
 * Go to specific page
 */
function goToPage(pageNum, type) {
    const locationInput = document.querySelector('[data-location-input]');
    const location = locationInput ? locationInput.value : '';
    
    if (type === 'jobs') {
        performJobLocationSearch(location, { page: pageNum });
    } else if (type === 'businesses') {
        performBusinessLocationSearch(location, { page: pageNum });
    }
}

/**
 * Show error message
 */
function showError(message) {
    const errorEl = document.querySelector('[data-error]');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
        setTimeout(() => {
            errorEl.style.display = 'none';
        }, 5000);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Setup location search for jobs page
    setupLocationSearch(
        '[data-location-input]',
        '[data-location-suggestions]',
        (location) => performJobLocationSearch(location)
    );
});
