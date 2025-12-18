"""
Search Campaign Health Checks
Checks: 1, 2, 4, 5, 6, 7, 8, 9, 10, 11
"""
import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from collections import defaultdict
from services.google_ads_client import execute_query
from config.constants import (
    SPEND_SPLIT_THRESHOLDS, SPEND_SPLIT_TOLERANCE,
    MIN_RSAS_PER_AD_GROUP, MIN_UNIQUE_RSA_RATIO,
    MIN_SITELINKS_PER_RSA, QUALITY_SCORE_THRESHOLDS,
    AD_GROUP_TYPE_KEYWORDS, CHECK_DESCRIPTIONS
)



def check_spend_split(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 1: Contribution of Spends - 70:20:10 (Exact:Phrase:Broad)
    Applicable for search campaigns only.
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_criterion.keyword.match_type,
            metrics.cost_micros,
            campaign.status,
            ad_group.status,
            ad_group_criterion.status
        FROM keyword_view
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_criterion.status = 'ENABLED'
        AND segments.date DURING LAST_30_DAYS
    """
    
    rows = execute_query(client, customer_id, query)
    
    if not rows:
        return {
            "status": "info",
            "score": None,
            "message": "No keyword data found for search campaigns",
            "details": pd.DataFrame()
        }
    
    # Aggregate spend by match type
    spend_by_match_type = defaultdict(float)
    total_spend = 0
    
    for row in rows:
        match_type = row.ad_group_criterion.keyword.match_type.name
        spend = row.metrics.cost_micros / 1_000_000
        spend_by_match_type[match_type] += spend
        total_spend += spend
    
    if total_spend == 0:
        return {
            "status": "info",
            "score": None,
            "message": "No spend data found",
            "details": pd.DataFrame()
        }
    
    # Calculate percentages
    exact_pct = spend_by_match_type.get("EXACT", 0) / total_spend
    phrase_pct = spend_by_match_type.get("PHRASE", 0) / total_spend
    broad_pct = spend_by_match_type.get("BROAD", 0) / total_spend
    
    # Check compliance
    exact_ok = exact_pct >= SPEND_SPLIT_THRESHOLDS["EXACT"] - SPEND_SPLIT_TOLERANCE
    phrase_ok = abs(phrase_pct - SPEND_SPLIT_THRESHOLDS["PHRASE"]) <= SPEND_SPLIT_TOLERANCE * 2
    broad_ok = abs(broad_pct - SPEND_SPLIT_THRESHOLDS["BROAD"]) <= SPEND_SPLIT_TOLERANCE * 2
    
    status = "pass" if exact_ok else "fail"
    # INVERTED: Score represents deviation/imperfection. 
    # If exact is 70% (good), score should be 0 (good).
    # If exact is 0% (bad), score should be 100 (bad).
    # However, this metric is special. Let's just track deviation from 70%.
    deviation = abs(exact_pct * 100 - 70)
    score = min(deviation * 2, 100) # Amplify deviation so 20% off = 40 score
    
    details_df = pd.DataFrame([
        {"Match Type": "EXACT", "Spend": spend_by_match_type.get("EXACT", 0), "Percentage": f"{exact_pct*100:.1f}%", "Target": "≥70%", "Status": "✅" if exact_ok else "❌"},
        {"Match Type": "PHRASE", "Spend": spend_by_match_type.get("PHRASE", 0), "Percentage": f"{phrase_pct*100:.1f}%", "Target": "~20%", "Status": "✅" if phrase_ok else "⚠️"},
        {"Match Type": "BROAD", "Spend": spend_by_match_type.get("BROAD", 0), "Percentage": f"{broad_pct*100:.1f}%", "Target": "~10%", "Status": "✅" if broad_ok else "⚠️"}
    ])
    
    return {
        "status": status,
        "score": score,
        "message": f"Exact: {exact_pct*100:.1f}%, Phrase: {phrase_pct*100:.1f}%, Broad: {broad_pct*100:.1f}%",
        "threshold": "70:20:10 (Exact:Phrase:Broad)",
        "details": details_df
    }



def check_audience_observation(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 2: Audience in Observation
    Should have all 3 - Remarketing, Inmarket, Affinity
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            campaign_criterion.criterion_id,
            campaign_criterion.type,
            campaign_criterion.user_list.user_list,
            campaign_criterion.user_interest.user_interest_category,
            campaign_criterion.status,
            campaign.status,
            campaign.advertising_channel_type
        FROM campaign_criterion
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND campaign_criterion.status = 'ENABLED'
        AND campaign_criterion.type IN ('USER_LIST', 'USER_INTEREST')
    """
    
    rows = execute_query(client, customer_id, query)
    
    # Track audience types by campaign
    campaign_audiences = defaultdict(lambda: {"remarketing": False, "inmarket": False, "affinity": False})
    
    for row in rows:
        campaign_id = str(row.campaign.id)
        criterion_type = row.campaign_criterion.type.name
        
        if criterion_type == "USER_LIST":
            campaign_audiences[campaign_id]["remarketing"] = True
        elif criterion_type == "USER_INTEREST":
            category = row.campaign_criterion.user_interest.user_interest_category
            if category:
                category_lower = category.lower() if isinstance(category, str) else ""
                if "inmarket" in category_lower or "in-market" in category_lower:
                    campaign_audiences[campaign_id]["inmarket"] = True
                elif "affinity" in category_lower:
                    campaign_audiences[campaign_id]["affinity"] = True
    
    # Get all search campaigns
    campaigns_query = """
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
    """
    campaign_rows = execute_query(client, customer_id, campaigns_query)
    
    campaigns_with_issues = []
    compliant_count = 0
    
    for row in campaign_rows:
        campaign_id = str(row.campaign.id)
        audiences = campaign_audiences.get(campaign_id, {"remarketing": False, "inmarket": False, "affinity": False})
        
        missing = []
        if not audiences["remarketing"]:
            missing.append("Remarketing")
        if not audiences["inmarket"]:
            missing.append("Inmarket")
        if not audiences["affinity"]:
            missing.append("Affinity")
        
        if missing:
            campaigns_with_issues.append({
                "campaign_id": campaign_id,
                "campaign_name": row.campaign.name,
                "missing_audiences": ", ".join(missing),
                "issue": f"Missing {len(missing)} audience type(s)"
            })
        else:
            compliant_count += 1
    
    total = len(campaign_rows)
    non_compliant_count = len(campaigns_with_issues)
    # INVERTED: Show percentage of campaigns MISSING audiences
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    # Determine status (inverted: low score = good, high score = bad)
    status = "pass" if score == 0 else "warning" if score <= 20 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant_count}/{total} campaigns have all 3 audience types",
        "threshold": "All campaigns should have Remarketing, Inmarket, and Affinity",
        "details": pd.DataFrame(campaigns_with_issues) if campaigns_with_issues else pd.DataFrame()
    }



