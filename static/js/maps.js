// Map functionality for Catanduanes Connect

let maps = {};
let mapMarkers = {};

// Initialize maps
document.addEventListener('DOMContentLoaded', function() {
    initializeMaps();
});

function initializeMaps() {
    // Initialize any maps present on the page
    const mapElements = document.querySelectorAll('[data-map]');
    mapElements.forEach(element => {
        const mapId = element.dataset.map;
        const mapType = element.dataset.mapType || 'default';
        const center = element.dataset.center ? JSON.parse(element.dataset.center) : [13.8000, 124.2000];
        const zoom = element.dataset.zoom || 10;
        
        createMap(mapId, center, zoom, mapType);
    });
}

function createMap(mapId, center, zoom, type = 'default') {
    // Create map container if it doesn't exist
    let mapElement = document.getElementById(mapId);
    if (!mapElement) {
        mapElement = document.createElement('div');
        mapElement.id = mapId;
        mapElement.style.height = '400px';
        document.body.appendChild(mapElement);
    }
    
    // Initialize Leaflet map
    const map = L.map(mapId).setView(center, zoom);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);
    
    // Store map reference
    maps[mapId] = map;
    mapMarkers[mapId] = [];
    
    // Add custom controls based on map type
    if (type === 'businesses') {
        addBusinessMapControls(map);
        // Load business markers automatically
        loadBusinessesMap(mapId);
    } else if (type === 'jobs') {
        addJobMapControls(map);
    }
    
    return map;
}

function addBusinessMapControls(map) {
    // Add search control
    const searchControl = L.control({ position: 'topright' });
    searchControl.onAdd = function() {
        const div = L.DomUtil.create('div', 'map-search-control bg-white p-2 rounded shadow-lg');
        div.innerHTML = `
            <div class="flex space-x-2">
                <input type="text" id="map-search" placeholder="Search businesses..." 
                       class="px-2 py-1 border rounded text-sm w-48">
                <button onclick="searchBusinesses()" class="bg-blue-600 text-white px-2 py-1 rounded text-sm">
                    <i class="fas fa-search"></i>
                </button>
            </div>
        `;
        return div;
    };
    searchControl.addTo(map);
    
    // Add category filter
    const categoryControl = L.control({ position: 'topright' });
    categoryControl.onAdd = function() {
        const div = L.DomUtil.create('div', 'map-category-control bg-white p-2 rounded shadow-lg mt-2');
        div.innerHTML = `
            <select id="map-category-filter" class="px-2 py-1 border rounded text-sm w-48" onchange="filterBusinessesByCategory()">
                <option value="">All Categories</option>
                <option value="restaurant">Restaurant</option>
                <option value="retail">Retail</option>
                <option value="services">Services</option>
                <option value="technology">Technology</option>
                <option value="healthcare">Healthcare</option>
                <option value="education">Education</option>
            </select>
        `;
        return div;
    };
    categoryControl.addTo(map);
}

function addJobMapControls(map) {
    // Add job type filter
    const jobTypeControl = L.control({ position: 'topright' });
    jobTypeControl.onAdd = function() {
        const div = L.DomUtil.create('div', 'map-jobtype-control bg-white p-2 rounded shadow-lg');
        div.innerHTML = `
            <select id="map-jobtype-filter" class="px-2 py-1 border rounded text-sm w-48" onchange="filterJobsByType()">
                <option value="">All Job Types</option>
                <option value="full_time">Full Time</option>
                <option value="part_time">Part Time</option>
                <option value="contract">Contract</option>
                <option value="internship">Internship</option>
            </select>
        `;
        return div;
    };
    jobTypeControl.addTo(map);
}

// Business map functions
function loadBusinessesMap(mapId) {
    if (!maps[mapId]) {
        console.error('Map not found:', mapId);
        return;
    }
    
    const map = maps[mapId];
    
    // Clear existing markers
    clearMapMarkers(mapId);
    
    // Fetch business markers from API
    fetch('/api/businesses/map-markers')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.markers) {
                // Add business markers
                data.markers.forEach(business => {
                    if (business.latitude && business.longitude) {
                        const marker = L.marker([business.latitude, business.longitude]);
                        
                        // Create popup content
                        const popupContent = createBusinessPopupContent(business);
                        marker.bindPopup(popupContent);
                        
                        // Add to map
                        marker.addTo(map);
                        mapMarkers[mapId].push(marker);
                    }
                });
                
                // Fit map to show all markers
                if (mapMarkers[mapId].length > 0) {
                    const group = new L.featureGroup(mapMarkers[mapId]);
                    map.fitBounds(group.getBounds().pad(0.1));
                }
            } else {
                console.error('Failed to load business markers:', data.error || 'Unknown error');
            }
        })
        .catch(error => {
            console.error('Error fetching business markers:', error);
        });
}

