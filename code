import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Library Subscription Decision Support", layout="wide")

st.title("📚 Library Subscription Analysis Dashboard")
st.markdown("""
This app analyzes COUNTER 5 TR (Title Report) data to identify low-performing subscriptions 
and support strategic cancellation decisions.
""")

# 1. Load and Clean Data
@st.cache_data
def load_data(file_path):
    # COUNTER 5 files usually have ~14 rows of metadata
    df = pd.read_csv(file_path, skiprows=14)
    
    # Identify month columns for melting
    month_cols = [col for col in df.columns if '-' in col and any(char.isdigit() for char in col)]
    metadata_cols = [col for col in df.columns if col not in month_cols]
    
    return df, month_cols, metadata_cols

# Use the specific file provided
try:
    data_file = 'ebsco_title_counter_2023_2026.xlsx - Sheet1.csv'
    df_raw, month_cols, metadata_cols = load_data(data_file)
    
    # --- Sidebar Filters ---
    st.sidebar.header("Filter Data")
    
    # Filter by Metric Type (Requests are usually more significant than Investigations)
    metric_options = df_raw['Metric_Type'].unique()
    selected_metric = st.sidebar.selectbox("Select Metric Type", metric_options, index=list(metric_options).index('Unique_Item_Requests') if 'Unique_Item_Requests' in metric_options else 0)
    
    # Filter by Data Type (Journal vs Book)
    data_types = df_raw['Data Type'].unique()
    selected_types = st.sidebar.multiselect("Data Type", data_types, default=list(data_types))
    
    # Filter by Publisher
    publishers = sorted(df_raw['Publisher'].dropna().unique())
    selected_publishers = st.sidebar.multiselect("Publishers", publishers, default=publishers[:5] if len(publishers) > 5 else publishers)

    # Apply Filters
    df_filtered = df_raw[
        (df_raw['Metric_Type'] == selected_metric) &
        (df_raw['Data Type'].isin(selected_types)) &
        (df_raw['Publisher'].isin(selected_publishers))
    ]

    # --- KPI Metrics ---
    col1, col2, col3 = st.columns(3)
    total_usage = df_filtered['Reporting Period_Total'].sum()
    unique_titles = df_filtered['Title'].nunique()
    avg_usage = total_usage / unique_titles if unique_titles > 0 else 0
    
    col1.metric("Total Usage (Selected Period)", f"{total_usage:,}")
    col2.metric("Total Titles", f"{unique_titles:,}")
    col3.metric("Avg Usage per Title", f"{avg_usage:.2f}")

    # --- 1. Top Performers vs. Potential Cancellations ---
    st.subheader("📊 Usage Distribution")
    tab1, tab2 = st.tabs(["Top 20 Titles", "Low-Usage Analysis (Potential Cancellations)"])

    with tab1:
        top_titles = df_filtered.nlargest(20, 'Reporting Period_Total')[['Title', 'Publisher', 'Reporting Period_Total']]
        fig_top = px.bar(top_titles, x='Reporting Period_Total', y='Title', orientation='h', 
                         title=f"Top 20 Titles by {selected_metric}", color='Reporting Period_Total')
        fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)

    with tab2:
        threshold = st.slider("Define 'Low Usage' Threshold (Total requests in period)", 0, 50, 5)
        low_use_df = df_filtered[df_filtered['Reporting Period_Total'] <= threshold].sort_values('Reporting Period_Total')
        
        st.warning(f"Found {len(low_use_df)} titles with {threshold} or fewer {selected_metric}.")
        st.dataframe(low_use_df[['Title', 'Publisher', 'Data Type', 'Reporting Period_Total']], use_container_width=True)
        
        # Download button for low-use report
        csv = low_use_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Cancellation Review List (CSV)", csv, "cancellation_review.csv", "text/csv")

    # --- 2. Trend Analysis ---
    st.subheader("📈 Usage Trends Over Time")
    # Melt data for time-series
    df_melted = df_filtered.melt(id_vars=['Title', 'Publisher'], value_vars=month_cols, var_name='Month', value_name='Usage')
    df_melted['Month'] = pd.to_datetime(df_melted['Month'], format='%b-%Y')
    monthly_trend = df_melted.groupby('Month')['Usage'].sum().reset_index()
    
    fig_trend = px.line(monthly_trend, x='Month', y='Usage', title=f"Total Monthly {selected_metric} Trend")
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- 3. Publisher Efficiency ---
    st.subheader("🏢 Publisher Summary")
    pub_summary = df_filtered.groupby('Publisher').agg({
        'Title': 'count',
        'Reporting Period_Total': 'sum'
    }).rename(columns={'Title': 'Title Count', 'Reporting Period_Total': 'Total Usage'}).reset_index()
    
    pub_summary['Usage Per Title'] = pub_summary['Total Usage'] / pub_summary['Title Count']
    st.dataframe(pub_summary.sort_values('Total Usage', ascending=False), use_container_width=True)

except FileNotFoundError:
    st.error("Data file not found. Please ensure the CSV is in the same directory.")
except Exception as e:
    st.error(f"An error occurred: {e}")
