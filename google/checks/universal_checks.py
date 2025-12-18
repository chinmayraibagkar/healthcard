"""
Universal Health Checks - Applicable to all campaign types
Checks: 3, 12, 13
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Tuple
from services.google_ads_client import execute_query, get_active_campaigns
from config.constants import LIMITED_BUDGET_THRESHOLD, CHECK_DESCRIPTIONS


def check_limited_by_budget(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 3: Limited by Budget Campaigns
    Should be less than 10% of all active campaigns
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign.status,
            campaign_budget.has_recommended_budget,
            campaign_budget.recommended_budget_amount_micros,
            campaign_budget.amount_micros
        FROM campaign
        WHERE campaign.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No active campaigns found",
            "details": pd.DataFrame()
        }
    
    total_campaigns = len(rows)
    limited_campaigns = []
    
    for row in rows:
        if row.campaign_budget.has_recommended_budget:
            limited_campaigns.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "current_budget": row.campaign_budget.amount_micros / 1_000_000,
                "recommended_budget": row.campaign_budget.recommended_budget_amount_micros / 1_000_000 if row.campaign_budget.recommended_budget_amount_micros else None,
                "issue": "Limited by Budget"
            })
    
    limited_count = len(limited_campaigns)
    limited_percentage = limited_count / total_campaigns if total_campaigns > 0 else 0
    
    # INVERTED: Show percentage limited by budget (affected)
    score = limited_percentage * 100
    
    # Status: low percentage is good, high is bad
    status = "pass" if limited_percentage < LIMITED_BUDGET_THRESHOLD else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{limited_count}/{total_campaigns} campaigns ({limited_percentage*100:.1f}%) limited by budget",
        "threshold": f"< {LIMITED_BUDGET_THRESHOLD*100}%",
        "details": pd.DataFrame(limited_campaigns) if limited_campaigns else pd.DataFrame()
    }


def check_conversion_goal(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 12: Conversion Goal - Campaign Specific
    Conversion goal should be 'Campaign Specific' and not 'Account Default'
    Uses conversion_goal_campaign_config.goal_config_level to detect this setting.
    CAMPAIGN = Campaign-specific goals, CUSTOMER = Account default goals
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign.status,
            conversion_goal_campaign_config.goal_config_level
        FROM conversion_goal_campaign_config
        WHERE campaign.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info", 
            "score": None,
            "message": "No active campaigns found",
            "threshold": "All campaigns should have campaign-specific conversion goals (dropdown = 'Campaign-specific')",
            "details": pd.DataFrame()
        }
    
    campaigns_with_issues = []
    campaigns_with_specific = 0
    
    for row in rows:
        # Check if campaign has campaign-level goals (not customer/account level)
        goal_level = row.conversion_goal_campaign_config.goal_config_level.name if row.conversion_goal_campaign_config.goal_config_level else "UNKNOWN"
        
        if goal_level == "CAMPAIGN":
            campaigns_with_specific += 1
        else:
            campaigns_with_issues.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "goal_config_level": goal_level,
                "issue": "Using Account Default goals, should be Campaign-specific"
            })
    
    total = len(rows)
    # INVERTED: Show percentage of campaigns WITHOUT campaign-specific goals (affected)
    score = (len(campaigns_with_issues) / total * 100) if total > 0 else 0
    
    # Determine status (inverted: low score = good, high score = bad)
    status = "pass" if score == 0 else "warning" if score <= 20 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{len(campaigns_with_issues)}/{total} campaigns missing campaign-specific conversion goals",
        "threshold": "All campaigns should have 'Campaign-specific' in Conversion goals dropdown",
        "details": pd.DataFrame(campaigns_with_issues) if campaigns_with_issues else pd.DataFrame()
    }


def check_location_targeting(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 13: Location Targeting - Presence Only
    Location targeting should be 'PRESENCE' only, not 'PRESENCE_OR_INTEREST'
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.geo_target_type_setting.positive_geo_target_type,
            campaign.geo_target_type_setting.negative_geo_target_type
        FROM campaign
        WHERE campaign.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No active campaigns found",
            "details": pd.DataFrame()
        }
    
    campaigns_with_issues = []
    compliant_count = 0
    
    for row in rows:
        positive_type = row.campaign.geo_target_type_setting.positive_geo_target_type.name
        
        if positive_type == "PRESENCE":
            compliant_count += 1
        else:
            campaigns_with_issues.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "current_setting": positive_type,
                "issue": "Should be PRESENCE only"
            })
    
    total = len(rows)
    non_compliant_count = len(campaigns_with_issues)
    # INVERTED: Show percentage of campaigns with incorrect targeting (affected)
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    # Determine status (inverted: low score = good, high score = bad)
    status = "pass" if score == 0 else "warning" if score <= 25 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{non_compliant_count}/{total} campaigns have incorrect location targeting",
        "threshold": "All campaigns should use PRESENCE only",
        "details": pd.DataFrame(campaigns_with_issues) if campaigns_with_issues else pd.DataFrame()
    }


def run_all_universal_checks(client, customer_id: str) -> Dict[int, Dict[str, Any]]:
    """
    Run all universal checks and return results.
    """
    results = {}
    
    with st.spinner("Running Check 3: Limited by Budget..."):
        results[3] = check_limited_by_budget(client, customer_id)
        results[3]["name"] = CHECK_DESCRIPTIONS[3]
    
    with st.spinner("Running Check 12: Conversion Goal..."):
        results[12] = check_conversion_goal(client, customer_id)
        results[12]["name"] = CHECK_DESCRIPTIONS[12]
    
    with st.spinner("Running Check 13: Location Targeting..."):
        results[13] = check_location_targeting(client, customer_id)
        results[13]["name"] = CHECK_DESCRIPTIONS[13]
    
    return results
