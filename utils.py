import pandas as pd
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import AgglomerativeClustering
import plotly.express as px
sns.set()
import warnings
warnings.filterwarnings('ignore')


def prepare(data):
    customer = data.groupby('Customer ID').agg(
        type = ('Event Type', lambda x: x.dropna().iloc[0] if not x.dropna().empty else None),
        source = ('Source', lambda x: x.dropna().iloc[0] if not x.dropna().empty else None),
        services = ('Service', 'count'),
        budget = ('Budget', 'sum'),
        B_commission = ('Commission B', 'sum'),
        S_commission = ('Commission S', 'sum'),
        total = ('Total Customer', 'sum')
    ).reset_index()
    return customer

def scale(data):
    clustering_data = data.drop(['Customer ID', 'type', 'source'], axis=1)
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(clustering_data)
    scaled_data = pd.DataFrame(scaled_data, columns=clustering_data.columns)
    return scaled_data

def pca(data):
    pca = PCA(n_components=2)
    pca_data = pca.fit_transform(data)
    pca_data = pd.DataFrame(pca_data, columns=['PC1', 'PC2'])
    return pca_data

def agglo(fulldata, customer, data, n):
    agg = AgglomerativeClustering(n_clusters=n)
    agg.fit(data)
    customer['Cluster'] = agg.labels_
    fulldata['Cluster'] = fulldata['Customer ID'].map(customer.set_index('Customer ID')['Cluster'])
    return customer, fulldata

def scatter(data):
    fig = px.scatter(data, x='PC1', y='PC2', color='Cluster', hover_data=['Customer ID', 'total', 'budget', 'B_commission', 'S_commission'], size='total')
    st.plotly_chart(fig)

def cluster_analysis(data, n):
    customer = prepare(data)
    scaled_data = scale(customer)
    pca_data = pca(scaled_data)
    customer = pd.concat([customer, pca_data], axis=1)
    customer, clustered_data = agglo(data, customer, pca_data, n)
    return customer, clustered_data

def describe_results(customer):
    results = customer.groupby('Cluster').agg(
    count = ('Cluster', 'count'),
    meanServices = ('services', 'mean'),
    meanBudget = ('budget', 'mean'),
    meanBudgetCommission = ('B_commission', 'mean'),
    meanSupplierCommission = ('S_commission', 'mean'),
    meanTotalProfit = ('total', 'mean'),
    totalCluster = ('total', 'sum'), 
    min_total = ('total', 'min'),
    max_total = ('total', 'max'),
    min_services = ('services', 'min'),
    max_services = ('services', 'max'),
    ).reset_index()
    st.write(results)
def plot_monthly_sales(data):
    # Data preparation
    data['YearMonth'] = data['Event Date'].dt.strftime('%Y-%m')
    year_month_sales = data.groupby('YearMonth')['Total Customer'].sum().reset_index()
    
    # Convert 'YearMonth' to datetime format for proper x-axis formatting
    year_month_sales['YearMonth'] = pd.to_datetime(year_month_sales['YearMonth'])
    
    # Set 'YearMonth' as index
    year_month_sales.set_index('YearMonth', inplace=True)
    
    # Plot using Streamlit's line_chart
    st.line_chart(year_month_sales['Total Customer'], use_container_width=True)
def plot_monthly_customers(data):
    # Data preparation
    data['YearMonth'] = data['Event Date'].dt.strftime('%Y-%m')
    year_month_customers = data.groupby('YearMonth')['Customer ID'].nunique().reset_index()
    year_month_customers['YearMonth'] = pd.to_datetime(year_month_customers['YearMonth'])
    year_month_customers.set_index('YearMonth', inplace=True)
    st.line_chart(year_month_customers['Customer ID'], use_container_width=True)

def top_suppliers(data, metric, n):
    if metric == 'count':
        top_suppliers = data['Supplier'].value_counts().head(n)
    else:
        top_suppliers = data.groupby('Supplier')[metric].sum().sort_values(ascending=False).head(n)
    st.bar_chart(top_suppliers, use_container_width=True)

def event_type_pie(data):
    Color = ["#B9DDF1", "#9FCAE6", "#73A4CA", "#497AA7", "#2E5B88" ,"#B0C4DE", "#A2B5CD"]
    def func(pct, allvalues):
        total = sum(allvalues)
        if total == 0:
            return '0 (0.0%)'
        absolute = int(pct / 100. * total)
        if absolute == 0 and pct > 0:
            absolute = 1
        return f'{absolute} ({pct:.1f}%)'
    pie_data = data.groupby('Customer ID')['Event Type'].first().reset_index()
    type_counts = pie_data['Event Type'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(type_counts,labels = type_counts.index,radius = 1.3 ,colors = Color ,
        shadow = True , autopct=lambda pct: func(pct, type_counts), pctdistance = 0.8 ,  
        wedgeprops ={"linewidth": 1, "edgecolor": "white"})
    st.pyplot(fig)
def source_pie(data):
    Color = ["#B9DDF1", "#9FCAE6", "#73A4CA", "#497AA7", "#2E5B88" ,"#B0C4DE", "#A2B5CD"]
    def func(pct, allvalues):
        total = sum(allvalues)
        if total == 0:
            return '0 (0.0%)'
        absolute = int(pct / 100. * total)
        if absolute == 0 and pct > 0:
            absolute = 1
        return f'{absolute} ({pct:.1f}%)'
    pie_data = data.groupby('Customer ID')['Source'].first().reset_index()
    source_counts = pie_data['Source'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(source_counts,labels = source_counts.index,radius = 1.3 ,colors = Color ,
        shadow = True , autopct=lambda pct: func(pct, source_counts), pctdistance = 0.8 ,  
        wedgeprops ={"linewidth": 1, "edgecolor": "white"})
    st.pyplot(fig)
def service_rev_freq(data):
    serv_rev = data.groupby('Service').agg(Frequency=('Service', 'count'), Revenue=('Total Commissions', 'sum')).sort_values(by='Revenue', ascending=False)
    max_count = serv_rev['Frequency'].max()
    fig, ax1 = plt.subplots(figsize=(10, 7))
    ax1.barh(serv_rev.index, serv_rev['Revenue'], color='#5E7FB7', label='Revenue')
    ax1.set_xlabel('Total Revenue', color='#5E7FB7')
    ax1.tick_params(axis='x', labelcolor='#5E7FB7')
    ax2 = ax1.twiny()
    ax2.barh(serv_rev.index, serv_rev['Frequency'], alpha=0.6, color='#DD8452', height=0.4, label='Frequency')
    ax2.set_xlabel('Frequency', color='#DD8452')
    ax2.tick_params(axis='x', labelcolor='#DD8452')
    ax2.set_xticks(np.arange(0, max_count, max(max_count//5, 1)))
    ax1.set_ylabel('Service')
    plt.title('Service Revenue and Frequency')
    plt.tight_layout()
    st.pyplot(fig)