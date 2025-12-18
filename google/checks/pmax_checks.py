"""
Performance Max Campaign Health Checks
Checks: 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from collections import defaultdict
from services.google_ads_client import execute_query
from config.constants import (
    PMAX_MIN_HEADLINES, PMAX_MAX_HEADLINES,
    PMAX_MIN_LONG_HEADLINES, PMAX_MIN_DESCRIPTIONS,
    PMAX_MIN_SITELINKS, PMAX_MIN_IMAGES, PMAX_MIN_VIDEOS,
    PMAX_SPEND_SPLIT, PMAX_SPEND_TOLERANCE, CHECK_DESCRIPTIONS
)



def check_age_exclusions(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 14: Age Exclusions at campaign level
    """
    # Get PMax campaigns
    campaigns_query = """
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
    """
    campaigns = execute_query(client, customer_id, campaigns_query)
    
    if not campaigns:
        return {
            "status": "info",
            "score": None,
            "message": "No active Performance Max campaigns found",
            "details": pd.DataFrame()
        }
    
    # Check for age exclusions
    exclusions_query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign_criterion.criterion_id,
            campaign_criterion.age_range.type,
            campaign_criterion.negative,
            campaign_criterion.status,
            campaign.status,
            campaign.advertising_channel_type
        FROM campaign_criterion
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND campaign_criterion.type = 'AGE_RANGE'
        AND campaign_criterion.negative = true
    """
    
    exclusions = execute_query(client, customer_id, exclusions_query)
    
    campaigns_with_exclusions = set()
    for row in exclusions:
        campaigns_with_exclusions.add(str(row.campaign.id))
    
    campaigns_without = []
    for row in campaigns:
        campaign_id = str(row.campaign.id)
        if campaign_id not in campaigns_with_exclusions:
            campaigns_without.append({
                "campaign_id": campaign_id,
                "campaign_name": row.campaign.name,
                "issue": "No age exclusions set"
            })
    
    total = len(campaigns)
    non_compliant_count = len(campaigns_without)
    # INVERTED: Show percentage of campaigns MISSING age exclusions
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 20 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} PMax campaigns have age exclusions",
        "threshold": "All PMax campaigns should have age exclusions",
        "details": pd.DataFrame(campaigns_without) if campaigns_without else pd.DataFrame()
    }



def check_brand_exclusions(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 15: Brand Exclusions at campaign level
    Check if campaigns have brand suitability or negative keyword lists attached
    """
    # Get PMax campaigns
    campaigns_query = """
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
    """
    campaigns = execute_query(client, customer_id, campaigns_query)
    
    if not campaigns:
        return {
            "status": "info",
            "score": None,
            "message": "No active Performance Max campaigns found",
            "threshold": "PMax campaigns should have brand exclusions configured",
            "details": pd.DataFrame()
        }
    
    # Check for brand exclusions via shared negative keyword sets
    brand_exclusions_query = """
        SELECT 
            campaign.id,
            campaign.name,
            shared_set.name,
            shared_set.type,
            campaign.status,
            campaign.advertising_channel_type
        FROM campaign_shared_set
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND shared_set.type = 'NEGATIVE_KEYWORDS'
    """
    
    exclusions = execute_query(client, customer_id, brand_exclusions_query)
    campaigns_with_exclusions = set(str(row.campaign.id) for row in exclusions)
    
    campaigns_without = []
    for row in campaigns:
        campaign_id = str(row.campaign.id)
        if campaign_id not in campaigns_with_exclusions:
            campaigns_without.append({
                "campaign_id": campaign_id,
                "campaign_name": row.campaign.name,
                "issue": "No negative keyword list attached"
            })
    
    total = len(campaigns)
    non_compliant_count = len(campaigns_without)
    # INVERTED: Show percentage of campaigns MISSING brand lists
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 20 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} PMax campaigns have brand exclusions",
        "threshold": "All PMax campaigns should have negative keyword lists for brand exclusions",
        "details": pd.DataFrame(campaigns_without) if campaigns_without else pd.DataFrame()
    }



