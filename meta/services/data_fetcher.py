"""
Data Fetcher Service for Meta HealthCard
Handles fetching ads, adsets, and campaigns data from Meta Graph API
"""

import streamlit as st
import requests
import time
from typing import List, Dict, Tuple, Optional
from meta.config.constants import BASE_URL, REQUEST_TIMEOUT
from meta.services.meta_api_client import get_token_params


def get_ads_for_account(account_id: str, access_token: str, date_preset: str = "last_30d") -> List[Dict]:
    """
    Get ads data for a specific ad account with full creative details.
    Only returns ads that have impressions in the specified date range.
    
    Args:
        account_id: Meta ad account ID
        access_token: Access token for authentication
        date_preset: Date range preset (e.g., 'last_7d', 'last_30d')
    
    Returns:
        List of ad dictionaries with nested creative, campaign, and adset data
    """
    try:
        clean_account_id = account_id if account_id.startswith('act_') else f"act_{account_id}"
        
        # First, get ad IDs with impressions in the date range
        insights_url = f"{BASE_URL}/{clean_account_id}/insights"
        insights_params = {
            'level': 'ad',
            'fields': 'ad_id,impressions',
            'date_preset': date_preset,
            'limit': 500,
            'access_token': access_token
        }
        
        ad_ids_with_impressions = set()
        
        while insights_url:
            response = requests.get(insights_url, params=insights_params, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                for row in data.get('data', []):
                    impressions = int(row.get('impressions', 0))
                    if impressions > 0:
                        ad_ids_with_impressions.add(row.get('ad_id'))
                insights_url = data.get('paging', {}).get('next')
                insights_params = {}
            else:
                break
        
        if not ad_ids_with_impressions:
            return []
        
        # Now fetch full ad details for ads with impressions
        url = f"{BASE_URL}/{clean_account_id}/ads"
        
        params = {
            'fields': 'id,name,effective_status,creative_asset_groups_spec,adset{id,name,effective_status,promoted_object},campaign{id,name,effective_status},tracking_specs{fb_pixel,application},creative{effective_object_story_id,product_set_id,url_tags,asset_feed_spec{titles{text},bodies{text},descriptions{text},images{hash},videos{video_id},call_to_action_types,ad_formats},object_story_spec{link_data{message,name,description,link,call_to_action{type},child_attachments{link,name,description,call_to_action{type}}},video_data{title,message,video_id,call_to_action{type}}}}',
            'limit': 100,
            'access_token': access_token,
            'filtering': '[{"field":"effective_status","operator":"IN","value":["ACTIVE"]}]'
        }
        
        all_ads = []
        
        while url:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                all_ads.extend(data.get('data', []))
                url = data.get('paging', {}).get('next')
                params = {}
            else:
                break
        
        # Filter to only ads with impressions in the date range
        filtered_ads = [ad for ad in all_ads if ad.get('id') in ad_ids_with_impressions]
        
        return filtered_ads
    
    except Exception as e:
        st.error(f"Error fetching ads: {e}")
        return []


def get_adsets_for_account(account_id: str, access_token: str, date_preset: str = "last_30d") -> List[Dict]:
    """
    Get adsets data for a specific ad account with targeting details.
    Only returns adsets that have impressions in the specified date range.
    
    Args:
        account_id: Meta ad account ID
        access_token: Access token for authentication
        date_preset: Date range preset (e.g., 'last_7d', 'last_30d')
    
    Returns:
        List of adset dictionaries with targeting and campaign data
    """
    try:
        clean_account_id = account_id if account_id.startswith('act_') else f"act_{account_id}"
        
        # First, get adset IDs with impressions in the date range
        insights_url = f"{BASE_URL}/{clean_account_id}/insights"
        insights_params = {
            'level': 'adset',
            'fields': 'adset_id,impressions',
            'date_preset': date_preset,
            'limit': 500,
            'access_token': access_token
        }
        
        adset_ids_with_impressions = set()
        
        while insights_url:
            response = requests.get(insights_url, params=insights_params, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                for row in data.get('data', []):
                    impressions = int(row.get('impressions', 0))
                    if impressions > 0:
                        adset_ids_with_impressions.add(row.get('adset_id'))
                insights_url = data.get('paging', {}).get('next')
                insights_params = {}
            else:
                break
        
        if not adset_ids_with_impressions:
            return []
        
        # Now fetch full adset details
        url = f"{BASE_URL}/{clean_account_id}/adsets"
        
        params = {
            'fields': 'id,name,effective_status,campaign{id,name,effective_status},optimization_goal,targeting{excluded_custom_audiences{name},custom_audiences{name},publisher_platforms,targeting_automation{advantage_audience},flexible_spec}',
            'limit': 500,
            'access_token': access_token,
            'filtering': '[{"field":"effective_status","operator":"IN","value":["ACTIVE"]}]'
        }
        
        all_adsets = []
        
        while url:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                all_adsets.extend(data.get('data', []))
                url = data.get('paging', {}).get('next')
                params = {}
            else:
                break
        
        # Filter to only adsets with impressions in the date range
        filtered_adsets = [adset for adset in all_adsets if adset.get('id') in adset_ids_with_impressions]
        
        return filtered_adsets
    
    except Exception as e:
        st.error(f"Error fetching adsets: {e}")
        return []


def get_campaigns_for_account(account_id: str, include_paused: bool = False) -> List[Dict]:
    """
    Get campaigns data for a specific ad account.
    
    Args:
        account_id: Meta ad account ID
        include_paused: If True, include paused campaigns
    
    Returns:
        List of campaign dictionaries
    """
    try:
        clean_account_id = account_id if account_id.startswith('act_') else f"act_{account_id}"
        url = f"{BASE_URL}/{clean_account_id}/campaigns"
        
        params = {
            'fields': 'id,name,status,objective,buying_type,special_ad_categories',
            'limit': 1000
        }
        params.update(get_token_params(0))
        
        all_campaigns = []
        
        while url:
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                for campaign in data.get('data', []):
                    if include_paused or campaign.get('status') != 'PAUSED':
                        all_campaigns.append(campaign)
                
                url = data.get('paging', {}).get('next')
                params = {}
            else:
                break
            
            time.sleep(0.5)
        
        return all_campaigns
    
    except Exception as e:
        st.error(f"Error fetching campaigns: {e}")
        return []


@st.cache_data(ttl=1800)
def get_campaigns_adsets_ads(account_id: str, include_paused: bool = False) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Get all campaigns, ad sets, and ads for an account.
    Cached for 30 minutes to reduce API calls.
    
    Args:
        account_id: Meta ad account ID
        include_paused: If True, include paused entities
    
    Returns:
        Tuple of (campaigns_list, adsets_list, ads_list)
    """
    try:
        campaigns_list, adsets_list, ads_list = [], [], []
        campaign_status_map, adset_status_map = {}, {}
        
        # Fetch campaigns
        url = f"{BASE_URL}/{account_id}/campaigns"
        params = {'fields': 'id,name,status', 'limit': 1000}
        params.update(get_token_params(0))
        
        while url:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                break
            
            data = response.json()
            for c in data.get('data', []):
                campaign_status = c.get('status', 'UNKNOWN')
                campaign_status_map[c['id']] = campaign_status
                
                if include_paused or campaign_status != 'PAUSED':
                    campaigns_list.append({
                        'id': c['id'],
                        'name': c['name'],
                        'type': 'campaign',
                        'status': campaign_status
                    })
            
            url = data.get('paging', {}).get('next')
            params = {}
            time.sleep(1)
        
        # Fetch adsets
        url = f"{BASE_URL}/{account_id}/adsets"
        params = {'fields': 'id,name,status,campaign_id', 'limit': 1000}
        params.update(get_token_params(1))
        
        while url:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                break
            
            data = response.json()
            for a in data.get('data', []):
                adset_status = a.get('status', 'UNKNOWN')
                campaign_id = a.get('campaign_id')
                adset_status_map[a['id']] = adset_status
                campaign_status = campaign_status_map.get(campaign_id, 'UNKNOWN')
                
                is_adset_active = (adset_status != 'PAUSED' and campaign_status != 'PAUSED')
                
                if include_paused or is_adset_active:
                    adsets_list.append({
                        'id': a['id'],
                        'name': a['name'],
                        'type': 'adset',
                        'campaign_id': campaign_id,
                        'status': adset_status if is_adset_active else 'PAUSED'
                    })
            
            url = data.get('paging', {}).get('next')
            params = {}
            time.sleep(1)
        
        # Fetch ads
        url = f"{BASE_URL}/{account_id}/ads"
        params = {'fields': 'id,name,status,adset_id', 'limit': 1000}
        params.update(get_token_params(2))
        
        while url:
            response = requests.get(url, params=params, timeout=30)
            if response.status_code != 200:
                break
            
            data = response.json()
            for ad in data.get('data', []):
                ad_status = ad.get('status', 'UNKNOWN')
                adset_id = ad.get('adset_id')
                adset_status = adset_status_map.get(adset_id, 'UNKNOWN')
                
                campaign_id = next((a['campaign_id'] for a in adsets_list if a['id'] == adset_id), None)
                campaign_status = campaign_status_map.get(campaign_id, 'UNKNOWN') if campaign_id else 'UNKNOWN'
                
                is_ad_active = (ad_status != 'PAUSED' and adset_status != 'PAUSED' and campaign_status != 'PAUSED')
                
                if include_paused or is_ad_active:
                    ads_list.append({
                        'id': ad['id'],
                        'name': ad['name'],
                        'type': 'ad',
                        'adset_id': adset_id,
                        'status': ad_status if is_ad_active else 'PAUSED'
                    })
            
            url = data.get('paging', {}).get('next')
            params = {}
            time.sleep(1)
        
        return campaigns_list, adsets_list, ads_list
    
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return [], [], []


def get_account_insights(
    account_id: str,
    date_preset: str = 'last_30d',
    fields: Optional[List[str]] = None
) -> Dict:
    """
    Get account-level insights/metrics.
    
    Args:
        account_id: Meta ad account ID
        date_preset: Date range preset (e.g., 'last_30d', 'last_7d')
        fields: List of metric fields to fetch
    
    Returns:
        Dictionary of insights data
    """
    try:
        if fields is None:
            fields = ['spend', 'impressions', 'clicks', 'reach', 'frequency', 'ctr', 'cpc', 'cpm']
        
        clean_account_id = account_id if account_id.startswith('act_') else f"act_{account_id}"
        url = f"{BASE_URL}/{clean_account_id}/insights"
        
        params = {
            'date_preset': date_preset,
            'fields': ','.join(fields),
            'level': 'account'
        }
        params.update(get_token_params(0))
        
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                return data['data'][0]
        
        return {}
    
    except Exception as e:
        st.error(f"Error fetching account insights: {e}")
        return {}
