import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('pararius_scraper')

class ParariusScraper:
    """
    Scraper for Pararius.com apartment listings.
    
    This class handles the extraction of apartment listings from Pararius.com
    based on specified search parameters.
    """
    
    BASE_URL = "https://www.pararius.com/apartments"
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the scraper with configuration.
        
        Args:
            config_path: Path to the configuration JSON file
        """
        self.config = self._load_config(config_path)
        self.headers = {'User-Agent': self.config.get('user_agent')}
        self.request_delay = self.config.get('request_delay', 5)
        self.max_retries = self.config.get('max_retries', 3)
        
    def _load_config(self, config_path: str) -> Dict:
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Dictionary containing configuration values
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading config: {e}")
            raise
    
    def _make_request(self, url: str) -> Optional[BeautifulSoup]:
        """
        Make an HTTP request with retry logic and parse the HTML.
        
        Args:
            url: URL to request
            
        Returns:
            BeautifulSoup object or None if request failed
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Requesting {url}")
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                # Add delay between requests for ethical scraping
                time.sleep(self.request_delay)
                
                return BeautifulSoup(response.text, 'lxml')
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Max retries reached for {url}")
                    return None
                time.sleep(self.request_delay * 2)  # Longer delay between retries
                
        return None
    
    def _build_search_url(self, city: str, page: int = 1) -> str:
        """
        Build URL for searching apartments based on city and filters.
        
        Args:
            city: City name (e.g., 'rotterdam', 'den-haag')
            page: Page number for pagination
            
        Returns:
            Complete search URL with filters
        """
        # Start with base URL including city
        url = f"{self.BASE_URL}/{city}"
        
        # Add parameters
        params = []
        
        # Add price range
        price_range = self.config.get('price_range', {})
        min_price = price_range.get('min', 0)
        max_price = price_range.get('max')
        
        if min_price is not None and max_price is not None:
            params.append(f"{min_price}-{max_price}")
        elif min_price:
            params.append(f"{min_price}+")
        elif max_price:
            params.append(f"0-{max_price}")
        
        # Add bedrooms
        min_bedrooms = self.config.get('min_bedrooms')
        if min_bedrooms:
            params.append(f"{min_bedrooms}-bedrooms")
        
        # Add size filter if specified
        min_size = self.config.get('min_size')
        if min_size:
            params.append(f"{min_size}-m2")
        
        # Combine all parameters
        if params:
            url = f"{url}/{'/'.join(params)}"
        
        # Add page number if not first page
        if page > 1:
            url = f"{url}/page-{page}"
        
        return url
    
    def _extract_listing_data(self, listing_element) -> Dict:
        """
        Extract data from a single listing element.
        
        Args:
            listing_element: BeautifulSoup element for a single listing
            
        Returns:
            Dictionary containing listing information
        """
        try:
            # Extract basic information
            listing_link = listing_element.select_one('a.listing-search-item__link--title')
            if not listing_link:
                return {}
                
            url = f"https://www.pararius.com{listing_link['href']}"
            listing_id = url.split('/')[-1]
            title = listing_link.text.strip()
            
            # Extract price
            price_elem = listing_element.select_one('.listing-search-item__price')
            price_text = price_elem.text.strip() if price_elem else "Unknown"
            price_match = re.search(r'€\s*([\d,.]+)', price_text)
            price = float(price_match.group(1).replace(',', '').replace('.', '')) if price_match else None
            
            # Extract location
            # Try to find any element that might contain location information
            location = "Unknown"
            location_elem = None
            
            # First attempt - try to find directly by tag content
            if listing_element.select_one('div.listing-search-item__sub-title'):
                location_elem = listing_element.select_one('div.listing-search-item__sub-title')
            # Second fallback - general search
            if not location_elem:
                for div in listing_element.select('div'):
                    if 'sub-title' in ' '.join(div.get('class', [])):
                        location_elem = div
                        break
            
            if location_elem:
                location = location_elem.text.strip()
            
            # Extract features from the new structure
            features = {}
            
            # Find all feature items
            feature_items = listing_element.select('.illustrated-features__item')
            for item in feature_items:
                item_class = item.get('class', [])
                item_text = item.text.strip()
                
                # Extract size
                if any('surface-area' in cls for cls in item_class):
                    size_match = re.search(r'(\d+)\s*m²', item_text)
                    features['size'] = int(size_match.group(1)) if size_match else None
                
                # Extract rooms
                elif any('number-of-rooms' in cls for cls in item_class):
                    rooms_match = re.search(r'(\d+)\s*rooms?', item_text)
                    features['rooms'] = int(rooms_match.group(1)) if rooms_match else None
                
                # Extract interior
                elif any('interior' in cls for cls in item_class):
                    features['interior'] = item_text
            
            # Extract image URL - Update to handle new image structure
            image_elem = listing_element.select_one('img.picture__image')
            image_url = image_elem['src'] if image_elem and 'src' in image_elem.attrs else None
            
            # Extract listing agency
            agency_elem = listing_element.select_one('.listing-search-item__info .listing-search-item__link')
            agency = agency_elem.text.strip() if agency_elem else "Unknown"
            
            return {
                'id': listing_id,
                'url': url,
                'title': title,
                'price': price,
                'size': features.get('size'),
                'rooms': features.get('rooms'),
                'location': location,
                'interior': features.get('interior', 'Unknown'),
                'image_url': image_url,
                'agency': agency,
                'first_seen': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return {}
            
    def scrape_city(self, city: str, max_pages: int = 5) -> List[Dict]:
        """
        Scrape listings for a specific city.
        
        Args:
            city: City name (e.g., 'rotterdam', 'den-haag')
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of listings as dictionaries
        """
        all_listings = []
        
        for page in range(1, max_pages + 1):
            url = self._build_search_url(city, page)
            soup = self._make_request(url)
            
            if not soup:
                logger.error(f"Failed to retrieve page {page} for {city}")
                break
                
            # Find all listing elements
            listing_elements = soup.select('.search-list__item .listing-search-item')
            
            if not listing_elements:
                logger.info(f"No more listings found on page {page} for {city}")
                break
                
            logger.info(f"Found {len(listing_elements)} listings on page {page} for {city}")
            
            # Process each listing
            for listing_element in listing_elements:
                listing_data = self._extract_listing_data(listing_element)
                if listing_data:
                    all_listings.append(listing_data)
                    
            # Check if there's a next page
            next_page = soup.select_one('.pagination__link--next')
            if not next_page:
                logger.info(f"No more pages available for {city}")
                break
                
        return all_listings
        
    def scrape_all_cities(self) -> List[Dict]:
        """
        Scrape listings for all configured cities.
        
        Returns:
            List of all listings as dictionaries
        """
        all_listings = []
        
        for city in self.config.get('cities', []):
            logger.info(f"Scraping listings for {city}")
            city_listings = self.scrape_city(city)
            all_listings.extend(city_listings)
            
        logger.info(f"Scraped a total of {len(all_listings)} listings")
        return all_listings
        
    def get_listing_details(self, url: str) -> Dict:
        """
        Get detailed information about a specific listing.
        
        Args:
            url: URL of the listing
            
        Returns:
            Dictionary with detailed listing information
        """
        soup = self._make_request(url)
        if not soup:
            logger.error(f"Failed to retrieve listing details for {url}")
            return {}
            
        try:
            # Extract title
            title_elem = soup.select_one('h1')
            title = title_elem.text.strip() if title_elem else "Unknown"
            
            # Extract price
            price_elem = soup.select_one('.listing-detail-summary__price')
            price_text = price_elem.text.strip() if price_elem else "Unknown"
            price_match = re.search(r'€\s*([\d,.]+)', price_text)
            price = float(price_match.group(1).replace(',', '').replace('.', '')) if price_match else None
            
            # Extract description
            description_elem = soup.select_one('.listing-detail-description__additional')
            description = description_elem.text.strip() if description_elem else ""
            
            # Extract characteristics
            characteristics = {}
            char_elems = soup.select('.listing-features__list .listing-features__feature')
            for elem in char_elems:
                label_elem = elem.select_one('.listing-features__label')
                value_elem = elem.select_one('.listing-features__value')
                if label_elem and value_elem:
                    label = label_elem.text.strip().rstrip(':')
                    value = value_elem.text.strip()
                    characteristics[label] = value
                    
            # Extract availability date
            available_elem = soup.select_one('.listing-detail-summary__item--available')
            available = available_elem.text.strip() if available_elem else "Unknown"
            
            # Extract all images
            image_elems = soup.select('.listing-detail-media__images img')
            images = [img['src'] for img in image_elems if 'src' in img.attrs]
            
            return {
                'url': url,
                'title': title,
                'price': price,
                'description': description,
                'characteristics': characteristics,
                'available': available,
                'images': images,
                'scraped_at': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error extracting listing details: {e}")
            return {}
            
if __name__ == "__main__":
    scraper = ParariusScraper()
    listings = scraper.scrape_all_cities()
    
    # Save to JSON file
    output_dir = Path("data")
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / "latest_listings.json", "w") as f:
        json.dump(listings, f, indent=2)
        
    logger.info(f"Saved {len(listings)} listings to data/latest_listings.json") 