def check_auto_asset_optimization(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 16: Auto Asset Optimization should be OFF
    Note: This requires manual verification as the API fields for auto-asset optimization
    settings are not directly queryable in the current API version.
    """
    # Get PMax campaigns
    campaigns_query = """
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
    """
    campaigns = execute_query(client, customer_id, campaigns_query)
    
    if not campaigns:
        return {
            "status": "info",
            "score": None,
            "message": "No active Performance Max campaigns found",
            "threshold": "Auto asset optimization should be turned OFF",
            "details": pd.DataFrame()
        }
    
    # List campaigns for manual verification
    campaigns_list = []
    for row in campaigns:
        campaigns_list.append({
            "campaign_id": str(row.campaign.id),
            "campaign_name": row.campaign.name,
            "note": "Requires manual verification in Google Ads UI"
        })
    
    return {
        "status": "info",
        "score": None,
        "message": f"Found {len(campaigns)} PMax campaigns - Auto-asset settings require manual verification",
        "threshold": "Auto asset optimization should be turned OFF (check in Google Ads UI > Campaign Settings)",
        "details": pd.DataFrame(campaigns_list)
    }



def check_search_themes(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 17: Search Themes in Asset Groups
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            asset_group.id,
            asset_group.name,
            asset_group.status,
            campaign.status
        FROM asset_group
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset_group.status = 'ENABLED'
    """
    
    asset_groups = execute_query(client, customer_id, query)
    
    if not asset_groups:
        return {
            "status": "info",
            "score": None,
            "message": "No active asset groups found",
            "details": pd.DataFrame()
        }
    
    # Check for search themes via asset_group_signal
    signals_query = """
        SELECT 
            asset_group.id,
            asset_group.name,
            campaign.name,
            asset_group_signal.search_theme.text,
            campaign.status,
            asset_group.status,
            campaign.advertising_channel_type
        FROM asset_group_signal
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset_group.status = 'ENABLED'
    """
    
    signals = execute_query(client, customer_id, signals_query)
    asset_groups_with_themes = set(str(row.asset_group.id) for row in signals if row.asset_group_signal.search_theme.text)
    
    asset_groups_without = []
    for row in asset_groups:
        if str(row.asset_group.id) not in asset_groups_with_themes:
            asset_groups_without.append({
                "campaign_name": row.campaign.name,
                "asset_group_id": str(row.asset_group.id),
                "asset_group_name": row.asset_group.name,
                "issue": "No search themes configured"
            })
    
    total = len(asset_groups)
    non_compliant_count = len(asset_groups_without)
    # INVERTED: Show percentage of asset groups MISSING search themes
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 10 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} asset groups have search themes",
        "threshold": "All asset groups should have search themes",
        "details": pd.DataFrame(asset_groups_without) if asset_groups_without else pd.DataFrame()
    }



def check_search_term_negation(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 18: Search Term Negation at campaign level
    Checks for negative keywords attached directly to campaign or via shared sets
    """
    campaigns_query = """
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
    """
    campaigns = execute_query(client, customer_id, campaigns_query)
    
    if not campaigns:
        return {
            "status": "info",
            "score": None,
            "message": "No active Performance Max campaigns found",
            "threshold": "All PMax campaigns should have negative keywords",
            "details": pd.DataFrame()
        }
    
    # Check for negative keywords via shared sets
    shared_negatives_query = """
        SELECT 
            campaign.id,
            campaign.name,
            shared_set.name,
            shared_set.type,
            campaign.status,
            campaign.advertising_channel_type
        FROM campaign_shared_set
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND shared_set.type = 'NEGATIVE_KEYWORDS'
    """
    shared_negatives = execute_query(client, customer_id, shared_negatives_query)
    campaigns_with_shared_negatives = set(str(row.campaign.id) for row in shared_negatives)
    
    # Check for direct campaign-level negative keywords
    direct_negatives_query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign_criterion.keyword.text,
            campaign_criterion.negative,
            campaign.status,
            campaign.advertising_channel_type
        FROM campaign_criterion
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND campaign_criterion.negative = true
    """
    direct_negatives = execute_query(client, customer_id, direct_negatives_query)
    campaigns_with_direct_negatives = set(str(row.campaign.id) for row in direct_negatives)
    
    # Combine both sources
    campaigns_with_negatives = campaigns_with_shared_negatives | campaigns_with_direct_negatives
    
    campaigns_without = []
    for row in campaigns:
        if str(row.campaign.id) not in campaigns_with_negatives:
            campaigns_without.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "issue": "No negative keywords (neither direct nor via shared set)"
            })
    
    total = len(campaigns)
    non_compliant_count = len(campaigns_without)
    # INVERTED: Show percentage of campaigns MISSING negative keywords
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 20 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} PMax campaigns have negative keywords",
        "threshold": "All PMax campaigns should have negative keywords (direct or via shared set)",
        "details": pd.DataFrame(campaigns_without) if campaigns_without else pd.DataFrame()
    }



