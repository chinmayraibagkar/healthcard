# Quick Setup Guide

## 🚀 Get Started in 5 Minutes

### 1. Navigate to Project
```powershell
cd "d:\Aristok Technologies\Code Trials\Project_API\Healthcard\Meta HealthCard\HealthCard_Platform"
```

### 2. Create Virtual Environment (Optional but Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Secrets

**Option A: Use existing Google Ads secrets**
- The `.streamlit/secrets.toml` already has Google Ads credentials
- Just add your Meta tokens

**Option B: Start fresh**
- Copy the template: `copy secrets.toml.template .streamlit\secrets.toml`
- Edit `.streamlit\secrets.toml` and add your credentials

#### Add Meta Access Tokens
Open `.streamlit\secrets.toml` and update:
```toml
[meta]
access_token_1 = "YOUR_META_ACCESS_TOKEN_HERE"
# Optional: Add more tokens for rate limiting
# access_token_2 = "YOUR_SECOND_TOKEN"
```

**How to get Meta Access Token:**
1. Go to https://developers.facebook.com/
2. Create or select your app
3. Go to Tools → Graph API Explorer
4. Generate token with permissions: `ads_read` and `ads_management`
5. For long-lived token, use the Access Token Debugger

### 5. Run the Application
```powershell
streamlit run app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

---

## 🎯 Using the Platform

### Select Platform
1. Use the sidebar radio button to choose:
   - 📘 **Meta Ads** (Facebook & Instagram)
   - 🔍 **Google Ads**

### Select Account
2. Choose your ad account from the dropdown

### Run Health Check
3. Click **"🔍 Run Health Check Analysis"**

### Review Results
4. Explore the tabs:
   - **Meta**: Tracking | Creative | Ad Formats | Audience
   - **Google**: Universal | Search | PMax | App

### Export Results
5. Use sidebar buttons to download:
   - CSV Report
   - Excel Report (with detail sheets)

---

## 🔧 Troubleshooting

### "No access token available"
- Check `.streamlit/secrets.toml` has `[meta]` section
- Verify token is not expired
- Ensure token has correct permissions

### "No accounts found"
- Verify token has access to ad accounts
- Check token permissions include `ads_read`
- Ensure accounts are active

### Module Import Errors
```powershell
pip install --upgrade -r requirements.txt
```

### Google Ads API Issues
- Verify developer token is approved
- Check refresh token is valid
- Ensure MCC customer ID is correct (no dashes)

---

## 📚 Next Steps

- **Read [README.md](README.md)** for comprehensive documentation
- **Review [walkthrough.md](walkthrough.md)** (in artifacts) for architecture details
- **Check [implementation_plan.md](implementation_plan.md)** (in artifacts) for design decisions

---

## ✅ Quick Checklist

Before running:
- [ ] Virtual environment activated (optional)
- [ ] Dependencies installed
- [ ] Meta access tokens configured in secrets.toml
- [ ] Google Ads credentials configured (if using Google checks)

Ready to audit!
- [ ] Streamlit app is running
- [ ] Platform selected
- [ ] Account selected
- [ ] Health check executed
- [ ] Results reviewed
- [ ] Report exported

---

**Need Help?** Check the README.md or review the error messages in the Streamlit interface.
