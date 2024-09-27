import pandas as pd
import streamlit as st

@st.cache_data
def get_data():
    df = pd.read_csv("stellantis_leads.csv", encoding='latin-1', low_memory=False)
    return df

@st.cache_data
def get_metrics(df, filter_name):
    metric_df = df.loc[df['StatusCheck'] == filter_name].copy()
    metric_df = metric_df['StatusCheck'].count()
    return metric_df
    