def check_asset_counts(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 19: Headlines, Long Headlines, Descriptions count
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            asset_group.id,
            asset_group.name,
            asset_group_asset.field_type,
            asset.id,
            asset.name,
            asset_group_asset.status,
            campaign.status,
            asset_group.status,
            campaign.advertising_channel_type
        FROM asset_group_asset
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset_group.status = 'ENABLED'
        AND asset_group_asset.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No asset group assets found",
            "details": pd.DataFrame()
        }
    
    # Count assets by type per asset group
    asset_group_counts = defaultdict(lambda: {
        "campaign_name": "",
        "asset_group_name": "",
        "HEADLINE": 0,
        "LONG_HEADLINE": 0,
        "DESCRIPTION": 0
    })
    
    for row in rows:
        key = str(row.asset_group.id)
        field_type = row.asset_group_asset.field_type.name
        asset_group_counts[key]["campaign_name"] = row.campaign.name
        asset_group_counts[key]["asset_group_name"] = row.asset_group.name
        asset_group_counts[key]["asset_group_id"] = key
        
        if field_type == "HEADLINE":
            asset_group_counts[key]["HEADLINE"] += 1
        elif field_type == "LONG_HEADLINE":
            asset_group_counts[key]["LONG_HEADLINE"] += 1
        elif field_type == "DESCRIPTION":
            asset_group_counts[key]["DESCRIPTION"] += 1
    
    issues = []
    compliant = 0
    
    for ag_id, counts in asset_group_counts.items():
        ag_issues = []
        
        if counts["HEADLINE"] < PMAX_MIN_HEADLINES:
            ag_issues.append(f"Headlines: {counts['HEADLINE']} (min {PMAX_MIN_HEADLINES})")
        if counts["LONG_HEADLINE"] < PMAX_MIN_LONG_HEADLINES:
            ag_issues.append(f"Long Headlines: {counts['LONG_HEADLINE']} (min {PMAX_MIN_LONG_HEADLINES})")
        if counts["DESCRIPTION"] < PMAX_MIN_DESCRIPTIONS:
            ag_issues.append(f"Descriptions: {counts['DESCRIPTION']} (min {PMAX_MIN_DESCRIPTIONS})")
        
        if ag_issues:
            issues.append({
                "campaign_name": counts["campaign_name"],
                "asset_group_id": ag_id,
                "asset_group_name": counts["asset_group_name"],
                "headlines": counts["HEADLINE"],
                "long_headlines": counts["LONG_HEADLINE"],
                "descriptions": counts["DESCRIPTION"],
                "issue": "; ".join(ag_issues)
            })
        else:
            compliant += 1
    
    total = len(asset_group_counts)
    non_compliant_count = len(issues)
    # INVERTED: Show percentage of asset groups with MISSING assets
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 10 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} asset groups meet asset requirements",
        "threshold": f"Min: {PMAX_MIN_HEADLINES} headlines, {PMAX_MIN_LONG_HEADLINES} long headlines, {PMAX_MIN_DESCRIPTIONS} descriptions",
        "details": pd.DataFrame(issues) if issues else pd.DataFrame()
    }



