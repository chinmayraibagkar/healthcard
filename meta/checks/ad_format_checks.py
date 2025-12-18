"""
Ad Format Health Checks for Meta Ads
Validates ad format distribution and best practices
"""

import pandas as pd
from typing import Dict, List, Any
from meta.utils.data_processing import is_empty_value, has_child_attachments


def determine_ad_type(row: pd.Series) -> str:
    """Determine ad type from row data"""
    asset_feed_ad_formats = row.get('asset_feed_ad_formats', 'NA')
    
    # Check asset feed ad formats first
    if not is_empty_value(asset_feed_ad_formats) and str(asset_feed_ad_formats).strip().upper() != 'AUTOMATIC_FORMAT':
        return str(asset_feed_ad_formats).strip()
    
    # Check for DCO (Dynamic Creative Optimization)
    if not is_empty_value(row.get('creative_asset_groups_spec')) and str(row.get('creative_asset_groups_spec')).strip().upper() != 'NA':
        return 'DCO'
    
    # Check for Carousel
    if has_child_attachments(row):
        return 'CAROUSEL'
    
    # Check for Image Ad
    if not is_empty_value(row.get('asset_feed_image_hashes')):
        return 'IMAGE'
    
    # Check for Video Ad
    if not is_empty_value(row.get('asset_feed_video_ids')) or not is_empty_value(row.get('story_video_id')):
        return 'VIDEO'
    
    return 'UNKNOWN'


def check_ad_format_distribution(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check distribution of ad formats.
    Healthy accounts should have diverse ad formats.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'Ad Format Distribution',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'distribution': {}
        }
    
    # Determine ad types
    ads_df['ad_type'] = ads_df.apply(determine_ad_type, axis=1)
    
    # Get distribution
    distribution = ads_df['ad_type'].value_counts().to_dict()
    total = len(ads_df)
    
    # Calculate percentages
    dist_pct = {k: round((v / total) * 100, 1) for k, v in distribution.items()}
    
    # Check diversity (should have at least 2 different formats)
    unique_formats = len(distribution)
    
    status = 'PASS' if unique_formats >= 2 else 'WARNING'
    
    message_parts = [f"{k}: {v} ({dist_pct[k]}%)" for k, v in distribution.items()]
    
    return {
        'check_name': 'Ad Format Distribution',
        'status': status,
        'message': f"{unique_formats} unique ad formats found: {', '.join(message_parts)}",
        'details': None,
        'distribution': dist_pct,
        'unique_formats': unique_formats,
        'total': total,
        'recommendation': 'Use diverse ad formats (Image, Video, Carousel, DCO) to reach different audiences effectively'
    }


def check_video_ad_presence(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if account is using video ads.
    Video ads typically perform better for engagement.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'Video Ad Usage',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'count': 0,
            'total': 0
        }
    
    video_ads = ads_df[
        ~ads_df['asset_feed_video_ids'].apply(is_empty_value) |
        ~ads_df['story_video_id'].apply(is_empty_value)
    ]
    
    count = len(video_ads)
    total = len(ads_df)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count > 0 else 'WARNING'
    
    return {
        'check_name': 'Video Ad Usage',
        'status': status,
        'message': f'{count} out of {total} ads use video ({percentage}%)',
        'details': None,
        'count': count,
        'total': total,
        'percentage': percentage,
        'recommendation': 'Consider adding video ads for better engagement and storytelling'
    }


def check_carousel_usage(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if account is using carousel ads.
    Carousels can showcase multiple products/features.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'Carousel Ad Usage',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'count': 0,
            'total': 0
        }
    
    carousel_ads = ads_df[ads_df.apply(has_child_attachments, axis=1)]
    
    count = len(carousel_ads)
    total = len(ads_df)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count > 0 else 'INFO'
    
    return {
        'check_name': 'Carousel Ad Usage',
        'status': status,
        'message': f'{count} out of {total} ads use carousel format ({percentage}%)',
        'details': None,
        'count': count,
        'total': total,
        'percentage': percentage,
        'recommendation': 'Use carousel ads to showcase multiple products or tell a story across cards'
    }


def check_dco_usage(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if account is using Dynamic Creative Optimization (DCO).
    DCO allows Meta to automatically test combinations.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'DCO (Dynamic Creative) Usage',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'count': 0,
            'total': 0
        }
    
    dco_ads = ads_df[
        ~ads_df['creative_asset_groups_spec'].apply(is_empty_value) &
        (ads_df['creative_asset_groups_spec'].str.upper() != 'NA')
    ]
    
    count = len(dco_ads)
    total = len(ads_df)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count > 0 else 'WARNING'
    
    return {
        'check_name': 'DCO (Dynamic Creative) Usage',
        'status': status,
        'message': f'{count} out of {total} ads use Dynamic Creative ({percentage}%)',
        'details': None,
        'count': count,
        'total': total,
        'percentage': percentage,
        'recommendation': 'Use Dynamic Creative to let Meta automatically test and optimize creative combinations'
    }


def run_all_ad_format_checks(ads_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Run all ad format-related health checks.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        List of check result dictionaries
    """
    return [
        check_ad_format_distribution(ads_df),
        check_video_ad_presence(ads_df),
        check_carousel_usage(ads_df),
        check_dco_usage(ads_df)
    ]
