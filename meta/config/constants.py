"""
Meta HealthCard Configuration and Constants
"""

# Meta API Configuration
API_VERSION = "v23.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

# Rate Limiting
DEFAULT_RETRY_COUNT = 5
BASE_WAIT_TIME = 5  # seconds
REQUEST_TIMEOUT = 60  # seconds

# Dimension Compliance
DIMENSION_TOLERANCE = 0.05  # 5% tolerance for margin errors

# Standard aspect ratios
ASPECT_RATIOS = {
    'SQUARE': 1.0,      # 1:1 (1080x1080)
    '4X5': 1.25,        # 4:5 (1080x1350)
    '9X16': 1.778,      # 9:16 (1080x1920)
}

# Health Check Thresholds
THRESHOLDS = {
    'min_headline_count': 3,
    'min_primary_text_count': 3,
    'min_description_count': 2,
    'min_creative_dimensions': 2,
    'max_audience_overlap_pct': 25,
    'min_optimization_goals': 2,
}

# Ad Format Types
AD_FORMATS = {
    'DCO': 'Dynamic Creative Optimization',
    'CAROUSEL': 'Carousel Ad',
    'IMAGE': 'Image Ad',
    'VIDEO': 'Video Ad',
    'COLLECTION': 'Collection Ad',
}

# Optimization Goals
OPTIMIZATION_GOALS = [
    'OFFSITE_CONVERSIONS',
    'LINK_CLICKS',
    'POST_ENGAGEMENT',
    'PAGE_LIKES',
    'EVENT_RESPONSES',
    'REACH',
    'IMPRESSIONS',
    'LANDING_PAGE_VIEWS',
    'LEAD_GENERATION',
]

# Publisher Platforms
PUBLISHER_PLATFORMS = [
    'facebook',
    'instagram',
    'messenger',
    'audience_network',
]
