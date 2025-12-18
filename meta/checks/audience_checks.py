"""
Audience Targeting Health Checks for Meta Ads
Validates audience configuration and targeting best practices
"""

import pandas as pd
import json
from typing import Dict, List, Any
from meta.utils.data_processing import is_empty_value
from meta.config.constants import THRESHOLDS, PUBLISHER_PLATFORMS


def check_audience_network_usage(adsets_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check usage of Audience Network placement.
    Excessive Audience Network usage may indicate low-quality traffic.
    
    Args:
        adsets_df: DataFrame with flattened adset data
    
    Returns:
        Dictionary with check results
    """
    if adsets_df.empty:
        return {
            'check_name': 'Audience Network Usage',
            'status': 'INFO',
            'message': 'No adsets to check',
            'details': None,
            'count': 0,
            'total': 0
        }
    
    audience_network_adsets = adsets_df[
        adsets_df['publisher_platforms'].apply(
            lambda p: not is_empty_value(p) and 'audience_network' in str(p).lower()
        )
    ]
    
    count = len(audience_network_adsets)
    total = len(adsets_df)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    # High Audience Network usage (>50%) may indicate quality issues
    status = 'PASS' if count < total * 0.5 else 'WARNING'
    
    # Enhanced details
    details = None
    if count > 0:
        details_list = []
        for _, row in audience_network_adsets.iterrows():
            platforms = str(row.get('publisher_platforms', '')).split(', ')
            details_list.append({
                'Campaign': row.get('campaign_name', 'N/A'),
                'Adset': row.get('adset_name', 'N/A'),
                'Adset ID': row.get('adset_id', 'N/A'),
                'Platforms': row.get('publisher_platforms', 'N/A'),
                'Optimization Goal': row.get('optimization_goal', 'N/A'),
                'Advantage+ Audience': row.get('advantage_audience', 'N/A'),
                'Status': row.get('adset_effective_status', 'N/A')
            })
        details = details_list
    
    return {
        'check_name': 'Audience Network Usage',
        'status': status,
        'message': f'{count} out of {total} adsets use Audience Network ({percentage}%)',
        'details': details,
        'count': count,
        'total': total,
        'percentage': percentage,
        'recommendation': 'Monitor Audience Network performance - it can expand reach but may have lower quality'
    }


def check_lookalike_utilization(adsets_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if account is utilizing Lookalike Audiences.
    Lookalikes help reach new users similar to existing customers.
    
    Args:
        adsets_df: DataFrame with flattened adset data
    
    Returns:
        Dictionary with check results
    """
    if adsets_df.empty:
        return {
            'check_name': 'Lookalike Audience Usage',
            'status': 'INFO',
            'message': 'No adsets to check',
            'details': None,
            'count': 0,
            'total': 0
        }
    
    lookalike_found = any(
        'lookalike' in str(v).lower()
        for v in adsets_df['custom_audiences']
        if not is_empty_value(v)
    )
    
    adsets_with_lookalike = adsets_df[
        adsets_df['custom_audiences'].str.contains('lookalike', case=False, na=False)
    ]
    
    count = len(adsets_with_lookalike)
    total = len(adsets_df)
    lookalike_found = count > 0
    
    status = 'PASS' if lookalike_found else 'WARNING'
    
    # Enhanced details
    details = None
    if count > 0:
        details_list = []
        for _, row in adsets_with_lookalike.iterrows():
            details_list.append({
                'Campaign': row.get(' campaign_name', 'N/A'),
                'Adset': row.get('adset_name', 'N/A'),
                'Adset ID': row.get('adset_id', 'N/A'),
                'Lookalike Audiences': row.get('custom_audiences', 'N/A'),
                'Optimization Goal': row.get('optimization_goal', 'N/A'),
                'Excluded Audiences': row.get('excluded_custom_audiences', 'N/A'),
                'Status': row.get('adset_effective_status', 'N/A')
            })
        details = details_list
    
    return {
        'check_name': 'Lookalike Audience Usage',
        'status': status,
        'message': f'Lookalike audiences: {"Utilized" if lookalike_found else "Not Utilized"} ({count} adsets)',
        'details': details,
        'count': count,
        'total': total,
        'recommendation': 'Create Lookalike Audiences based on your best customers to expand reach efficiently'
    }


def check_interest_targeting(adsets_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if interest-based targeting is being utilized.
    
    Args:
        adsets_df: DataFrame with flattened adset data
    
    Returns:
        Dictionary with check results
    """
    if adsets_df.empty:
        return {
            'check_name': 'Interest Targeting Usage',
            'status': 'INFO',
            'message': 'No adsets to check',
            'details': None,
            'count': 0,
            'total': 0
        }
    
    interest_utilized = any(
        not is_empty_value(v) and v not in ['NA', '[]', 'null']
        for v in adsets_df['flexible_spec']
    )
    
    adsets_with_interests = adsets_df[
        ~adsets_df['flexible_spec'].apply(is_empty_value) &
        (adsets_df['flexible_spec'] != 'NA') &
        (adsets_df['flexible_spec'] != '[]')
    ]
    
    count = len(adsets_with_interests)
    total = len(adsets_df)
    
    status = 'PASS' if interest_utilized else 'INFO'
    
    return {
        'check_name': 'Interest Targeting Usage',
        'status': status,
        'message': f'Interest targeting: {"Utilized" if interest_utilized else "Not Utilized"} ({count} adsets)',
        'details': None,
        'count': count,
        'total': total,
        'recommendation': 'Use interest targeting to reach users based on their behaviors and preferences'
    }


def check_optimization_goal_diversity(adsets_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if multiple optimization goals are being used.
    Using diverse optimization goals helps test different strategies.
    
    Args:
        adsets_df: DataFrame with flattened adset data
    
    Returns:
        Dictionary with check results
    """
    if adsets_df.empty:
        return {
            'check_name': 'Optimization Goal Diversity',
            'status': 'INFO',
            'message': 'No adsets to check',
            'details': None,
            'unique_goals': 0
        }
    
    optimization_goals = adsets_df['optimization_goal'].dropna()
    unique_goals = set(str(g).strip() for g in optimization_goals if not is_empty_value(g))
    
    goal_counts = adsets_df['optimization_goal'].value_counts().to_dict()
    
    # Check if using OFFSITE_CONVERSIONS with other goals
    has_offsite_conversions = 'OFFSITE_CONVERSIONS' in unique_goals
    other_goals = unique_goals - {'OFFSITE_CONVERSIONS'}
    
    min_goals = THRESHOLDS['min_optimization_goals']
    
    if has_offsite_conversions and len(other_goals) >= 1:
        status = 'PASS'
        message = f'Good diversity: {len(unique_goals)} unique optimization goals'
    elif len(unique_goals) >= min_goals:
        status = 'PASS'
        message = f'{len(unique_goals)} unique optimization goals being tested'
    else:
        status = 'WARNING'
        message = f'Limited diversity: only {len(unique_goals)} optimization goal(s)'
    
    return {
        'check_name': 'Optimization Goal Diversity',
        'status': status,
        'message': message,
        'details': goal_counts,
        'unique_goals': len(unique_goals),
        'goals_list': list(unique_goals),
        'recommendation': 'Test multiple optimization goals (Conversions, Link Clicks, Reach, etc.) to find what works best'
    }


def check_advantage_audience_usage(adsets_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if Advantage+ Audience (formerly Advantage Lookalike) is being used.
    This automated feature helps Meta expand targeting.
    
    Args:
        adsets_df: DataFrame with flattened adset data
    
    Returns:
        Dictionary with check results
    """
    if adsets_df.empty:
        return {
            'check_name': 'Advantage+ Audience Usage',
            'status': 'INFO',
            'message': 'No adsets to check',
            'details': None,
            'count': 0,
            'total': 0
        }
    
    advantage_enabled = adsets_df[
        ~adsets_df['advantage_audience'].apply(is_empty_value) &
        (adsets_df['advantage_audience'].str.upper() != 'NA') &
        (adsets_df['advantage_audience'].str.upper() != 'FALSE') &
        (adsets_df['advantage_audience'] != '0')
    ]
    
    count = len(advantage_enabled)
    total = len(adsets_df)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count > 0 else 'INFO'
    
    return {
        'check_name': 'Advantage+ Audience Usage',
        'status': status,
        'message': f'{count} out of {total} adsets use Advantage+ Audience ({percentage}%)',
        'details': None,
        'count': count,
        'total': total,
        'percentage': percentage,
        'recommendation': 'Enable Advantage+ Audience to let Meta automatically expand your targeting'
    }


def check_custom_audience_usage(adsets_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if Custom Audiences are being utilized for retargeting.
    
    Args:
        adsets_df: DataFrame with flattened adset data
    
    Returns:
        Dictionary with check results
    """
    if adsets_df.empty:
        return {
            'check_name': 'Custom Audience Usage',
            'status': 'INFO',
            'message': 'No adsets to check',
            'details': None,
            'count': 0,
            'total': 0
        }
    
    adsets_with_custom = adsets_df[
        ~adsets_df['custom_audiences'].apply(is_empty_value) &
        (adsets_df['custom_audiences'] != 'NA')
    ]
    
    count = len(adsets_with_custom)
    total = len(adsets_df)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count > 0 else 'WARNING'
    
    return {
        'check_name': 'Custom Audience Usage',
        'status': status,
        'message': f'{count} out of {total} adsets use Custom Audiences ({percentage}%)',
        'details': None,
        'count': count,
        'total': total,
        'percentage': percentage,
        'recommendation': 'Create Custom Audiences from website visitors, customer lists, or app users for effective retargeting'
    }


def run_all_audience_checks(adsets_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Run all audience targeting-related health checks.
    
    Args:
        adsets_df: DataFrame with flattened adset data
    
    Returns:
        List of check result dictionaries
    """
    return [
        check_audience_network_usage(adsets_df),
        check_lookalike_utilization(adsets_df),
        check_interest_targeting(adsets_df),
        check_optimization_goal_diversity(adsets_df),
        check_advantage_audience_usage(adsets_df),
        check_custom_audience_usage(adsets_df)
    ]
