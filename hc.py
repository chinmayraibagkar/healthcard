import pandas as pd
import numpy as np
from functions import *
import streamlit as st
import tempfile
import plotly.express as px

st.session_state.Account_Name = {
    "1-to-1 help": "3064238231",
    "Apna-Klab": "5179768580",
    "Boston lvy": "4182451167",
    "CFS": "1702864408",
    "City Mall": "7101386686",
    "Creditt": "2472364292",
    "Elevate": "4811436152",
    "FNP App Account": "7654170390",
    "FNP Brand": "7131559721",
    "FNP Generic": "1991620806",
    "Godrej Proffesional": "1069710737",
    "Keya Foods": "7656314899",
    "Medikabazzar": "1332183046",
    "Medikabazzar - MBARC": "7867734746",
    "Mesky": "1914289078",
    "Mygate": "8158102088",
    "Ozell Cooner Paints": "5197232531",
    "Peperfry": "6617270902",
    "Pepperfry App Account": "1688452376",
    "Pepperfry Furniture": "3577253261",
    "Pepperfry Main": "6617270902",
    "Pepperfry UAC": "2058916916",
    "Pepperfry YT New": "3827510607",
    "Porter India": "9680382253",
    "Porter India 2.0": "4840834180",
    "Porter UAE": "6231867854",
    "Rotimatic - US": "5741817215",
    "Saagah Mart": "4680093295",
    "Stahl Kitchens": "3994900785",
    "TC Global": "1519464043",
    "Tjori 2": "2989824180",
    "Torrins Anthem": "3016502090",
    "Virtualness": "2519200735",
    "Yangpoo": "5658536021"
}

st.session_state.channel_type_map = {
    0: "UNSPECIFIED",
    1: "UNKNOWN",
    2: "SEARCH",
    3: "DISPLAY",
    4: "SHOPPING",
    5: "HOTEL",
    6: "VIDEO",
    7: "MULTI_CHANNEL",
    8: "LOCAL",
    9: "SMART",
    10: "PERFORMANCE_MAX",
    11: "LOCAL_SERVICES",
    12: "DISCOVERY"
}

st.session_state.ad_strength_map = {
    7: "Excellent",
    2: "Pending",
    4: "Poor",
    5: "Average",
    6: "Good"
}

st.header("Healthcard")

# Create an account selector
selected_accounts = st.multiselect("Select Account Names", list(st.session_state.Account_Name.keys()))
date_range = st.date_input("Select Date Range", [pd.to_datetime("2024-06-01"), pd.to_datetime("2024-06-30")])
campaign_types_present = st.multiselect("Select Present Campaign Types", ["Search", "Pmax", "UAC"])
if 'Porter India' in selected_accounts:
    segment = st.selectbox("Select Segment", ["Bottom_7", "Spot", "P&M", "2W", "Pure Brand", "Courier"])
else:
    segment = None

st.sidebar.header("Google Ads Credentials")
st.sidebar.write("Upload your Google Ads credentials file here:")
st.sidebar.write("Note: This file will be active until the session ends.")

# Handle credentials upload
if 'mycred' not in st.session_state:
    credentials_file = st.sidebar.file_uploader("Upload Google Ads Credentials", type=["yaml"])
    if credentials_file is not None:
        st.session_state.mycred = credentials_file
else:
    st.sidebar.write("Credentials file already uploaded.")

# Fetch data logic
if 'fetch_data' not in st.session_state:    
    st.session_state.fetch_data = False

if st.button("Fetch Data"):
    if 'mycred' not in st.session_state or st.session_state.mycred is None:
        st.error("Please upload your Google Ads credentials file before fetching data.")
    else:
        st.session_state.fetch_data = True