function createBusinessPopupContent(business) {
    return `
        <div class="business-popup">
            <h3 class="font-bold text-lg">${business.name}</h3>
            <p class="text-sm text-gray-600">${business.business_type || 'Business'}</p>
            <p class="text-sm mt-2">${business.address || 'No address provided'}</p>
            ${business.description ? `<p class="text-sm mt-2">${business.description}</p>` : ''}
            <a href="/businesses/${business.id}" class="inline-block mt-2 text-blue-600 hover:text-blue-800">View Details</a>
        </div>
    `;
    
    return `
        <div class="business-popup p-2 min-w-64">
            <h3 class="font-semibold text-lg mb-2">${business.name}</h3>
            <p class="text-sm text-gray-600 mb-2 capitalize">${business.category.replace('_', ' ')}</p>
            <div class="flex items-center mb-2">
                <span class="text-sm mr-2">${rating}</span>
                ${verifiedBadge}
            </div>
            <p class="text-sm text-gray-700 mb-3">${business.description ? truncateText(business.description, 100) : 'No description available'}</p>
            <div class="flex space-x-2">
                <a href="/businesses/${business.id}" class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                    View Details
                </a>
                <button onclick="contactBusiness('${business.id}')" class="bg-gray-200 text-gray-700 px-3 py-1 rounded text-sm hover:bg-gray-300">
                    Contact
                </button>
            </div>
        </div>
    `;
}

