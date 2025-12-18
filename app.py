"""
Unified HealthCard Platform
Comprehensive health audit dashboard for Meta Ads and Google Ads

Switch between platforms to run health checks and monitor ad account performance.
"""

import streamlit as st
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Page configuration
st.set_page_config(
    page_title="HealthCard Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for platform switcher and dark theme compatibility
st.markdown("""
<style>
    /* Main headers - works in both themes */
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1877F2, #4285f4, #34a853);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    /* Sub header with theme awareness */
    .sub-header {
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2rem;
        color: var(--text-color);
    }
    
    /* Platform badges with better contrast */
    .platform-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        margin: 5px;
        cursor: pointer;
    }
    
    .meta-badge {
        background: linear-gradient(90deg, #0668E1, #1877F2);
        color: white;
    }
    
    .google-badge {
        background: linear-gradient(90deg, #4285f4, #34a453);
        color: white;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
    }
    
    /* Better visibility for dark theme */
    [data-theme="dark"] .sub-header {
        opacity: 0.85;
    }
    
    [data-theme="light"] .sub-header {
        opacity: 0.7;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'selected_platform' not in st.session_state:
    st.session_state.selected_platform = 'meta'


def main():
    # Initialize authentication
    from auth.authenticator import Authenticator
    auth = Authenticator()
    
    # Check authentication
    if not auth.is_authenticated():
        auth.show_login_page()
        st.stop()
    
    # Header
    st.markdown('<h1 class="main-header">🏥 HealthCard Platform</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Comprehensive Advertising Health Audit Dashboard</p>', unsafe_allow_html=True)
    
    # Platform selector in sidebar
    st.sidebar.title("🚀 Platform Selection")
    
    platform_options = {
        "📘 Meta Ads": "meta",
        "🔍 Google Ads": "google"
    }
    
    selected_display = st.sidebar.radio(
        "Select Advertising Platform",
        options=list(platform_options.keys()),
        index=0 if st.session_state.selected_platform == 'meta' else 1,
        key="platform_radio"
    )
    
    st.session_state.selected_platform = platform_options[selected_display]
    
    # # Platform description with better theme compatibility
    # if st.session_state.selected_platform == 'meta':
    #     st.sidebar.info(
    #         """
    #         **Meta Ads HealthCard**
            
    #         Comprehensive audit for Facebook & Instagram ads:
    #         - 🎯 Tracking validation
    #         - 🎨 Creative analysis
    #         - 📱 Ad format distribution
    #         - 👥 Audience targeting
    #         """
    #     )
    # else:
    #     st.sidebar.info(
    #         """
    #         **Google Ads HealthCard**
            
    #         31 health checks across:
    #         - 🌐 Universal (3 checks)
    #         - 🔍 Search (10 checks)
    #         - 🚀 Performance Max (14 checks)
    #         - 📱 App Campaigns (4 checks)
    #         """
    #     )
    
    st.sidebar.markdown("---")
    
    # Route to appropriate platform
    if st.session_state.selected_platform == 'meta':
        from meta.app import run_meta_healthcard
        run_meta_healthcard()
    
    elif st.session_state.selected_platform == 'google':
        # Import Google app module - avoid conflict with built-in google package
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "google_app",
            os.path.join(os.path.dirname(__file__), "google", "app.py")
        )
        google_app = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(google_app)
        
        # Run Google healthcard
        st.markdown("### Google Ads HealthCard")
        st.caption("Comprehensive health audit for your Google Ads campaigns")
        google_app.main()

    # Show user info
    auth.show_user_info()
    
    # # Footer
    # st.markdown("---")
    # st.markdown(
    #     """
    #     <div style="text-align: center; color: #999; font-size: 0.85rem; padding: 20px;">
    #         <p><strong>HealthCard Platform v1.0</strong></p>
    #         <p>Unified advertising health monitoring for Meta & Google Ads</p>
    #         <p>Built with ❤️ using Streamlit</p>
    #     </div>
    #     """,
    #     unsafe_allow_html=True
    # )


if __name__ == "__main__":
    main()
