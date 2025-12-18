"""
UI Components for the Health Card Dashboard
Theme-aware components that work with both dark and light mode
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from config.constants import STATUS_COLORS, CHECK_DESCRIPTIONS


def render_metric_card(check_num: int, result: Dict[str, Any]):
    """
    Render a single metric card for a health check with intelligent color-coded background.
    Color coding based on AFFECTED percentage:
    - Green: < 5% affected (excellent)
    - Yellow: 5-20% affected (good)
    - Amber: 20-50% affected (warning)
    - Red: > 50% affected (critical)
    """
    status = result.get("status", "info")
    score = result.get("score")
    message = result.get("message", "")
    name = result.get("name", CHECK_DESCRIPTIONS.get(check_num, f"Check {check_num}"))
    threshold = result.get("threshold", "")
    
    # Calculate affected percentage (inverse of score for most checks)
    # If score represents "good" percentage, affected = 100 - score
    # The score should represent affected percentage
    affected_pct = score if score is not None else 0
    
    # Intelligent color coding based on affected percentage
    if affected_pct < 5:
        # Excellent - very few issues (Affected < 5%)
        config = {
            "icon": "✅",
            "color": "#00C851",
            "emoji": "🟢",
            "bg_color": "rgba(0, 200, 81, 0.15)",
            "border_color": "#00C851",
            "status_text": "PASS"
        }
    elif affected_pct < 20:
        # Good - minor issues (Affected 5-20%)
        config = {
            "icon": "✓",
            "color": "#FDD835",  # Yellow
            "emoji": "🟡",
            "bg_color": "rgba(253, 216, 53, 0.15)",
            "border_color": "#FDD835",
            "status_text": "GOOD"
        }
    elif affected_pct < 50:
        # Warning - significant issues (Affected 20-50%)
        config = {
            "icon": "⚠️",
            "color": "#ffbb33",  # Amber
            "emoji": "🟠",
            "bg_color": "rgba(255, 187, 51, 0.15)",
            "border_color": "#ffbb33",
            "status_text": "WARNING"
        }
    else:
        # Critical - major issues (Affected > 50%)
        config = {
            "icon": "❌",
            "color": "#ff4444",  # Red
            "emoji": "🔴",
            "bg_color": "rgba(255, 68, 68, 0.15)",
            "border_color": "#ff4444",
            "status_text": "FAIL"
        }
    
    # Score display - Show as "Affected"
    score_display = f"{affected_pct:.0f}% Affected" if score is not None else "N/A"
    
    # Create colored container with border (removed empty div)
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
                        {config['icon']} {name}
                    </div>
                    <div style="color: {config['color']}; font-size: 0.8em; font-weight: bold;">
                        {score_display}
                    </div>
                </div>
        """, unsafe_allow_html=True)
        
        # Show threshold as the criterion/requirement
        if threshold:
            st.caption(f"📋 {threshold}")
        
        # Compact visual progress bar showing affected percentage
        if score is not None:
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
                        width: {min(affected_pct, 100)}%;
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
    
    return config


def render_detail_expander(check_num: int, result: Dict[str, Any]):
    """
    Render an expander with detailed information and download button.
    """
    status = result.get("status", "info")
    details = result.get("details", pd.DataFrame())
    issues = result.get("issues", pd.DataFrame())
    name = result.get("name", CHECK_DESCRIPTIONS.get(check_num, f"Check {check_num}"))
    
    if status not in ["fail", "warning"] and (details.empty if isinstance(details, pd.DataFrame) else not details):
        return
    
    with st.expander(f"📋 Details: {name}", expanded=False):
        threshold = result.get("threshold", "")
        if threshold:
            st.info(f"**Threshold:** {threshold}")
        
        # Show summary details
        if isinstance(details, pd.DataFrame) and not details.empty:
            st.dataframe(details, use_container_width=True, hide_index=True)
            
            # Download button
            csv = details.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"check_{check_num}_details.csv",
                mime="text/csv",
                key=f"download_check_{check_num}"
            )
        
        # Show issues if available
        if isinstance(issues, pd.DataFrame) and not issues.empty:
            st.subheader("Issues Found")
            st.dataframe(issues, use_container_width=True, hide_index=True)
            
            csv_issues = issues.to_csv(index=False)
            st.download_button(
                label="⬇️ Download Issues CSV",
                data=csv_issues,
                file_name=f"check_{check_num}_issues.csv",
                mime="text/csv",
                key=f"download_check_{check_num}_issues"
            )


