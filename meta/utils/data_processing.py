"""
Data Processing Utilities for Meta HealthCard
Helper functions for data transformation and analysis
"""

import pandas as pd
import json
from typing import List, Any, Optional


def is_empty_value(value: Any) -> bool:
    """
    Check if a value is empty.
    Handles None, NaN, empty strings, and 'NA'/'NONE' values.
    """
    if pd.isna(value):
        return True
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == '' or value.strip().upper() in ['NA', 'NONE']
    return False


def count_pipe_separated_values(value: Any) -> int:
    """
    Count non-empty values separated by |
    Returns: Number of valid non-empty values
    """
    if is_empty_value(value):
        return 0
    
    if isinstance(value, str):
        values = [v.strip() for v in value.split('|')]
        return len([v for v in values if v and v.upper() not in ['NA', 'NONE']])
    
    return 0


def has_child_attachments(row: pd.Series) -> bool:
    """
    Check if any child attachments are present in the row.
    Used for carousel ads detection.
    """
    for i in range(1, 6):
        link_col = f'child_attachment_{i}_link'
        if link_col in row and not is_empty_value(row[link_col]):
            return True
    return False


def is_catalogue_ad(row: pd.Series) -> bool:
    """
    Check if ad is a catalogue ad (product catalog ad).
    Catalogue ads pull content dynamically from product catalogs and shouldn't be
    checked for static headline/text variations.
    
    Identified by having a product_set_id in the creative or adset's promoted_object.
    """
    product_set_id = row.get('product_set_id', 'NA')
    if pd.isna(product_set_id):
        return False
    product_set_str = str(product_set_id).strip().upper()
    return product_set_str != 'NA' and product_set_str != '' and product_set_str != 'NONE'


def is_boosted_post_ad(row: pd.Series) -> bool:
    """
    Check if ad is a boosted post or existing post used as an ad.
    These ads use existing page posts as creative, so they have fixed content
    and shouldn't be checked for headline/text variations.
    
    A true boosted post has:
    - effective_object_story_id (indicates using an existing post)
    - AND NO asset_feed_spec content (no uploaded titles/bodies/descriptions)
    
    Ads created in Ads Manager with custom creative will have asset_feed_spec
    even if they also have an effective_object_story_id.
    """
    story_id = row.get('effective_object_story_id', 'NA')
    
    # Check if has effective_object_story_id
    if pd.isna(story_id):
        return False
    story_str = str(story_id).strip().upper()
    has_story_id = story_str != 'NA' and story_str != '' and story_str != 'NONE'
    
    if not has_story_id:
        return False
    
    # Check if has asset_feed_spec content (uploaded creative)
    # If it has asset feed content, it's an Ads Manager ad, not a boosted post
    titles = row.get('asset_feed_titles', 'NA')
    bodies = row.get('asset_feed_bodies', 'NA')
    
    has_asset_titles = not is_empty_value(titles)
    has_asset_bodies = not is_empty_value(bodies)
    
    # True boosted post = has story ID but NO uploaded asset feed content
    return not (has_asset_titles or has_asset_bodies)


def join_unique(values: List[str]) -> str:
    """
    Join unique non-None values with pipe separator.
    Maintains order while removing duplicates.
    """
    seen = []
    for v in values:
        if v is None:
            continue
        v = str(v)
        if v not in seen:
            seen.append(v)
    return "|".join(seen)


def chunked(seq: List[Any], size: int) -> List[List[Any]]:
    """
    Split a sequence into chunks of specified size.
    Useful for batching API requests.
    """
    seq = list(seq)
    return [seq[i:i+size] for i in range(0, len(seq), size)]


def safe_json_loads(value: Any, default: Any = None) -> Any:
    """Safely parse JSON string, return default if parsing fails"""
    if is_empty_value(value):
        return default
    
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return default
    
    return value


def calculate_percentage(numerator: float, denominator: float, decimals: int = 2) -> float:
    """Calculate percentage safely, handling division by zero"""
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, decimals)


def extract_nested_value(data: dict, path: str, default: Any = None) -> Any:
    """
    Extract value from nested dictionary using dot notation path.
    Example: extract_nested_value(data, 'campaign.name', 'Unknown')
    """
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current


