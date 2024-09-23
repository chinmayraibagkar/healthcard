import pandas as pd
import numpy as np
from functions import *
import streamlit as st
import tempfile

st.session_state.Account_Name = {
    "CFS" : "1702864408",
    "Cretify" : "2472364292",
    "Porter India" : "9680382253",
    "Porter India 2.0" : "4840834180",
    "Stahl Kitchens" : "3994900785",
    "Torrins Anthem" : "3016502090",
    "Rotimatic - US" : "5741817215",
    "Medikabazzar" : "7867734746",
    "Keya Foods" : "7656314899",
    "Peperfry" : "6617270902",
    "FNP Generic" : "1991620806",
    "FNP App Account" : "7654170390",
    "FNP Brand" : "7131559721",
    "Pepperfry Main" : "6617270902",
    "Pepperfry Furniture" : "3577253261",
    "Pepperfry App Account" : "1688452376",
    "Pepperfry UAC" : "2058916916",
    "Pepperfry YT New" : "3827510607",
    "Yangpoo" : "5658536021",
    "Porter UAE" : "6231867854"
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

st.header("Healthcard")

# Create an account selector
selected_accounts = st.multiselect("Select Account Names", list(st.session_state.Account_Name.keys()))
date_range = st.date_input("Select Date Range", [pd.to_datetime("2024-06-01"), pd.to_datetime("2024-06-30")])

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
        st.session_state.kw_data = get_kw_data(client, st.session_state.Account_Name[account], st.session_state.start_date, st.session_state.end_date)
        
        # Calculate weighted average of quality score for each ad group
        st.session_state.kw_data["Impressions"] = st.session_state.kw_data["Impressions"].astype(int)
        st.session_state.kw_data["Quality Score"] = st.session_state.kw_data["Quality Score"].astype(float)
        st.session_state.weighted_avg_quality_score = (st.session_state.kw_data.loc[st.session_state.kw_data["Quality Score"] != 0, "Impressions"] * st.session_state.kw_data.loc[st.session_state.kw_data["Quality Score"] != 0, "Quality Score"]).sum() / st.session_state.kw_data.loc[st.session_state.kw_data["Quality Score"] != 0, "Impressions"].sum()
        st.session_state.weighted_avg_quality_score = st.session_state.weighted_avg_quality_score.round(2)

        if st.session_state.weighted_avg_quality_score < 6:
            bg = ":red-background"
        elif st.session_state.weighted_avg_quality_score < 8 and st.session_state.weighted_avg_quality_score >= 6:
            bg = ":orange-background"
        else:
            bg = ":green-background"

        st.markdown(f":blue-background[**Weighted Average Quality Score**] : {bg}[{st.session_state.weighted_avg_quality_score}]")

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
            file_name='full_mapped_data.csv',
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
        st.session_state.ad_data = get_ad_data(client, st.session_state.Account_Name[account], st.session_state.start_date, st.session_state.end_date)
        st.session_state.ad_data['Headlines'] = st.session_state.ad_data['Headlines'].fillna('').astype(str)
        st.session_state.ad_data['Descriptions'] = st.session_state.ad_data['Descriptions'].apply(lambda x: ' '.join(x) if isinstance(x, list) else str(x))
        st.session_state.ad_data['Headlines'] = st.session_state.ad_data['Headlines'].apply(extract_texts)
        st.session_state.ad_data['Descriptions'] = st.session_state.ad_data['Descriptions'].apply(extract_texts)

        # Unique ads per ad group
        st.session_state.ad_data["Ad"] = st.session_state.ad_data["Headlines"] + st.session_state.ad_data["Descriptions"]
        st.session_state.ad_data["Ad"] = st.session_state.ad_data["Ad"].astype(str)
        st.session_state.ad_data_unique = st.session_state.ad_data.groupby(["Campaign","Ad Group"])["Ad"].nunique()
        ad_data_unique_mean = st.session_state.ad_data.groupby(["Campaign","Ad Group"])["Ad"].nunique().mean().round(3)

        total_unique_ads = st.session_state.ad_data["Ad"].nunique()
        st.markdown(''':blue-background[**Total Unique Ads in the Account**]''')
        st.write("(Combination of Headlines and Description has been considered here, as a unique ad.)")
        st.write(total_unique_ads)

        st.markdown(''':blue-background[**Unique Ads per Ad Group**]''')
        st.write("(Combination of Headlines and Description has been considered here, as a unique ad.)")
        st.write(ad_data_unique_mean)
        st.dataframe(st.session_state.ad_data_unique) 

        # P-max data analysis
        st.session_state.pmax_raw = get_pmax_data(client, st.session_state.Account_Name[account], st.session_state.start_date, st.session_state.end_date)
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
