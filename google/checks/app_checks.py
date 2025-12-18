"""
App Campaign Health Checks
Checks: 28, 29, 30, 31
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from collections import defaultdict
from services.google_ads_client import execute_query
from config.constants import APP_MIN_HEADLINES, APP_MIN_DESCRIPTIONS, CHECK_DESCRIPTIONS


def check_single_in_app_action(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 28: Single In-App Action Optimization
    Campaign should be optimized on single in-app-action event.
    Uses app_campaign_setting.bidding_strategy_goal_type to identify optimization goal.
    OPTIMIZE_IN_APP_CONVERSIONS_TARGET_CONVERSION_COST = optimizing for in-app actions
    """
    # Query for App campaigns with their bidding strategy goal
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign.app_campaign_setting.app_id,
            campaign.app_campaign_setting.app_store,
            campaign.app_campaign_setting.bidding_strategy_goal_type
        FROM campaign
        WHERE campaign.advertising_channel_sub_type IN ('APP_CAMPAIGN', 'APP_CAMPAIGN_FOR_ENGAGEMENT')
        AND campaign.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No active App campaigns found",
            "threshold": "App campaigns should be optimized on single in-app action event",
            "details": pd.DataFrame()
        }
    
    compliant = 0
    issues = []
    
    for row in rows:
        goal_type = row.campaign.app_campaign_setting.bidding_strategy_goal_type.name if row.campaign.app_campaign_setting.bidding_strategy_goal_type else "UNKNOWN"
        app_id = row.campaign.app_campaign_setting.app_id or "N/A"
        
        # Check if optimizing for in-app conversions (single action)
        # Valid values: OPTIMIZE_IN_APP_CONVERSIONS_TARGET_CONVERSION_COST, OPTIMIZE_IN_APP_CONVERSIONS_TARGET_INSTALL_COST
        if goal_type in ["OPTIMIZE_IN_APP_CONVERSIONS_TARGET_CONVERSION_COST", "OPTIMIZE_IN_APP_CONVERSIONS_TARGET_INSTALL_COST", "OPTIMIZE_RETURN_ON_ADVERTISING_SPEND"]:
            compliant += 1
        else:
            issues.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "app_id": app_id,
                "bidding_goal": goal_type,
                "issue": f"Goal type is '{goal_type}' - not optimizing for in-app action"
            })
    
    total = len(rows)
    non_compliant_count = len(issues)
    # INVERTED: Show percentage of App campaigns NOT optimized on in-app action
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 50 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} App campaigns optimized on in-app action",
        "threshold": "Campaign bidding_strategy_goal_type should be set to in-app conversion optimization",
        "details": pd.DataFrame(issues) if issues else pd.DataFrame()
    }


def check_deferred_deep_linking(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 29: Deferred Deep Linking (DDL)
    Should have in at least some campaigns, not necessary for all
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign.app_campaign_setting.app_id,
            campaign.app_campaign_setting.app_store
        FROM campaign
        WHERE campaign.advertising_channel_type = 'MULTI_CHANNEL'
        AND campaign.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No active App campaigns found",
            "details": pd.DataFrame()
        }
    
    # DDL is typically configured at the app level, not campaign level
    # This is a simplified check - full implementation would need app configuration data
    campaigns_list = []
    for row in rows:
        campaigns_list.append({
            "campaign_id": str(row.campaign.id),
            "campaign_name": row.campaign.name,
            "app_id": row.campaign.app_campaign_setting.app_id,
            "app_store": row.campaign.app_campaign_setting.app_store.name if row.campaign.app_campaign_setting.app_store else "Unknown"
        })
    
    return {
        "status": "info",
        "score": None,
        "message": f"Found {len(rows)} App campaigns - DDL check requires manual verification",
        "threshold": "At least some campaigns should have DDL",
        "details": pd.DataFrame(campaigns_list) if campaigns_list else pd.DataFrame([{
            "Note": "Deferred Deep Linking requires manual verification in app configuration"
        }])
    }


