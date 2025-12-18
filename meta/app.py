"""
Meta HealthCard Dashboard Application
Orchestrates all health checks for Meta Ads
"""

import streamlit as st
import pandas as pd
from meta.services.meta_api_client import get_all_accounts
from meta.services.data_fetcher import get_ads_for_account, get_adsets_for_account
from meta.utils.data_processing import flatten_ad_data, flatten_adset_data
from meta.checks.tracking_checks import run_all_tracking_checks
from meta.checks.creative_checks import run_all_creative_checks
from meta.checks.ad_format_checks import run_all_ad_format_checks
from meta.checks.audience_checks import run_all_audience_checks
from meta.components.ui_components import (
    render_check_grid,
    render_summary_stats,
    render_sidebar_account_selector,
    render_download_button,
    render_platform_badge
)
from meta.audiences_explorer import render_audiences_explorer


def run_meta_healthcard():
    """Main function to run Meta HealthCard dashboard"""
    
    # Platform badge
    render_platform_badge('meta')
    
    # Load accounts
    if 'meta_accounts' not in st.session_state:
        with st.spinner("Loading Meta ad accounts..."):
            accounts = get_all_accounts()
            st.session_state.meta_accounts = accounts
    else:
        accounts = st.session_state.meta_accounts
    
    if not accounts:
        st.error("❌ No Meta ad accounts found. Please check your access token configuration.")
        st.stop()
    
    # Account selector
    selected_account_id = render_sidebar_account_selector(accounts)
    
    if not selected_account_id:
        st.info("👈 Please select an account from the sidebar to begin.")
        return
    
    # Get access token
    from meta.services.meta_api_client import get_token_for_request
    access_token = get_token_for_request(0)
    
    if not access_token:
        st.error("❌ No access token available. Please configure your secrets.")
        st.stop()
    
    # Date range selector (similar to Google)
    st.sidebar.markdown("### 📅 Date Range")
    date_options = {
        "Last 7 Days": "last_7d",
        "Last 14 Days": "last_14d",
        "Last 30 Days": "last_30d",
        "Last 90 Days": "last_90d",
        "This Month": "this_month",
        "Last Month": "last_month"
    }
    selected_date_range = st.sidebar.selectbox(
        "Select Date Range",
        options=list(date_options.keys()),
        index=2,  # Default to Last 30 Days
        key="meta_date_range"
    )
    date_preset = date_options[selected_date_range]
    
    # Run analysis button
    st.sidebar.markdown("---")
    if st.sidebar.button("🔍 Run Health Check Analysis", type="primary", use_container_width=True):
        # Clear previous results
        st.session_state.meta_results = {}
        
        # Fetch data with impressions filtering
        with st.spinner(f"Fetching ads and adsets with impressions ({selected_date_range})..."):
            try:
                ads_raw = get_ads_for_account(selected_account_id, access_token, date_preset=date_preset)
                adsets_raw = get_adsets_for_account(selected_account_id, access_token, date_preset=date_preset)
                
                if not ads_raw and not adsets_raw:
                    st.warning("⚠️ No active ads or adsets found for this account.")
                    return
                
                # Flatten data
                ads_df = flatten_ad_data(ads_raw) if ads_raw else pd.DataFrame()
                adsets_df = flatten_adset_data(adsets_raw) if adsets_raw else pd.DataFrame()
                
                # Data fetched successfully
                
            except Exception as e:
                st.error(f"❌ Error fetching data: {e}")
                return
        
        # Create tabs (Audiences Explorer temporarily disabled)
        tab_tracking, tab_creative, tab_format, tab_audience = st.tabs([
            "🎯 Tracking",
            "🎨 Creative",
            "📱 Ad Formats",
            "👥 Audience"
        ])
        
        # Run Tracking Checks
        with tab_tracking:
            st.header("Tracking & Analytics")
            st.caption("Validate tracking setup for conversions and performance measurement")
            
            with st.spinner("Running tracking checks..."):
                try:
                    tracking_results = run_all_tracking_checks(ads_df)
                    st.session_state.meta_results['tracking'] = tracking_results
                    render_summary_stats(tracking_results)
                    render_check_grid(tracking_results, columns=2)
                except Exception as e:
                    st.error(f"Error running tracking checks: {e}")
        
        # Run Creative Checks
        with tab_creative:
            st.header("Creative Assets")
            st.caption("Validate ad copy, headlines, and creative variations")
            
            with st.spinner("Running creative checks..."):
                try:
                    creative_results = run_all_creative_checks(ads_df)
                    st.session_state.meta_results['creative'] = creative_results
                    render_summary_stats(creative_results)
                    render_check_grid(creative_results, columns=2)
                except Exception as e:
                    st.error(f"Error running creative checks: {e}")
        
        # Run Ad Format Checks
        with tab_format:
            st.header("Ad Format Distribution")
            st.caption("Analyze ad format diversity and usage patterns")
            
            with st.spinner("Running ad format checks..."):
                try:
                    format_results = run_all_ad_format_checks(ads_df)
                    st.session_state.meta_results['format'] = format_results
                    render_summary_stats(format_results)
                    render_check_grid(format_results, columns=2)
                except Exception as e:
                    st.error(f"Error running ad format checks: {e}")
        
        # Run Audience Checks
        with tab_audience:
            st.header("Audience Targeting")
            st.caption("Validate audience setup and targeting strategy")
            
            with st.spinner("Running audience checks..."):
                try:
                    audience_results = run_all_audience_checks(adsets_df)
                    st.session_state.meta_results['audience'] = audience_results
                    render_summary_stats(audience_results)
                    render_check_grid(audience_results, columns=2)
                except Exception as e:
                    st.error(f"Error running audience checks: {e}")
        
        # Audiences Explorer Tab - temporarily disabled
        # with tab_explorer:
        #     render_audiences_explorer(selected_account_id, access_token)
        
        # Download button
        if st.session_state.meta_results:
            all_results = []
            for category_results in st.session_state.meta_results.values():
                all_results.extend(category_results)
            render_download_button(all_results, filename="meta_healthcard_report")
    
    # Show cached results if available
    elif 'meta_results' in st.session_state and st.session_state.meta_results:
        tab_tracking, tab_creative, tab_format, tab_audience = st.tabs([
            "🎯 Tracking",
            "🎨 Creative",
            "📱 Ad Formats",
            "👥 Audience"
        ])
        
        with tab_tracking:
            if 'tracking' in st.session_state.meta_results:
                st.header("Tracking & Analytics")
                results = st.session_state.meta_results['tracking']
                render_summary_stats(results)
                render_check_grid(results, columns=2)
        
        with tab_creative:
            if 'creative' in st.session_state.meta_results:
                st.header("Creative Assets")
                results = st.session_state.meta_results['creative']
                render_summary_stats(results)
                render_check_grid(results, columns=2)
        
        with tab_format:
            if 'format' in st.session_state.meta_results:
                st.header("Ad Format Distribution")
                results = st.session_state.meta_results['format']
                render_summary_stats(results)
                render_check_grid(results, columns=2)
        
        with tab_audience:
            if 'audience' in st.session_state.meta_results:
                st.header("Audience Targeting")
                results = st.session_state.meta_results['audience']
                render_summary_stats(results)
                render_check_grid(results, columns=2)
        
        # Audiences Explorer - temporarily disabled
        # with tab_explorer:
        #     # Get access token for explorer
        #     from meta.services.meta_api_client import get_token_for_request
        #     access_token = get_token_for_request(0)
        #     if access_token and selected_account_id:
        #         render_audiences_explorer(selected_account_id, access_token)
        #     else:
        #         st.warning("Please select an account to use Audiences Explorer.")
        
        # Download button for cached results
        all_results = []
        for category_results in st.session_state.meta_results.values():
            all_results.extend(category_results)
        render_download_button(all_results, filename="meta_healthcard_report")
    
    else:
        st.info("👆 Click 'Run Health Check Analysis' in the sidebar to start the audit.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #999; font-size: 0.85rem;">
            <p>Meta Ads HealthCard Dashboard | Comprehensive Ad Account Audit</p>
            <p>Tracking (3) • Creative (5) • Ad Formats (4) • Audience (6)</p>
        </div>
        """,
        unsafe_allow_html=True
    )