// Job map functions
function loadJobsMap(mapId, jobs) {
    if (!maps[mapId]) {
        console.error('Map not found:', mapId);
        return;
    }
    
    const map = maps[mapId];
    
    // Clear existing markers
    clearMapMarkers(mapId);
    
    // Add job markers
    jobs.forEach(job => {
        if (job.latitude && job.longitude) {
            const marker = L.marker([job.latitude, job.longitude]);
            
            // Create popup content
            const popupContent = createJobPopupContent(job);
            marker.bindPopup(popupContent);
            
            // Add to map
            marker.addTo(map);
            mapMarkers[mapId].push(marker);
        }
    });
    
    // Fit map to show all markers
    if (mapMarkers[mapId].length > 0) {
        const group = new L.featureGroup(mapMarkers[mapId]);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

function createJobPopupContent(job) {
    const salary = job.salary_min || job.salary_max ? 
        `₱${job.salary_min ? job.salary_min.toLocaleString() : ''}${job.salary_max ? '-' + job.salary_max.toLocaleString() : ''}` : 
        'Salary not specified';
    
    return `
        <div class="job-popup p-2 min-w-64">
            <h3 class="font-semibold text-lg mb-2">${job.title}</h3>
            <p class="text-sm text-blue-600 mb-2">${job.business_name}</p>
            <div class="flex items-center text-sm text-gray-600 mb-2">
                <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full mr-2">
                    ${job.type.replace('_', ' ').toUpperCase()}
                </span>
                <span>${salary}</span>
            </div>
            <p class="text-sm text-gray-700 mb-3">${job.description ? truncateText(job.description, 100) : 'No description available'}</p>
            <div class="flex space-x-2">
                <a href="/jobs/${job.id}" class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                    View Job
                </a>
                ${currentUser && currentUser.role === 'job_seeker' ? `
                    <button onclick="applyToJob('${job.id}')" class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                        Apply Now
                    </button>
                ` : ''}
            </div>
        </div>
    `;
}

// Service map functions
function loadServicesMap(mapId, services) {
    if (!maps[mapId]) {
        console.error('Map not found:', mapId);
        return;
    }
    
    const map = maps[mapId];
    
    // Clear existing markers
    clearMapMarkers(mapId);
    
    // Add service markers
    services.forEach(service => {
        if (service.latitude && service.longitude) {
            const marker = L.marker([service.latitude, service.longitude]);
            
            // Create popup content
            const popupContent = createServicePopupContent(service);
            marker.bindPopup(popupContent);
            
            // Add to map
            marker.addTo(map);
            mapMarkers[mapId].push(marker);
        }
    });
    
    // Fit map to show all markers
    if (mapMarkers[mapId].length > 0) {
        const group = new L.featureGroup(mapMarkers[mapId]);
        map.fitBounds(group.getBounds().pad(0.1));
    }
}

function createServicePopupContent(service) {
    const price = service.price ? 
        `₱${service.price.toLocaleString()} ${service.price_type === 'hourly' ? '/hour' : service.price_type === 'daily' ? '/day' : ''}` : 
        'Price not specified';
    
    return `
        <div class="service-popup p-2 min-w-64">
            <h3 class="font-semibold text-lg mb-2">${service.title}</h3>
            <p class="text-sm text-blue-600 mb-2 capitalize">${service.category.replace('_', ' ')}</p>
            <div class="flex items-center text-sm text-gray-600 mb-2">
                <span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full mr-2">
                    ${price}
                </span>
                <span>${service.duration || 'Duration varies'}</span>
            </div>
            <p class="text-sm text-gray-700 mb-3">${service.description ? truncateText(service.description, 100) : 'No description available'}</p>
            <div class="flex space-x-2">
                <a href="/services/${service.id}" class="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700">
                    View Service
                </a>
                <button onclick="contactServiceProvider('${service.id}')" class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                    Contact
                </button>
            </div>
        </div>
    `;
}

// Map utility functions
function clearMapMarkers(mapId) {
    if (mapMarkers[mapId]) {
        mapMarkers[mapId].forEach(marker => {
            marker.remove();
        });
        mapMarkers[mapId] = [];
    }
}

function centerMapOnLocation(mapId, lat, lng, zoom = 15) {
    if (maps[mapId]) {
        maps[mapId].setView([lat, lng], zoom);
    }
}

function addMapMarker(mapId, lat, lng, popupContent = '', icon = null) {
    if (!maps[mapId]) return null;
    
    const marker = icon ? L.marker([lat, lng], { icon }) : L.marker([lat, lng]);
    
    if (popupContent) {
        marker.bindPopup(popupContent);
    }
    
    marker.addTo(maps[mapId]);
    mapMarkers[mapId].push(marker);
    
    return marker;
}

function removeMapMarker(mapId, marker) {
    if (mapMarkers[mapId]) {
        const index = mapMarkers[mapId].indexOf(marker);
        if (index > -1) {
            mapMarkers[mapId].splice(index, 1);
            marker.remove();
        }
    }
}

// Search and filter functions
function searchBusinesses() {
    const searchTerm = document.getElementById('map-search').value.toLowerCase();
    
    // Filter visible markers based on search
    Object.keys(mapMarkers).forEach(mapId => {
        if (mapId.includes('business')) {
            mapMarkers[mapId].forEach(marker => {
                const popup = marker.getPopup();
                const content = popup.getContent().toLowerCase();
                
                if (content.includes(searchTerm)) {
                    marker.addTo(maps[mapId]);
                } else {
                    marker.remove();
                }
            });
        }
    });
}

function filterBusinessesByCategory() {
    const selectedCategory = document.getElementById('map-category-filter').value;
    
    // This would typically fetch filtered data from the server
    fetch(`/api/businesses?category=${selectedCategory}`)
        .then(response => response.json())
        .then(data => {
            if (data.businesses) {
                loadBusinessesMap('businesses-map', data.businesses);
            }
        })
        .catch(error => console.error('Failed to filter businesses:', error));
}

function filterJobsByType() {
    const selectedType = document.getElementById('map-jobtype-filter').value;
    
    // This would typically fetch filtered data from the server
    fetch(`/api/jobs?type=${selectedType}`)
        .then(response => response.json())
        .then(data => {
            if (data.jobs) {
                loadJobsMap('jobs-map', data.jobs);
            }
        })
        .catch(error => console.error('Failed to filter jobs:', error));
}

// Custom icons
function createCustomIcon(iconType, color = 'blue') {
    const iconMap = {
        business: 'building',
        job: 'briefcase',
        service: 'cog',
        restaurant: 'utensils',
        healthcare: 'hospital',
        technology: 'laptop'
    };
    
    const iconName = iconMap[iconType] || 'map-marker';
    
    return L.divIcon({
        html: `<div class="bg-${color}-600 text-white rounded-full w-8 h-8 flex items-center justify-center shadow-lg">
                 <i class="fas fa-${iconName}"></i>
               </div>`,
        className: 'custom-marker',
        iconSize: [32, 32],
        iconAnchor: [16, 32]
    });
}

// Geolocation
function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported'));
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            position => resolve({
                lat: position.coords.latitude,
                lng: position.coords.longitude
            }),
            error => reject(error),
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 300000
            }
        );
    });
}

function centerMapOnUser(mapId) {
    getCurrentPosition()
        .then(position => {
            centerMapOnLocation(mapId, position.lat, position.lng, 15);
            
            // Add user location marker
            const userIcon = L.divIcon({
                html: '<div class="bg-blue-600 text-white rounded-full w-4 h-4 flex items-center justify-center"><i class="fas fa-user text-xs"></i></div>',
                className: 'user-location-marker',
                iconSize: [16, 16],
                iconAnchor: [8, 8]
            });
            
            addMapMarker(mapId, position.lat, position.lng, 'Your location', userIcon);
        })
        .catch(error => {
            console.error('Failed to get user location:', error);
            alert('Unable to get your location. Please check your browser settings.');
        });
}

// Export functions
window.Maps = {
    createMap,
    loadBusinessesMap,
    loadJobsMap,
    loadServicesMap,
    centerMapOnLocation,
    addMapMarker,
    removeMapMarker,
    clearMapMarkers,
    searchBusinesses,
    filterBusinessesByCategory,
    filterJobsByType,
    createCustomIcon,
    getCurrentPosition,
    centerMapOnUser
};