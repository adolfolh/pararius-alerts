/**
 * Pararius Apartment Alerts - Web Interface
 * 
 * This script handles loading and displaying apartment listings data
 * for the GitHub Pages interface.
 */

// Global variables
let allListings = [];
let configData = {};

// IMPORTANT: Update these values before deploying to GitHub Pages
// Replace 'adolfolh' with your actual GitHub username
// Replace 'pararius-alerts' with your repository name if different
const REPO_OWNER = 'adolfolh';
const REPO_NAME = 'pararius-alerts';

// DOM Elements
const listingsContainer = document.getElementById('listingsContainer');
const lastUpdatedElement = document.getElementById('lastUpdated');
const configDisplayElement = document.getElementById('configDisplay');

// Stats elements
const totalListingsElement = document.getElementById('totalListings');
const newListings24hElement = document.getElementById('newListings24h');
const avgPriceElement = document.getElementById('avgPrice');
const avgSizeElement = document.getElementById('avgSize');

// Initialize the application
document.addEventListener('DOMContentLoaded', init);

// Functions

/**
 * Initialize the application
 */
async function init() {
    await loadListings();
    await loadConfiguration();
    updateStats();
    displayListings();
}

/**
 * Load listings data from the repository
 */
async function loadListings() {
    try {
        // Check if we're running on GitHub Pages or locally
        const isGitHubPages = window.location.hostname.includes('github.io');
        let listingsUrl, statsUrl;
        
        if (isGitHubPages) {
            // We're on GitHub Pages - use the raw GitHub URL
            listingsUrl = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/main/data/listings.json`;
            statsUrl = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/main/data/run_stats.json`;
        } else {
            // We're running locally - use relative paths
            listingsUrl = '../data/listings.json';
            statsUrl = '../data/run_stats.json';
        }
        
        // Get listings
        const response = await fetch(listingsUrl);
        
        if (!response.ok) {
            throw new Error(`Failed to load listings data: ${response.status} ${response.statusText}`);
        }
        
        allListings = await response.json();
        
        // Get last updated timestamp
        try {
            const statsResponse = await fetch(statsUrl);
            
            if (statsResponse.ok) {
                const stats = await statsResponse.json();
                if (stats.length > 0) {
                    const lastRun = stats[stats.length - 1];
                    const lastUpdated = new Date(lastRun.timestamp);
                    lastUpdatedElement.textContent = lastUpdated.toLocaleString();
                }
            }
        } catch (statsError) {
            console.warn('Could not load stats data:', statsError);
            lastUpdatedElement.textContent = 'Unknown';
        }
        
    } catch (error) {
        console.error('Error loading data:', error);
        listingsContainer.innerHTML = `
            <div class="col-12 text-center my-5">
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    Failed to load listings data: ${error.message}
                </div>
            </div>
        `;
    }
}

/**
 * Load configuration data
 */
async function loadConfiguration() {
    try {
        // Check if we're running on GitHub Pages or locally
        const isGitHubPages = window.location.hostname.includes('github.io');
        let configUrl;
        
        if (isGitHubPages) {
            // We're on GitHub Pages - use the raw GitHub URL
            configUrl = `https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/main/config.json`;
        } else {
            // We're running locally - use relative path
            configUrl = '../config.json';
        }
        
        const response = await fetch(configUrl);
        
        if (!response.ok) {
            throw new Error(`Failed to load configuration: ${response.status} ${response.statusText}`);
        }
        
        configData = await response.json();
        
        // Format and display the configuration
        const formattedConfig = JSON.stringify(configData, null, 2);
        configDisplayElement.textContent = formattedConfig;
        
    } catch (error) {
        console.error('Error loading configuration:', error);
        configDisplayElement.textContent = 'Error loading configuration. Please check the repository.';
    }
}

/**
 * Update statistics based on loaded data
 */
function updateStats() {
    if (allListings.length === 0) return;
    
    // Total listings
    totalListingsElement.textContent = allListings.length;
    
    // New listings in the last 24 hours
    const oneDayAgo = new Date();
    oneDayAgo.setDate(oneDayAgo.getDate() - 1);
    
    const newListings = allListings.filter(listing => {
        const firstSeen = new Date(listing.first_seen);
        return firstSeen >= oneDayAgo;
    });
    
    newListings24hElement.textContent = newListings.length;
    
    // Average price
    const validPrices = allListings.filter(listing => listing.price !== null && !isNaN(listing.price));
    if (validPrices.length > 0) {
        const totalPrice = validPrices.reduce((sum, listing) => sum + listing.price, 0);
        const avgPrice = totalPrice / validPrices.length;
        avgPriceElement.textContent = `€${Math.round(avgPrice).toLocaleString()}`;
    }
    
    // Average size
    const validSizes = allListings.filter(listing => listing.size !== null && !isNaN(listing.size));
    if (validSizes.length > 0) {
        const totalSize = validSizes.reduce((sum, listing) => sum + listing.size, 0);
        const avgSize = totalSize / validSizes.length;
        avgSizeElement.textContent = `${Math.round(avgSize)}`;
    }
}

/**
 * Display listings in the UI
 */
function displayListings() {
    // Clear previous listings
    listingsContainer.innerHTML = '';
    
    // Show message if no listings
    if (allListings.length === 0) {
        listingsContainer.innerHTML = `
            <div class="col-12 text-center my-5">
                <div class="alert alert-info">
                    No listings available yet.
                </div>
            </div>
        `;
        return;
    }
    
    // Sort by newest first by default
    const sortedListings = [...allListings].sort((a, b) => new Date(b.first_seen) - new Date(a.first_seen));
    
    // Get the template
    const template = document.getElementById('listingCardTemplate');
    
    // Create and append listing cards
    sortedListings.forEach(listing => {
        // Clone the template
        const listingCard = template.content.cloneNode(true);
        
        // Set listing data
        const image = listingCard.querySelector('.card-img-top');
        image.src = listing.image_url || 'img/placeholder.jpg';
        image.alt = listing.title || 'Apartment';
        
        listingCard.querySelector('.listing-title').textContent = listing.title || 'Unknown';
        listingCard.querySelector('.card-price').textContent = listing.price ? `€${listing.price.toLocaleString()}` : 'Price unknown';
        listingCard.querySelector('.listing-location').textContent = listing.location || 'Unknown location';
        listingCard.querySelector('.listing-size').textContent = listing.size ? `${listing.size} m²` : 'Unknown';
        listingCard.querySelector('.listing-rooms').textContent = listing.rooms ? `${listing.rooms} rooms` : 'Unknown';
        listingCard.querySelector('.listing-interior').textContent = listing.interior || 'Unknown';
        
        // Format date
        const firstSeen = new Date(listing.first_seen);
        const now = new Date();
        const diffDays = Math.floor((now - firstSeen) / (1000 * 60 * 60 * 24));
        
        let dateText;
        if (diffDays === 0) {
            dateText = 'Added today';
        } else if (diffDays === 1) {
            dateText = 'Added yesterday';
        } else {
            dateText = `Added ${diffDays} days ago`;
        }
        
        listingCard.querySelector('.listing-date').textContent = dateText;
        
        // Set link
        const link = listingCard.querySelector('.listing-link');
        link.href = listing.url || '#';
        
        // Append to container
        listingsContainer.appendChild(listingCard);
    });
} 