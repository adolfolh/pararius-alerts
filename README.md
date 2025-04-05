# Pararius Apartment Alerts

An automated scraper that monitors apartment listings on Pararius.com for Rotterdam and Den Haag, with GitHub Issues notifications for new listings.

## Features

- Monitors Pararius.com for new apartment listings in Rotterdam and Den Haag
- Creates GitHub Issues when new listings appear, automatically notifying repository watchers
- Configurable search parameters (price range, size, bedrooms, etc.)
- Web interface to view recent listings
- Running entirely on GitHub Actions (no server required)

## Setup

1. Fork this repository
2. Enable GitHub Actions for the repository
3. Enable GitHub Pages for the repository (set to deploy from the `gh-pages` branch)
4. Customize your search parameters in `config.json`
5. Watch the repository to receive notifications when new apartments are found

## Notification System

This project uses GitHub Issues for notifications, which means:

- No email server setup required
- Anyone watching the repository will receive notifications based on their GitHub notification preferences
- Each notification includes full listing details with images, formatted nicely as a GitHub Issue
- All notification history is preserved in the repository's Issues tab
- You can comment on issues to discuss specific listings

To customize your GitHub notification preferences:
1. Go to your GitHub [notification settings](https://github.com/settings/notifications)
2. Adjust how you want to receive notifications (email, web, mobile)
3. You can also customize notifications per repository by clicking "Watch" and selecting your preference

## Configuration

Edit the `config.json` file to customize your search:

```json
{
  "cities": ["rotterdam", "den-haag"],
  "price_range": {
    "min": 800,
    "max": 1500
  },
  "min_size": 50,
  "min_bedrooms": 2,
  "property_types": ["apartment"],
  "interior": ["furnished", "upholstered"],
  "max_listings_age_days": 30
}
```

## Development

To contribute to this project:

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

MIT License 