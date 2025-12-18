# HealthCard Platform

A unified advertising health audit dashboard for **Meta Ads** (Facebook & Instagram) and **Google Ads**. This platform provides comprehensive health checks to ensure your advertising campaigns are optimized for maximum performance.

![Platform](https://img.shields.io/badge/Platform-Meta%20%26%20Google%20Ads-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)

## 🌟 Features

### Meta Ads HealthCard (18 Checks)
- **🎯 Tracking & Analytics** (3 checks)
  - URL tags presence validation
  - Facebook Pixel tracking
  - Overall tracking coverage

- **🎨 Creative Assets** (5 checks)
  - Headline variations (min 3)
  - Primary text variations (min 3)
  - Description variations (min 2)
  - Missing copy elements detection
  - Call-to-action presence

- **📱 Ad Format Distribution** (4 checks)
  - Ad format diversity analysis
  - Video ad usage
  - Carousel ad adoption
  - Dynamic Creative Optimization (DCO) usage

- **👥 Audience Targeting** (6 checks)
  - Audience Network usage
  - Lookalike audience utilization
  - Interest targeting validation
  - Optimization goal diversity
  - Advantage+ Audience usage
  - Custom audience adoption

### Google Ads HealthCard (31 Checks)
- **🌐 Universal Checks** (3 checks)
  - Cross-campaign validations

- **🔍 Search Campaigns** (10 checks)
  - Search-specific optimizations

- **🚀 Performance Max** (14 checks)
  - PMax campaign validations

- **📱 App Campaigns** (4 checks)
  - App campaign best practices

## 📁 Project Structure

```
HealthCard_Platform/
├── app.py                          # Main unified application
├── requirements.txt                # Combined dependencies
├── secrets.toml.template          # Secrets configuration template
│
├── .streamlit/
│   └── secrets.toml               # Your actual credentials (gitignored)
│
├── meta/                          # Meta Ads HealthCard
│   ├── app.py                     # Meta app orchestrator
│   ├── checks/                    # Health check modules
│   │   ├── tracking_checks.py
│   │   ├── creative_checks.py
│   │   ├── ad_format_checks.py
│   │   └── audience_checks.py
│   ├── services/                  # API services
│   │   ├── meta_api_client.py
│   │   └── data_fetcher.py
│   ├── components/                # UI components
│   │   └── ui_components.py
│   ├── utils/                     # Utilities
│   │   ├── data_processing.py
│   │   └── dimension_utils.py
│   └── config/                    # Configuration
│       └── constants.py
│
└── google/                        # Google Ads HealthCard
    ├── app.py                     # Google app
    ├── checks/                    # Health check modules
    ├── services/                  # API services
    ├── components/                # UI components
    ├── utils/                     # Utilities
    └── config/                    # Configuration
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Meta Ads account with API access
- Google Ads account with API access
- Access tokens/credentials for both platforms

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd "d:\Aristok Technologies\Code Trials\Project_API\Healthcard\Meta HealthCard\HealthCard_Platform"
   ```

2. **Create a virtual environment (recommended):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure secrets:**
   - Copy `secrets.toml.template` to `.streamlit/secrets.toml`
   - Fill in your credentials (see Configuration section below)

5. **Run the application:**
   ```powershell
   streamlit run app.py
   ```

## ⚙️ Configuration

### Meta Ads Credentials

You need Meta Access Tokens to use the Meta HealthCard. You can configure multiple tokens for rate limit distribution.

**Steps to get Meta Access Token:**
1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create or select your app
3. Generate a User Access Token with these permissions:
   - `ads_read`
   - `ads_management`
4. For long-lived tokens, exchange your short-lived token

**Add to `.streamlit/secrets.toml`:**
```toml
[meta]
access_token_1 = "YOUR_META_ACCESS_TOKEN_1"
access_token_2 = "YOUR_META_ACCESS_TOKEN_2"  # Optional
access_token_3 = "YOUR_META_ACCESS_TOKEN_3"  # Optional
```

### Google Ads Credentials

You need Google Ads API credentials including developer token, OAuth2 credentials, and MCC account ID.

**Steps to get Google Ads credentials:**
1. Apply for a [Developer Token](https://developers.google.com/google-ads/api/docs/get-started/dev-token)
2. Set up [OAuth2 credentials](https://developers.google.com/google-ads/api/docs/oauth/overview)
3. Generate refresh token using OAuth2 playground
4. Note your MCC (Manager) account ID

**Add to `.streamlit/secrets.toml`:**
```toml
[google_ads]
developer_token = "YOUR_DEVELOPER_TOKEN"
client_id = "YOUR_CLIENT_ID.apps.googleusercontent.com"
client_secret = "YOUR_CLIENT_SECRET"
refresh_token = "YOUR_REFRESH_TOKEN"
login_customer_id = "YOUR_MCC_CUSTOMER_ID"
use_proto_plus = true
```

## 📖 Usage

1. **Launch the application:**
   ```powershell
   streamlit run app.py
   ```

2. **Select Platform:**
   - Use the sidebar to switch between Meta Ads and Google Ads

3. **Select Account:**
   - Choose the ad account you want to audit

4. **Run Health Check:**
   - Click "Run Health Check Analysis" button
   - Wait for checks to complete

5. **Review Results:**
   - Explore results organized by category tabs
   - View detailed analysis for failed/warning checks
   - Download reports as CSV or Excel

6. **Export Results:**
   - Use the sidebar download buttons to export results
   - Available formats: CSV, Excel

## 🎯 Health Check Categories

### Meta Ads

#### Tracking Checks
- ✅ **URL Tags**: Validates UTM parameters and tracking URLs
- ✅ **Pixel Tracking**: Ensures Facebook Pixel is installed
- ✅ **Coverage**: Verifies at least one tracking method per ad

#### Creative Checks
- ✅ **Headlines**: Minimum 3 headline variations
- ✅ **Primary Text**: Minimum 3 body copy variations
- ✅ **Descriptions**: Minimum 2 description variations
- ✅ **Copy Elements**: No missing essential copy
- ✅ **CTA**: Call-to-action button configured

#### Ad Format Checks
- ✅ **Distribution**: Diverse ad format usage
- ✅ **Video**: Video ad adoption
- ✅ **Carousel**: Carousel format usage
- ✅ **DCO**: Dynamic Creative Optimization

#### Audience Checks
- ✅ **Audience Network**: Placement strategy
- ✅ **Lookalike**: Lookalike audience usage
- ✅ **Interests**: Interest targeting
- ✅ **Goals**: Optimization goal diversity
- ✅ **Advantage+**: Automated audience expansion
- ✅ **Custom**: Custom audience for retargeting

### Google Ads

Includes 31 checks across Universal, Search, Performance Max, and App campaigns covering bidding strategies, budgets, targeting, extensions, and more.

## 🛠️ Troubleshooting

### Common Issues

**1. "No access token available"**
- Ensure Meta access tokens are properly configured in `.streamlit/secrets.toml`
- Verify token has required permissions
- Check if token has expired

**2. "Failed to connect to Google Ads API"**
- Verify all Google Ads credentials are correct
- Ensure developer token is approved
- Check MCC account ID format (no dashes)

**3. "No accounts found"**
- Verify API access permissions
- Check if tokens have access to ad accounts
- Ensure accounts are active

**4. Import Errors**
- Reinstall dependencies: `pip install -r requirements.txt`
- Ensure Python version is 3.8+

## 📊 Best Practices

### Meta Ads
- Use at least 3-5 creative variations per ad
- Implement both URL tracking and Pixel
- Test multiple ad formats
- Leverage Lookalike and Custom Audiences
- Enable Advantage+ features

### Google Ads
- Maintain recommended budget levels
- Use all relevant ad extensions
- Implement conversion tracking
- Monitor Quality Scores
- Test multiple ad variations

## 🔒 Security

- Never commit `.streamlit/secrets.toml` to version control
- Keep access tokens and API credentials secure
- Rotate tokens periodically
- Use environment-specific credentials

## 📝 License

This project is proprietary software developed for Aristok Technologies.

## 👥 Support

For issues or questions:
- Check the troubleshooting section
- Review Meta API documentation: https://developers.facebook.com/docs/marketing-apis
- Review Google Ads API documentation: https://developers.google.com/google-ads/api

## 🔄 Version History

### v1.0.0 (Current)
- Initial release
- Meta Ads HealthCard with 18 checks
- Google Ads HealthCard with 31 checks
- Unified platform with easy switching
- Export functionality (CSV & Excel)

---

**Built with ❤️ using Streamlit**
