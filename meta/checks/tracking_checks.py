"""
Tracking Health Checks for Meta Ads
Validates tracking setup including URL tags and Facebook Pixels
"""

import pandas as pd
from typing import Dict, List, Any
from meta.utils.data_processing import is_empty_value


def check_url_tags_presence(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if ads have URL tags configured for tracking.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'URL Tags Presence',
            'status': 'INFO',
            'message': 'No ads to check',
            ' ': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    ads_without_tags = ads_df[ads_df['url_tags'].apply(is_empty_value)]
    count = len(ads_without_tags)
    total = len(ads_df)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count == 0 else 'WARNING' if count < total * 0.2 else 'FAIL'
    
    # Enhanced details with complete ad information
    details = None
    if count > 0:
        details_list = []
        for _, row in ads_without_tags.iterrows():
            details_list.append({
                'Campaign': row.get('campaign_name', 'N/A'),
                'Campaign ID': row.get('campaign_id', 'N/A'),
                'Adset': row.get('adset_name', 'N/A'),
                'Adset ID': row.get('adset_id', 'N/A'),
                'Ad Name': row.get('ad_name', 'N/A'),
                'Ad ID': row.get('ad_id', 'N/A'),
                'URL Tags': 'Missing',
                'FB Pixel': 'Present' if not is_empty_value(row.get('fb_pixel')) else 'Missing',
                'Campaign Status': row.get('campaign_status', 'N/A'),
                'Adset Status': row.get('adset_status', 'N/A')
            })
        details = details_list
    
    return {
        'check_name': 'URL Tags Presence',
        'status': status,
        'message': f'{count} out of {total} active ads missing URL tags ({percentage}%)',
        'details': details,
        'count': count,
        'total': total,
        'percentage': percentage,
        'threshold': '< 20%',
        'recommendation': 'Add URL parameters to track ad performance and conversions accurately'
    }


def check_pixel_tracking(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if ads have Facebook Pixel tracking configured.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'Facebook Pixel Tracking',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    # Filter non-app ads only (app ads don't need pixel)
    non_app_ads = ads_df[ads_df['application'].apply(is_empty_value)]
    
    if non_app_ads.empty:
        return {
            'check_name': 'Facebook Pixel Tracking',
            'status': 'INFO',
            'message': 'All ads are app ads (pixel not required)',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    ads_without_pixel = non_app_ads[non_app_ads['fb_pixel'].apply(is_empty_value)]
    count = len(ads_without_pixel)
    total = len(non_app_ads)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count == 0 else 'WARNING' if count < total * 0.3 else 'FAIL'
    
    # Enhanced details
    details = None
    if count > 0:
        details_list = []
        for _, row in ads_without_pixel.iterrows():
            details_list.append({
                'Campaign': row.get('campaign_name', 'N/A'),
                'Adset': row.get('adset_name', 'N/A'),
                'Ad Name': row.get('ad_name', 'N/A'),
                'Ad ID': row.get('ad_id', 'N/A'),
                'FB Pixel': 'Missing',
                'URL Tags': 'Present' if not is_empty_value(row.get('url_tags')) else 'Missing',
                'Ad Type': 'App Ad' if not is_empty_value(row.get('application')) else 'Non-App Ad'
            })
        details = details_list
    
    return {
        'check_name': 'Facebook Pixel Tracking',
        'status': status,
        'message': f'{count} out of {total} non-app ads missing pixel tracking ({percentage}%)',
        'details': details,
        'count': count,
        'total': total,
        'percentage': percentage,
        'threshold': '< 30%',
        'recommendation': 'Install Facebook Pixel to track conversions and optimize ad delivery'
    }


def check_tracking_coverage(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check overall tracking coverage (URL tags OR pixel).
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'Overall Tracking Coverage',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    # Ads without any tracking (no URL tags AND no pixel)
    ads_without_tracking = ads_df[
        ads_df['url_tags'].apply(is_empty_value) & 
        ads_df['fb_pixel'].apply(is_empty_value)
    ]
    
    count = len(ads_without_tracking)
    total = len(ads_df)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count == 0 else 'WARNING' if count < total * 0.1 else 'FAIL'
    
    # Enhanced details
    details = None
    if count > 0:
        details_list = []
        for _, row in ads_without_tracking.iterrows():
            details_list.append({
                'Campaign': row.get('campaign_name', 'N/A'),
                'Adset': row.get('adset_name', 'N/A'),
                'Ad Name': row.get('ad_name', 'N/A'),
                'Ad ID': row.get('ad_id', 'N/A'),
                'URL Tags': 'Missing',
                'FB Pixel': 'Missing',
                'Impact': 'Critical - No tracking available'
            })
        details = details_list
    
    return {
        'check_name': 'Overall Tracking Coverage',
        'status': status,
        'message': f'{count} out of {total} ads have NO tracking at all ({percentage}%)',
        'details': details,
        'count': count,
        'total': total,
        'percentage': percentage,
        'threshold': '< 10%',
        'recommendation': 'Every ad should have at least URL tags or pixel tracking configured'
    }


def run_all_tracking_checks(ads_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Run all tracking-related health checks.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        List of check result dictionaries
    """
    return [
        check_url_tags_presence(ads_df),
        check_pixel_tracking(ads_df),
        check_tracking_coverage(ads_df)
    ]
