import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('pararius_storage')

class ListingStorage:
    """
    Handles storage and retrieval of apartment listings.
    
    This class manages reading and writing listing data to JSON files,
    as well as comparing new and existing listings to detect changes.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the storage with configuration.
        
        Args:
            config_path: Path to the configuration JSON file
        """
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        self.listings_file = self.data_dir / "listings.json"
        
        self.config = self._load_config(config_path)
        self.max_age_days = self.config.get('max_listings_age_days', 30)
        
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
            return {}
    
    def load_listings(self) -> List[Dict]:
        """
        Load all stored listings from JSON file.
        
        Returns:
            List of listings as dictionaries
        """
        if not self.listings_file.exists():
            logger.info(f"Listings file does not exist at {self.listings_file}")
            return []
            
        try:
            with open(self.listings_file, 'r') as f:
                listings = json.load(f)
                logger.info(f"Loaded {len(listings)} listings from storage")
                return listings
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading listings: {e}")
            return []
    
    def save_listings(self, listings: List[Dict]) -> bool:
        """
        Save listings to JSON file.
        
        Args:
            listings: List of listings to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.listings_file, 'w') as f:
                json.dump(listings, f, indent=2)
                logger.info(f"Saved {len(listings)} listings to storage")
            return True
        except IOError as e:
            logger.error(f"Error saving listings: {e}")
            return False
    
    def save_latest_listings(self, listings: List[Dict]) -> bool:
        """
        Save latest scraped listings to separate JSON file.
        
        Args:
            listings: List of listings to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            latest_file = self.data_dir / "latest_listings.json"
            with open(latest_file, 'w') as f:
                json.dump(listings, f, indent=2)
                logger.info(f"Saved {len(listings)} listings to latest listings file")
            return True
        except IOError as e:
            logger.error(f"Error saving latest listings: {e}")
            return False
    
    def compare_listings(self, new_listings: List[Dict], existing_listings: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Compare new listings with existing ones to identify changes.
        
        Args:
            new_listings: List of newly scraped listings
            existing_listings: List of previously stored listings
            
        Returns:
            Tuple of (added_listings, updated_listings, all_current_listings)
        """
        # Create lookup dictionaries for faster comparison
        existing_by_id = {listing['id']: listing for listing in existing_listings}
        new_by_id = {listing['id']: listing for listing in new_listings}
        
        added_listings = []
        updated_listings = []
        
        # Find new and updated listings
        for listing_id, new_listing in new_by_id.items():
            if listing_id not in existing_by_id:
                # This is a new listing
                logger.info(f"New listing found: {new_listing['title']} - {new_listing['url']}")
                added_listings.append(new_listing)
            else:
                # This listing exists, check for updates
                existing_listing = existing_by_id[listing_id]
                if self._is_listing_updated(new_listing, existing_listing):
                    # Preserve the original first_seen date
                    new_listing['first_seen'] = existing_listing['first_seen']
                    new_listing['last_updated'] = datetime.now().isoformat()
                    logger.info(f"Updated listing found: {new_listing['title']} - {new_listing['url']}")
                    updated_listings.append(new_listing)
                else:
                    # No update, use existing listing with original dates
                    new_by_id[listing_id] = existing_listing
        
        # Combine existing listings that are still relevant with new listings
        preserved_listings = [
            listing for listing_id, listing in existing_by_id.items()
            if listing_id not in new_by_id and not self._is_listing_too_old(listing)
        ]
        
        # Create the final list of all current listings
        all_current_listings = list(new_by_id.values()) + preserved_listings
        
        logger.info(f"Found {len(added_listings)} new listings and {len(updated_listings)} updated listings")
        logger.info(f"Total current listings: {len(all_current_listings)}")
        
        return added_listings, updated_listings, all_current_listings
    
    def _is_listing_updated(self, new_listing: Dict, existing_listing: Dict) -> bool:
        """
        Check if a listing has been updated.
        
        Args:
            new_listing: Newly scraped listing
            existing_listing: Previously stored listing
            
        Returns:
            True if the listing has changed significantly, False otherwise
        """
        # Check for price changes
        if new_listing.get('price') != existing_listing.get('price'):
            return True
            
        # Check for changes in availability
        if new_listing.get('available') != existing_listing.get('available'):
            return True
            
        # Check for changes in description
        if new_listing.get('description') != existing_listing.get('description'):
            return True
            
        return False
    
    def _is_listing_too_old(self, listing: Dict) -> bool:
        """
        Check if a listing is older than the maximum age.
        
        Args:
            listing: Listing to check
            
        Returns:
            True if the listing is too old, False otherwise
        """
        try:
            first_seen = datetime.fromisoformat(listing.get('first_seen', datetime.now().isoformat()))
            max_age = timedelta(days=self.max_age_days)
            return datetime.now() - first_seen > max_age
        except (ValueError, TypeError):
            # If we can't parse the date, assume it's not too old
            return False
    
    def clean_old_listings(self) -> int:
        """
        Remove listings that are older than the maximum age.
        
        Returns:
            Number of listings removed
        """
        listings = self.load_listings()
        
        original_count = len(listings)
        listings = [listing for listing in listings if not self._is_listing_too_old(listing)]
        
        removed_count = original_count - len(listings)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} old listings")
            self.save_listings(listings)
            
        return removed_count 