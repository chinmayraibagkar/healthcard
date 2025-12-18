"""
Creative Health Checks for Meta Ads
Validates creative assets including headlines, descriptions, and copy
"""

import pandas as pd
from typing import Dict, List, Any
from meta.utils.data_processing import is_empty_value, count_pipe_separated_values, has_child_attachments, is_catalogue_ad, is_boosted_post_ad
from meta.config.constants import THRESHOLDS


def check_headline_count(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if ads have sufficient headline variations.
    Meta best practice: At least 3-5 headlines for better performance.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'Headline Variations',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    # Exclude carousel, catalogue, and boosted post ads (they have dynamic/fixed creative)
    is_carousel = ads_df.apply(has_child_attachments, axis=1)
    is_catalogue = ads_df.apply(is_catalogue_ad, axis=1)
    is_boosted = ads_df.apply(is_boosted_post_ad, axis=1)
    standard_ads = ads_df[~is_carousel & ~is_catalogue & ~is_boosted].copy()
    
    if standard_ads.empty:
        return {
            'check_name': 'Headline Variations',
            'status': 'INFO',
            'message': 'No standard ads to check (all are carousel/catalogue/boosted)',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    # Calculate headline counts - consider both asset feed and story-based ads
    def count_headlines(row):
        # First try asset_feed_titles (DCO/dynamic ads)
        asset_count = count_pipe_separated_values(row.get('asset_feed_titles', 'NA'))
        if asset_count > 0:
            return asset_count
        
        # For story-based ads, check story_link_name and story_video_title
        story_headline = 0
        story_name = row.get('story_link_name', 'NA')
        video_title = row.get('story_video_title', 'NA')
        
        if not is_empty_value(story_name):
            story_headline += 1
        if not is_empty_value(video_title):
            story_headline += 1
            
        return story_headline
    
    standard_ads['headline_count'] = standard_ads.apply(count_headlines, axis=1)
    
    min_headlines = THRESHOLDS['min_headline_count']
    ads_insufficient = standard_ads[standard_ads['headline_count'] < min_headlines]
    
    count = len(ads_insufficient)
    total = len(standard_ads)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count == 0 else 'WARNING' if count < total * 0.3 else 'FAIL'
    
    details_df = ads_insufficient[['campaign_name', 'adset_name', 'ad_name', 'ad_id', 'headline_count']].copy()
    
    return {
        'check_name': 'Headline Variations',
        'status': status,
        'message': f'{count} out of {total} ads have fewer than {min_headlines} headlines ({percentage}%)',
        'details': details_df.to_dict('records') if count > 0 else None,
        'count': count,
        'total': total,
        'percentage': percentage,
        'threshold': f'>= {min_headlines} headlines',
        'recommendation': f'Add at least {min_headlines} headline variations to allow Meta to optimize performance'
    }


def check_primary_text_count(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if ads have sufficient primary text variations.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'Primary Text Variations',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    # Exclude carousel, catalogue, and boosted post ads
    is_carousel = ads_df.apply(has_child_attachments, axis=1)
    is_catalogue = ads_df.apply(is_catalogue_ad, axis=1)
    is_boosted = ads_df.apply(is_boosted_post_ad, axis=1)
    standard_ads = ads_df[~is_carousel & ~is_catalogue & ~is_boosted].copy()
    
    if standard_ads.empty:
        return {
            'check_name': 'Primary Text Variations',
            'status': 'INFO',
            'message': 'No standard ads to check (all are carousel/catalogue/boosted)',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    # Calculate primary text counts - consider both asset feed and story-based ads
    def count_primary_text(row):
        # First try asset_feed_bodies
        asset_count = count_pipe_separated_values(row.get('asset_feed_bodies', 'NA'))
        if asset_count > 0:
            return asset_count
        
        # For story-based ads, check story_link_message and story_video_message
        story_text = 0
        link_message = row.get('story_link_message', 'NA')
        video_message = row.get('story_video_message', 'NA')
        
        if not is_empty_value(link_message):
            story_text += 1
        if not is_empty_value(video_message):
            story_text += 1
            
        return story_text
    
    standard_ads['primary_text_count'] = standard_ads.apply(count_primary_text, axis=1)
    
    min_texts = THRESHOLDS['min_primary_text_count']
    ads_insufficient = standard_ads[standard_ads['primary_text_count'] < min_texts]
    
    count = len(ads_insufficient)
    total = len(standard_ads)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count == 0 else 'WARNING' if count < total * 0.3 else 'FAIL'
    
    details_df = ads_insufficient[['campaign_name', 'adset_name', 'ad_name', 'ad_id', 'primary_text_count']].copy()
    
    return {
        'check_name': 'Primary Text Variations',
        'status': status,
        'message': f'{count} out of {total} ads have fewer than {min_texts} primary texts ({percentage}%)',
        'details': details_df.to_dict('records') if count > 0 else None,
        'count': count,
        'total': total,
        'percentage': percentage,
        'threshold': f'>= {min_texts} primary texts',
        'recommendation': f'Add at least {min_texts} primary text variations for optimal performance'
    }


def check_description_count(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if ads have sufficient description variations.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'Description Variations',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    # Exclude carousel, catalogue, and boosted post ads
    is_carousel = ads_df.apply(has_child_attachments, axis=1)
    is_catalogue = ads_df.apply(is_catalogue_ad, axis=1)
    is_boosted = ads_df.apply(is_boosted_post_ad, axis=1)
    standard_ads = ads_df[~is_carousel & ~is_catalogue & ~is_boosted].copy()
    
    if standard_ads.empty:
        return {
            'check_name': 'Description Variations',
            'status': 'INFO',
            'message': 'No standard ads to check (all are carousel/catalogue/boosted)',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    # Calculate description counts - consider both asset feed and story-based ads
    def count_descriptions(row):
        # First try asset_feed_descriptions
        asset_count = count_pipe_separated_values(row.get('asset_feed_descriptions', 'NA'))
        if asset_count > 0:
            return asset_count
        
        # For story-based ads, check story_link_description
        story_desc = 0
        link_desc = row.get('story_link_description', 'NA')
        
        if not is_empty_value(link_desc):
            story_desc += 1
            
        return story_desc
    
    standard_ads['description_count'] = standard_ads.apply(count_descriptions, axis=1)
    
    min_descriptions = THRESHOLDS['min_description_count']
    ads_insufficient = standard_ads[standard_ads['description_count'] < min_descriptions]
    
    count = len(ads_insufficient)
    total = len(standard_ads)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count == 0 else 'WARNING' if count < total * 0.4 else 'FAIL'
    
    details_df = ads_insufficient[['campaign_name', 'adset_name', 'ad_name', 'ad_id', 'description_count']].copy()
    
    return {
        'check_name': 'Description Variations',
        'status': status,
        'message': f'{count} out of {total} ads have fewer than {min_descriptions} descriptions ({percentage}%)',
        'details': details_df.to_dict('records') if count > 0 else None,
        'count': count,
        'total': total,
        'percentage': percentage,
        'threshold': f'>= {min_descriptions} descriptions',
        'recommendation': f'Add at least {min_descriptions} description variations to enhance ad relevance'
    }


def check_missing_copy_elements(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check for ads missing critical copy elements (headline, body, or description).
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'Missing Copy Elements',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    ads_missing_copy = ads_df[
        ads_df['asset_feed_titles'].apply(is_empty_value) |
        ads_df['asset_feed_bodies'].apply(is_empty_value)
    ]
    
    count = len(ads_missing_copy)
    total = len(ads_df)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count == 0 else 'FAIL'
    
    return {
        'check_name': 'Missing Copy Elements',
        'status': status,
        'message': f'{count} out of {total} ads missing headlines or primary text ({percentage}%)',
        'details': ads_missing_copy[['campaign_name', 'adset_name', 'ad_name', 'ad_id']].to_dict('records') if count > 0 else None,
        'count': count,
        'total': total,
        'percentage': percentage,
        'threshold': '0%',
        'recommendation': 'All ads should have both headlines and primary text'
    }


def check_cta_presence(ads_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if ads have call-to-action (CTA) configured.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        Dictionary with check results
    """
    if ads_df.empty:
        return {
            'check_name': 'Call-to-Action Presence',
            'status': 'INFO',
            'message': 'No ads to check',
            'details': None,
            'count': 0,
            'total': 0,
            'percentage': 0
        }
    
    ads_without_cta = ads_df[
        ads_df['asset_feed_call_to_action_types'].apply(is_empty_value) &
        ads_df['story_link_call_to_action'].apply(is_empty_value) &
        ads_df['story_video_call_to_action'].apply(is_empty_value)
    ]
    
    count = len(ads_without_cta)
    total = len(ads_df)
    percentage = round((count / total) * 100, 2) if total > 0 else 0
    
    status = 'PASS' if count == 0 else 'WARNING' if count < total * 0.2 else 'FAIL'
    
    return {
        'check_name': 'Call-to-Action Presence',
        'status': status,
        'message': f'{count} out of {total} ads missing call-to-action ({percentage}%)',
        'details': ads_without_cta[['campaign_name', 'adset_name', 'ad_name', 'ad_id']].to_dict('records') if count > 0 else None,
        'count': count,
        'total': total,
        'percentage': percentage,
        'threshold': '< 20%',
        'recommendation': 'Add clear call-to-action buttons to drive user engagement'
    }


def run_all_creative_checks(ads_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Run all creative-related health checks.
    
    Args:
        ads_df: DataFrame with flattened ad data
    
    Returns:
        List of check result dictionaries
    """
    return [
        check_headline_count(ads_df),
        check_primary_text_count(ads_df),
        check_description_count(ads_df),
        check_missing_copy_elements(ads_df),
        check_cta_presence(ads_df)
    ]
