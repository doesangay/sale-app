"""
Executive Sales Dashboard.
This module loads sales data, computes insights, and displays interactive charts.
Includes an expanded AI-style prompt engine for data interrogation.
"""

import sys
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit import runtime
from streamlit.web import cli as stcli

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

        # Clean numeric columns (remove commas/quotes)
        for col_name in columns:
            if col_name in df_data.columns:
                df_data[col_name] = pd.to_numeric(
                    df_data[col_name].astype(str).str.replace(',', '').str.replace('"', ''),
                    errors='coerce'
                )

        # Clean Dates
        df_data['Date'] = pd.to_datetime(
            df_data['Date'].astype(str).str.strip(), errors='coerce', dayfirst=True
        )
        df_data = df_data.dropna(subset=['Date'])
        df_data['Day of Week'] = df_data['Date'].dt.day_name()
        df_data['Total Sales'] = df_data[columns].sum(axis=1)

        return df_data, columns

    df, product_cols = load_data()

    if not df.empty:
        # --- Pre-calculations for Insights ---
        total_revenue = df['Total Sales'].sum()
        avg_daily = df['Total Sales'].mean()
        
        product_totals = df[product_cols].sum().sort_values(ascending=False)
        best_product = product_totals.index[0]
        best_product_sales = product_totals.iloc[0]

        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_totals = df.groupby('Day of Week')['Total Sales'].sum().reindex(days_order)
        
        best_day = day_totals.idxmax()
        best_day_sales = day_totals.max()

        # KPI Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Revenue", f"${total_revenue:,.0f}")
        col2.metric("Avg Daily Sales", f"${avg_daily:,.0f}")
        col3.metric("Top Product", best_product, f"${best_product_sales:,.0f}")
        col4.metric("Best Day", best_day, f"${best_day_sales:,.0f}")

        # Overview Box
        st.info(
            f"**📖 Dashboard Overview:** Total revenue is **${total_revenue:,.0f}**. "
            f"The flagship product is **{best_product}**, driving **${best_product_sales:,.0f}**. "
            f"Activity heavily peaks on **{best_day}s**."
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
                day_prod = df_long.groupby(['Day of Week', 'Product'])['Sales'].sum().reset_index()
                day_prod['Day of Week'] = pd.Categorical(day_prod['Day of Week'], categories=days_order, ordered=True)
                
                fig_bar = px.bar(
                    day_prod.sort_values('Day of Week'), x='Day of Week', y='Sales', color='Product',
                    title='Weekly Sales Breakdown', barmode='group', color_discrete_sequence=custom_colors
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
            st.subheader("Weekly Sales Summary")
            pivot = df.groupby('Day of Week')[product_cols].sum().reindex(days_order).reset_index()
            # Dynamic formatting for the table
            st.dataframe(pivot.style.format(subset=product_cols, formatter="${:,.0f}"), use_container_width=True)

        st.divider()

        # ==========================================
        # 2. EXPANDED SMART INSIGHTS ENGINE
        # ==========================================
        st.subheader("🤖 Ask Your Data a Question")
        st.markdown(
            "Try: **'compare Lotto vs Bingo'**, **'percent of total'**, "
            "**'is Friday better than Monday?'**, or **'weekend report'**"
        )

        user_query = st.text_input("Search Insights:", placeholder="e.g., compare Lotto vs Bingo")

        if user_query:
            q = user_query.lower()

            # A. Product Comparison (e.g., "compare Lotto vs Bingo")
            if "compare" in q and "vs" in q:
                try:
                    parts = q.replace("compare", "").split("vs")
                    p1 = parts[0].strip().title()
                    p2 = parts[1].strip().title()
                    
                    if p1 in product_cols and p2 in product_cols:
                        v1, v2 = product_totals[p1], product_totals[p2]
                        diff = abs(v1 - v2)
                        leader = p1 if v1 > v2 else p2
                        st.info(f"⚖️ **Comparison:** {p1} (${v1:,.0f}) vs {p2} (${v2:,.0f}). "
                                f"**{leader}** is leading by **${diff:,.0f}**.")
                    else:
                        st.warning(f"Could not find those products. Available: {', '.join(product_cols[:4])}...")
                except:
                    st.error("Try format: 'compare Lotto vs Bingo'")

            # B. Percentage Share (e.g., "percent of total")
            elif "percent" in q or "share" in q:
                pct = (best_product_sales / total_revenue) * 100
                st.info(f"📊 **Market Share:** {best_product} represents **{pct:.1f}%** of total revenue.")

            # C. Day Battle (e.g., "is Friday better than Monday?")
            elif "better than" in q:
                found_days = [d for d in days_order if d.lower() in q]
                if len(found_days) == 2:
                    d1, d2 = found_days[0], found_days[1]
                    v1, v2 = day_totals[d1], day_totals[d2]
                    winner = d1 if v1 > v2 else d2
                    st.success(f"📅 **Day Battle:** {d1} (${v1:,.0f}) vs {d2} (${v2:,.0f}). **{winner}** is stronger.")
                else:
                    st.warning("Please mention two days (e.g., 'Is Monday better than Friday?')")

            # D. Weekend Performance
            elif "weekend" in q:
                wknd = day_totals.get('Saturday', 0) + day_totals.get('Sunday', 0)
                st.info(f"🏖️ **Weekend Performance:** Saturday and Sunday combined for **${wknd:,.0f}**.")

            # E. Legacy Queries
            elif "best product" in q or "top product" in q:
                st.success(f"🏆 The top product is **{best_product}** with **${best_product_sales:,.0f}**.")
            elif "top 3" in q:
                t3 = product_totals.head(3)
                st.success(f"🥇 1st: {t3.index[0]} | 🥈 2nd: {t3.index[1]} | 🥉 3rd: {t3.index[2]}")
            elif "average" in q:
                st.info(f"📈 Average daily revenue is **${avg_daily:,.0f}**.")
            elif "worst day" in q or "lowest day" in q:
                w_day = day_totals.idxmin()
                st.warning(f"📉 The slowest day is **{w_day}** (${day_totals.min():,.0f}).")
            else:
                st.error("I'm not sure about that one! Try asking about products, comparisons, or specific days.")

# ==========================================
# 3. EXECUTION HANDLER (Safe for VS Code & Cloud)
# ==========================================
if __name__ == '__main__':
    if runtime.exists():
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
