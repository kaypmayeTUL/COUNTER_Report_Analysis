import streamlit as st
import pandas as pd
import plotly.express as px

# Set page configuration
st.set_page_config(page_title="Library Subscription Analysis", layout="wide")

st.title("📚 Library Subscription Analysis Dashboard")
st.markdown("""
Upload a COUNTER 5 TR (Title Report) CSV file to analyze usage trends and identify potential cancellations.
""")

# 1. File Upload Component
uploaded_file = st.file_uploader("Upload your EBSCO/COUNTER 5 CSV file", type=["csv"])

@st.cache_data
def load_data(file):
    # COUNTER 5 files usually have ~14 rows of metadata
    df = pd.read_csv(file, skiprows=14)
    
    # Identify month columns for melting
    # Look for columns with a dash and a year (e.g., Jan-2025)
    month_cols = [col for col in df.columns if '-' in col and any(char.isdigit() for char in col)]
    metadata_cols = [col for col in df.columns if col not in month_cols]
    
    return df, month_cols, metadata_cols

if uploaded_file is not None:
    try:
        df_raw, month_cols, metadata_cols = load_data(uploaded_file)
        
        # --- Sidebar Filters ---
        st.sidebar.header("Analysis Settings")
        
        # Metric Type Filter
        metric_options = df_raw['Metric_Type'].unique()
        selected_metric = st.sidebar.selectbox(
            "Select Metric Type", 
            metric_options, 
            index=list(metric_options).index('Unique_Item_Requests') if 'Unique_Item_Requests' in metric_options else 0
        )
        
        # Data Type Filter
        data_types = sorted(df_raw['Data Type'].unique())
        selected_types = st.sidebar.multiselect("Filter by Data Type", data_types, default=data_types)
        
        # Publisher Filter
        publishers = sorted(df_raw['Publisher'].dropna().unique())
        selected_publishers = st.sidebar.multiselect("Filter by Publisher", publishers, default=publishers)

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
        
        col1.metric("Total Usage", f"{total_usage:,}")
        col2.metric("Total Unique Titles", f"{unique_titles:,}")
        col3.metric("Avg Usage per Title", f"{avg_usage:.2f}")

        # --- Usage Analysis Tabs ---
        st.subheader("📊 Performance Analysis")
        tab1, tab2, tab3 = st.tabs(["Top Titles", "Cancellation Review", "Publisher Summary"])

        with tab1:
            top_n = st.slider("Show Top X Titles", 5, 50, 20)
            top_titles = df_filtered.nlargest(top_n, 'Reporting Period_Total')[['Title', 'Publisher', 'Reporting Period_Total']]
            fig_top = px.bar(top_titles, x='Reporting Period_Total', y='Title', orientation='h', 
                             title=f"Top {top_n} Titles", color='Reporting Period_Total',
                             color_continuous_scale='Viridis')
            fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top, use_container_width=True)

        with tab2:
            st.info("Identify titles with low usage for potential cancellation review.")
            threshold = st.number_input("Low Usage Threshold (Total for period)", min_value=0, value=5)
            low_use_df = df_filtered[df_filtered['Reporting Period_Total'] <= threshold].sort_values('Reporting Period_Total')
            
            st.write(f"Found **{len(low_use_df)}** titles at or below threshold.")
            st.dataframe(low_use_df[['Title', 'Publisher', 'Reporting Period_Total', 'Data Type']], use_container_width=True)
            
            csv = low_use_df.to_csv(index=False).encode('utf-8')
            st.download_button("Export Review List as CSV", csv, "potential_cancellations.csv", "text/csv")

        with tab3:
            pub_summary = df_filtered.groupby('Publisher').agg({
                'Title': 'nunique',
                'Reporting Period_Total': 'sum'
            }).rename(columns={'Title': 'Title Count', 'Reporting Period_Total': 'Total Usage'}).reset_index()
            pub_summary['Usage Density'] = pub_summary['Total Usage'] / pub_summary['Title Count']
            st.dataframe(pub_summary.sort_values('Total Usage', ascending=False), use_container_width=True)

        # --- Trend Analysis ---
        st.subheader("📈 Usage Trends")
        df_melted = df_filtered.melt(id_vars=['Title', 'Publisher'], value_vars=month_cols, var_name='Month', value_name='Usage')
        # Convert 'Jan-2025' format to datetime for proper sorting
        df_melted['Month'] = pd.to_datetime(df_melted['Month'], format='%b-%Y')
        monthly_trend = df_melted.groupby('Month')['Usage'].sum().reset_index()
        
        fig_trend = px.line(monthly_trend, x='Month', y='Usage', title="Monthly Usage Trend (All Selected Titles)")
        st.plotly_chart(fig_trend, use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.info("Ensure you are uploading a standard COUNTER 5 TR CSV file.")
else:
    st.info("Please upload a CSV file to begin analysis.")
