import streamlit as st
import pandas as pd
from google.ads.googleads.client import GoogleAdsClient
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import traceback
import pandas as pd
import plotly.express as px
import numpy as np
import re
from datetime import datetime, timedelta
import pandas as pd
from enum import Enum


# Function to update Google Sheet
def update_google_sheet(dataframe, sheet_id, worksheet_title):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("sheetsapi.json", scope)
        client = gspread.authorize(creds)
        st.success("Google Sheets credentials loaded successfully.")
        
        # Logging the sheet ID and worksheet title
        st.write(f"Attempting to open Google Sheet with ID: {sheet_id} and Worksheet: {worksheet_title}")

        # Open the Google Sheet using its ID
        sheet = client.open_by_key(sheet_id)

        # Open the specific worksheet by title
        worksheet = sheet.worksheet(worksheet_title)
        st.success(f"Opened the worksheet: {worksheet_title}")

        # Handle NaN values in the DataFrame
        dataframe = dataframe.fillna('')  # Replace NaN with empty string

        # Convert DataFrame to list of lists
        data = [dataframe.columns.values.tolist()] + dataframe.values.tolist()

        # Clear existing data
        worksheet.clear()

        # Update worksheet with new data
        worksheet.update("A1", data)
        st.success("Worksheet updated successfully.")
    except gspread.SpreadsheetNotFound:
        st.error(f"Spreadsheet not found with ID: {sheet_id}. Please check the sheet ID and service account permissions.")
    except gspread.WorksheetNotFound:
        st.error(f"Worksheet not found with title: {worksheet_title}. Please check the worksheet title.")
    except gspread.GSpreadException as e:
        st.error(f"GSpreadException: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.error(traceback.format_exc())


def get_google_ads_client(mycred):
    google_ads_client = GoogleAdsClient.load_from_storage(mycred)
    return google_ads_client


# Function to fetch Google Ads data
def get_kw_data(client, customer_id, start_date, end_date):
    ga_service = client.get_service("GoogleAdsService", version="v17")

    # Constructing the query
    query = f"""
    SELECT
        campaign.name,
        ad_group.name,
        ad_group_criterion.keyword.text,
        ad_group_criterion.keyword.match_type,
        metrics.impressions,
        metrics.cost_micros,
        metrics.historical_quality_score,
        ad_group_criterion.status,
        ad_group_criterion.location.geo_target_constant,
        campaign.labels
    FROM
        keyword_view
    WHERE
        segments.date BETWEEN '{start_date}' AND '{end_date}' AND campaign.status = 'ENABLED' AND ad_group.status = 'ENABLED' AND ad_group_criterion.status = 'ENABLED' 
        AND ad_group_criterion.negative != TRUE AND campaign.advertising_channel_type = 'SEARCH'
    """

    response = ga_service.search_stream(customer_id=customer_id, query=query)
    
    data = []
    for batch in response:
        for row in batch.results:
            data.append({
                "Campaign Name": row.campaign.name if hasattr(row.campaign, 'name') else 'NA',
                "Ad Group": row.ad_group.name if hasattr(row.ad_group, 'name') else 'NA',
                "Keyword Text": row.ad_group_criterion.keyword.text if hasattr(row.ad_group_criterion.keyword, 'text') else 'NA',
                "Match Type": row.ad_group_criterion.keyword.match_type.name if hasattr(row.ad_group_criterion.keyword, 'match_type') else 'NA',
                "Impressions": row.metrics.impressions if hasattr(row.metrics, 'impressions') else 'NA',
                "Cost": row.metrics.cost_micros / 1e6 if hasattr(row.metrics, 'cost_micros') else 'NA', # Converting micros to standard currency unit
                "Quality Score": row.metrics.historical_quality_score if hasattr(row.metrics, 'historical_quality_score') else 'NA',
                "Status": row.ad_group_criterion.status if hasattr(row.ad_group_criterion, 'status') else 'NA',
                "Labels": row.campaign.labels if hasattr(row.campaign, 'labels') else 'NA',
            })
    
    return pd.DataFrame(data)


# Function to fetch ad level data
def get_ad_data(client, customer_id, start_date, end_date):
    ga_service = client.get_service("GoogleAdsService", version="v17")

    # Constructing the query
    query = f"""
    SELECT
        campaign.name,
        ad_group.name,
        ad_group_ad.ad.responsive_search_ad.headlines,
        ad_group_ad.ad.responsive_search_ad.descriptions,
        metrics.impressions,
        metrics.clicks,
        metrics.cost_micros,
        campaign.advertising_channel_type,
        campaign.labels,
        ad_group_ad.ad_strength
    FROM
        ad_group_ad
    WHERE
        segments.date BETWEEN '{start_date}' AND '{end_date}' AND campaign.status = 'ENABLED' AND ad_group.status = 'ENABLED' 
        AND ad_group_ad.status = 'ENABLED' AND campaign.advertising_channel_type = 'SEARCH'
    """

    response = ga_service.search_stream(customer_id=customer_id, query=query)
    
    data = []
    for batch in response:
        for row in batch.results:
            data.append({
                "Campaign": row.campaign.name if hasattr(row.ad_group, 'campaign') else 'NA',
                "Ad Group": row.ad_group.name if hasattr(row.ad_group, 'name') else 'NA',
                "Headlines": row.ad_group_ad.ad.responsive_search_ad.headlines if hasattr(row.ad_group_ad.ad.responsive_search_ad, 'headlines') else 'NA',
                "Descriptions": row.ad_group_ad.ad.responsive_search_ad.descriptions if hasattr(row.ad_group_ad.ad.responsive_search_ad, 'descriptions') else 'NA',
                "Impressions": row.metrics.impressions if hasattr(row.metrics, 'impressions') else 'NA',
                "Clicks": row.metrics.clicks if hasattr(row.metrics, 'clicks') else 'NA',
                "Cost": row.metrics.cost_micros / 1e6 if hasattr(row.metrics, 'cost_micros') else 'NA',  # Converting micros to standard currency unit
                "Campaign Type": row.campaign.advertising_channel_type if hasattr(row.campaign, 'advertising_channel_type') else 'NA',
                "Labels": row.campaign.labels if hasattr(row.campaign, 'labels') else 'NA',
                "Ad Strength": row.ad_group_ad.ad_strength if hasattr(row.ad_group_ad, 'ad_strength') else 'NA',
            })

    # map advertising channel type
    data = pd.DataFrame(data)
    data["Campaign Type"] = data["Campaign Type"].map(st.session_state.channel_type_map)
    return pd.DataFrame(data)


def extract_texts(data):
    # Regular expression to find all text entries
    pattern = r'text:\s*"([^"]+)"'
    # Find all matches and join them with a space
    texts = re.findall(pattern, data)
    return ' '.join(texts)


def get_pmax_data(client, customer_id, start_date, end_date):
    ga_service = client.get_service("GoogleAdsService", version="v17")

    # Constructing the query
    query = f"""
    SELECT
        campaign.name,
        asset_group.name,
        segments.ad_network_type,
        asset_group_listing_group_filter.case_value.product_item_id.value,
        metrics.cost_micros,
        metrics.impressions,
        campaign.advertising_channel_type,
        campaign.advertising_channel_sub_type
    FROM
        asset_group_product_group_view
    WHERE
        segments.date BETWEEN '{start_date}' AND '{end_date}' AND campaign.status = 'ENABLED' AND campaign.advertising_channel_type = 'PERFORMANCE_MAX'
    """

    response = ga_service.search_stream(customer_id=customer_id, query=query)
    
    data = []
    for batch in response:
        for row in batch.results:
            data.append({
                "Campaign Name": row.campaign.name if hasattr(row.campaign, 'name') else 'NA',
                "Asset Group Name": row.asset_group.name if hasattr(row.asset_group, 'name') else 'NA',
                "Ad Network Type": row.segments.ad_network_type.name if hasattr(row.segments, 'ad_network_type') else 'NA',
                "Product Item ID": row.asset_group_listing_group_filter.case_value.product_item_id.value if hasattr(row.asset_group_listing_group_filter.case_value.product_item_id, 'value') else 'NA',
                "Cost": row.metrics.cost_micros / 1e6 if hasattr(row.metrics, 'cost_micros') else 'NA',  # Converting micros to standard currency unit
                "Impressions": row.metrics.impressions if hasattr(row.metrics, 'impressions') else 'NA',
                "Advertising Channel Type": row.campaign.advertising_channel_type.name if hasattr(row.campaign, 'advertising_channel_type') else 'NA',
                "Advertising Channel Sub Type": row.campaign.advertising_channel_sub_type.name if hasattr(row.campaign, 'advertising_channel_sub_type') else 'NA',
            })
    
    return pd.DataFrame(data)


def get_nested_attr(obj, attr):
    """Recursively gets an attribute from a nested object.

    Args:
      obj: The object to retrieve the attribute from.
      attr: The attribute path as a string, with nested attributes separated by periods.

    Returns:
      The value of the nested attribute or None if it doesn't exist.
    """
    try:
        for part in attr.split('.'):
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        return None


def get_nested_attr(obj, attr):
    """Recursively gets an attribute from a nested object."""
    try:
        for part in attr.split('.'):
            obj = getattr(obj, part)
        return obj
    except AttributeError:
        return None


def serialize_changed_fields(changed_fields):
    """Converts the list of changed fields into a serializable string."""
    return ", ".join([f"{field['Field']}: {field.get('Old Value', 'N/A')} -> {field['New Value']}" for field in changed_fields])


def get_change_history(client, customer_id, start_date, end_date):
    """Gets specific details about changes in the given account within a date range."""
    googleads_service = client.get_service("GoogleAdsService", version="v17")

    # Ensure that start_date is within the last 30 days
    max_allowed_start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if start_date < max_allowed_start_date:
        print(f"Start date is too old. Adjusting to {max_allowed_start_date}.")
        start_date = max_allowed_start_date

    # Constructing the query
    query = f"""
    SELECT
        change_event.resource_name,
        change_event.change_date_time,
        change_event.change_resource_name,
        change_event.user_email,
        change_event.client_type,
        change_event.change_resource_type,
        change_event.old_resource,
        change_event.new_resource,
        change_event.resource_change_operation,
        change_event.changed_fields
    FROM
        change_event
    WHERE
        change_event.change_date_time BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY
        change_event.change_date_time DESC
    LIMIT 10000
    """

    response = googleads_service.search_stream(customer_id=customer_id, query=query)

    data = []

    for batch in response:
        for row in batch.results:
            event = row.change_event
            resource_type = event.change_resource_type.name
            operation_type = event.resource_change_operation.name

            if resource_type == "AD":
                old_resource = event.old_resource.ad
                new_resource = event.new_resource.ad
            elif resource_type == "AD_GROUP":
                old_resource = event.old_resource.ad_group
                new_resource = event.new_resource.ad_group
            elif resource_type == "AD_GROUP_AD":
                old_resource = event.old_resource.ad_group_ad
                new_resource = event.new_resource.ad_group_ad
            elif resource_type == "AD_GROUP_ASSET":
                old_resource = event.old_resource.ad_group_asset
                new_resource = event.new_resource.ad_group_asset
            elif resource_type == "AD_GROUP_CRITERION":
                old_resource = event.old_resource.ad_group_criterion
                new_resource = event.new_resource.ad_group_criterion
            elif resource_type == "AD_GROUP_BID_MODIFIER":
                old_resource = event.old_resource.ad_group_bid_modifier
                new_resource = event.new_resource.ad_group_bid_modifier
            elif resource_type == "AD_GROUP_FEED":
                old_resource = event.old_resource.ad_group_feed
                new_resource = event.new_resource.ad_group_feed
            elif resource_type == "ASSET":
                old_resource = event.old_resource.asset
                new_resource = event.new_resource.asset
            elif resource_type == "ASSET_SET":
                old_resource = event.old_resource.asset_set
                new_resource = event.new_resource.asset_set
            elif resource_type == "ASSET_SET_ASSET":
                old_resource = event.old_resource.asset_set_asset
                new_resource = event.new_resource.asset_set_asset
            elif resource_type == "CAMPAIGN":
                old_resource = event.old_resource.campaign
                new_resource = event.new_resource.campaign
            elif resource_type == "CAMPAIGN_ASSET":
                old_resource = event.old_resource.campaign_asset
                new_resource = event.new_resource.campaign_asset
            elif resource_type == "CAMPAIGN_ASSET_SET":
                old_resource = event.old_resource.campaign_asset_set
                new_resource = event.new_resource.campaign_asset_set
            elif resource_type == "CAMPAIGN_BUDGET":
                old_resource = event.old_resource.campaign_budget
                new_resource = event.new_resource.campaign_budget
            elif resource_type == "CAMPAIGN_CRITERION":
                old_resource = event.old_resource.campaign_criterion
                new_resource = event.new_resource.campaign_criterion
            elif resource_type == "CAMPAIGN_FEED":
                old_resource = event.old_resource.campaign_feed
                new_resource = event.new_resource.campaign_feed
            elif resource_type == "CUSTOMER_ASSET":
                old_resource = event.old_resource.customer_asset
                new_resource = event.new_resource.customer_asset
            elif resource_type == "FEED":
                old_resource = event.old_resource.feed
                new_resource = event.new_resource.feed
            elif resource_type == "FEED_ITEM":
                old_resource = event.old_resource.feed_item
                new_resource = event.new_resource.feed_item
            else:
                resource_name = "UNKNOWN"

            changed_fields = []
            if operation_type in ("UPDATE", "CREATE"):
                for changed_field in event.changed_fields.paths:
                    if changed_field == "type":
                        changed_field = "type_"

                    new_value = get_nested_attr(new_resource, changed_field)
                    if isinstance(new_value, Enum):
                        new_value = new_value.name

                    if operation_type == "CREATE":
                        changed_fields.append({
                            "Field": changed_field,
                            "New Value": new_value
                        })
                    else:
                        old_value = get_nested_attr(old_resource, changed_field)
                        if isinstance(old_value, Enum):
                            old_value = old_value.name

                        changed_fields.append({
                            "Field": changed_field,
                            "Old Value": old_value,
                            "New Value": new_value
                        })

            # Serialize changed fields to a string for display
            serialized_changed_fields = serialize_changed_fields(changed_fields)

            data.append({
                "Change Date Time": event.change_date_time,
                "User Email": event.user_email,
                "Client Type": event.client_type.name,
                "Resource Change Operation": operation_type,
                "Resource Type": resource_type,
                "Resource Name": event.change_resource_name,
                "Changed Fields": serialized_changed_fields
            })

    return pd.DataFrame(data)

# define function to plot pie chart
def plot_pie_chart(data, column, title, names, color):
    colors = ['#FF1493', '#4682B4', '#32CD32', '#FFD700', '#8A2BE2']  # Attractive colors for a black background
    fig = px.pie(data, values=column, names=names, title=title, color=color, hole=0.3)
    fig.update_traces(marker=dict(colors=colors))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='white'
    )
    st.plotly_chart(fig)


