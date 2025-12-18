"""
Google Ads HealthCard Dashboard
A comprehensive Streamlit dashboard for auditing Google Ads accounts
with 31 health checks across Search, Performance Max, and App campaigns.
"""

import streamlit as st
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.google_ads_client import get_google_ads_client, get_accessible_customers
from checks.universal_checks import run_all_universal_checks
from checks.search_checks import run_all_search_checks
from checks.pmax_checks import run_all_pmax_checks
from checks.app_checks import run_all_app_checks
from components.ui_components import (
    render_check_grid, 
    render_summary_stats,
    render_sidebar_account_selector,
    render_download_all_button
)
from utils.data_processing import calculate_overall_health_score

# Page configuration
st.set_page_config(
    page_title="Google Ads HealthCard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Theme aware
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #4285f4, #34a853, #fbbc05, #ea4335);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        opacity: 0.7;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4285f4 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'client' not in st.session_state:
    st.session_state.client = None
if 'accounts' not in st.session_state:
    st.session_state.accounts = None
if 'selected_customer_id' not in st.session_state:
    st.session_state.selected_customer_id = None
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'date_range' not in st.session_state:
    st.session_state.date_range = "LAST_30_DAYS"


def initialize_client():
    """Initialize the Google Ads API client."""
    if st.session_state.client is None:
        try:
            st.session_state.client = get_google_ads_client()
            st.success("✅ Connected to Google Ads API")
        except Exception as e:
            st.error(f"❌ Failed to connect to Google Ads API: {str(e)}")
            st.stop()


def load_accounts():
    """Load accessible Google Ads accounts."""
    if st.session_state.accounts is None:
        with st.spinner("Loading accounts..."):
            try:
                st.session_state.accounts = get_accessible_customers(st.session_state.client)
            except Exception as e:
                st.error(f"Failed to load accounts: {str(e)}")
                st.session_state.accounts = None


def main():
    # Initialize API client
    initialize_client()
    
    if st.session_state.client is None:
        st.error("Unable to connect to Google Ads API. Please check your credentials.")
        st.stop()
    
    # Load accounts
    load_accounts()
    
    # Sidebar - Account Selection
    if st.session_state.accounts is not None and not st.session_state.accounts.empty:
        selected_id = render_sidebar_account_selector(st.session_state.accounts)
        
        if selected_id:
            st.session_state.selected_customer_id = selected_id
    else:
        st.sidebar.warning("No accounts available")
    
    # Sidebar - Date Range Selector
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Date Range")
    date_options = {
        "Last 7 Days": "LAST_7_DAYS",
        "Last 14 Days": "LAST_14_DAYS",
        "Last 30 Days": "LAST_30_DAYS",
        "Last 90 Days": "LAST_90_DAYS",
        "This Month": "THIS_MONTH",
        "Last Month": "LAST_MONTH"
    }
    selected_date_range = st.sidebar.selectbox(
        "Select Date Range",
        options=list(date_options.keys()),
        index=2,  # Default to Last 30 Days
        key="date_range_selector"
    )
    st.session_state.date_range = date_options[selected_date_range]
    st.sidebar.caption(f"Used for: Spend Split, Keywords w/o Impressions, Quality Score")
    
    # Main content
    if st.session_state.selected_customer_id:
        customer_id = st.session_state.selected_customer_id
        
        # Run Analysis Button
        st.sidebar.markdown("---")
        if st.sidebar.button("🔍 Run Health Check Analysis", type="primary", use_container_width=True):
            st.session_state.results = {}
            
            # Create tabs
            tab_universal, tab_search, tab_pmax, tab_app = st.tabs([
                "🌐 Universal", 
                "🔍 Search Campaigns", 
                "🚀 Performance Max", 
                "📱 App Campaigns"
            ])
            
            # Run Universal Checks
            with tab_universal:
                st.header("Universal Checks")
                st.caption("Applicable to all campaign types")
                with st.spinner("Running universal checks..."):
                    try:
                        universal_results = run_all_universal_checks(st.session_state.client, customer_id)
                        st.session_state.results["Universal"] = universal_results
                        render_summary_stats(universal_results)
                        render_check_grid(universal_results, columns=3)
                    except Exception as e:
                        st.error(f"Error running universal checks: {str(e)}")
            
            # Run Search Checks
            with tab_search:
                st.header("Search Campaign Checks")
                st.caption("Specific to Search campaigns")
                with st.spinner("Running search campaign checks..."):
                    try:
                        search_results = run_all_search_checks(st.session_state.client, customer_id)
                        st.session_state.results["Search"] = search_results
                        render_summary_stats(search_results)
                        render_check_grid(search_results, columns=3)
                    except Exception as e:
                        st.error(f"Error running search checks: {str(e)}")
            
            # Run PMax Checks
            with tab_pmax:
                st.header("Performance Max Checks")
                st.caption("Specific to Performance Max campaigns")
                with st.spinner("Running Performance Max checks..."):
                    try:
                        pmax_results = run_all_pmax_checks(st.session_state.client, customer_id)
                        st.session_state.results["PMax"] = pmax_results
                        render_summary_stats(pmax_results)
                        render_check_grid(pmax_results, columns=3)
                    except Exception as e:
                        st.error(f"Error running PMax checks: {str(e)}")
            
            # Run App Checks
            with tab_app:
                st.header("App Campaign Checks")
                st.caption("Specific to App campaigns")
                with st.spinner("Running App campaign checks..."):
                    try:
                        app_results = run_all_app_checks(st.session_state.client, customer_id)
                        st.session_state.results["App"] = app_results
                        render_summary_stats(app_results)
                        render_check_grid(app_results, columns=2)
                    except Exception as e:
                        st.error(f"Error running App checks: {str(e)}")
            
            # Download all results
            if st.session_state.results:
                render_download_all_button(st.session_state.results)
        
        # Show cached results if available
        elif st.session_state.results:
            tab_universal, tab_search, tab_pmax, tab_app = st.tabs([
                "🌐 Universal", 
                "🔍 Search Campaigns", 
                "🚀 Performance Max", 
                "📱 App Campaigns"
            ])
            
            with tab_universal:
                if "Universal" in st.session_state.results:
                    st.header("Universal Checks")
                    render_summary_stats(st.session_state.results["Universal"])
                    render_check_grid(st.session_state.results["Universal"], columns=3)
            
            with tab_search:
                if "Search" in st.session_state.results:
                    st.header("Search Campaign Checks")
                    render_summary_stats(st.session_state.results["Search"])
                    render_check_grid(st.session_state.results["Search"], columns=3)
            
            with tab_pmax:
                if "PMax" in st.session_state.results:
                    st.header("Performance Max Checks")
                    render_summary_stats(st.session_state.results["PMax"])
                    render_check_grid(st.session_state.results["PMax"], columns=3)
            
            with tab_app:
                if "App" in st.session_state.results:
                    st.header("App Campaign Checks")
                    render_summary_stats(st.session_state.results["App"])
                    render_check_grid(st.session_state.results["App"], columns=2)
            
            render_download_all_button(st.session_state.results)
        else:
            st.info("👆 Click 'Run Health Check Analysis' in the sidebar to start the audit.")
    else:
        st.info("👈 Please select an account from the sidebar to begin.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.85rem;">
        <p>Google Ads HealthCard Dashboard | 31 Health Checks</p>
        <p>Universal (3) • Search (10) • Performance Max (14) • App (4)</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