def flatten_ad_data(ads_data: List[dict]) -> pd.DataFrame:
    """
    Flatten the nested ad data into a structured DataFrame.
    Extracts campaign, adset, creative, and tracking information.
    """
    flattened_data = []
    
    for ad in ads_data:
        ad_info = {
            'ad_id': ad.get('id', 'NA'),
            'ad_name': ad.get('name', 'NA'),
            'ad_effective_status': ad.get('effective_status', 'NA')
        }
        
        # Extract adset information
        adset = ad.get('adset', {})
        ad_info.update({
            'adset_id': adset.get('id', 'NA'),
            'adset_name': adset.get('name', 'NA'),
            'adset_status': adset.get('effective_status', 'NA')
        })
        
        # Extract campaign information
        campaign = ad.get('campaign', {})
        ad_info.update({
            'campaign_id': campaign.get('id', 'NA'),
            'campaign_name': campaign.get('name', 'NA'),
            'campaign_status': campaign.get('effective_status', 'NA')
        })
        
        # Extract tracking specs
        tracking_specs_list = ad.get('tracking_specs', [])
        fb_pixels, applications = [], []
        
        for ts in tracking_specs_list:
            fb_pixels.extend(ts.get('fb_pixel', []))
            applications.extend(ts.get('application', []))
        
        ad_info.update({
            'fb_pixel': ', '.join(fb_pixels) if fb_pixels else 'NA',
            'application': ', '.join(applications) if applications else 'NA'
        })
        
        # Extract creative information
        creative = ad.get('creative', {})
        adset = ad.get('adset', {})
        promoted_object = adset.get('promoted_object', {})
        
        ad_info.update({
            'creative_id': creative.get('id', 'NA'),
            'url_tags': creative.get('url_tags', 'NA'),
            'creative_asset_groups_spec': str(ad.get('creative_asset_groups_spec', 'NA')),
            'product_set_id': creative.get('product_set_id', promoted_object.get('product_set_id', 'NA')),
            'effective_object_story_id': creative.get('effective_object_story_id', 'NA')
        })
        
        # Extract asset feed spec
        asset_feed_spec = creative.get('asset_feed_spec', {})
        if asset_feed_spec:
            titles = [t.get('text', '') for t in asset_feed_spec.get('titles', [])]
            bodies = [b.get('text', '') for b in asset_feed_spec.get('bodies', [])]
            descriptions = [d.get('text', '') for d in asset_feed_spec.get('descriptions', [])]
            images = [i.get('hash', '') for i in asset_feed_spec.get('images', [])]
            videos = [v.get('video_id', '') for v in asset_feed_spec.get('videos', [])]
            
            ad_info.update({
                'asset_feed_titles': ' | '.join([t for t in titles if t]) or 'NA',
                'asset_feed_bodies': ' | '.join([b for b in bodies if b]) or 'NA',
                'asset_feed_descriptions': ' | '.join([d for d in descriptions if d]) or 'NA',
                'asset_feed_image_hashes': ' | '.join([i for i in images if i]) or 'NA',
                'asset_feed_video_ids': ' | '.join([v for v in videos if v]) or 'NA',
                'asset_feed_call_to_action_types': ' | '.join(asset_feed_spec.get('call_to_action_types', [])) or 'NA',
                'asset_feed_ad_formats': ' | '.join(asset_feed_spec.get('ad_formats', [])) or 'NA'
            })
        else:
            ad_info.update({
                'asset_feed_titles': 'NA',
                'asset_feed_bodies': 'NA',
                'asset_feed_descriptions': 'NA',
                'asset_feed_image_hashes': 'NA',
                'asset_feed_video_ids': 'NA',
                'asset_feed_call_to_action_types': 'NA',
                'asset_feed_ad_formats': 'NA'
            })
        
        # Initialize story type fields
        ad_info.update({
            'story_type': 'NA',
            'story_link_message': 'NA',
            'story_link_name': 'NA',
            'story_link_description': 'NA',
            'story_link_url': 'NA',
            'story_link_call_to_action': 'NA',
            'story_video_title': 'NA',
            'story_video_message': 'NA',
            'story_video_id': 'NA',
            'story_video_call_to_action': 'NA'
        })
        
        # Initialize child attachments
        for i in range(1, 6):
            ad_info.update({
                f'child_attachment_{i}_link': 'NA',
                f'child_attachment_{i}_name': 'NA',
                f'child_attachment_{i}_description': 'NA',
                f'child_attachment_{i}_cta': 'NA'
            })
        
        # Extract object story spec
        object_story_spec = creative.get('object_story_spec', {})
        if object_story_spec:
            if 'video_data' in object_story_spec:
                vd = object_story_spec['video_data']
                ad_info.update({
                    'story_type': 'video',
                    'story_video_title': vd.get('title', 'NA'),
                    'story_video_message': vd.get('message', 'NA'),
                    'story_video_id': vd.get('video_id', 'NA'),
                    'story_video_call_to_action': vd.get('call_to_action', {}).get('type', 'NA')
                })
            
            elif 'link_data' in object_story_spec:
                ld = object_story_spec['link_data']
                ad_info.update({
                    'story_type': 'link',
                    'story_link_message': ld.get('message', 'NA'),
                    'story_link_name': ld.get('name', 'NA'),
                    'story_link_description': ld.get('description', 'NA'),
                    'story_link_url': ld.get('link', 'NA'),
                    'story_link_call_to_action': ld.get('call_to_action', {}).get('type', 'NA')
                })
                
                # Extract child attachments for carousel
                for i, att in enumerate(ld.get('child_attachments', [])[:5], 1):
                    ad_info.update({
                        f'child_attachment_{i}_link': att.get('link', 'NA'),
                        f'child_attachment_{i}_name': att.get('name', 'NA'),
                        f'child_attachment_{i}_description': att.get('description', 'NA'),
                        f'child_attachment_{i}_cta': att.get('call_to_action', {}).get('type', 'NA')
                    })
        
        flattened_data.append(ad_info)
    
    df = pd.DataFrame(flattened_data)
    
    # Filter to keep only truly active ads (ad, adset, AND campaign must be ACTIVE)
    if not df.empty and 'ad_effective_status' in df.columns:
        active_mask = (
            (df['ad_effective_status'] == 'ACTIVE') &
            (df['adset_status'] == 'ACTIVE') &
            (df['campaign_status'] == 'ACTIVE')
        )
        df = df[active_mask].reset_index(drop=True)
    
    return df