def get_UAC_data_asset_level(client, customer_id, start_date, end_date):
    ga_service = client.get_service("GoogleAdsService", version="v17")

    # Constructing the query
    query = f"""
    SELECT
        campaign.name, 
        ad_group.name,
        asset.name,
        asset.text_asset.text,
        asset.youtube_video_asset.youtube_video_title,
        asset.type,
        segments.ad_network_type,
        metrics.biddable_app_post_install_conversions,
        metrics.impressions,
        metrics.cost_micros
    FROM 
    ad_group_ad_asset_view
    WHERE 
        segments.date BETWEEN '{start_date}' AND '{end_date}' AND campaign.status = 'ENABLED' AND ad_group.status = 'ENABLED' AND campaign.advertising_channel_type = 'MULTI_CHANNEL'
    """

    response = ga_service.search_stream(customer_id=customer_id, query=query)
    
    data = []
    for batch in response:
        print(f"Batch: {batch}")
        for row in batch.results:
            data.append({
                "Campaign Name": row.campaign.name if hasattr(row.campaign, 'name') else 'NA',
                "Ad Group": row.ad_group.name if hasattr(row.ad_group, 'name') else 'NA',
                "Asset Name": row.asset.name if hasattr(row.asset, 'name') else 'NA',
                "Asset Text": row.asset.text_asset.text if hasattr(row.asset.text_asset, 'text') else 'NA',
                "Video Title": row.asset.youtube_video_asset.youtube_video_title if hasattr(row.asset.youtube_video_asset, 'youtube_video_title') else 'NA',
                "Asset Type": row.asset.type.name if hasattr(row.asset, 'type') else 'NA',
                "Ad Network Type": row.segments.ad_network_type.name if hasattr(row.segments, 'ad_network_type') else 'NA',
                "Impressions": row.metrics.impressions if hasattr(row.metrics, 'impressions') else 'NA',
                "Cost": round(row.metrics.cost_micros / 1e6) if hasattr(row.metrics, 'cost_micros') else 'NA',  # Rounding off cost to nearest integer
                "In-app-actions": row.metrics.biddable_app_post_install_conversions if hasattr(row.metrics, 'biddable_app_post_install_conversions') else 'NA',
            })
    
    return pd.DataFrame(data)

