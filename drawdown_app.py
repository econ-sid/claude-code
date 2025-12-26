import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Drawdown Analyzer", layout="wide")

st.title("📉 Stock Drawdown Chart Builder")
st.markdown("Analyze drawdowns for any stock using Yahoo Finance data")

# Sidebar inputs
with st.sidebar:
    st.header("Settings")
    ticker = st.text_input("Stock Ticker", value="SPY", help="Enter any valid Yahoo Finance ticker").upper()
    
    period_options = {
        "1 Month": "1mo",
        "3 Months": "3mo",
        "6 Months": "6mo",
        "1 Year": "1y",
        "2 Years": "2y",
        "5 Years": "5y",
        "10 Years": "10y",
        "Max": "max"
    }
    
    selected_period = st.selectbox("Time Period", list(period_options.keys()), index=3)
    period = period_options[selected_period]
    
    show_price_chart = st.checkbox("Show Price Chart", value=True)

# Fetch data
@st.cache_data(ttl=3600)
def get_stock_data(ticker, period):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None, None
        info = stock.info
        return df, info
    except:
        return None, None

# Calculate drawdown
def calculate_drawdown(prices):
    cumulative_max = prices.cummax()
    drawdown = (prices - cumulative_max) / cumulative_max * 100
    return drawdown, cumulative_max

# Main app
if ticker:
    with st.spinner(f"Fetching data for {ticker}..."):
        df, info = get_stock_data(ticker, period)
    
    if df is not None and not df.empty:
        # Get stock name
        stock_name = info.get('longName', ticker) if info else ticker
        
        # Calculate drawdown
        prices = df['Close']
        drawdown, cumulative_max = calculate_drawdown(prices)
        
        # Find max drawdown
        max_drawdown = drawdown.min()
        max_drawdown_date = drawdown.idxmin()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Price", f"${prices.iloc[-1]:.2f}")
        with col2:
            st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
        with col3:
            st.metric("Max DD Date", max_drawdown_date.strftime("%Y-%m-%d"))
        with col4:
            current_dd = drawdown.iloc[-1]
            st.metric("Current Drawdown", f"{current_dd:.2f}%")
        
        # Create charts
        if show_price_chart:
            # Price chart
            fig_price = go.Figure()
            fig_price.add_trace(go.Scatter(
                x=df.index,
                y=df['Close'],
                name='Price',
                line=dict(color='#2E86AB', width=2)
            ))
            fig_price.add_trace(go.Scatter(
                x=df.index,
                y=cumulative_max,
                name='All-Time High',
                line=dict(color='#A23B72', width=1, dash='dash'),
                opacity=0.7
            ))
            fig_price.update_layout(
                title=f"{stock_name} ({ticker}) - Price Chart",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                hovermode='x unified',
                height=400,
                template='plotly_white'
            )
            st.plotly_chart(fig_price, use_container_width=True)
        
        # Drawdown chart
        fig_dd = go.Figure()
        
        # Color the drawdown area
        colors = ['red' if x < 0 else 'green' for x in drawdown]
        
        fig_dd.add_trace(go.Scatter(
            x=df.index,
            y=drawdown,
            fill='tozeroy',
            name='Drawdown',
            line=dict(color='#C73E1D', width=2),
            fillcolor='rgba(199, 62, 29, 0.3)'
        ))
        
        # Mark maximum drawdown
        fig_dd.add_trace(go.Scatter(
            x=[max_drawdown_date],
            y=[max_drawdown],
            mode='markers',
            name='Max Drawdown',
            marker=dict(color='darkred', size=12, symbol='diamond'),
            hovertemplate=f'Max DD: {max_drawdown:.2f}%<br>Date: {max_drawdown_date.strftime("%Y-%m-%d")}<extra></extra>'
        ))
        
        fig_dd.update_layout(
            title=f"{stock_name} ({ticker}) - Drawdown Chart",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode='x unified',
            height=450,
            template='plotly_white',
            yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black')
        )
        
        st.plotly_chart(fig_dd, use_container_width=True)
        
        # Summary statistics
        with st.expander("📊 Drawdown Statistics"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Average Drawdown:** {drawdown[drawdown < 0].mean():.2f}%")
                st.write(f"**Time in Drawdown:** {(drawdown < -0.5).sum() / len(drawdown) * 100:.1f}% of days")
            with col2:
                st.write(f"**Number of -10%+ Drawdowns:** {(drawdown <= -10).sum()}")
                st.write(f"**Number of -20%+ Drawdowns:** {(drawdown <= -20).sum()}")
        
    else:
        st.error(f"Unable to fetch data for ticker: {ticker}. Please check the ticker symbol and try again.")
else:
    st.info("Enter a stock ticker in the sidebar to get started!")

# Footer
st.markdown("---")
st.caption("Data provided by Yahoo Finance. Drawdown calculated as percentage decline from peak.")
