import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

from src.scraper import ParariusScraper
from src.storage import ListingStorage
from src.notification import GitHubNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('pararius_main')

def load_config(config_path: str = "config.json") -> Dict:
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

def save_run_stats(stats: Dict) -> None:
    """
    Save statistics from the current run.
    
    Args:
        stats: Dictionary containing run statistics
    """
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    stats_file = data_dir / "run_stats.json"
    
    # Load existing stats
    all_stats = []
    if stats_file.exists():
        try:
            with open(stats_file, 'r') as f:
                all_stats = json.load(f)
        except (json.JSONDecodeError, IOError):
            all_stats = []
    
    # Add new stats
    all_stats.append(stats)
    
    # Keep only the last 100 runs to avoid file growth
    if len(all_stats) > 100:
        all_stats = all_stats[-100:]
    
    # Save updated stats
    try:
        with open(stats_file, 'w') as f:
            json.dump(all_stats, f, indent=2)
            logger.info("Run statistics saved")
    except IOError as e:
        logger.error(f"Error saving run statistics: {e}")

def main() -> int:
    """
    Main function to run the scraper and notification process.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    start_time = datetime.now()
    logger.info("Starting Pararius apartment scraper")
    
    # Create stats dictionary to track this run
    stats = {
        'timestamp': start_time.isoformat(),
        'success': False,
        'new_listings_count': 0,
        'updated_listings_count': 0,
        'total_listings_count': 0,
        'notification_sent': False,
        'errors': []
    }
    
    try:
        # Load configuration
        config = load_config()
        if not config:
            stats['errors'].append("Failed to load configuration")
            logger.error("Exiting due to configuration error")
            return 1
            
        # Initialize components
        scraper = ParariusScraper()
        storage = ListingStorage()
        notifier = GitHubNotifier()
        
        # Clean old listings
        removed_count = storage.clean_old_listings()
        logger.info(f"Removed {removed_count} old listings from storage")
        
        # Load existing listings
        existing_listings = storage.load_listings()
        logger.info(f"Loaded {len(existing_listings)} existing listings from storage")
        
        # Scrape new listings
        logger.info("Starting scraping process")
        new_scraped_listings = scraper.scrape_all_cities()
        logger.info(f"Scraped {len(new_scraped_listings)} listings")
        
        # Save latest scraped listings for reference
        storage.save_latest_listings(new_scraped_listings)
        
        # Compare with existing listings to find changes
        added_listings, updated_listings, all_current_listings = storage.compare_listings(
            new_scraped_listings, existing_listings
        )
        
        # Update stats
        stats['new_listings_count'] = len(added_listings)
        stats['updated_listings_count'] = len(updated_listings)
        stats['total_listings_count'] = len(all_current_listings)
        
        # Save all current listings
        storage.save_listings(all_current_listings)
        
        # Send notifications if needed
        if added_listings or updated_listings:
            logger.info(f"Sending notifications for {len(added_listings)} new and {len(updated_listings)} updated listings")
            notification_sent = notifier.send_notification(added_listings, updated_listings)
            stats['notification_sent'] = notification_sent
            
            # Save notification history
            notifier.save_notification_history(added_listings, updated_listings)
        else:
            logger.info("No new or updated listings found, skipping notification")
            
        # Mark success
        stats['success'] = True
        
    except Exception as e:
        error_msg = f"Error during execution: {str(e)}"
        logger.error(error_msg, exc_info=True)
        stats['errors'].append(error_msg)
        
    finally:
        # Calculate run duration
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        stats['duration_seconds'] = duration
        logger.info(f"Run completed in {duration:.2f} seconds")
        
        # Save run statistics
        save_run_stats(stats)
        
    return 0 if stats['success'] else 1

if __name__ == "__main__":
    sys.exit(main()) 