def get_UAC_data_network_level(client, customer_id, start_date, end_date):
    ga_service = client.get_service("GoogleAdsService", version="v17")

    # Constructing the query
    query = f"""
    SELECT
        campaign.name, 
        ad_group.name,
        segments.ad_network_type,
        metrics.cost_micros,
        campaign.status
    FROM 
    ad_group
    WHERE 
        segments.date BETWEEN '{start_date}' AND '{end_date}' AND campaign.status = 'ENABLED' AND ad_group.status = 'ENABLED' AND campaign.advertising_channel_type = 'MULTI_CHANNEL'
    """

    response = ga_service.search_stream(customer_id=customer_id, query=query)
    
    data = []
    for batch in response:
        for row in batch.results:
            data.append({
                "Campaign Name": row.campaign.name if hasattr(row.campaign, 'name') else 'NA',
                "Ad Group": row.ad_group.name if hasattr(row.ad_group, 'name') else 'NA',
                "Ad Network Type": row.segments.ad_network_type.name if hasattr(row.segments, 'ad_network_type') else 'NA',
                "Cost_t": round(row.metrics.cost_micros / 1e6) if hasattr(row.metrics, 'cost_micros') else 'NA',  # Converting micros to standard currency unit
            })
    
    return pd.DataFrame(data)
