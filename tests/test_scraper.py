import unittest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
import sys
import os

# Add the parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.scraper import ParariusScraper

class TestParariusScraper(unittest.TestCase):
    """Test cases for the ParariusScraper class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock config
        self.mock_config = {
            "cities": ["rotterdam", "den-haag"],
            "price_range": {
                "min": 800,
                "max": 1500
            },
            "min_size": 50,
            "min_bedrooms": 2,
            "property_types": ["apartment"],
            "interior": ["furnished", "upholstered", "shell"],
            "max_listings_age_days": 30,
            "user_agent": "Mozilla/5.0 (Test)",
            "request_delay": 0.1,  # Short delay for tests
            "max_retries": 1
        }
        
        # Save mock config to temporary file
        self.config_path = Path('test_config.json')
        with open(self.config_path, 'w') as f:
            json.dump(self.mock_config, f)
            
        # Create scraper instance with test config
        self.scraper = ParariusScraper(config_path=str(self.config_path))
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Remove test config file
        if self.config_path.exists():
            self.config_path.unlink()
    
    def test_initialization(self):
        """Test that the scraper initializes correctly with the config."""
        self.assertEqual(self.scraper.headers['User-Agent'], self.mock_config['user_agent'])
        self.assertEqual(self.scraper.request_delay, self.mock_config['request_delay'])
        self.assertEqual(self.scraper.max_retries, self.mock_config['max_retries'])
        
    def test_build_search_url(self):
        """Test URL construction with different parameters."""
        # Test basic URL for Rotterdam with all parameters
        url = self.scraper._build_search_url('rotterdam')
        expected = "https://www.pararius.com/apartments/rotterdam/800-1500/2-bedrooms/50-m2"
        self.assertEqual(url, expected)
        
        # Test URL with page number
        url = self.scraper._build_search_url('den-haag', page=3)
        expected = "https://www.pararius.com/apartments/den-haag/800-1500/2-bedrooms/50-m2/page-3"
        self.assertEqual(url, expected)
        
        # Test with only price min
        self.scraper.config['price_range'] = {'min': 1000}
        self.scraper.config.pop('max_price', None)
        url = self.scraper._build_search_url('rotterdam')
        expected = "https://www.pararius.com/apartments/rotterdam/1000+/2-bedrooms/50-m2"
        self.assertEqual(url, expected)
        
        # Test with only price max
        self.scraper.config['price_range'] = {'max': 2000}
        url = self.scraper._build_search_url('rotterdam')
        expected = "https://www.pararius.com/apartments/rotterdam/0-2000/2-bedrooms/50-m2"
        self.assertEqual(url, expected)
        
    @patch('src.scraper.requests.get')
    def test_make_request(self, mock_get):
        """Test request making functionality."""
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Call the method
        result = self.scraper._make_request("https://www.pararius.com/test")
        
        # Verify the request was made with correct headers
        mock_get.assert_called_once_with("https://www.pararius.com/test", headers=self.scraper.headers)
        
        # Verify result is a BeautifulSoup object with the expected content
        self.assertIsNotNone(result)
        self.assertEqual(result.body.text, "Test")
        
    def test_extract_listing_data(self):
        """Test extraction of listing data from HTML."""
        # Create a mock listing element
        html = """
        <div class="listing-search-item">
            <a class="listing-search-item__link--title" href="/apartment-for-rent/rotterdam/test123">Test Apartment</a>
            <div class="listing-search-item__price">€ 1,200 per month</div>
            <div class="listing-search-item__features">
                <li class="surface">75 m²</li>
                <li class="number-of-rooms">3 rooms</li>
                <li class="interior">Furnished</li>
            </div>
            <div class="listing-search-item__location">Rotterdam, Centrum</div>
            <div class="listing-search-item__image"><img src="https://www.pararius.com/images/test.jpg"></div>
            <div class="listing-search-item__info">
                <a class="listing-search-item__link">Test Agency</a>
            </div>
        </div>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        listing_element = soup.select_one('.listing-search-item')
        
        # Extract data
        result = self.scraper._extract_listing_data(listing_element)
        
        # Check results
        self.assertEqual(result['id'], 'test123')
        self.assertEqual(result['url'], 'https://www.pararius.com/apartment-for-rent/rotterdam/test123')
        self.assertEqual(result['title'], 'Test Apartment')
        self.assertEqual(result['price'], 1200)
        self.assertEqual(result['size'], 75)
        self.assertEqual(result['rooms'], 3)
        self.assertEqual(result['location'], 'Rotterdam, Centrum')
        self.assertEqual(result['interior'], 'Furnished')
        self.assertEqual(result['image_url'], 'https://www.pararius.com/images/test.jpg')
        self.assertEqual(result['agency'], 'Test Agency')
        self.assertIn('first_seen', result)
        self.assertIn('last_updated', result)

if __name__ == '__main__':
    unittest.main() 