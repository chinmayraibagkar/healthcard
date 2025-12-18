"""
Constants and configuration for Google Ads HealthCard Dashboard
"""

# API Version
GOOGLE_ADS_API_VERSION = "v17"

# =============================
# THRESHOLDS FOR HEALTH CHECKS
# =============================

# Check 1: Spend Split (Search Campaigns)
SPEND_SPLIT_THRESHOLDS = {
    "EXACT": 0.70,      # Exact should be >= 70%
    "PHRASE": 0.20,     # Phrase should be ~20%
    "BROAD": 0.10       # Broad should be ~10%
}
SPEND_SPLIT_TOLERANCE = 0.05  # 5% tolerance

# Check 3: Limited by Budget
LIMITED_BUDGET_THRESHOLD = 0.10  # Should be less than 10%

# Check 4: RSAs per Ad Group
MIN_RSAS_PER_AD_GROUP = 2

# Check 5: Unique RSAs Ratio
MIN_UNIQUE_RSA_RATIO = 1.0  # 1:1 ratio

# Check 8: Sitelinks per RSA
MIN_SITELINKS_PER_RSA = 4

# Check 10: Quality Score Thresholds
QUALITY_SCORE_THRESHOLDS = {
    "brand": 9,        # Brand QS should be >= 9
    "non_brand": 7,    # Non-Brand QS should be >= 7
    "competitor": 5    # Competitor QS should be >= 5
}

# Check 19 & 31: Asset Counts
PMAX_MIN_HEADLINES = 3
PMAX_MAX_HEADLINES = 15
PMAX_MIN_LONG_HEADLINES = 1
PMAX_MAX_LONG_HEADLINES = 5
PMAX_MIN_DESCRIPTIONS = 2
PMAX_MAX_DESCRIPTIONS = 5

APP_MIN_HEADLINES = 5
APP_MIN_DESCRIPTIONS = 5

# Check 21: PMax Sitelinks
PMAX_MIN_SITELINKS = 4

# Check 25: Asset-only PMax
PMAX_MIN_IMAGES = 5
PMAX_MIN_VIDEOS = 1

# Check 26: PMax Spend Split
PMAX_SPEND_SPLIT = {
    "SHOPPING": 0.80,
    "VIDEO": 0.10,
    "OTHER": 0.10
}
PMAX_SPEND_TOLERANCE = 0.10  # 10% tolerance

# =============================
# CAMPAIGN TYPE IDENTIFIERS
# =============================

CAMPAIGN_TYPES = {
    "SEARCH": "SEARCH",
    "PERFORMANCE_MAX": "PERFORMANCE_MAX",
    "APP": "MULTI_CHANNEL",  # App campaigns
    "DISPLAY": "DISPLAY",
    "VIDEO": "VIDEO",
    "SHOPPING": "SHOPPING"
}

# Keywords to identify ad group types
AD_GROUP_TYPE_KEYWORDS = {
    "brand": ["brand", "branded"],
    "competitor": ["competitor", "competitive", "comp"]
}

# =============================
# AD STRENGTH VALUES
# =============================

AD_STRENGTH_VALUES = [
    "EXCELLENT",
    "GOOD", 
    "AVERAGE",
    "POOR",
    "PENDING",
    "UNSPECIFIED",
    "UNKNOWN"
]

# =============================
# CHECK CATEGORIES
# =============================

UNIVERSAL_CHECKS = [3, 12, 13]
SEARCH_CHECKS = [1, 2, 4, 5, 6, 7, 8, 9, 10, 11]
PMAX_CHECKS = [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27]
APP_CHECKS = [28, 29, 30, 31]

# =============================
# CHECK DESCRIPTIONS
# =============================

CHECK_DESCRIPTIONS = {
    1: "Contribution of Spends - 70:20:10 (Exact:Phrase:Broad)",
    2: "Audience in Observation - Remarketing, Inmarket, Affinity",
    3: "Limited by Budget Campaigns - Should be <10%",
    4: "Number of RSAs - At least 2 per ad group",
    5: "Unique RSAs Ratio - At least 1:1",
    6: "Cross Keyword Negation",
    7: "Ad Copy Quality - Ad Strength Distribution",
    8: "4 Unique Sitelinks per RSA",
    9: "Display Path Added",
    10: "Weighted Average Quality Score",
    11: "Percentage of Keywords without Impressions",
    12: "Conversion Goal - Campaign Specific",
    13: "Location Targeting - Presence Only",
    14: "Age Exclusions (PMax)",
    15: "Brand Exclusions (PMax)",
    16: "Auto Asset Optimization Off (PMax)",
    17: "Search Themes Present (PMax)",
    18: "Search Term Negation (PMax)",
    19: "Headlines/Descriptions Count (PMax)",
    20: "Call to Action Not Automated",
    21: "Sitelinks >= 4 (PMax)",
    22: "Display Path Present (PMax)",
    23: "Callouts Present (PMax)",
    24: "Structured Snippets Present (PMax)",
    25: "5 Images & 1 Video in Asset Groups (PMax)",
    26: "PMax Spend Split - 80:10:10",
    27: "Product Coverage through Ads",
    28: "Single In-App Action Optimization",
    29: "Deferred Deep Linking",
    30: "Custom Store Listing",
    31: "Headlines/Descriptions >= 5 each (App)"
}

# =============================
# UI COLORS
# =============================

STATUS_COLORS = {
    "pass": "#00C851",      # Green
    "warning": "#ffbb33",   # Yellow/Orange
    "fail": "#ff4444",      # Red
    "info": "#33b5e5"       # Blue
}