def check_cta_not_automated(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 20: Call to Action should not be 'Automated'
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            asset_group.id,
            asset_group.name,
            asset_group_asset.field_type,
            asset.call_to_action_asset.call_to_action,
            asset_group_asset.status,
            campaign.status,
            asset_group.status,
            campaign.advertising_channel_type
        FROM asset_group_asset
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset_group.status = 'ENABLED'
        AND asset_group_asset.field_type = 'CALL_TO_ACTION_SELECTION'
    """
    
    rows = execute_query(client, customer_id, query)
    
    # Get all asset groups
    all_ag_query = """
        SELECT campaign.id, campaign.name, asset_group.id, asset_group.name, asset_group.status, campaign.status
        FROM asset_group
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset_group.status = 'ENABLED'
    """
    all_ags = execute_query(client, customer_id, all_ag_query)
    
    # Track CTAs
    ag_ctas = {}
    for row in rows:
        ag_id = str(row.asset_group.id)
        cta = row.asset.call_to_action_asset.call_to_action.name if row.asset.call_to_action_asset.call_to_action else "AUTOMATED"
        ag_ctas[ag_id] = {
            "campaign_name": row.campaign.name,
            "asset_group_name": row.asset_group.name,
            "cta": cta
        }
    
    issues = []
    compliant = 0
    
    for row in all_ags:
        ag_id = str(row.asset_group.id)
        cta_data = ag_ctas.get(ag_id)
        
        if not cta_data or cta_data["cta"] in ["AUTOMATED", "UNKNOWN", "UNSPECIFIED"]:
            issues.append({
                "campaign_name": row.campaign.name,
                "asset_group_id": ag_id,
                "asset_group_name": row.asset_group.name,
                "cta": cta_data["cta"] if cta_data else "Not Set / Automated",
                "issue": "CTA is automated or not set"
            })
        else:
            compliant += 1
    
    total = len(all_ags)
    non_compliant_count = len(issues)
    # INVERTED: Show percentage of asset groups USING Automated CTA
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 10 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} asset groups have specific CTAs",
        "threshold": "CTA should not be Automated",
        "details": pd.DataFrame(issues) if issues else pd.DataFrame()
    }



def check_pmax_sitelinks(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 21: At least 4 sitelinks at campaign level for PMax
    Checks both campaign-level assets and asset group assets for sitelinks
    """
    campaigns_query = """
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
    """
    campaigns = execute_query(client, customer_id, campaigns_query)
    
    if not campaigns:
        return {
            "status": "info",
            "score": None,
            "message": "No active Performance Max campaigns found",
            "threshold": f"At least {PMAX_MIN_SITELINKS} sitelinks per campaign",
            "details": pd.DataFrame()
        }
    
    # Get sitelinks from campaign_asset
    campaign_sitelinks_query = """
        SELECT 
            campaign.id,
            campaign.name,
            asset.id,
            asset.sitelink_asset.link_text,
            campaign.status
        FROM campaign_asset
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset.type = 'SITELINK'
        AND campaign_asset.status = 'ENABLED'
    """
    campaign_sitelinks = execute_query(client, customer_id, campaign_sitelinks_query)
    
    campaign_sitelink_count = defaultdict(int)
    for row in campaign_sitelinks:
        campaign_sitelink_count[str(row.campaign.id)] += 1
    
    # Also get sitelinks from asset_group_asset
    ag_sitelinks_query = """
        SELECT 
            campaign.id,
            asset_group.id,
            asset_group_asset.field_type,
            campaign.status,
            asset_group.status,
            campaign.advertising_channel_type
        FROM asset_group_asset
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset_group.status = 'ENABLED'
        AND asset_group_asset.field_type = 'SITELINK'
    """
    ag_sitelinks = execute_query(client, customer_id, ag_sitelinks_query)
    
    # Add asset group sitelinks to campaign count
    for row in ag_sitelinks:
        campaign_sitelink_count[str(row.campaign.id)] += 1
    
    issues = []
    compliant = 0
    
    for row in campaigns:
        campaign_id = str(row.campaign.id)
        count = campaign_sitelink_count.get(campaign_id, 0)
        
        if count >= PMAX_MIN_SITELINKS:
            compliant += 1
        else:
            issues.append({
                "campaign_id": campaign_id,
                "campaign_name": row.campaign.name,
                "sitelink_count": count,
                "issue": f"Has {count} sitelinks, needs {PMAX_MIN_SITELINKS}"
            })
    
    total = len(campaigns)
    non_compliant_count = len(issues)
    # INVERTED: Show percentage of campaigns MISSING sitelinks
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 20 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} PMax campaigns have {PMAX_MIN_SITELINKS}+ sitelinks",
        "threshold": f"At least {PMAX_MIN_SITELINKS} sitelinks per campaign (campaign-level or asset group)",
        "details": pd.DataFrame(issues) if issues else pd.DataFrame()
    }