def flatten_adset_data(adsets_data: List[dict]) -> pd.DataFrame:
    """Flatten adset data into DataFrame"""
    flattened_data = []
    
    for adset in adsets_data:
        adset_info = {
            'adset_id': adset.get('id', 'NA'),
            'adset_name': adset.get('name', 'NA'),
            'adset_effective_status': adset.get('effective_status', 'NA'),
            'optimization_goal': adset.get('optimization_goal', 'NA')
        }
        
        # Extract campaign information
        campaign = adset.get('campaign', {})
        adset_info.update({
            'campaign_id': campaign.get('id', 'NA'),
            'campaign_name': campaign.get('name', 'NA'),
            'campaign_status': campaign.get('effective_status', 'NA')
        })
        
        # Extract targeting information
        targeting = adset.get('targeting', {})
        
        custom_audiences = [a.get('name', '') for a in targeting.get('custom_audiences', [])]
        adset_info['custom_audiences'] = ', '.join(custom_audiences) if custom_audiences else 'NA'
        
        excluded = [a.get('name', '') for a in targeting.get('excluded_custom_audiences', [])]
        adset_info['excluded_custom_audiences'] = ', '.join(excluded) if excluded else 'NA'
        
        platforms = targeting.get('publisher_platforms', [])
        adset_info['publisher_platforms'] = ', '.join(platforms) if platforms else 'NA'
        
        adset_info['advantage_audience'] = str(targeting.get('targeting_automation', {}).get('advantage_audience', 'NA'))
        
        flex_spec = targeting.get('flexible_spec', [])
        adset_info['flexible_spec'] = json.dumps(flex_spec, ensure_ascii=False) if flex_spec else 'NA'
        
        flattened_data.append(adset_info)
    
    df = pd.DataFrame(flattened_data)
    
    # Filter to keep only truly active adsets (adset AND campaign must be ACTIVE)
    if not df.empty and 'adset_effective_status' in df.columns:
        active_mask = (
            (df['adset_effective_status'] == 'ACTIVE') &
            (df['campaign_status'] == 'ACTIVE')
        )
        df = df[active_mask].reset_index(drop=True)
    
    return df
