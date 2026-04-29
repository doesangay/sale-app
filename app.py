"""
Executive Sales Dashboard Streamlit Application.
This module loads sales data, computes insights, and displays interactive charts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
from streamlit.web import cli as stcli
from streamlit import runtime

# ==========================================
# 1. MAIN DASHBOARD FUNCTION
# ==========================================
def main():
    # Website Configuration
    st.set_page_config(page_title="Executive Sales Dashboard", layout="wide", page_icon="📈")
    st.title("📈 Executive Sales & Insights Dashboard")
    st.markdown(
        "Explore your product performance, daily trends, and use the "
        "AI-style prompt at the bottom to ask your data questions!"
    )
    st.divider()

    # Data Loading
    @st.cache_data
    def load_data():
        """Loads and cleans the online sales data from the CSV file."""
        try:
            df_data = pd.read_csv('Online sales1.csv')
        except FileNotFoundError:
            st.error("⚠️ 'Online sales1.csv' not found. Ensure it is in the same folder.")
            return pd.DataFrame(), []

        columns = [
            'Lotto', 'Bingo', 'Crossword', 'Terdrup', 'Crossword Paradise',
            'Spin the Wheel', 'Race 6', 'Pick 3', 'Pick 4', 'Spin Roulette'
        ]

        for col_name in columns:
            if col_name in df_data.columns:
                df_data[col_name] = pd.to_numeric(
                    df_data[col_name].astype(str).str.replace(',', '').str.replace('"', ''),
                    errors='coerce'
                )

        df_data['Date'] = pd.to_datetime(
            df_data['Date'].astype(str).str.strip(), errors='coerce', dayfirst=True
        )
        df_data = df_data.dropna(subset=['Date'])
        df_data['Day of Week'] = df_data['Date'].dt.day_name()
        df_data['Total Sales'] = df_data[columns].sum(axis=1)

        return df_data, columns

    df, product_cols = load_data()

    if not df.empty:
        # Statistical Insights
        total_revenue = df['Total Sales'].sum()
        avg_daily = df['Total Sales'].mean()

        product_totals = df[product_cols].sum().sort_values(ascending=False)
        best_product = product_totals.index[0]
        best_product_sales = product_totals.iloc[0]

        day_totals = df.groupby('Day of Week')['Total Sales'].sum().sort_values(ascending=False)
        best_day = day_totals.index[0]
        best_day_sales = day_totals.iloc[0]

        # KPI Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"${total_revenue:,.0f}")
        col2.metric("Avg Daily Sales", f"${avg_daily:,.0f}")
        col3.metric("Top Product", best_product, f"${best_product_sales:,.0f}")
        col4.metric("Best Day", best_day, f"${best_day_sales:,.0f}")

        # Storytelling Box
        st.info(
            f"**📖 Data Story & Strategy Insight:** During this period, the platform generated "
            f"a grand total of **${total_revenue:,.0f}**. Your flagship product is currently "
            f"**{best_product}**, pulling in **${best_product_sales:,.0f}**, making it the "
            f"primary driver of revenue. Activity heavily peaks on **{best_day}s**. "
            f"*Recommendation:* Target your heaviest marketing campaigns and promotional events "
            f"leading up to {best_day} to maximize player engagement!"
        )

        # Visuals
        custom_colors = px.colors.qualitative.Prism
        tab1, tab2, tab3 = st.tabs(["📊 Main Charts", "📈 Timeline Trend", "🗄️ Raw Data Table"])

        with tab1:
            row1_col1, row1_col2 = st.columns(2)

            with row1_col1:
                fig_donut = px.pie(
                    names=product_totals.index, values=product_totals.values, hole=0.4,
                    title='Total Revenue Share by Product', color_discrete_sequence=custom_colors
                )
                fig_donut.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_donut, use_container_width=True)

            with row1_col2:
                df_long = df.melt(
                    id_vars=['Date', 'Day of Week'],
                    value_vars=[c for c in product_cols if c in df.columns],
                    var_name='Product', value_name='Sales'
                )
                day_product_sales = df_long.groupby(
                    ['Day of Week', 'Product']
                )['Sales'].sum().reset_index()
                
                days_order = [
                    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
                ]
                day_product_sales['Day of Week'] = pd.Categorical(
                    day_product_sales['Day of Week'], categories=days_order, ordered=True
                )
                day_product_sales = day_product_sales.sort_values(['Day of Week', 'Product'])

                fig_bar = px.bar(
                    day_product_sales, x='Day of Week', y='Sales', color='Product',
                    title='Weekly Sales Breakdown', color_discrete_sequence=custom_colors,
                    barmode='group'
                )
                fig_bar.update_layout(yaxis=dict(tickformat='$,.0f'))
                st.plotly_chart(fig_bar, use_container_width=True)

        with tab2:
            fig_area = px.area(
                df_long.sort_values('Date'), x='Date', y='Sales', color='Product',
                title='Daily Sales Timeline', color_discrete_sequence=custom_colors
            )
            fig_area.update_layout(yaxis=dict(tickformat='$,.0f'), hovermode='x unified')
            fig_area.update_xaxes(rangeslider_visible=True)
            st.plotly_chart(fig_area, use_container_width=True)

        with tab3:
            st.subheader("Weekly Sales Pivot Table")
            pivot_table = df.groupby('Day of Week')[product_cols].sum().reset_index()
            pivot_table['Day of Week'] = pd.Categorical(
                pivot_table['Day of Week'], categories=days_order, ordered=True
            )
            pivot_table = pivot_table.sort_values('Day of Week')
            pivot_table['Daily Total'] = pivot_table[product_cols].sum(axis=1)

            display_table = pivot_table.copy()
            for c in product_cols + ['Daily Total']:
                display_table[c] = display_table[c].apply(lambda x: f"${x:,.0f}")
            st.dataframe(display_table, use_container_width=True, hide_index=True)

        st.divider()

        # Smart Interactive Prompt
        st.subheader("🤖 Ask Your Data a Question")
        st.markdown(
            "Type a query like: **'best product'**, **'average sales'**, "
            "**'top 3 products'**, or **'worst day'**"
        )

        user_query = st.text_input("Search Insights:", placeholder="e.g., What is the top product?")

        if user_query:
            query = user_query.lower()

            if "best product" in query or "top product" in query:
                st.success(f"**Insight:** Best product is **{best_product}** (${best_product_sales:,.0f})")
            elif "top 3" in query or "best 3" in query:
                top_3 = product_totals.head(3)
                st.success(
                    f"**Insight:** Top 3 products are:\n"
                    f"1. {top_3.index[0]} (${top_3.iloc[0]:,.0f})\n"
                    f"2. {top_3.index[1]} (${top_3.iloc[1]:,.0f})\n"
                    f"3. {top_3.index[2]} (${top_3.iloc[2]:,.0f})"
                )
            elif "worst product" in query or "lowest product" in query:
                worst_prod = product_totals.index[-1]
                val = product_totals.iloc[-1]
                st.warning(f"**Insight:** Lowest-performing is **{worst_prod}** (${val:,.0f}).")
            elif "best day" in query or "highest day" in query:
                st.success(f"**Insight:** Your best day is **{best_day}** (${best_day_sales:,.0f}).")
            elif "worst day" in query or "lowest day" in query:
                worst_day = day_totals.index[-1]
                val = day_totals.iloc[-1]
                st.warning(f"**Insight:** Your slowest day is **{worst_day}** (${val:,.0f}).")
            elif "total sales" in query or "total revenue" in query:
                st.info(f"**Insight:** Total revenue is **${total_revenue:,.0f}**.")
            elif "average" in query:
                st.info(f"**Insight:** You average **${avg_daily:,.0f}** in sales per active day.")
            else:
                st.error("I am programmed to answer about 'best/worst product', 'worst day', etc.")
            

# ==========================================
# 2. BULLETPROOF PLAY BUTTON FIX
# ==========================================
if __name__ == '__main__':
    # Check if the Streamlit server is already running
    if runtime.exists():
        main()
    else:
        # If it's NOT running, we intercept the Visual Studio "Play" button!
        # sys.argv[0] automatically gets your exact file name, so it won't crash
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
