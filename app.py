"""
Frontend Streamlit app for Retail / E-commerce Sales Dashboard.
Run with: streamlit run app.py
"""

import streamlit as st
import plotly.express as px

import backend as bk

st.set_page_config(
    page_title="Retail Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Retail Sales Analytics Dashboard")
st.caption("Python dashboard using the given retail_sales.csv and sales_data.csv datasets")


@st.cache_data
def load_data():
    return bk.load_sales_data()


try:
    data = load_data()
except Exception as error:
    st.error(f"Data loading failed: {error}")
    st.stop()

# ---------------- SIDEBAR FILTERS ----------------
st.sidebar.header("🔍 Filters")

source_filter = st.sidebar.multiselect(
    "Dataset Source",
    options=sorted(data["Source"].unique()),
    default=sorted(data["Source"].unique()),
)

category_filter = st.sidebar.multiselect(
    "Category",
    options=sorted(data["Category"].unique()),
    default=sorted(data["Category"].unique()),
)

product_filter = st.sidebar.multiselect(
    "Product",
    options=sorted(data["Product"].unique()),
    default=sorted(data["Product"].unique()),
)

city_filter = st.sidebar.multiselect(
    "AP City",
    options=sorted(data["City"].unique()),
    default=sorted(data["City"].unique()),
)

min_date = data["Date"].min().date()
max_date = data["Date"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

filtered_data = bk.filter_data(
    data,
    categories=category_filter,
    products=product_filter,
    cities=city_filter,
    sources=source_filter,
    start_date=start_date,
    end_date=end_date,
)

if filtered_data.empty:
    st.warning("⚠️ No data available for the selected filters.")
    st.stop()

# ---------------- KPI SECTION ----------------
st.subheader("📌 Key Performance Indicators")
kpis = bk.get_kpis(filtered_data)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales", f"₹{kpis['total_sales']:,.2f}")
col2.metric("Total Orders", f"{kpis['total_orders']:,}")
col3.metric("Quantity Sold", f"{kpis['total_quantity']:,}")
col4.metric("Avg Order Value", f"₹{kpis['avg_order_value']:,.2f}")

st.markdown("---")

# ---------------- VISUALIZATION SECTION ----------------
st.subheader("📊 Sales Analysis")

left_col, right_col = st.columns(2)

with left_col:
    top_product_sales = bk.top_products_by_sales(filtered_data, limit=10)
    fig_top_product = px.bar(
        top_product_sales,
        x="Product",
        y="Sales",
        text="Sales",
        color="Sales",
        color_continuous_scale=["blue", "cyan", "green"],
        title="Top 10 Products by Sales",
    )
    fig_top_product.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig_top_product.update_layout(xaxis_title="Product", yaxis_title="Sales", coloraxis_showscale=False)
    st.plotly_chart(fig_top_product, use_container_width=True)

with right_col:
    bottom_product_sales = bk.bottom_products_by_sales(filtered_data, limit=10)
    fig_bottom_product = px.bar(
        bottom_product_sales,
        x="Product",
        y="Sales",
        text="Sales",
        color="Sales",
        color_continuous_scale=["red", "purple", "blue"],
        title="Bottom 10 Products by Sales",
    )
    fig_bottom_product.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig_bottom_product.update_layout(xaxis_title="Product", yaxis_title="Sales", coloraxis_showscale=False)
    st.plotly_chart(fig_bottom_product, use_container_width=True)

left_col, right_col = st.columns(2)

with left_col:
    city_sales = bk.sales_by_city(filtered_data)
    fig_city = px.bar(
        city_sales,
        x="City",
        y="Sales",
        text="Sales",
        color="City",
        title="City-wise Sales in Andhra Pradesh",
    )
    fig_city.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig_city.update_layout(xaxis_title="AP City", yaxis_title="Sales", showlegend=False)
    st.plotly_chart(fig_city, use_container_width=True)

with right_col:
    category_sales = bk.sales_by_category(filtered_data)
    fig_category = px.pie(
        category_sales,
        names="Category",
        values="Sales",
        hole=0.4,
        title="Category-wise Sales Share",
    )
    st.plotly_chart(fig_category, use_container_width=True)

st.markdown("---")

# ---------------- TREND SECTION ----------------
st.subheader("📈 Sales Trend Over Time")
freq = bk.choose_trend_frequency(start_date, end_date)
trend_data = bk.sales_trend(filtered_data, freq=freq)

fig_trend = px.line(
    trend_data,
    x="Date",
    y="Sales",
    markers=True,
    title="Sales Trend",
)
fig_trend.update_layout(xaxis_title="Date", yaxis_title="Sales")
st.plotly_chart(fig_trend, use_container_width=True)

# ---------------- DATA TABLE AND DOWNLOAD ----------------
st.markdown("---")
st.subheader("📄 Filtered Dataset")
display_data = filtered_data.drop(columns=["Source"], errors="ignore")
st.dataframe(display_data, use_container_width=True)

st.download_button(
    label="⬇️ Download Filtered Data",
    data=display_data.to_csv(index=False),
    file_name="filtered_sales_report.csv",
    mime="text/csv",
)
