import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('pararius_notification')

class GitHubNotifier:
    """
    Handles sending notifications for new apartment listings using GitHub Issues.
    
    This class manages creating GitHub issues to notify about new listings,
    eliminating the need for email configuration.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the notifier with configuration.
        
        Args:
            config_path: Path to the configuration JSON file
        """
        self.config = self._load_config(config_path)
        
        # Set up GitHub API details
        # When running in GitHub Actions, GITHUB_TOKEN is automatically available
        self.github_token = os.environ.get('GITHUB_TOKEN')
        self.repo_name = os.environ.get('GITHUB_REPOSITORY')
        
        # Default to enabled if we're running in GitHub Actions
        self.notifications_enabled = bool(self.github_token and self.repo_name)
        
        if not self.notifications_enabled and os.environ.get('CI'):
            logger.warning("GitHub notifications enabled but missing GITHUB_TOKEN or GITHUB_REPOSITORY")
        
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
    
    def _create_issue_content(self, new_listings: List[Dict], updated_listings: List[Dict] = None) -> Dict:
        """
        Create GitHub issue title and body for notifications.
        
        Args:
            new_listings: List of new listings to include
            updated_listings: List of updated listings to include (optional)
            
        Returns:
            Dictionary with issue title and body
        """
        # Create issue title
        now = datetime.now().strftime("%Y-%m-%d")
        title = f"🏠 New Apartment Listings: {len(new_listings)} new listings found - {now}"
        
        # Start building the issue body
        body = "## Pararius Apartment Alerts\n\n"
        
        # Add search parameters section
        body += "### 🔍 Search Parameters\n"
        body += "```json\n"
        body += json.dumps(self.config, indent=2)
        body += "\n```\n\n"
        
        # Add new listings section
        if new_listings:
            body += f"### 🆕 New Listings ({len(new_listings)})\n\n"
            for listing in new_listings:
                body += self._format_listing_markdown(listing)
            
        # Add updated listings section if provided
        if updated_listings and len(updated_listings) > 0:
            body += f"\n### 🔄 Updated Listings ({len(updated_listings)})\n\n"
            for listing in updated_listings:
                body += self._format_listing_markdown(listing)
        
        # Add footer
        body += "\n---\n"
        body += "*This issue was automatically created by the Pararius Apartment Alerts system.*\n"
        body += "*View all listings on the [web interface](https://"+os.environ.get('GITHUB_REPOSITORY_OWNER')+".github.io/"+self.repo_name.split('/')[-1]+"/web/).*"
        
        return {
            "title": title,
            "body": body
        }
    
    def _format_listing_markdown(self, listing: Dict) -> str:
        """
        Format a single listing as Markdown for GitHub issues.
        
        Args:
            listing: Listing data to format
            
        Returns:
            Markdown string for the listing
        """
        # Format price
        price = f"€{listing.get('price', 0):,.0f}" if listing.get('price') is not None else "Unknown"
        
        # Create markdown for the listing
        markdown = f"#### [{listing.get('title', 'Unknown Listing')}]({listing.get('url', '#')})\n"
        markdown += f"- **Price:** {price}\n"
        markdown += f"- **Size:** {listing.get('size', 'Unknown')} m²\n"
        markdown += f"- **Rooms:** {listing.get('rooms', 'Unknown')}\n"
        markdown += f"- **Location:** {listing.get('location', 'Unknown')}\n"
        markdown += f"- **Interior:** {listing.get('interior', 'Unknown')}\n"
        markdown += f"- **Agency:** {listing.get('agency', 'Unknown')}\n"
        
        # Add image if available
        if listing.get('image_url'):
            markdown += f"\n![Apartment]({listing['image_url']})\n"
        
        markdown += "\n---\n\n"
        return markdown
    
    def send_notification(self, new_listings: List[Dict], updated_listings: List[Dict] = None) -> bool:
        """
        Send notification by creating a GitHub issue.
        
        Args:
            new_listings: List of new listings to notify about
            updated_listings: List of updated listings to notify about (optional)
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        # Skip if no listings to notify about
        if not new_listings and not (updated_listings and len(updated_listings) > 0):
            logger.info("No new or updated listings to notify about")
            return True
            
        # Skip if notifications are disabled
        if not self.notifications_enabled:
            logger.info("Notifications are disabled (not running in GitHub Actions or missing token)")
            return True
            
        try:
            # Create issue content
            issue_content = self._create_issue_content(new_listings, updated_listings)
            
            # API endpoint for creating issues
            api_url = f"https://api.github.com/repos/{self.repo_name}/issues"
            
            # Headers for GitHub API
            headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Create issue data
            issue_data = {
                "title": issue_content["title"],
                "body": issue_content["body"],
                "labels": ["notification", "new-listings"]
            }
            
            # Make the API request
            response = requests.post(api_url, json=issue_data, headers=headers)
            response.raise_for_status()
            
            # Get the issue URL from the response
            issue_url = response.json()["html_url"]
            
            logger.info(f"Notification issue created successfully: {issue_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating notification issue: {e}")
            return False
            
    def save_notification_history(self, new_listings: List[Dict], updated_listings: List[Dict] = None) -> None:
        """
        Save notification history to JSON file.
        
        Args:
            new_listings: List of new listings notified about
            updated_listings: List of updated listings notified about (optional)
        """
        try:
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            
            history_file = data_dir / "notification_history.json"
            
            # Load existing history
            history = []
            if history_file.exists():
                with open(history_file, 'r') as f:
                    history = json.load(f)
                    
            # Add new notification record
            notification_record = {
                'timestamp': datetime.now().isoformat(),
                'new_listings_count': len(new_listings),
                'updated_listings_count': len(updated_listings) if updated_listings else 0,
                'new_listing_ids': [listing.get('id') for listing in new_listings],
                'updated_listing_ids': [listing.get('id') for listing in updated_listings] if updated_listings else []
            }
            
            history.append(notification_record)
            
            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
            logger.info(f"Notification history saved")
            
        except Exception as e:
            logger.error(f"Error saving notification history: {e}")

def send_test_notification() -> bool:
    """
    Send a test notification to verify GitHub issue creation.
    
    Returns:
        True if notification was sent successfully, False otherwise
    """
    notifier = GitHubNotifier()
    
    # Create a test listing
    test_listing = {
        'id': 'test123',
        'url': 'https://www.pararius.com/apartment-for-rent/den-haag/test123',
        'title': 'Test Apartment',
        'price': 1500,
        'size': 75,
        'rooms': 3,
        'location': 'Den Haag, Centrum',
        'interior': 'Furnished',
        'image_url': 'https://www.pararius.com/images/test.jpg',
        'agency': 'Test Agency',
        'first_seen': datetime.now().isoformat(),
        'last_updated': datetime.now().isoformat()
    }
    
    return notifier.send_notification([test_listing]) 