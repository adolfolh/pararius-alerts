import requests
from bs4 import BeautifulSoup
import re

def test_pararius_listing():
    """Fetch a sample listing from Pararius to check HTML structure."""
    
    # Use a sample URL from the logs
    url = "https://www.pararius.com/apartments/den-haag/0-1000/1-bedrooms"
    
    # Set a user agent to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Make the request
    print(f"Requesting {url}")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch URL: {response.status_code}")
        return
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Find all listing elements
    listing_elements = soup.select('.search-list__item .listing-search-item')
    print(f"Found {len(listing_elements)} listings")
    
    if not listing_elements:
        print("No listings found!")
        return
    
    # Analyze the first listing
    listing = listing_elements[0]
    
    # Print the listing HTML structure for analysis
    print("\nListing HTML structure:")
    print(listing.prettify())
    
    # Check specific elements we're trying to extract
    print("\nChecking specific elements:")
    
    # Title
    title_elem = listing.select_one('.listing-search-item__link--title')
    print(f"Title element found: {title_elem is not None}")
    if title_elem:
        print(f"Title text: {title_elem.text.strip()}")
    
    # Price
    price_elem = listing.select_one('.listing-search-item__price')
    print(f"Price element found: {price_elem is not None}")
    if price_elem:
        print(f"Price text: {price_elem.text.strip()}")
    
    # Features (size, rooms, etc.)
    features_elem = listing.select_one('.listing-search-item__features')
    print(f"Features element found: {features_elem is not None}")
    if features_elem:
        print("Features HTML:")
        print(features_elem.prettify())
        
        # Check for specific feature elements
        size_elem = features_elem.select_one('.surface')
        rooms_elem = features_elem.select_one('.number-of-rooms')
        interior_elem = features_elem.select_one('.interior')
        
        print(f"Size element found: {size_elem is not None}")
        print(f"Rooms element found: {rooms_elem is not None}")
        print(f"Interior element found: {interior_elem is not None}")
        
        # Look for alternative class patterns
        print("\nSearching for alternative feature patterns:")
        feature_items = features_elem.select('li')
        for item in feature_items:
            print(f"Feature item: {item.text.strip()} (class: {item.get('class', 'none')})")
    
    # Location
    location_elem = listing.select_one('.listing-search-item__location')
    print(f"Location element found: {location_elem is not None}")
    if location_elem:
        print(f"Location text: {location_elem.text.strip()}")
    
    # Agency
    agency_elem = listing.select_one('.listing-search-item__info .listing-search-item__link')
    print(f"Agency element found: {agency_elem is not None}")
    if agency_elem:
        print(f"Agency text: {agency_elem.text.strip()}")

if __name__ == "__main__":
    test_pararius_listing() 