if st.session_state.fetch_data:

    st.session_state.start_date = date_range[0].strftime("%Y-%m-%d")
    st.session_state.end_date = date_range[1].strftime("%Y-%m-%d")
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(st.session_state.mycred.getvalue())
        tmp.flush()  # Ensure the data is written
        client = get_google_ads_client(tmp.name)
    st.session_state.all_data = pd.DataFrame()

    for account in selected_accounts:
        def KW_data_analysis():
            st.session_state.kw_data = get_kw_data(client, st.session_state.Account_Name[account], st.session_state.start_date, st.session_state.end_date)
            st.session_state.kw_data['Labels'] = st.session_state.kw_data['Labels'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
            #st.dataframe(st.session_state.kw_data)

            # Filter-out data according to labels
            if segment == "2W":
                st.session_state.kw_data = st.session_state.kw_data[st.session_state.kw_data["Labels"].str.contains("customers/9680382253/labels/21974198167")]
            elif segment == "Spot":
                st.session_state.kw_data = st.session_state.kw_data[st.session_state.kw_data["Labels"].str.contains("customers/9680382253/labels/21995256971")]
            elif segment == "Bottom_7":
                st.session_state.kw_data = st.session_state.kw_data[st.session_state.kw_data["Labels"].str.contains("customers/9680382253/labels/21977071705")]
            elif segment == "P&M":
                st.session_state.kw_data = st.session_state.kw_data[st.session_state.kw_data["Labels"].str.contains("customers/9680382253/labels/21977073160")]
            elif segment == "Pure Brand":
                st.session_state.kw_data = st.session_state.kw_data[st.session_state.kw_data["Labels"].str.contains("customers/9680382253/labels/21995300594")]
            elif segment == "Courier":
                st.session_state.kw_data = st.session_state.kw_data[st.session_state.kw_data["Labels"].str.contains("customers/9680382253/labels/21977123539")]

            #get a list of duplicate KWs which have same keyword text and match type, but different ad group. Get campain name, ad group name, keyword text, match type.
            st.session_state.duplicate_kw = st.session_state.kw_data[st.session_state.kw_data.duplicated(subset=["Keyword Text", "Match Type", "Campaign Name"], keep=False)]
            st.session_state.duplicate_kw = st.session_state.duplicate_kw[["Campaign Name", "Ad Group", "Keyword Text", "Match Type"]]
            st.session_state.duplicate_kw.reset_index(drop=True, inplace=True)
            st.markdown(''':blue-background[**Duplicate Keywords**]''')
            st.dataframe(st.session_state.duplicate_kw)
            
            # Calculate weighted average of quality score for each ad group
            st.session_state.kw_data["Impressions"] = st.session_state.kw_data["Impressions"].astype(int)
            st.session_state.kw_data["Quality Score"] = st.session_state.kw_data["Quality Score"].astype(float)
            st.session_state.weighted_avg_quality_score = (st.session_state.kw_data.loc[st.session_state.kw_data["Quality Score"] != 0, "Impressions"] * st.session_state.kw_data.loc[st.session_state.kw_data["Quality Score"] != 0, "Quality Score"]).sum() / st.session_state.kw_data.loc[st.session_state.kw_data["Quality Score"] != 0, "Impressions"].sum()
            st.session_state.weighted_avg_quality_score = st.session_state.weighted_avg_quality_score.round(2)

            bg = ":orange-background"
            st.markdown(f":blue-background[**Weighted Average Quality Score of Account**] : {bg}[{st.session_state.weighted_avg_quality_score}]")

            # Weighted average quality scores for Campaigns containing Brand, Generic, and Competitor in campaign name
            st.session_state.brand_kw_data = st.session_state.kw_data[st.session_state.kw_data["Campaign Name"].str.contains("Brand", case=False)]
            st.session_state.generic_kw_data = st.session_state.kw_data[st.session_state.kw_data["Campaign Name"].str.contains("Generic", case=False)]
            st.session_state.competitor_kw_data = st.session_state.kw_data[st.session_state.kw_data["Campaign Name"].str.contains("Competitor", case=False)]

            st.session_state.brand_weighted_avg_quality_score = (st.session_state.brand_kw_data.loc[st.session_state.brand_kw_data["Quality Score"] != 0, "Impressions"] * st.session_state.brand_kw_data.loc[st.session_state.brand_kw_data["Quality Score"] != 0, "Quality Score"]).sum() / st.session_state.brand_kw_data.loc[st.session_state.brand_kw_data["Quality Score"] != 0, "Impressions"].sum()
            st.session_state.brand_weighted_avg_quality_score = st.session_state.brand_weighted_avg_quality_score.round(2)

            st.session_state.generic_weighted_avg_quality_score = (st.session_state.generic_kw_data.loc[st.session_state.generic_kw_data["Quality Score"] != 0, "Impressions"] * st.session_state.generic_kw_data.loc[st.session_state.generic_kw_data["Quality Score"] != 0, "Quality Score"]).sum() / st.session_state.generic_kw_data.loc[st.session_state.generic_kw_data["Quality Score"] != 0, "Impressions"].sum()
            st.session_state.generic_weighted_avg_quality_score = st.session_state.generic_weighted_avg_quality_score.round(2)

            st.session_state.competitor_weighted_avg_quality_score = (st.session_state.competitor_kw_data.loc[st.session_state.competitor_kw_data["Quality Score"] != 0, "Impressions"] * st.session_state.competitor_kw_data.loc[st.session_state.competitor_kw_data["Quality Score"] != 0, "Quality Score"]).sum() / st.session_state.competitor_kw_data.loc[st.session_state.competitor_kw_data["Quality Score"] != 0, "Impressions"].sum()
            st.session_state.competitor_weighted_avg_quality_score = st.session_state.competitor_weighted_avg_quality_score.round(2)

            st.markdown(f":blue-background[**Weighted Average Quality Score for Brand Campaigns**] : {bg}[{st.session_state.brand_weighted_avg_quality_score}]")
            st.markdown(f":blue-background[**Weighted Average Quality Score for Generic Campaigns**] : {bg}[{st.session_state.generic_weighted_avg_quality_score}]")
            st.markdown(f":blue-background[**Weighted Average Quality Score for Competitor Campaigns**] : {bg}[{st.session_state.competitor_weighted_avg_quality_score}]")

            # Weighted average quality score for each campaign
            st.session_state.campaign_level_weighted_avg_quality_score = st.session_state.kw_data.groupby("Campaign Name").apply(lambda x: (x["Impressions"] * x["Quality Score"]).sum() / x["Impressions"].sum()).reset_index()
            st.session_state.campaign_level_weighted_avg_quality_score.columns = ["Campaign Name", "Weighted Average Quality Score"]
            st.session_state.campaign_level_weighted_avg_quality_score["Weighted Average Quality Score"] = st.session_state.campaign_level_weighted_avg_quality_score["Weighted Average Quality Score"].round(2)
            st.session_state.campaign_level_weighted_avg_quality_score = st.session_state.campaign_level_weighted_avg_quality_score.sort_values(by="Weighted Average Quality Score", ascending=True)
            st.session_state.campaign_level_weighted_avg_quality_score.reset_index(drop=True, inplace=True)
            st.markdown(''':blue-background[**Weighted Average Quality Score for Campaigns**]''')
            st.dataframe(st.session_state.campaign_level_weighted_avg_quality_score) 

            # Days difference between start and end date
            days_diff = int((pd.to_datetime(st.session_state.end_date) - pd.to_datetime(st.session_state.start_date)).days)

            # Calculate the mean of all non-zero impressions
            mean_impressions = days_diff * 10
            if np.isnan(mean_impressions) or np.isinf(mean_impressions):
                st.write("Error: mean_impressions is NaN or Inf.")
                mean_impressions = 1.01
            if mean_impressions <= 1:
                mean_impressions = 1.01

            # Impressions bucket analysis
            st.session_state.kw_data["Impressions Bucket"] = np.where(st.session_state.kw_data["Impressions"] == 0, "0", np.where(st.session_state.kw_data["Impressions"] < 0.5*mean_impressions, "1 - avg", "> avg"))       
            st.session_state.kw_impr_count = st.session_state.kw_data.groupby("Impressions Bucket").agg({"Keyword Text" : "count"}).reset_index()
            st.session_state.kw_impr_count["Percentage"] = (st.session_state.kw_impr_count["Keyword Text"] / st.session_state.kw_impr_count["Keyword Text"].sum() * 100).round(2)
            st.session_state.kw_impr_count = st.session_state.kw_impr_count.rename(columns={"Keyword Text": "Keyword Count"})
            st.dataframe(st.session_state.kw_impr_count)

            # Download keywords with zero impressions
            st.session_state.zero_impr = st.session_state.kw_data[st.session_state.kw_data["Impressions"] == 0]
            st.download_button(
                label="Download KWs with ZERO Impressions",
                data=st.session_state.zero_impr.to_csv(index=False),
                file_name='KWs_with_zero_impressions.csv',
                mime='text/csv',
            )

            # Plot pie chart for impressions bucket
            plot_pie_chart(st.session_state.kw_impr_count, "Keyword Count", "Impressions of Keywords", "Impressions Bucket", "Keyword Count")

            # Quality Score bucket analysis
            st.session_state.kw_data["Quality Score Bucket"] = np.where(st.session_state.kw_data["Quality Score"] <= 6, "0-6", np.where(st.session_state.kw_data["Quality Score"] < 8, "6-8", "8-10"))
            st.session_state.kw_quality_score = st.session_state.kw_data.groupby("Quality Score Bucket").agg({"Keyword Text" : "count"}).reset_index()
            st.session_state.kw_quality_score["Percentage"] = (st.session_state.kw_quality_score["Keyword Text"] / st.session_state.kw_quality_score["Keyword Text"].sum() * 100).round(2)
            st.session_state.kw_quality_score = st.session_state.kw_quality_score.rename(columns={"Keyword Text": "Keyword Count"})
            st.dataframe(st.session_state.kw_quality_score)
            plot_pie_chart(st.session_state.kw_quality_score, "Keyword Count", "Quality Score of Keywords", "Quality Score Bucket", "Keyword Count")

            # Match Type analysis
            st.session_state.kw_mch_type = st.session_state.kw_data.groupby("Match Type").agg({
                "Impressions": np.sum,
                "Cost": np.sum,
            }).reset_index()

            st.session_state.kw_mch_type["Cost"] = st.session_state.kw_mch_type["Cost"].round().astype(int)
            st.session_state.kw_mch_type["Impressions Share"] = (st.session_state.kw_mch_type["Impressions"] / st.session_state.kw_mch_type["Impressions"].sum() * 100).round(2)
            st.session_state.kw_mch_type["Cost Share"] = (st.session_state.kw_mch_type["Cost"] / st.session_state.kw_mch_type["Cost"].sum() * 100).round(2)
            st.dataframe(st.session_state.kw_mch_type)

            col1, col2 = st.columns(2)
            with col1:
                plot_pie_chart(st.session_state.kw_mch_type, "Impressions", "Impressions Share by Match Type", "Match Type", "Impressions")
            with col2:
                plot_pie_chart(st.session_state.kw_mch_type, "Cost", "Cost Share by Match Type","Match Type", "Impressions")

        # Ads data analysis
        def ads_data_analysis():
            st.session_state.ad_data = get_ad_data(client, st.session_state.Account_Name[account], st.session_state.start_date, st.session_state.end_date)

            st.session_state.ad_data['Labels'] = st.session_state.ad_data['Labels'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))

            # Filter-out data accorfing to labels
            if segment == "2W":
                st.session_state.ad_data = st.session_state.ad_data[st.session_state.ad_data["Labels"].str.contains("customers/9680382253/labels/21974198167")]
            elif segment == "Spot":
                st.session_state.ad_data = st.session_state.ad_data[st.session_state.ad_data["Labels"].str.contains("customers/9680382253/labels/21995256971")]
            elif segment == "Bottom_7":
                st.session_state.ad_data = st.session_state.ad_data[st.session_state.ad_data["Labels"].str.contains("customers/9680382253/labels/21977071705")]
            elif segment == "P&M":
                st.session_state.ad_data = st.session_state.ad_data[st.session_state.ad_data["Labels"].str.contains("customers/9680382253/labels/21977073160")]
            elif segment == "Pure Brand":
                st.session_state.ad_data = st.session_state.ad_data[st.session_state.ad_data["Labels"].str.contains("customers/9680382253/labels/21995300594")]
            elif segment == "Courier":
                st.session_state.ad_data = st.session_state.ad_data[st.session_state.ad_data["Labels"].str.contains("customers/9680382253/labels/21977123539")]

            #map ad strength to ad strength name
            st.session_state.ad_data["Ad Strength"] = st.session_state.ad_data["Ad Strength"].map(st.session_state.ad_strength_map)

            # Extract texts from Headlines and Descriptions
            st.session_state.ad_data['Headlines'] = st.session_state.ad_data['Headlines'].fillna('').astype(str)
            st.session_state.ad_data['Descriptions'] = st.session_state.ad_data['Descriptions'].apply(lambda x: ' '.join(x) if isinstance(x, list) else str(x))
            st.session_state.ad_data['Headlines'] = st.session_state.ad_data['Headlines'].apply(extract_texts)
            st.session_state.ad_data['Descriptions'] = st.session_state.ad_data['Descriptions'].apply(extract_texts)

            # Unique ads per ad group
            st.session_state.ad_data["Ad"] = st.session_state.ad_data["Headlines"] + st.session_state.ad_data["Descriptions"]
            st.session_state.ad_data["Ad"] = st.session_state.ad_data["Ad"].astype(str)
            st.session_state.ad_data_unique = st.session_state.ad_data.groupby(["Ad Strength","Campaign","Ad Group"])["Ad"].nunique()
            ad_data_unique_mean = st.session_state.ad_data.groupby(["Campaign","Ad Group"])["Ad"].nunique().mean().round(3)

            total_unique_ads = st.session_state.ad_data["Ad"].nunique()
            st.markdown(''':blue-background[**Total Unique Ads in the Account**]''')
            st.write("(Combination of Headlines and Description has been considered here, as a unique ad.)")
            st.write(total_unique_ads , " (No. of Ad Groups" + " : " , st.session_state.ad_data["Ad Group"].nunique(), ")")

            st.markdown(''':blue-background[**Unique Ads per Ad Group**]''')
            st.write("(Combination of Headlines and Description has been considered here, as a unique ad.)")
            st.write(ad_data_unique_mean)
            #st.session_state.ad_data_unique = st.session_state.ad_data_unique[["Campaign", "Ad Group", "Ad Strength", "Ad"]].reset_index()
            st.dataframe(st.session_state.ad_data_unique)

            # ads with zero clicks
            st.session_state.ad_data_zero_clicks = st.session_state.ad_data[st.session_state.ad_data["Clicks"] == 0]
            st.download_button(           
                    label="Download Ads with ZERO Clicks",
                    data=st.session_state.ad_data_zero_clicks.to_csv(index=False),
                    file_name='Ads_with_zero_clicks.csv',
                    mime='text/csv',
                )
            
            # Count of ads according to Ad Strength
            st.markdown(''':blue-background[**Count of Ads according to Ad Strength**]''')
            st.session_state.ad_data["Ad Strength"] = st.session_state.ad_data["Ad Strength"].fillna("No Strength")
            st.session_state.ad_data_ad_strength = st.session_state.ad_data.groupby("Ad Strength").agg({"Ad": "count"}).reset_index()
            st.dataframe(st.session_state.ad_data_ad_strength)

        # P-max data analysis
        def pmax_data_analysis():
            st.session_state.pmax_raw = get_pmax_data(client, st.session_state.Account_Name[account], st.session_state.start_date, st.session_state.end_date)
            st.session_state.uac_raw['Labels'] = st.session_state.uac_raw['Labels'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
            #st.dataframe(st.session_state.pmax_raw)

            # Filter-out data according to labels
            if segment == "2W":
                st.session_state.pmax_raw = st.session_state.pmax_raw[st.session_state.pmax_raw["Labels"].str.contains("customers/9680382253/labels/21974198167")]
            elif segment == "Spot":
                st.session_state.pmax_raw = st.session_state.pmax_raw[st.session_state.pmax_raw["Labels"].str.contains("customers/9680382253/labels/21995256971")]
            elif segment == "Bottom_7":
                st.session_state.pmax_raw = st.session_state.pmax_raw[st.session_state.pmax_raw["Labels"].str.contains("customers/9680382253/labels/21977071705")]
            elif segment == "P&M":
                st.session_state.pmax_raw = st.session_state.pmax_raw[st.session_state.pmax_raw["Labels"].str.contains("customers/9680382253/labels/21977073160")]
            elif segment == "Pure Brand":
                st.session_state.pmax_raw = st.session_state.pmax_raw[st.session_state.pmax_raw["Labels"].str.contains("customers/9680382253/labels/21995300594")]
            elif segment == "Courier":
                st.session_state.pmax_raw = st.session_state.pmax_raw[st.session_state.pmax_raw["Labels"].str.contains("customers/9680382253/labels/21977123539")]    

            st.subheader("P-max Data")
            if st.session_state.pmax_raw is not None:
                st.session_state.pmax_zero_cost = st.session_state.pmax_raw[st.session_state.pmax_raw["Cost"] == 0]
                st.session_state.pmax_zero_cost = st.session_state.pmax_zero_cost[["Product Item ID", "Cost"]]
                st.session_state.pmax_zero_cost.reset_index(drop=True, inplace=True)
                st.markdown(''':blue-background[**Product Item ID where Cost is zero**]''')
                st.dataframe(st.session_state.pmax_zero_cost)

                st.session_state.pmax_zero_impressions = st.session_state.pmax_raw[st.session_state.pmax_raw["Impressions"] == 0]
                st.session_state.pmax_zero_impressions = st.session_state.pmax_zero_impressions[["Product Item ID", "Impressions"]]
                st.session_state.pmax_zero_impressions.reset_index(drop=True, inplace=True)
                st.markdown(''':blue-background[**Product Item ID where Impressions are zero**]''')
                st.dataframe(st.session_state.pmax_zero_impressions)

        def uac_data_analysis():
            st.session_state.uac_raw = get_UAC_data_asset_level(client, st.session_state.Account_Name[account], st.session_state.start_date, st.session_state.end_date)
            st.session_state.uac_raw['Labels'] = st.session_state.uac_raw['Labels'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
            #st.dataframe(st.session_state.uac_raw)

            # Filter-out data according to labels
            if segment == "2W":
                st.session_state.uac_raw = st.session_state.uac_raw[st.session_state.uac_raw["Labels"].str.contains("customers/9680382253/labels/21974198167")]
            elif segment == "Spot":
                st.session_state.uac_raw = st.session_state.uac_raw[st.session_state.uac_raw["Labels"].str.contains("customers/9680382253/labels/21995256971")]
            elif segment == "Bottom_7":
                st.session_state.uac_raw = st.session_state.uac_raw[st.session_state.uac_raw["Labels"].str.contains("customers/9680382253/labels/21977071705")]
            elif segment == "P&M":
                st.session_state.uac_raw = st.session_state.uac_raw[st.session_state.uac_raw["Labels"].str.contains("customers/9680382253/labels/21977073160")]
            elif segment == "Pure Brand":
                st.session_state.uac_raw = st.session_state.uac_raw[st.session_state.uac_raw["Labels"].str.contains("customers/9680382253/labels/21995300594")]
            elif segment == "Courier":
                st.session_state.uac_raw = st.session_state.uac_raw[st.session_state.uac_raw["Labels"].str.contains("customers/9680382253/labels/21977123539")]

            st.subheader("UAC Data")
            st.session_state.uac_raw["Cost / In-app"] = (st.session_state.uac_raw["Cost"] / st.session_state.uac_raw["In-app-actions"]).replace([np.inf, -np.inf], 0).fillna(0).round()

            # Group the cost by uniques in Asset type & Ad Network Type
            st.session_state.uac_network_level = st.session_state.uac_raw.groupby(['Ad Network Type']).agg({
                "Impressions": np.sum,
                "Cost": np.sum,
                "In-app-actions": np.sum,
                }).reset_index()
            st.session_state.uac_network_level["Cost / In-app"] = (st.session_state.uac_network_level["Cost"] / st.session_state.uac_network_level["In-app-actions"]).replace([np.inf, -np.inf], 0).fillna(0).round()
            st.session_state.uac_network_level["Cost %"] = (st.session_state.uac_network_level["Cost"] / st.session_state.uac_network_level["Cost"].sum() * 100).round().astype(int).astype(str) + ' %'
            st.session_state.uac_network_level = st.session_state.uac_network_level[['Ad Network Type', 'Impressions', 'Cost','Cost %', 'In-app-actions', 'Cost / In-app']]
            
            st.session_state.uac_asset_type_level = st.session_state.uac_raw.groupby(['Asset Type']).agg({
                "Impressions": np.sum,
                "Cost": np.sum,
                "In-app-actions": np.sum,
                }).reset_index()
            st.session_state.uac_asset_type_level["Cost / In-app"] = (st.session_state.uac_asset_type_level["Cost"] / st.session_state.uac_asset_type_level["In-app-actions"]).replace([np.inf, -np.inf], 0).fillna(0).round()
            st.session_state.uac_asset_type_level["Cost %"] = (st.session_state.uac_asset_type_level["Cost"] / st.session_state.uac_asset_type_level["Cost"].sum() * 100).round().astype(int).astype(str) + ' %'
            st.session_state.uac_asset_type_level = st.session_state.uac_asset_type_level[['Asset Type', 'Impressions', 'Cost','Cost %', 'In-app-actions', 'Cost / In-app']]

            st.session_state.asset_type_network_level = st.session_state.uac_raw.groupby(['Asset Type', 'Ad Network Type']).agg({
                "Impressions": np.sum,
                "Cost": np.sum,
                }).reset_index()
                
            fig1 = px.bar(st.session_state.asset_type_network_level, x="Ad Network Type", y="Cost", color="Asset Type", barmode="stack")
            fig1.update_layout(title="Cost by Asset Type and Ad Network Type", xaxis_title="Asset Type", yaxis_title="Cost")

            fig2 = px.bar(st.session_state.asset_type_network_level, x="Ad Network Type", y="Impressions", color="Asset Type", barmode="stack")
            fig2.update_layout(title="Impressions by Asset Type and Ad Network Type", xaxis_title="Asset Type", yaxis_title="Impressions")

            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig1)
            with col2:
                st.plotly_chart(fig2)
            
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(st.session_state.uac_asset_type_level)
            with col2:
                st.dataframe(st.session_state.uac_network_level)

            st.dataframe(st.session_state.asset_type_network_level)

            st.session_state.assets_with_zero_spends = st.session_state.uac_raw[st.session_state.uac_raw["Cost"] == 0]
            st.download_button(
                    label="Download Assets with ZERO Spends",
                    data=st.session_state.assets_with_zero_spends.to_csv(index=False),
                    file_name='Assets_with_Zero_Spends.csv',
                    mime='text/csv',
                )
            
            # get number of unique Text assets
            st.session_state.unique_text_assets = st.session_state.uac_raw[st.session_state.uac_raw["Asset Type"] == "TEXT"]
            st.session_state.unique_text_assets = st.session_state.unique_text_assets["Asset Text"].nunique()
            st.markdown(''':blue-background[**Unique Text Assets**]''')
            st.write("Text Assets : ", st.session_state.unique_text_assets, " (Number of ad groups : ", st.session_state.uac_raw["Ad Group"].nunique(), ")")

            # get number of unique Image assets
            st.session_state.unique_image_assets = st.session_state.uac_raw[st.session_state.uac_raw["Asset Type"] == "IMAGE"]
            st.session_state.unique_image_assets = st.session_state.unique_image_assets["Asset Name"].nunique()
            st.markdown(''':blue-background[**Unique Image Assets**]''')
            st.write("Image Assets : ", st.session_state.unique_image_assets, " (Number of ad groups : ", st.session_state.uac_raw["Ad Group"].nunique(), ")")

            # get number of unique Video assets
            st.session_state.unique_video_assets = st.session_state.uac_raw[st.session_state.uac_raw["Asset Type"] == "YOUTUBE_VIDEO"]
            st.session_state.unique_video_assets = st.session_state.unique_video_assets["Video Title"].nunique()
            st.markdown(''':blue-background[**Unique Video Assets**]''')
            st.write("Video Assets : ", st.session_state.unique_video_assets, " (Number of ad groups : ", st.session_state.uac_raw["Ad Group"].nunique(), ")")

            # UAC total spends
            st.session_state.total_spends_data = get_UAC_data_network_level(client, st.session_state.Account_Name[account], st.session_state.start_date, st.session_state.end_date)
            st.session_state.total_spends_data['Labels'] = st.session_state.total_spends_data['Labels'].apply(lambda x: ', '.join(x) if isinstance(x, list) else str(x))
            #st.dataframe(st.session_state.total_spends_data)

            # Filter-out data according to labels
            if segment == "2W":
                st.session_state.total_spends_data = st.session_state.total_spends_data[st.session_state.total_spends_data["Labels"].str.contains("customers/9680382253/labels/21974198167")]
            elif segment == "Spot":
                st.session_state.total_spends_data = st.session_state.total_spends_data[st.session_state.total_spends_data["Labels"].str.contains("customers/9680382253/labels/21995256971")]
            elif segment == "Bottom_7":
                st.session_state.total_spends_data = st.session_state.total_spends_data[st.session_state.total_spends_data["Labels"].str.contains("customers/9680382253/labels/21977071705")]
            elif segment == "P&M":
                st.session_state.total_spends_data = st.session_state.total_spends_data[st.session_state.total_spends_data["Labels"].str.contains("customers/9680382253/labels/21977073160")]
            elif segment == "Pure Brand":
                st.session_state.total_spends_data = st.session_state.total_spends_data[st.session_state.total_spends_data["Labels"].str.contains("customers/9680382253/labels/21995300594")]
            elif segment == "Courier":
                st.session_state.total_spends_data = st.session_state.total_spends_data[st.session_state.total_spends_data["Labels"].str.contains("customers/9680382253/labels/21977123539")]
                
            st.session_state.total_spends_data = st.session_state.total_spends_data.groupby(["Ad Network Type", "Ad Group", "Campaign Name"]).agg({"Cost_t": np.sum}).reset_index()
            st.session_state.spends_on_assets = st.session_state.uac_raw.groupby(["Ad Network Type", "Ad Group", "Campaign Name"]).agg({"Cost": np.sum}).reset_index()

            st.session_state.total_spends_data = st.session_state.total_spends_data.merge(st.session_state.spends_on_assets, on=["Campaign Name", "Ad Group", "Ad Network Type"], how="inner")
            st.session_state.total_spends_data = st.session_state.total_spends_data[st.session_state.total_spends_data['Cost_t'] > st.session_state.total_spends_data['Cost']].reset_index(drop=True)

            st.markdown(''':blue-background[**Spends on Automated Assets**]''')
            st.session_state.total_spends_data["Cost %"] = (100-(st.session_state.total_spends_data["Cost"] / st.session_state.total_spends_data["Cost_t"] * 100)).round().astype(int).astype(str) + ' %'
            st.dataframe(st.session_state.total_spends_data)
    
    #call respective functions for selection:
    if "Search" in campaign_types_present:
        KW_data_analysis()
        ads_data_analysis() 
    if "Pmax" in campaign_types_present:
        pmax_data_analysis()
    if "UAC" in campaign_types_present:
        uac_data_analysis()