def check_pmax_display_path(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 22: Display Path should be present in PMax
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            asset_group.id,
            asset_group.name,
            asset_group.path1,
            asset_group.path2,
            campaign.status,
            asset_group.status,
            campaign.advertising_channel_type
        FROM asset_group
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset_group.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No active asset groups found",
            "details": pd.DataFrame()
        }
    
    issues = []
    compliant = 0
    
    for row in rows:
        path1 = row.asset_group.path1 or ""
        path2 = row.asset_group.path2 or ""
        
        if path1.strip():
            compliant += 1
        else:
            issues.append({
                "campaign_name": row.campaign.name,
                "asset_group_id": str(row.asset_group.id),
                "asset_group_name": row.asset_group.name,
                "path1": path1 or "Missing",
                "path2": path2 or "-",
                "issue": "Display path not set"
            })
    
    total = len(rows)
    non_compliant_count = len(issues)
    # INVERTED: Show percentage of asset groups MISSING display path
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 10 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} asset groups have display path",
        "threshold": "Display path should be filled",
        "details": pd.DataFrame(issues) if issues else pd.DataFrame()
    }



def check_callouts(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 23: Callouts should be present
    """
    campaigns_query = """
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
    """
    campaigns = execute_query(client, customer_id, campaigns_query)
    
    if not campaigns:
        return {
            "status": "info",
            "score": None,
            "message": "No active Performance Max campaigns found",
            "details": pd.DataFrame()
        }
    
    callouts_query = """
        SELECT 
            campaign.id,
            campaign.name,
            asset.id,
            campaign.status,
            campaign_asset.status,
            campaign.advertising_channel_type
        FROM campaign_asset
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset.type = 'CALLOUT'
        AND campaign_asset.status = 'ENABLED'
    """
    
    callouts = execute_query(client, customer_id, callouts_query)
    campaigns_with_callouts = set(str(row.campaign.id) for row in callouts)
    
    issues = []
    for row in campaigns:
        if str(row.campaign.id) not in campaigns_with_callouts:
            issues.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "issue": "No callouts present"
            })
    
    compliant = len(campaigns) - len(issues)
    total = len(campaigns)
    non_compliant_count = len(issues)
    # INVERTED: Show percentage of campaigns MISSING callouts
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 20 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} PMax campaigns have callouts",
        "threshold": "Callouts should be present",
        "details": pd.DataFrame(issues) if issues else pd.DataFrame()
    }



def check_structured_snippets(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 24: Structured Snippets should be present
    """
    campaigns_query = """
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
    """
    campaigns = execute_query(client, customer_id, campaigns_query)
    
    if not campaigns:
        return {
            "status": "info",
            "score": None,
            "message": "No active Performance Max campaigns found",
            "details": pd.DataFrame()
        }
    
    snippets_query = """
        SELECT 
            campaign.id,
            campaign.name,
            asset.id,
            campaign.status,
            campaign_asset.status,
            campaign.advertising_channel_type
        FROM campaign_asset
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset.type = 'STRUCTURED_SNIPPET'
        AND campaign_asset.status = 'ENABLED'
    """
    
    snippets = execute_query(client, customer_id, snippets_query)
    campaigns_with_snippets = set(str(row.campaign.id) for row in snippets)
    
    issues = []
    for row in campaigns:
        if str(row.campaign.id) not in campaigns_with_snippets:
            issues.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "issue": "No structured snippets present"
            })
    
    total = len(campaigns)
    non_compliant_count = len(issues)
    # INVERTED: Show percentage of campaigns MISSING snippets
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 20 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant}/{total} PMax campaigns have structured snippets",
        "threshold": "Structured snippets should be present",
        "details": pd.DataFrame(issues) if issues else pd.DataFrame()
    }



