"""
Google Ads API Client initialization and management
"""
import streamlit as st
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from typing import Optional, Dict, Any, List
import pandas as pd


def get_google_ads_client() -> GoogleAdsClient:
    """
    Initialize and return Google Ads API client using credentials from secrets.
    """
    try:
        credentials = {
            "developer_token": st.secrets["google_ads"]["developer_token"],
            "client_id": st.secrets["google_ads"]["client_id"],
            "client_secret": st.secrets["google_ads"]["client_secret"],
            "refresh_token": st.secrets["google_ads"]["refresh_token"],
            "login_customer_id": st.secrets["google_ads"]["login_customer_id"],
            "use_proto_plus": st.secrets["google_ads"]["use_proto_plus"]
        }
        return GoogleAdsClient.load_from_dict(credentials)
    except Exception as e:
        error_msg = str(e)
        if "invalid_grant" in error_msg:
            st.error("❌ Authentication Error: Google Ads Refresh Token Expired")
            st.warning("""
                **Action Required:** Your Google Ads refresh token is invalid or expired.
                
                1. If using a Test Token, it expires every 7 days.
                2. Generate a new refresh token using the OAuth playground or script.
                3. Update `refresh_token` in `.streamlit/secrets.toml`.
            """)
        else:
            st.error(f"❌ Failed to connect to Google Ads API: {error_msg}")
        return None


def execute_query(client: GoogleAdsClient, customer_id: str, query: str) -> List[Any]:
    """
    Execute a GAQL query and return all rows.
    
    Args:
        client: GoogleAdsClient instance
        customer_id: Google Ads customer ID (without dashes)
        query: GAQL query string
    
    Returns:
        List of row objects from the query response
    """
    ga_service = client.get_service("GoogleAdsService")
    
    try:
        response = ga_service.search_stream(customer_id=customer_id, query=query)
        rows = []
        for batch in response:
            for row in batch.results:
                rows.append(row)
        return rows
    except GoogleAdsException as ex:
        st.error(f"Google Ads API Error: {ex.failure.errors[0].message}")
        return []


def get_accessible_customers(client: GoogleAdsClient) -> pd.DataFrame:
    """
    Fetch all accounts under the MCC account with currency information.
    Uses customer_client query for reliable account listing.
    
    Returns:
        DataFrame with columns: customer_id, descriptive_name, currency_code
    """
    ga_service = client.get_service("GoogleAdsService")
    
    try:
        query = """
            SELECT 
                customer_client.descriptive_name,
                customer_client.id,
                customer_client.currency_code,
                customer_client.manager,
                customer_client.status
            FROM customer_client
            WHERE customer_client.status = 'ENABLED'
            ORDER BY customer_client.descriptive_name
        """
        
        search_request = client.get_type("SearchGoogleAdsRequest")
        search_request.customer_id = st.secrets["google_ads"]["login_customer_id"]
        search_request.query = query
        
        accounts_data = []
        for row in ga_service.search(request=search_request):
            # Skip manager accounts - we only want client accounts
            if not row.customer_client.manager:
                accounts_data.append({
                    'customer_id': str(row.customer_client.id),
                    'currency_code': row.customer_client.currency_code,
                    'descriptive_name': row.customer_client.descriptive_name
                        if row.customer_client.descriptive_name
                        else f"Account {row.customer_client.id}"
                })
        
        return pd.DataFrame(accounts_data)
    
    except GoogleAdsException as ex:
        error_msg = ex.failure.errors[0].message
        if "User doesn't have permission" in error_msg:
            st.error("❌ Permission Error: Access Denied to Ad Account")
            st.warning(f"""
                **Diagnosis:** The authenticated Google User (Refresh Token) does not have access to the configured `login_customer_id` ({st.secrets["google_ads"]["login_customer_id"]}).
                
                **Possible Solutions:**
                1. **Check Access:** Ensure your email is added to the Ad Account/MCC with ID {st.secrets["google_ads"]["login_customer_id"]}.
                2. **Wrong ID:** If {st.secrets["google_ads"]["login_customer_id"]} is a Client Account (not Manager), try removing `login_customer_id` from secrets or setting it to the Manager ID if accessing via MCC.
                3. **New Token:** If you changed the Refresh Token, ensure it corresponds to an email that *has access*.
            """)
        else:
            st.error(f"Error fetching accounts: {error_msg}")
        return pd.DataFrame()


def get_active_campaigns(client: GoogleAdsClient, customer_id: str, campaign_type: Optional[str] = None) -> pd.DataFrame:
    """
    Get all active campaigns for a customer.
    
    Args:
        client: GoogleAdsClient instance
        customer_id: Customer ID
        campaign_type: Optional filter for campaign type (SEARCH, PERFORMANCE_MAX, MULTI_CHANNEL)
    
    Returns:
        DataFrame with campaign details
    """
    type_filter = ""
    if campaign_type:
        type_filter = f"AND campaign.advertising_channel_type = '{campaign_type}'"
    
    query = f"""
        SELECT 
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign.advertising_channel_sub_type,
            campaign.bidding_strategy_type,
            campaign_budget.amount_micros,
            campaign_budget.has_recommended_budget,
            campaign.geo_target_type_setting.positive_geo_target_type,
            campaign.geo_target_type_setting.negative_geo_target_type
        FROM campaign
        WHERE campaign.status = 'ENABLED'
        {type_filter}
    """
    
    rows = execute_query(client, customer_id, query)
    
    campaigns_data = []
    for row in rows:
        campaigns_data.append({
            "campaign_id": str(row.campaign.id),
            "campaign_name": row.campaign.name,
            "campaign_type": row.campaign.advertising_channel_type.name,
            "channel_sub_type": row.campaign.advertising_channel_sub_type.name if row.campaign.advertising_channel_sub_type else None,
            "bidding_strategy": row.campaign.bidding_strategy_type.name,
            "budget_micros": row.campaign_budget.amount_micros,
            "has_recommended_budget": row.campaign_budget.has_recommended_budget,
            "positive_geo_target_type": row.campaign.geo_target_type_setting.positive_geo_target_type.name,
            "negative_geo_target_type": row.campaign.geo_target_type_setting.negative_geo_target_type.name
        })
    
    return pd.DataFrame(campaigns_data)


def get_active_ad_groups(client: GoogleAdsClient, customer_id: str, campaign_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Get all active ad groups from active campaigns.
    
    Args:
        client: GoogleAdsClient instance
        customer_id: Customer ID
        campaign_ids: Optional list of campaign IDs to filter
    
    Returns:
        DataFrame with ad group details
    """
    campaign_filter = ""
    if campaign_ids:
        ids_str = ",".join(campaign_ids)
        campaign_filter = f"AND campaign.id IN ({ids_str})"
    
    query = f"""
        SELECT 
            ad_group.id,
            ad_group.name,
            ad_group.status,
            ad_group.type,
            campaign.id,
            campaign.name,
            campaign.advertising_channel_type
        FROM ad_group
        WHERE ad_group.status = 'ENABLED'
        AND campaign.status = 'ENABLED'
        {campaign_filter}
    """
    
    rows = execute_query(client, customer_id, query)
    
    ad_groups_data = []
    for row in rows:
        ad_groups_data.append({
            "ad_group_id": str(row.ad_group.id),
            "ad_group_name": row.ad_group.name,
            "ad_group_type": row.ad_group.type.name,
            "campaign_id": str(row.campaign.id),
            "campaign_name": row.campaign.name,
            "campaign_type": row.campaign.advertising_channel_type.name
        })
    
    return pd.DataFrame(ad_groups_data)