def render_check_grid(results: Dict[int, Dict[str, Any]], columns: int = 3):
    """
    Render a grid of check cards.
    """
    check_nums = sorted(results.keys())
    
    # Create rows of cards
    for i in range(0, len(check_nums), columns):
        cols = st.columns(columns)
        for j, col in enumerate(cols):
            if i + j < len(check_nums):
                check_num = check_nums[i + j]
                with col:
                    render_metric_card(check_num, results[check_num])
    
    # Render expanders for failed checks
    st.markdown("---")
    failed_checks = [num for num, res in results.items() if res.get("status") in ["fail", "warning"]]
    
    if failed_checks:
        st.subheader("📊 Details for Non-Compliant Checks")
        for check_num in sorted(failed_checks):
            render_detail_expander(check_num, results[check_num])


def render_summary_stats(results: Dict[int, Dict[str, Any]]):
    """
    Render summary statistics at the top using native Streamlit metrics.
    """
    total = len(results)
    passed = sum(1 for r in results.values() if r.get("status") == "pass")
    failed = sum(1 for r in results.values() if r.get("status") == "fail")
    warnings = sum(1 for r in results.values() if r.get("status") == "warning")
    info = total - passed - failed - warnings
    
    # Overall score (Inverted from Agreggated Affected Score)
    # Individual checks return "Affected %" (0 is Good)
    # Overall score should be "Positive %" (100 is Good)
    scores = [r.get("score", 0) for r in results.values() if r.get("score") is not None]
    avg_affected = sum(scores) / len(scores) if scores else 0
    overall_positive_score = max(0, 100 - avg_affected)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Overall Health", f"{overall_positive_score:.0f}%")
    with col2:
        st.metric("✅ Passed", passed)
    with col3:
        st.metric("❌ Failed", failed)
    with col4:
        st.metric("⚠️ Warnings", warnings)
    with col5:
        st.metric("ℹ️ Info", info)


def render_sidebar_account_selector(accounts_df: pd.DataFrame):
    """
    Render the account selector in the sidebar.
    """
    st.sidebar.header("🎯 Account Selection")
    
    if accounts_df.empty:
        st.sidebar.warning("No accounts found")
        return None
    
    # Create display names - handle potential missing columns
    if 'descriptive_name' in accounts_df.columns and 'customer_id' in accounts_df.columns:
        accounts_df = accounts_df.copy()
        accounts_df["display_name"] = accounts_df.apply(
            lambda x: f"{x['descriptive_name']} ({x['customer_id']})",
            axis=1
        )
    else:
        st.sidebar.error("Invalid accounts data format")
        return None
    
    selected = st.sidebar.selectbox(
        "Select Account",
        options=accounts_df["display_name"].tolist(),
        key="account_selector"
    )
    
    if selected:
        selected_row = accounts_df[accounts_df["display_name"] == selected].iloc[0]
        st.sidebar.success(f"**Customer ID:** {selected_row['customer_id']}")
        return selected_row["customer_id"]
    
    return None


def render_download_all_button(all_results: Dict[str, Dict[int, Dict[str, Any]]]):
    """
    Render a button to download all check results as an Excel file.
    """
    st.sidebar.markdown("---")
    st.sidebar.subheader("📥 Export Results")
    
    if st.sidebar.button("📥 Download All Results", key="download_all", type="primary"):
        import io
        
        # Create Excel file with multiple sheets
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for tab_name, results in all_results.items():
                # Create summary sheet
                summary_data = []
                for check_num, result in results.items():
                    summary_data.append({
                        "Check #": check_num,
                        "Name": result.get("name", ""),
                        "Status": result.get("status", ""),
                        "Score": result.get("score", ""),
                        "Message": result.get("message", "")
                    })
                
                if summary_data:
                    pd.DataFrame(summary_data).to_excel(
                        writer, 
                        sheet_name=f"{tab_name[:20]}_Summary",
                        index=False
                    )
        
        output.seek(0)
        st.sidebar.download_button(
            label="⬇️ Download Excel",
            data=output.getvalue(),
            file_name="google_ads_healthcard_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
