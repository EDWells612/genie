import streamlit as st
import pandas as pd
import numpy as np
from utils import cluster_analysis, describe_results, scatter, plot_monthly_sales, plot_monthly_customers, top_suppliers, event_type_pie, source_pie, service_rev_freq
from streamlit_gsheets import GSheetsConnection

def update():
    # clear cache
    st.cache_data.clear()
    st.cache_resource.clear()
    conn = st.connection("gsheets", type=GSheetsConnection)
    data = conn.read(worksheet="data")

st.sidebar.button("update data", on_click=update)

page = st.sidebar.selectbox("Select Page", ["Home", "Suppliers", "clustering analysis"])

# data = pd.read_csv('data.csv', parse_dates=['Event Date'])
# data['Event Date'] = pd.to_datetime(data['Event Date'], format='%Y-%m-%d')

conn = st.connection("gsheets", type=GSheetsConnection)
data = conn.read(worksheet="data")
data['Event Date'] = pd.to_datetime(data['Event Date'], format='%d-%m-%Y')
# Set default dates
min_date = data['Event Date'].min().date()
max_date = data['Event Date'].max().date()

# Date input
start_date = st.sidebar.date_input('Start Date', min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input('End Date', min_value=start_date, max_value=max_date, value=max_date)

# Filter data by date range
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)
filtered_data = data[(data['Event Date'].between(start_date, end_date))]
# ----------------------------------------------------------
# ----------------------- Navigation -----------------------
# ----------------------------------------------------------

# ------------- Home page -------------
if page == "Home":
    st.snow()
    st.title("Farahy Genie")
    search = st.text_input("Search", "", help="Search in suppliers")
    if search:
        # to be replaced by names
        filtered_data = filtered_data[filtered_data['Supplier'].str.contains(search, case=False, na=False)]
    if filtered_data.empty:
        st.write("No results found.")
    else:
        col1, col2, col3 = st.columns(3)
        event = col1.selectbox("filter By Event Type", ['All'] + list(filtered_data['Event Type'].unique()))
        service = col2.selectbox("filter By Service", ['All'] + list(filtered_data['Service'].unique()))
        year = col3.selectbox("filter By Year", ['All'] + list(filtered_data['Event Date'].dt.year.unique()))
        if (event != 'All'):
            filtered_data = filtered_data[filtered_data['Event Type'] == event]
        if (service != 'All'):
            filtered_data = filtered_data[filtered_data['Service'] == service]
        if (year != 'All'):
            filtered_data = filtered_data[filtered_data['Event Date'].dt.year == year]
        n = 1
        if (len(filtered_data) > 1):
            n = st.slider('Number of rows to view', 1, len(filtered_data), len(filtered_data))
        # st.dataframe(filtered_data.iloc[:n], column_config={'Event Date': st.column_config.DateColumn(format="YYYY-MM-DD")})
        edited_data = st.data_editor(filtered_data.iloc[:n],key = 'data_editor', num_rows = 'dynamic', column_config={'Event Date': st.column_config.DateColumn(format="DD-MM-YYYY")})
        if st.button("Save Changes"):
            edited_data['Event Date'] = pd.to_datetime(edited_data['Event Date'], format='%d-%m-%Y').dt.strftime('%Y-%m-%d')
            data.update(edited_data)
            conn.update(data=edited_data, worksheet="data")
            update()
        # metrics
        col1, col2, col3 = st.columns(3)
        metr = col1.radio("metric", ['sum', 'mean', 'median'], label_visibility='collapsed')
        col2.metric("Total Revenue", f"{filtered_data.groupby('Customer ID')['Total Customer'].sum().agg(metr):.2f}")
        col3.metric("Total Customers", filtered_data['Customer ID'].nunique())
        # plots
        st.markdown("""<div style="text-align: center;">Monthly Sales</div>""", unsafe_allow_html=True)
        plot_monthly_sales(filtered_data)
        st.markdown("""<div style="text-align: center;">Monthly Customers</div>""", unsafe_allow_html=True)
        plot_monthly_customers(filtered_data)
# ------------- Suppliers page -------------
elif page == "Suppliers":
    st.title("Suppliers")
    service = st.sidebar.selectbox('Select Service', ['All'] + sorted(list(filtered_data['Service'].unique())))
    if service != 'All':
        filtered_data = filtered_data[filtered_data['Service'] == service]
    supplier = st.sidebar.selectbox('Select Supplier', ['All'] + sorted(list(filtered_data['Supplier'].unique())))
    if supplier != 'All':
        filtered_data = filtered_data[filtered_data['Supplier'] == supplier]

    if not filtered_data.empty:
        n = 1
        if (len(filtered_data) > 1):
            n = st.slider('Number of rows to view', 1, len(filtered_data), len(filtered_data))
        st.dataframe(filtered_data.iloc[:n], column_config={'Event Date': st.column_config.DateColumn(format="YYYY-MM-DD")})
        st.dataframe(filtered_data.describe(), column_config={'Event Date': st.column_config.DateColumn(format="YYYY-MM-DD")})
        mt = st.radio("metric", ['Total Commissions','Commission B',
       'Total B', 'Commission S', 'Actual S',
       'count'], label_visibility='collapsed', horizontal=True)
        numberOfSuppliers = filtered_data['Supplier'].nunique()
        if numberOfSuppliers:
            num = st.slider('Number of suppliers', 1, numberOfSuppliers, 5)
            top_suppliers(filtered_data, mt, num)

# ------------- clustering analysis page -------------
elif page == "clustering analysis":
    st.title("clustering analysis")
    cluster = st.sidebar.selectbox('Select Cluster', ['All'] + list(np.arange(0, 5)))
    if not filtered_data.empty:
        if cluster == 'All':
            customer, cluster_data = cluster_analysis(filtered_data, 5)
            scatter(customer)
            describe_results(customer)
            event_type_pie(filtered_data)
            source_pie(filtered_data)
            service_rev_freq(filtered_data)
        else:
            customer, cluster_data = cluster_analysis(filtered_data, 5)
            cluster_data = cluster_data[cluster_data['Cluster'] == cluster]
            describe_results(customer[customer['Cluster'] == cluster])
            st.dataframe(cluster_data, column_config={'Event Date': st.column_config.DateColumn(format="YYYY-MM-DD")})
            # metrics
            col1, col2, col3 = st.columns(3)
            metr = col1.radio("metric", ['sum', 'mean', 'median'], label_visibility='collapsed')
            col2.metric(f"Total Revenue (%{(100*cluster_data.groupby('Customer ID')['Total Customer'].sum().sum() / data['Total Customer'].sum()):.2f})", f"{cluster_data.groupby('Customer ID')['Total Customer'].sum().agg(metr):.2f}")
            col3.metric(f"Total Customers (%{(100*cluster_data['Customer ID'].nunique() / data['Customer ID'].nunique()):.2f})", cluster_data['Customer ID'].nunique())
            event_type_pie(cluster_data)
            source_pie(cluster_data)
            service_rev_freq(cluster_data)
            mt = st.radio("metric", ['Total Commissions','Commission B',
                                    'Total B', 'Commission S', 'Actual S',
                                    'count'], label_visibility='collapsed', horizontal=True)
            category = st.selectbox('Select Service', ['All'] + list(cluster_data['Service'].unique()))
            if category != 'All':
                cluster_data = cluster_data[cluster_data['Service'] == category]
            numberOfSuppliers = cluster_data['Supplier'].nunique()
            if numberOfSuppliers:
                num = st.slider('Number of suppliers', 1, numberOfSuppliers, 5)
                top_suppliers(cluster_data, mt, num)