def check_images_videos(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 25: At least 5 images & 1 video in asset-only PMax campaigns
    Skips asset groups that have product feed attached (retail/shopping campaigns)
    """
    # First, detect asset groups with product feeds (listing group filters)
    product_feed_query = """
        SELECT 
            asset_group.id,
            asset_group.name,
            campaign.id,
            campaign.status,
            campaign.advertising_channel_type
        FROM asset_group_listing_group_filter
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset_group.status = 'ENABLED'
    """
    
    product_feed_rows = execute_query(client, customer_id, product_feed_query)
    asset_groups_with_feed = set(str(row.asset_group.id) for row in product_feed_rows) if product_feed_rows else set()
    
    # Get all asset group assets
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            asset_group.id,
            asset_group.name,
            asset_group_asset.field_type,
            asset.type,
            asset_group.status,
            asset_group_asset.status,
            campaign.status
        FROM asset_group_asset
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND asset_group.status = 'ENABLED'
        AND asset_group_asset.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No asset group assets found",
            "threshold": f"Min: {PMAX_MIN_IMAGES} images, {PMAX_MIN_VIDEOS} video (asset-only campaigns)",
            "details": pd.DataFrame()
        }
    
    # Count images and videos per asset group
    asset_group_media = defaultdict(lambda: {
        "campaign_name": "",
        "asset_group_name": "",
        "images": 0,
        "videos": 0,
        "has_product_feed": False
    })
    
    for row in rows:
        ag_id = str(row.asset_group.id)
        asset_type = row.asset.type.name
        field_type = row.asset_group_asset.field_type.name
        
        asset_group_media[ag_id]["campaign_name"] = row.campaign.name
        asset_group_media[ag_id]["asset_group_name"] = row.asset_group.name
        asset_group_media[ag_id]["asset_group_id"] = ag_id
        asset_group_media[ag_id]["has_product_feed"] = ag_id in asset_groups_with_feed
        
        if asset_type == "IMAGE" or "IMAGE" in field_type:
            asset_group_media[ag_id]["images"] += 1
        elif asset_type == "YOUTUBE_VIDEO" or "VIDEO" in field_type:
            asset_group_media[ag_id]["videos"] += 1
    
    issues = []
    compliant = 0
    skipped_product_feed = 0
    
    for ag_id, media in asset_group_media.items():
        # Skip asset groups with product feeds
        if media["has_product_feed"]:
            skipped_product_feed += 1
            compliant += 1  # Consider product feed campaigns as compliant
            continue
        
        ag_issues = []
        
        if media["images"] < PMAX_MIN_IMAGES:
            ag_issues.append(f"Images: {media['images']} (min {PMAX_MIN_IMAGES})")
        if media["videos"] < PMAX_MIN_VIDEOS:
            ag_issues.append(f"Videos: {media['videos']} (min {PMAX_MIN_VIDEOS})")
        
        if ag_issues:
            issues.append({
                "campaign_name": media["campaign_name"],
                "asset_group_id": ag_id,
                "asset_group_name": media["asset_group_name"],
                "images": media["images"],
                "videos": media["videos"],
                "issue": "; ".join(ag_issues)
            })
        else:
            compliant += 1
    
    total = len(asset_group_media)
    non_compliant_count = len(issues)
    # INVERTED: Show percentage of asset groups MISSING media
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    status = "pass" if score == 0 else "warning" if score <= 10 else "fail"
    
    message = f"{compliant}/{total} asset groups meet media requirements"
    if skipped_product_feed > 0:
        message += f" ({skipped_product_feed} with product feed skipped)"
    
    return {
        "status": status,
        "score": score,
        "message": message,
        "threshold": f"Min: {PMAX_MIN_IMAGES} images, {PMAX_MIN_VIDEOS} video (asset-only campaigns - product feed campaigns are skipped)",
        "details": pd.DataFrame(issues) if issues else pd.DataFrame()
    }



def check_pmax_spend_split(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 26: PMax Spend Split - 80:10:10 (Shopping:Video:Other)
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            segments.asset_interaction_target.interaction_on_this_asset,
            metrics.cost_micros,
            campaign.status
        FROM campaign
        WHERE campaign.advertising_channel_type = 'PERFORMANCE_MAX'
        AND campaign.status = 'ENABLED'
        AND segments.date DURING LAST_30_DAYS
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No PMax spend data found",
            "details": pd.DataFrame()
        }
    
    # This is a simplified version - actual implementation would need performance_max_placement_view
    spend_by_type = {
        "SHOPPING": 0,
        "VIDEO": 0,
        "OTHER": 0
    }
    total_spend = 0
    
    for row in rows:
        spend = row.metrics.cost_micros / 1_000_000
        total_spend += spend
        # In a real implementation, we'd categorize by asset_interaction_target
        spend_by_type["OTHER"] += spend
    
    if total_spend == 0:
        return {
            "status": "info",
            "score": None,
            "message": "No spend data to analyze",
            "details": pd.DataFrame()
        }
    
    # Calculate percentages
    shopping_pct = spend_by_type["SHOPPING"] / total_spend
    video_pct = spend_by_type["VIDEO"] / total_spend
    other_pct = spend_by_type["OTHER"] / total_spend
    
    # Check compliance
    shopping_ok = abs(shopping_pct - PMAX_SPEND_SPLIT["SHOPPING"]) <= PMAX_SPEND_TOLERANCE
    video_ok = abs(video_pct - PMAX_SPEND_SPLIT["VIDEO"]) <= PMAX_SPEND_TOLERANCE
    
    status = "pass" if shopping_ok and video_ok else "warning"
    
    # INVERTED: Score represents deviation from ideal shopping % (80%)
    # If 80% (ideal) -> deviation 0 -> score 0
    # If 0% (bad) -> deviation 80 -> score 100 (amplified)
    deviation = abs(shopping_pct * 100 - (PMAX_SPEND_SPLIT["SHOPPING"] * 100))
    score = min(deviation * 1.5, 100) # Amplify deviation
    
    details_df = pd.DataFrame([
        {"Channel": "Shopping", "Spend": spend_by_type["SHOPPING"], "Percentage": f"{shopping_pct*100:.1f}%", "Target": "~80%"},
        {"Channel": "Video", "Spend": spend_by_type["VIDEO"], "Percentage": f"{video_pct*100:.1f}%", "Target": "~10%"},
        {"Channel": "Other", "Spend": spend_by_type["OTHER"], "Percentage": f"{other_pct*100:.1f}%", "Target": "~10%"}
    ])
    
    return {
        "status": status,
        "score": score,
        "message": f"Shopping: {shopping_pct*100:.1f}%, Video: {video_pct*100:.1f}%, Other: {other_pct*100:.1f}%",
        "threshold": "80:10:10 (Shopping:Video:Other)",
        "details": details_df
    }



def check_product_coverage(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 27: Product Coverage through Ads
    Note: This requires Merchant Center integration
    """
    # This check requires shopping_performance_view or merchant center data
    # Returning a placeholder for now
    return {
        "status": "info",
        "score": None,
        "message": "Product coverage check requires Merchant Center integration",
        "threshold": "All products should have active ads",
        "details": pd.DataFrame([{
            "Note": "This check requires Google Merchant Center data access"
        }])
    }



def run_all_pmax_checks(client, customer_id: str) -> Dict[int, Dict[str, Any]]:
    """
    Run all Performance Max checks and return results.
    """
    results = {}
    
    checks = [
        (14, "Age Exclusions", check_age_exclusions),
        (15, "Brand Exclusions", check_brand_exclusions),
        # (16, "Auto Asset Optimization", check_auto_asset_optimization),  # Requires manual verification
        (17, "Search Themes", check_search_themes),
        (18, "Search Term Negation", check_search_term_negation),
        (19, "Asset Counts", check_asset_counts),
        (20, "CTA Not Automated", check_cta_not_automated),
        (21, "Sitelinks", check_pmax_sitelinks),
        (22, "Display Path", check_pmax_display_path),
        (23, "Callouts", check_callouts),
        (24, "Structured Snippets", check_structured_snippets),
        (25, "Images & Videos", check_images_videos),
        # (26, "Spend Split", check_pmax_spend_split),  # Channel performance not accessible via API
        # (27, "Product Coverage", check_product_coverage)  # Requires manual verification
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


