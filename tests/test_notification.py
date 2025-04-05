import os
import sys
from datetime import datetime

from src.notification import GitHubNotifier, send_test_notification

def main():
    """
    Test the GitHub notification system.
    
    For local testing, you need to set:
    - GITHUB_TOKEN: A personal access token with repo scope
    - GITHUB_REPOSITORY: Your repository name (e.g., "username/repo")
    - GITHUB_REPOSITORY_OWNER: Your GitHub username
    """
    # Check if environment variables are set
    if not os.environ.get('GITHUB_TOKEN'):
        print("Error: GITHUB_TOKEN environment variable is not set")
        print("To test locally, you need to create a personal access token with repo scope")
        print("Visit https://github.com/settings/tokens to create one")
        return 1
        
    if not os.environ.get('GITHUB_REPOSITORY'):
        print("Error: GITHUB_REPOSITORY environment variable is not set")
        print("Set it to your repository name, e.g., 'adolfolh/pararius-alerts'")
        return 1
        
    if not os.environ.get('GITHUB_REPOSITORY_OWNER'):
        # Try to extract from GITHUB_REPOSITORY
        if '/' in os.environ.get('GITHUB_REPOSITORY', ''):
            os.environ['GITHUB_REPOSITORY_OWNER'] = os.environ['GITHUB_REPOSITORY'].split('/')[0]
        else:
            print("Error: GITHUB_REPOSITORY_OWNER environment variable is not set")
            print("Set it to your GitHub username")
            return 1
    
    print("Testing GitHub notification system...")
    
    # Create sample listings
    listings = [
        {
            'id': 'test123',
            'url': 'https://www.pararius.com/apartment-for-rent/rotterdam/test123',
            'title': 'Test Apartment in Rotterdam',
            'price': 1200,
            'size': 65,
            'rooms': 2,
            'location': 'Rotterdam, Centrum',
            'interior': 'Furnished',
            'image_url': 'https://www.pararius.com/images/test.jpg',
            'agency': 'Test Agency',
            'first_seen': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        },
        {
            'id': 'test456',
            'url': 'https://www.pararius.com/apartment-for-rent/den-haag/test456',
            'title': 'Test Apartment in Den Haag',
            'price': 950,
            'size': 50,
            'rooms': 1,
            'location': 'Den Haag, Centrum',
            'interior': 'Upholstered',
            'image_url': 'https://www.pararius.com/images/test2.jpg',
            'agency': 'Another Agency',
            'first_seen': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    ]
    
    # Create notifier
    notifier = GitHubNotifier()
    
    # Send notification
    result = notifier.send_notification(listings)
    
    if result:
        print("✅ Notification sent successfully!")
        print("Check your repository's Issues tab to see the notification")
    else:
        print("❌ Failed to send notification")
        print("Check the logs for more information")
    
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main()) 