def check_custom_store_listing(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 30: Custom Store Listing
    At least one campaign should have custom store listing implemented
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign.app_campaign_setting.app_id,
            campaign.app_campaign_setting.app_store
        FROM campaign
        WHERE campaign.advertising_channel_type = 'MULTI_CHANNEL'
        AND campaign.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No active App campaigns found",
            "details": pd.DataFrame()
        }
    
    # Custom store listing is configured at the Play Store/App Store level
    # This requires manual verification
    campaigns_list = []
    for row in rows:
        campaigns_list.append({
            "campaign_id": str(row.campaign.id),
            "campaign_name": row.campaign.name,
            "app_id": row.campaign.app_campaign_setting.app_id,
            "app_store": row.campaign.app_campaign_setting.app_store.name if row.campaign.app_campaign_setting.app_store else "Unknown"
        })
    
    return {
        "status": "info",
        "score": None,
        "message": f"Found {len(rows)} App campaigns - Custom Store Listing requires manual verification",
        "threshold": "At least one campaign should have custom store listing",
        "details": pd.DataFrame(campaigns_list) if campaigns_list else pd.DataFrame([{
            "Note": "Custom Store Listing configuration requires manual verification in Play Store/App Store"
        }])
    }


def check_app_asset_counts(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 31: Headlines and Descriptions count (>=5 each)
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_ad.ad.id,
            ad_group_ad.ad.app_ad.headlines,
            ad_group_ad.ad.app_ad.descriptions
        FROM ad_group_ad
        WHERE campaign.advertising_channel_type = 'MULTI_CHANNEL'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_ad.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No active App campaign ads found",
            "details": pd.DataFrame()
        }
    
    issues = []
    compliant = 0
    
    for row in rows:
        headlines = row.ad_group_ad.ad.app_ad.headlines or []
        descriptions = row.ad_group_ad.ad.app_ad.descriptions or []
        
        headline_count = len(headlines)
        description_count = len(descriptions)
        
        ad_issues = []
        if headline_count < APP_MIN_HEADLINES:
            ad_issues.append(f"Headlines: {headline_count} (min {APP_MIN_HEADLINES})")
        if description_count < APP_MIN_DESCRIPTIONS:
            ad_issues.append(f"Descriptions: {description_count} (min {APP_MIN_DESCRIPTIONS})")
        
        if ad_issues:
            issues.append({
                "campaign_name": row.campaign.name,
                "ad_group_name": row.ad_group.name,
                "ad_id": str(row.ad_group_ad.ad.id),
                "headlines": headline_count,
                "descriptions": description_count,
                "issue": "; ".join(ad_issues)
            })
        else:
            compliant += 1
    
    total = len(rows)
    non_compliant_count = len(issues)
    # INVERTED: Show percentage of App ads with MISSING assets
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 10 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} App ads meet asset requirements",
        "threshold": f"Min: {APP_MIN_HEADLINES} headlines, {APP_MIN_DESCRIPTIONS} descriptions",
        "details": pd.DataFrame(issues) if issues else pd.DataFrame()
    }


def run_all_app_checks(client, customer_id: str) -> Dict[int, Dict[str, Any]]:
    """
    Run all App campaign checks and return results.
    """
    results = {}
    
    checks = [
        (28, "Single In-App Action", check_single_in_app_action),
        # (29, "Deferred Deep Linking", check_deferred_deep_linking),  # Requires manual verification
        # (30, "Custom Store Listing", check_custom_store_listing),  # Requires manual verification
        (31, "Asset Counts", check_app_asset_counts)
    ]
    
    for check_num, check_name, check_func in checks:
        with st.spinner(f"Running Check {check_num}: {check_name}..."):
            try:
                results[check_num] = check_func(client, customer_id)
                results[check_num]["name"] = CHECK_DESCRIPTIONS[check_num]
            except Exception as e:
                results[check_num] = {
                    "status": "error",
                    "score": None,
                    "message": f"Error: {str(e)}",
                    "name": CHECK_DESCRIPTIONS[check_num],
                    "details": pd.DataFrame()
                }
    
    return results
