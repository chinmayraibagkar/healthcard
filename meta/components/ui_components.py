"""
UI Components for Meta HealthCard Dashboard
Theme-aware components that work with both dark and light mode
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Any


def render_check_card(result: Dict[str, Any]):
    """
    Render a single health check card with Google-like UI style.
    """
    status = result.get('status', 'INFO')
    check_name = result.get('check_name', 'Unknown Check')
    message = result.get('message', '')
    threshold = result.get('threshold', '')
    recommendation = result.get('recommendation', '')
    percentage = result.get('percentage', 0)
    
    # Status configuration matching Google's style
    if status == 'PASS':
        config = {
            "icon": "✅",
            "color": "#00C851",
            "emoji": "🟢",
            "bg_color": "rgba(0, 200, 81, 0.15)",
            "border_color": "#00C851",
            "status_text": "PASS"
        }
    elif status == 'WARNING':
        config = {
            "icon": "⚠️",
            "color": "#ffbb33",
            "emoji": "🟠",
            "bg_color": "rgba(255, 187, 51, 0.15)",
            "border_color": "#ffbb33",
            "status_text": "WARNING"
        }
    elif status == 'FAIL':
        config = {
            "icon": "❌",
            "color": "#ff4444",
            "emoji": "🔴",
            "bg_color": "rgba(255, 68, 68, 0.15)",
            "border_color": "#ff4444",
            "status_text": "FAIL"
        }
    else:
        config = {
            "icon": "ℹ️",
            "color": "#33b5e5",
            "emoji": "🔵",
            "bg_color": "rgba(51, 181, 229, 0.15)",
            "border_color": "#33b5e5",
            "status_text": "INFO"
        }
    
    # Score display
    score_display = f"{percentage:.0f}% Affected" if percentage is not None else "N/A"
    
    # Create colored container with border
    with st.container(border=True):
        # Add colored background and left border using CSS
        st.markdown(f"""
            <div style="
                background: {config['bg_color']};
                border-left: 4px solid {config['border_color']};
                border-radius: 4px;
                padding: 12px;
                margin: -16px;
                margin-bottom: 0px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="font-weight: 600; font-size: 0.95rem;">
                        {config['icon']} {check_name}
                    </div>
                    <div style="color: {config['color']}; font-size: 0.8em; font-weight: bold;">
                        {score_display}
                    </div>
                </div>
        """, unsafe_allow_html=True)
        
        # Show threshold
        if threshold:
            st.caption(f"📋 {threshold}")
        
        # Compact visual progress bar showing affected percentage
        if percentage is not None:
            st.markdown(f"""
                <div style="
                    width: 100%;
                    height: 6px;
                    background: rgba(128, 128, 128, 0.2);
                    border-radius: 3px;
                    margin: 8px 0;
                    overflow: hidden;
                ">
                    <div style="
                        width: {min(percentage, 100)}%;
                        height: 100%;
                        background: {config['color']};
                        border-radius: 3px;
                        transition: width 0.3s ease;
                    "></div>
                </div>
            """, unsafe_allow_html=True)
        
        # Message with status indicator
        st.markdown(f"""
            <div style='color: {config['color']}; font-size: 0.9em; margin-top: 4px; margin-bottom: 8px;'>
                {config['emoji']} {message}
            </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Recommendation in expander
        if recommendation and status in ['FAIL', 'WARNING']:
            with st.expander("💡 Recommendation"):
                st.write(recommendation)


def render_check_grid(results: List[Dict[str, Any]], columns: int = 3):
    """
    Render a grid of health check cards.
    
    Args:
        results: List of check result dictionaries
        columns: Number of columns in the grid
    """
    if not results:
        st.info("No checks to display")
        return
    
    # Create grid
    for i in range(0, len(results), columns):
        cols = st.columns(columns)
        for j, col in enumerate(cols):
            if i + j < len(results):
                with col:
                    render_check_card(results[i + j])
    
    # Show details for failed/warning checks
    st.markdown("---")
    failed_checks = [r for r in results if r.get('status') in ['FAIL', 'WARNING'] and r.get('details')]
    
    if failed_checks:
        st.subheader("📊 Detailed Analysis")
        for result in failed_checks:
            render_detail_expander(result)
    else:
        st.success("🎉 All checks passed!")


def render_detail_expander(result: Dict[str, Any]):
    """
    Render an expander with detailed check information.
    
    Args:
        result: Check result dictionary
    """
    check_name = result.get('check_name', 'Check Details')
    details = result.get('details')
    
    if not details:
        return
    
    with st.expander(f"📋 {check_name} - Details", expanded=False):
        if isinstance(details, list) and len(details) > 0:
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(details)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"{check_name.lower().replace(' ', '_')}_details.csv",
                mime="text/csv",
                key=f"download_{check_name.replace(' ', '_')}"
            )
        elif isinstance(details, dict):
            # Display key-value pairs
            for key, value in details.items():
                st.write(f"**{key}:** {value}")
        else:
            st.write(details)