def check_rsa_count(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 4: Number of RSAs
    Each ad group should have at least 2 RSAs
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_ad.ad.id,
            ad_group_ad.ad.type,
            ad_group_ad.status,
            campaign.status,
            ad_group.status,
            campaign.advertising_channel_type
        FROM ad_group_ad
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_ad.status = 'ENABLED'
        AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """
    
    rows = execute_query(client, customer_id, query)
    
    # Count RSAs per ad group
    ad_group_rsa_count = defaultdict(lambda: {"count": 0, "campaign_name": "", "ad_group_name": ""})
    
    for row in rows:
        key = f"{row.campaign.id}_{row.ad_group.id}"
        ad_group_rsa_count[key]["count"] += 1
        ad_group_rsa_count[key]["campaign_name"] = row.campaign.name
        ad_group_rsa_count[key]["campaign_id"] = str(row.campaign.id)
        ad_group_rsa_count[key]["ad_group_name"] = row.ad_group.name
        ad_group_rsa_count[key]["ad_group_id"] = str(row.ad_group.id)
    
    # Get all active ad groups
    all_ad_groups_query = """
        SELECT campaign.id, campaign.name, ad_group.id, ad_group.name, ad_group.status, campaign.status
        FROM ad_group
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
    """
    all_ad_groups = execute_query(client, customer_id, all_ad_groups_query)
    
    ad_groups_with_issues = []
    compliant_count = 0
    
    for row in all_ad_groups:
        key = f"{row.campaign.id}_{row.ad_group.id}"
        rsa_count = ad_group_rsa_count.get(key, {}).get("count", 0)
        
        if rsa_count >= MIN_RSAS_PER_AD_GROUP:
            compliant_count += 1
        else:
            ad_groups_with_issues.append({
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "rsa_count": rsa_count,
                "issue": f"Has {rsa_count} RSAs, needs at least {MIN_RSAS_PER_AD_GROUP}"
            })
    
    total = len(all_ad_groups)
    non_compliant_count = len(ad_groups_with_issues)
    # INVERTED: Show percentage of ad groups with FEWER than 2 RSAs
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    # Determine status (inverted: low score = good, high score = bad)
    status = "pass" if score == 0 else "warning" if score <= 10 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant_count}/{total} ad groups have {MIN_RSAS_PER_AD_GROUP}+ RSAs",
        "threshold": f"Each ad group should have at least {MIN_RSAS_PER_AD_GROUP} RSAs",
        "details": pd.DataFrame(ad_groups_with_issues) if ad_groups_with_issues else pd.DataFrame()
    }



def check_unique_rsas_ratio(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 5: Unique RSAs Ratio
    Unique RSAs to ad group ratio should be at least 1:1
    """
    # Get all RSAs with their headlines and descriptions to determine uniqueness
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_ad.ad.id,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.status,
            campaign.status,
            ad_group.status,
            campaign.advertising_channel_type
        FROM ad_group_ad
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_ad.status = 'ENABLED'
        AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """
    
    rows = execute_query(client, customer_id, query)
    
    # Track unique RSAs
    unique_rsas = set()
    total_ad_groups = set()
    
    for row in rows:
        ad_group_key = f"{row.campaign.id}_{row.ad_group.id}"
        total_ad_groups.add(ad_group_key)
        
        # Create a signature for the RSA based on headlines and descriptions
        headlines = []
        descriptions = []
        
        if row.ad_group_ad.ad.responsive_search_ad.headlines:
            for h in row.ad_group_ad.ad.responsive_search_ad.headlines:
                if hasattr(h, 'text'):
                    headlines.append(h.text)
        
        if row.ad_group_ad.ad.responsive_search_ad.descriptions:
            for d in row.ad_group_ad.ad.responsive_search_ad.descriptions:
                if hasattr(d, 'text'):
                    descriptions.append(d.text)
        
        signature = f"{sorted(headlines)}_{sorted(descriptions)}"
        unique_rsas.add(signature)
    
    unique_count = len(unique_rsas)
    ad_group_count = len(total_ad_groups)
    
    if ad_group_count == 0:
        return {
            "status": "info",
            "score": None,
            "message": "No search ad groups found",
            "details": pd.DataFrame()
        }
    
    ratio = unique_count / ad_group_count
    status = "pass" if ratio >= MIN_UNIQUE_RSA_RATIO else "fail"
    
    # INVERTED: Score based on gap from 1:1 ratio
    # If ratio 1.0 -> gap 0 -> score 0 (Good)
    # If ratio 0.5 -> gap 0.5 -> score 50 (Bad)
    gap = max(0, MIN_UNIQUE_RSA_RATIO - ratio)
    score = min(gap * 100, 100)
    
    return {
        "status": status,
        "score": score,
        "message": f"Unique RSAs: {unique_count}, Ad Groups: {ad_group_count}, Ratio: {ratio:.2f}:1",
        "threshold": f"Ratio should be at least {MIN_UNIQUE_RSA_RATIO}:1",
        "details": pd.DataFrame([{
            "Metric": "Unique RSAs", "Value": unique_count
        }, {
            "Metric": "Total Ad Groups", "Value": ad_group_count
        }, {
            "Metric": "Ratio", "Value": f"{ratio:.2f}:1"
        }])
    }



def check_cross_keyword_negation(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 6: Cross Keyword Negation
    Keywords from any ad-group should be negated in other ad-groups within the SAME CAMPAIGN as Exact Match.
    This ensures a keyword from Ad Group A is negated in Ad Group B (within same campaign).
    """
    # Get positive keywords by campaign and ad group
    positive_query = """
        SELECT 
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.status,
            campaign.status,
            ad_group.status,
            campaign.advertising_channel_type
        FROM keyword_view
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_criterion.status = 'ENABLED'
        AND ad_group_criterion.negative = false
    """
    
    positive_rows = execute_query(client, customer_id, positive_query)
    
    # Get negative keywords
    negative_query = """
        SELECT 
            campaign.id,
            ad_group.id,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.status,
            campaign.status,
            ad_group.status,
            campaign.advertising_channel_type
        FROM keyword_view
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_criterion.status = 'ENABLED'
        AND ad_group_criterion.negative = true
    """
    
    negative_rows = execute_query(client, customer_id, negative_query)
    
    # Organize data by campaign
    campaign_data = defaultdict(lambda: {
        "name": "",
        "ad_groups": {},
        "negatives": defaultdict(set)
    })
    
    for row in positive_rows:
        campaign_id = str(row.campaign.id)
        ad_group_id = str(row.ad_group.id)
        campaign_data[campaign_id]["name"] = row.campaign.name
        
        if ad_group_id not in campaign_data[campaign_id]["ad_groups"]:
            campaign_data[campaign_id]["ad_groups"][ad_group_id] = {
                "name": row.ad_group.name,
                "keywords": set()
            }
        campaign_data[campaign_id]["ad_groups"][ad_group_id]["keywords"].add(
            row.ad_group_criterion.keyword.text.lower()
        )
    
    for row in negative_rows:
        campaign_id = str(row.campaign.id)
        ad_group_id = str(row.ad_group.id)
        match_type = row.ad_group_criterion.keyword.match_type.name
        if match_type == "EXACT":
            campaign_data[campaign_id]["negatives"][ad_group_id].add(
                row.ad_group_criterion.keyword.text.lower()
            )
    
    # Check cross-negation within each campaign
    missing_negations = []
    total_checks = 0
    passed_checks = 0
    
    for campaign_id, data in campaign_data.items():
        ad_group_ids = list(data["ad_groups"].keys())
        if len(ad_group_ids) < 2:
            continue  # Need at least 2 ad groups for cross-negation
        
        for ag_id in ad_group_ids:
            ag_info = data["ad_groups"][ag_id]
            
            # Check if each keyword is negated in OTHER ad groups
            for keyword in ag_info["keywords"]:
                for other_ag_id in ad_group_ids:
                    if other_ag_id == ag_id:
                        continue  # Skip same ad group
                    
                    total_checks += 1
                    other_negatives = data["negatives"].get(other_ag_id, set())
                    
                    if keyword in other_negatives:
                        passed_checks += 1
                    else:
                        missing_negations.append({
                            "campaign_name": data["name"],
                            "source_ad_group": ag_info["name"],
                            "keyword": keyword,
                            "missing_in_ad_group": data["ad_groups"][other_ag_id]["name"],
                            "issue": f"Keyword not negated in other ad group"
                        })
    
    if total_checks == 0:
        return {
            "status": "info",
            "score": None,
            "message": "No campaigns with multiple ad groups found for cross-negation",
            "threshold": "Keywords from one ad group should be negated in other ad groups (within same campaign)",
            "details": pd.DataFrame()
        }
    
    score = ((total_checks - passed_checks) / total_checks * 100) if total_checks > 0 else 0
    # Inverted status: low score (failing items) is good
    status = "pass" if score <= 10 else ("warning" if score <= 30 else "fail")
    
    return {
        "status": status,
        "score": score,
        "message": f"{passed_checks}/{total_checks} cross-negations in place ({score:.1f}%)",
        "threshold": "Keywords from one ad group should be negated in other ad groups (within same campaign)",
        "details": pd.DataFrame(missing_negations[:100]) if missing_negations else pd.DataFrame()  # Limit to 100 rows
    }



def check_ad_copy_quality(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 7: Ad Copy Quality
    Count of ads with ad strengths: Excellent, Good, Average, Poor, Pending
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_ad.ad.id,
            ad_group_ad.ad_strength,
            campaign.status,
            ad_group.status,
            ad_group_ad.status
        FROM ad_group_ad
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_ad.status = 'ENABLED'
        AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """
    
    rows = execute_query(client, customer_id, query)
    
    strength_counts = defaultdict(int)
    strength_details = defaultdict(list)
    
    for row in rows:
        strength = row.ad_group_ad.ad_strength.name if row.ad_group_ad.ad_strength else "UNKNOWN"
        strength_counts[strength] += 1
        
        if strength in ["POOR", "PENDING", "UNKNOWN"]:
            strength_details[strength].append({
                "campaign_name": row.campaign.name,
                "ad_group_name": row.ad_group.name,
                "ad_id": str(row.ad_group_ad.ad.id),
                "ad_strength": strength
            })
    
    total_ads = sum(strength_counts.values())
    excellent_good = strength_counts.get("EXCELLENT", 0) + strength_counts.get("GOOD", 0)
    poor_average = total_ads - excellent_good
    # INVERTED: Score represents % of non-excellent/good ads
    score = (poor_average / total_ads * 100) if total_ads > 0 else 0
    
    # Inverted status: low % of poor ads is good
    status = "pass" if score <= 30 else ("warning" if score <= 50 else "fail")
    
    summary_df = pd.DataFrame([
        {"Ad Strength": k, "Count": v, "Percentage": f"{v/total_ads*100:.1f}%" if total_ads > 0 else "0%"}
        for k, v in sorted(strength_counts.items())
    ])
    
    # Combine poor/pending ads for details
    poor_ads = []
    for ads in strength_details.values():
        poor_ads.extend(ads)
    
    return {
        "status": status,
        "score": score,
        "message": f"Excellent/Good: {excellent_good}/{total_ads} ({score:.1f}%)",
        "threshold": "Majority of ads should have Excellent or Good strength",
        "details": summary_df,
        "issues": pd.DataFrame(poor_ads) if poor_ads else pd.DataFrame()
    }



def check_sitelinks(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 8: 4 Unique Sitelinks per RSA
    Each RSA must have 4 unique sitelinks
    """
    # Get sitelink assets at campaign level
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            asset.id,
            asset.name,
            asset.sitelink_asset.link_text,
            campaign.status,
            campaign_asset.status,
            campaign.advertising_channel_type
        FROM campaign_asset
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND asset.type = 'SITELINK'
        AND campaign_asset.status = 'ENABLED'
    """
    
    rows = execute_query(client, customer_id, query)
    
    # Count sitelinks per campaign
    campaign_sitelinks = defaultdict(lambda: {"count": 0, "name": "", "sitelinks": set()})
    
    for row in rows:
        campaign_id = str(row.campaign.id)
        campaign_sitelinks[campaign_id]["count"] += 1
        campaign_sitelinks[campaign_id]["name"] = row.campaign.name
        if row.asset.sitelink_asset.link_text:
            campaign_sitelinks[campaign_id]["sitelinks"].add(row.asset.sitelink_asset.link_text)
    
    # Get all search campaigns
    campaigns_query = """
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
    """
    all_campaigns = execute_query(client, customer_id, campaigns_query)
    
    campaigns_with_issues = []
    compliant_count = 0
    
    for row in all_campaigns:
        campaign_id = str(row.campaign.id)
        sitelink_data = campaign_sitelinks.get(campaign_id, {"count": 0, "sitelinks": set()})
        unique_count = len(sitelink_data["sitelinks"])
        
        if unique_count >= MIN_SITELINKS_PER_RSA:
            compliant_count += 1
        else:
            campaigns_with_issues.append({
                "campaign_id": campaign_id,
                "campaign_name": row.campaign.name,
                "sitelink_count": unique_count,
                "issue": f"Has {unique_count} sitelinks, needs at least {MIN_SITELINKS_PER_RSA}"
            })
    
    total = len(all_campaigns)
    non_compliant_count = len(campaigns_with_issues)
    # INVERTED: Show percentage of campaigns with FEWER than 4 sitelinks
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    # Inverted status: low score = good
    status = "pass" if score == 0 else "warning" if score <= 20 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant_count}/{total} campaigns have {MIN_SITELINKS_PER_RSA}+ sitelinks",
        "threshold": f"Each campaign should have at least {MIN_SITELINKS_PER_RSA} unique sitelinks",
        "details": pd.DataFrame(campaigns_with_issues) if campaigns_with_issues else pd.DataFrame()
    }



def check_display_path(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 9: Display Path Added
    Ads must have display path filled
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_ad.ad.id,
            ad_group_ad.ad.responsive_search_ad.path1,
            ad_group_ad.ad.responsive_search_ad.path2,
            campaign.status,
            ad_group.status,
            ad_group_ad.status
        FROM ad_group_ad
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_ad.status = 'ENABLED'
        AND ad_group_ad.ad.type = 'RESPONSIVE_SEARCH_AD'
    """
    
    rows = execute_query(client, customer_id, query)
    
    ads_with_issues = []
    compliant_count = 0
    
    for row in rows:
        path1 = row.ad_group_ad.ad.responsive_search_ad.path1 or ""
        path2 = row.ad_group_ad.ad.responsive_search_ad.path2 or ""
        
        if path1.strip():  # At least path1 should be filled
            compliant_count += 1
        else:
            ads_with_issues.append({
                "campaign_name": row.campaign.name,
                "ad_group_name": row.ad_group.name,
                "ad_id": str(row.ad_group_ad.ad.id),
                "path1": path1 or "Missing",
                "path2": path2 or "-",
                "issue": "Display path not set"
            })
    
    total = len(rows)
    non_compliant_count = len(ads_with_issues)
    # INVERTED: Show percentage of ads MISSING display path
    score = (non_compliant_count / total * 100) if total > 0 else 0
    
    # Inverted status: low score = good
    status = "pass" if score == 0 else "warning" if score <= 10 else "fail"
    
    return {
        "status": status,
        "score": score,
        "message": f"{compliant_count}/{total} ads have display path set",
        "threshold": "All ads should have display path",
        "details": pd.DataFrame(ads_with_issues) if ads_with_issues else pd.DataFrame()
    }



def check_weighted_quality_score(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 10: Weighted Average Quality Score
    Brand QS >= 9, Non-Brand QS >= 7, Competitor QS >= 5
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.quality_info.quality_score,
            metrics.impressions,
            campaign.status,
            ad_group.status,
            ad_group_criterion.status
        FROM keyword_view
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_criterion.status = 'ENABLED'
        AND metrics.impressions > 0
    """
    
    rows = execute_query(client, customer_id, query)
    
    # Categorize keywords
    brand_data = []
    non_brand_data = []
    competitor_data = []
    
    for row in rows:
        ad_group_name = row.ad_group.name.lower()
        quality_score = row.ad_group_criterion.quality_info.quality_score
        impressions = row.metrics.impressions
        
        if quality_score is None or quality_score == 0:
            continue  # Skip keywords without quality score
        
        kw_data = {
            "campaign_name": row.campaign.name,
            "ad_group_name": row.ad_group.name,
            "keyword": row.ad_group_criterion.keyword.text,
            "quality_score": quality_score,
            "impressions": impressions
        }
        
        # Categorize based on ad group name
        if any(kw in ad_group_name for kw in AD_GROUP_TYPE_KEYWORDS["brand"]):
            brand_data.append(kw_data)
        elif any(kw in ad_group_name for kw in AD_GROUP_TYPE_KEYWORDS["competitor"]):
            competitor_data.append(kw_data)
        else:
            non_brand_data.append(kw_data)
    
    # Calculate weighted averages
    def calc_weighted_avg(data):
        if not data:
            return None
        total_weight = sum(d["quality_score"] * d["impressions"] for d in data)
        total_impressions = sum(d["impressions"] for d in data)
        return total_weight / total_impressions if total_impressions > 0 else None
    
    brand_wqs = calc_weighted_avg(brand_data)
    non_brand_wqs = calc_weighted_avg(non_brand_data)
    competitor_wqs = calc_weighted_avg(competitor_data)
    
    results = []
    issues = []
    
    if brand_wqs is not None:
        status = "✅" if brand_wqs >= QUALITY_SCORE_THRESHOLDS["brand"] else "❌"
        results.append({
            "Category": "Brand",
            "Weighted QS": f"{brand_wqs:.2f}",
            "Threshold": f">= {QUALITY_SCORE_THRESHOLDS['brand']}",
            "Keywords": len(brand_data),
            "Status": status
        })
        if brand_wqs < QUALITY_SCORE_THRESHOLDS["brand"]:
            issues.append("Brand")
    
    if non_brand_wqs is not None:
        status = "✅" if non_brand_wqs >= QUALITY_SCORE_THRESHOLDS["non_brand"] else "❌"
        results.append({
            "Category": "Non-Brand",
            "Weighted QS": f"{non_brand_wqs:.2f}",
            "Threshold": f">= {QUALITY_SCORE_THRESHOLDS['non_brand']}",
            "Keywords": len(non_brand_data),
            "Status": status
        })
        if non_brand_wqs < QUALITY_SCORE_THRESHOLDS["non_brand"]:
            issues.append("Non-Brand")
    
    if competitor_wqs is not None:
        status = "✅" if competitor_wqs >= QUALITY_SCORE_THRESHOLDS["competitor"] else "❌"
        results.append({
            "Category": "Competitor",
            "Weighted QS": f"{competitor_wqs:.2f}",
            "Threshold": f">= {QUALITY_SCORE_THRESHOLDS['competitor']}",
            "Keywords": len(competitor_data),
            "Status": status
        })
        if competitor_wqs < QUALITY_SCORE_THRESHOLDS["competitor"]:
            issues.append("Competitor")
    
    status = "pass" if len(issues) == 0 else "fail"
    
    # Calculate overall score as average of compliant categories
    scores = []
    # Calculate inverted scores for quality score (100 = bad, 0 = good)
    inv_scores = []
    
    if brand_wqs:
         # If QS is 10 (perfect) -> gap 0 -> score 0
         # If QS is 5 (bad, threshold 9) -> gap 4 -> score 44
         gap = max(0, QUALITY_SCORE_THRESHOLDS["brand"] - brand_wqs)
         inv_scores.append(min(gap / QUALITY_SCORE_THRESHOLDS["brand"] * 100 * 2, 100))
    
    if non_brand_wqs:
         gap = max(0, QUALITY_SCORE_THRESHOLDS["non_brand"] - non_brand_wqs)
         inv_scores.append(min(gap / QUALITY_SCORE_THRESHOLDS["non_brand"] * 100 * 2, 100))
         
    if competitor_wqs:
         gap = max(0, QUALITY_SCORE_THRESHOLDS["competitor"] - competitor_wqs)
         inv_scores.append(min(gap / QUALITY_SCORE_THRESHOLDS["competitor"] * 100 * 2, 100))
    
    overall_score = sum(inv_scores) / len(inv_scores) if inv_scores else 0
    
    # Format the message properly
    brand_str = f"{brand_wqs:.2f}" if brand_wqs is not None else "N/A"
    non_brand_str = f"{non_brand_wqs:.2f}" if non_brand_wqs is not None else "N/A"
    competitor_str = f"{competitor_wqs:.2f}" if competitor_wqs is not None else "N/A"
    
    return {
        "status": status,
        "score": overall_score,
        "message": f"Brand: {brand_str}, Non-Brand: {non_brand_str}, Competitor: {competitor_str}",
        "threshold": "Brand>=9, Non-Brand>=7, Competitor>=5",
        "details": pd.DataFrame(results) if results else pd.DataFrame()
    }



def check_keywords_without_impressions(client, customer_id: str) -> Dict[str, Any]:
    """
    Check 11: Percentage of Keywords without Impressions
    """
    query = """
        SELECT 
            campaign.id,
            campaign.name,
            ad_group.id,
            ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            metrics.impressions,
            campaign.status,
            ad_group.status,
            ad_group_criterion.status
        FROM keyword_view
        WHERE campaign.advertising_channel_type = 'SEARCH'
        AND campaign.status = 'ENABLED'
        AND ad_group.status = 'ENABLED'
        AND ad_group_criterion.status = 'ENABLED'
        AND segments.date DURING LAST_30_DAYS
    """
    
    rows = execute_query(client, customer_id, query)
    
    keywords_without_impressions = []
    total_keywords = len(rows)
    
    for row in rows:
        if row.metrics.impressions == 0:
            keywords_without_impressions.append({
                "campaign_name": row.campaign.name,
                "ad_group_name": row.ad_group.name,
                "keyword": row.ad_group_criterion.keyword.text,
                "match_type": row.ad_group_criterion.keyword.match_type.name,
                "impressions": 0
            })
    
    zero_impression_count = len(keywords_without_impressions)
    percentage = (zero_impression_count / total_keywords * 100) if total_keywords > 0 else 0
    
    # Lower percentage is better
    score = 100 - percentage
    status = "pass" if percentage < 20 else ("warning" if percentage < 40 else "fail")
    
    return {
        "status": status,   
        "score": score,
        "message": f"{zero_impression_count}/{total_keywords} keywords ({percentage:.1f}%) have zero impressions",
        "threshold": "Lower percentage is better",
        "details": pd.DataFrame(keywords_without_impressions) if keywords_without_impressions else pd.DataFrame()
    }



def run_all_search_checks(client, customer_id: str) -> Dict[int, Dict[str, Any]]:
    """
    Run all search campaign checks and return results.
    """
    results = {}
    
    checks = [
        (1, "Spend Split", check_spend_split),
        (2, "Audience Observation", check_audience_observation),
        (4, "RSA Count", check_rsa_count),
        (5, "Unique RSAs Ratio", check_unique_rsas_ratio),
        (6, "Cross Keyword Negation", check_cross_keyword_negation),
        (7, "Ad Copy Quality", check_ad_copy_quality),
        (8, "Sitelinks", check_sitelinks),
        (9, "Display Path", check_display_path),
        (10, "Quality Score", check_weighted_quality_score),
        (11, "Keywords w/o Impressions", check_keywords_without_impressions)
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


