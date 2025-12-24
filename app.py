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


def check_domain_access(email: str) -> bool:
    """Check if user's email domain is allowed"""
    allowed_domains = st.secrets.get("auth", {}).get("allowed_domains", ["aristok.com"])
    allowed_emails = st.secrets.get("auth", {}).get("allowed_emails", [])
    
    if not email:
        return False
    
    # Check if email is explicitly allowed
    if email.lower() in [e.lower() for e in allowed_emails]:
        return True
    
    # Check domain
    try:
        domain = email.split('@')[-1].lower()
        return domain in [d.lower() for d in allowed_domains]
    except:
        return False


def show_login_page():
    """Display styled login page"""
    st.markdown("""
        <div style="text-align: center; padding: 50px 20px;">
            <h1 style="font-size: 3rem; font-weight: 700; background: linear-gradient(90deg, #1877F2, #4285f4, #34a853); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px;">
                🏥 HealthCard Platform
            </h1>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 40px; border: 1px solid rgba(255, 255, 255, 0.1);">
                <h2 style="text-align: center; margin-bottom: 30px;">Sign In</h2>
                <p style="text-align: center; color: #666; font-size: 0.9em; margin-bottom: 20px;">
                    Sign in with your corporate Google credentials.
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.button("🔐 Sign in with Google", on_click=st.login, width="stretch", type="primary")


def is_local_development() -> bool:
    """Check if running in local development mode"""
    try:
        # Check if the redirect_uri contains localhost
        redirect_uri = st.secrets.get("auth", {}).get("redirect_uri", "")
        return "localhost" in redirect_uri or "127.0.0.1" in redirect_uri
    except:
        return True  # Default to dev mode if secrets not loaded


def main():
    # Check if running in local development mode
    dev_mode = is_local_development()
    
    if dev_mode:
        # Skip auth for local development
        user_email = "dev@aristok.com"
        st.sidebar.info("🔧 Dev Mode: Auth bypassed")
    else:
        # Check if user is logged in using Streamlit's built-in auth
        if not st.user.is_logged_in:
            show_login_page()
            st.stop()
        
        # Check domain access
        user_email = st.user.get("email", "")
        if not check_domain_access(user_email):
            st.error(f"❌ Access denied for {user_email}")
            st.warning("Your email domain is not authorized to use this application.")
            st.button("🚪 Logout", on_click=st.logout)
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

    # Show user info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**👤 Logged in as:**")
    st.sidebar.caption(user_email)
    st.sidebar.button("🚪 Logout", on_click=st.logout, width="stretch")
    
    # AI Chatbot in main area (below platform content) - TEMPORARILY DISABLED
    # st.markdown("---")
    # from shared.chatbot import render_chatbot_expander
    # render_chatbot_expander()
    
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