def render_summary_stats(results: List[Dict[str, Any]]):
    """
    Render summary statistics for all checks.
    
    Args:
        results: List of check result dictionaries
    """
    if not results:
        return
    
    total = len(results)
    passed = sum(1 for r in results if r.get('status') == 'PASS')
    failed = sum(1 for r in results if r.get('status') == 'FAIL')
    warnings = sum(1 for r in results if r.get('status') == 'WARNING')
    info = sum(1 for r in results if r.get('status') == 'INFO')
    
    # Calculate overall health score
    score_map = {'PASS': 100, 'WARNING': 50, 'FAIL': 0, 'INFO': 100}
    scores = [score_map.get(r.get('status'), 0) for r in results if r.get('status') != 'INFO']
    avg_score = sum(scores) / len(scores) if scores else 100
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Health Score", f"{avg_score:.0f}%")
    with col2:
        st.metric("✅ Passed", passed)
    with col3:
        st.metric("❌ Failed", failed)
    with col4:
        st.metric("⚠️ Warnings", warnings)
    with col5:
        st.metric("ℹ️ Info", info)


def render_sidebar_account_selector(accounts: List[Dict[str, Any]]):
    """
    Render account selector in the sidebar.
    
    Args:
        accounts: List of account dictionaries
    
    Returns:
        Selected account ID or None
    """
    st.sidebar.header("🎯 Account Selection")
    
    if not accounts:
        st.sidebar.warning("No accounts found")
        return None
    
    # Create display options
    account_options = {
        f"{acc['account_name']} ({acc['account_id']})": acc['account_id']
        for acc in accounts
    }
    
    selected_display = st.sidebar.selectbox(
        "Select Ad Account",
        options=list(account_options.keys()),
        key="meta_account_selector"
    )
    
    if selected_display:
        selected_id = account_options[selected_display]
        st.sidebar.success(f"**Account ID:** {selected_id}")
        return selected_id
    
    return None


def render_download_button(results: List[Dict[str, Any]], filename: str = "meta_healthcard_report"):
    """
    Render download button for check results.
    
    Args:
        results: List of check result dictionaries
        filename: Base filename for download
    """
    st.sidebar.markdown("---")

    st.sidebar.subheader("📥 Export Results")
    
    if not results:
        st.sidebar.info("No results to export")
        return
    
    # Create summary DataFrame
    summary_data = []
    for result in results:
        summary_data.append({
            'Check Name': result.get('check_name', ''),
            'Status': result.get('status', ''),
            'Message': result.get('message', ''),
            'Count': result.get('count', ''),
            'Total': result.get('total', ''),
            'Percentage': result.get('percentage', ''),
            'Threshold': result.get('threshold', ''),
            'Recommendation': result.get('recommendation', '')
        })
    
    df = pd.DataFrame(summary_data)
    
    # CSV download
    csv = df.to_csv(index=False)
    st.sidebar.download_button(
        label="⬇️ Download CSV Report",
        data=csv,
        file_name=f"{filename}.csv",
        mime="text/csv",
        key="download_meta_csv"
    )
    
    # Excel download
    try:
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Add detail sheets for checks with details
            for result in results:
                if result.get('details') and isinstance(result.get('details'), list):
                    check_name = result['check_name'][:30].replace(' ', '_')
                    detail_df = pd.DataFrame(result['details'])
                    detail_df.to_excel(writer, sheet_name=check_name, index=False)
        
        output.seek(0)
        st.sidebar.download_button(
            label="⬇️ Download Excel Report",
            data=output.getvalue(),
            file_name=f"{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_meta_excel"
        )
    except Exception as e:
        st.sidebar.error(f"Excel export error: {e}")


def render_platform_badge(platform: str):
    """
    Render a styled platform badge with theme-aware visibility.
    
    Args:
        platform: Platform name ('meta' or 'google')
    """
    if platform.lower() == 'meta':
        st.markdown(
            """
            <div style="text-align: center; padding: 15px; 
                        background: linear-gradient(135deg, #0668E1 0%, #1877F2 100%); 
                        border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <h2 style="color: white; margin: 0; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);">
                    📘 Meta Ads HealthCard
                </h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif platform.lower() == 'google':
        st.markdown(
            """
            <div style="text-align: center; padding: 15px; 
                        background: linear-gradient(135deg, #4285f4 0%, #34a853 50%, #fbbc05 75%, #ea4335 100%); 
                        border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                <h2 style="color:  white; margin: 0; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);">
                    🔍 Google Ads HealthCard
                </h2>
            </div>
            """,
            unsafe_allow_html=True
        )
