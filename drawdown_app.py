import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(page_title="Stock Drawdown Analyzer", layout="wide")

st.title("📉 Stock Drawdown Chart Builder")
st.markdown("Analyze and compare drawdowns for stocks using Yahoo Finance data")

# Sidebar inputs
with st.sidebar:
    st.header("Settings")
    ticker1 = st.text_input("Stock Ticker 1", value="SPY", help="Enter any valid Yahoo Finance ticker").upper()
    ticker2 = st.text_input("Stock Ticker 2 (Optional)", value="", help="Enter second ticker to compare").upper()
    
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
if ticker1:
    with st.spinner(f"Fetching data for {ticker1}{' and ' + ticker2 if ticker2 else ''}..."):
        df1, info1 = get_stock_data(ticker1, period)
        
        if ticker2:
            df2, info2 = get_stock_data(ticker2, period)
        else:
            df2, info2 = None, None
    
    if df1 is not None and not df1.empty:
        # Get stock names
        stock_name1 = info1.get('longName', ticker1) if info1 else ticker1
        
        # Calculate drawdown for stock 1
        prices1 = df1['Close']
        drawdown1, cumulative_max1 = calculate_drawdown(prices1)
        
        # Find max drawdown for stock 1
        max_drawdown1 = drawdown1.min()
        max_drawdown_date1 = drawdown1.idxmin()
        
    # Process stock 2 if provided
    if df2 is not None and not df2.empty:
        stock_name2 = info2.get('longName', ticker2) if info2 else ticker2
    
        # Align time periods - use only overlapping dates
        common_dates = df1.index.intersection(df2.index)
        df1 = df1.loc[common_dates]
        df2 = df2.loc[common_dates]
    
        # Recalculate for stock 1 with aligned dates
        prices1 = df1['Close']
        drawdown1, cumulative_max1 = calculate_drawdown(prices1)
        max_drawdown1 = drawdown1.min()
        max_drawdown_date1 = drawdown1.idxmin()
    
        # Calculate for stock 2
        prices2 = df2['Close']
        drawdown2, cumulative_max2 = calculate_drawdown(prices2)
        max_drawdown2 = drawdown2.min()
        max_drawdown_date2 = drawdown2.idxmin()
        
        # Display metrics
        if ticker2 and df2 is not None:
            cols = st.columns(8)
            with cols[0]:
                st.metric(f"{ticker1} Price", f"${prices1.iloc[-1]:.2f}")
            with cols[1]:
                st.metric(f"{ticker1} Max DD", f"{max_drawdown1:.2f}%")
            with cols[2]:
                st.metric(f"{ticker1} Max DD Date", max_drawdown_date1.strftime("%Y-%m-%d"))
            with cols[3]:
                current_dd1 = drawdown1.iloc[-1]
                st.metric(f"{ticker1} Current DD", f"{current_dd1:.2f}%")
            with cols[4]:
                st.metric(f"{ticker2} Price", f"${prices2.iloc[-1]:.2f}")
            with cols[5]:
                st.metric(f"{ticker2} Max DD", f"{max_drawdown2:.2f}%")
            with cols[6]:
                st.metric(f"{ticker2} Max DD Date", max_drawdown_date2.strftime("%Y-%m-%d"))
            with cols[7]:
                current_dd2 = drawdown2.iloc[-1]
                st.metric(f"{ticker2} Current DD", f"{current_dd2:.2f}%")
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Price", f"${prices1.iloc[-1]:.2f}")
            with col2:
                st.metric("Max Drawdown", f"{max_drawdown1:.2f}%")
            with col3:
                st.metric("Max DD Date", max_drawdown_date1.strftime("%Y-%m-%d"))
            with col4:
                current_dd1 = drawdown1.iloc[-1]
                st.metric("Current Drawdown", f"{current_dd1:.2f}%")
        
        # Create charts
        if show_price_chart:
            # Price chart with dual Y-axes if comparing two stocks
            if ticker2 and df2 is not None:
                fig_price = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Stock 1
                fig_price.add_trace(
                    go.Scatter(x=df1.index, y=df1['Close'], name=f'{ticker1} Price',
                               line=dict(color='#2E86AB', width=2)),
                    secondary_y=False
                )
                fig_price.add_trace(
                    go.Scatter(x=df1.index, y=cumulative_max1, name=f'{ticker1} Peak',
                               line=dict(color='#A23B72', width=1, dash='dash'), opacity=0.7),
                    secondary_y=False
                )
                
                # Stock 2
                fig_price.add_trace(
                    go.Scatter(x=df2.index, y=df2['Close'], name=f'{ticker2} Price',
                               line=dict(color='#F77F00', width=2)),
                    secondary_y=True
                )
                fig_price.add_trace(
                    go.Scatter(x=df2.index, y=cumulative_max2, name=f'{ticker2} Peak',
                               line=dict(color='#06A77D', width=1, dash='dash'), opacity=0.7),
                    secondary_y=True
                )
                
                fig_price.update_xaxes(title_text="Date")
                fig_price.update_yaxes(title_text=f"{ticker1} Price ($)", secondary_y=False)
                fig_price.update_yaxes(title_text=f"{ticker2} Price ($)", secondary_y=True)
                
                fig_price.update_layout(
                    title=f"{ticker1} vs {ticker2} - Price Comparison",
                    hovermode='x unified',
                    height=400,
                    template='plotly_white'
                )
            else:
                # Single stock price chart
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=df1.index, y=df1['Close'], name='Price',
                    line=dict(color='#2E86AB', width=2)
                ))
                fig_price.add_trace(go.Scatter(
                    x=df1.index, y=cumulative_max1, name='All-Time High',
                    line=dict(color='#A23B72', width=1, dash='dash'), opacity=0.7
                ))
                fig_price.update_layout(
                    title=f"{stock_name1} ({ticker1}) - Price Chart",
                    xaxis_title="Date", yaxis_title="Price ($)",
                    hovermode='x unified', height=400, template='plotly_white'
                )
            
            st.plotly_chart(fig_price, use_container_width=True)
        
        # Drawdown chart - both stocks on same axis
        fig_dd = go.Figure()
        
        fig_dd.add_trace(go.Scatter(
            x=df1.index, y=drawdown1, fill='tozeroy', name=f'{ticker1} Drawdown',
            line=dict(color='#C73E1D', width=2),
            fillcolor='rgba(199, 62, 29, 0.3)'
        ))
        
        # Mark maximum drawdown for stock 1
        fig_dd.add_trace(go.Scatter(
            x=[max_drawdown_date1], y=[max_drawdown1],
            mode='markers', name=f'{ticker1} Max DD',
            marker=dict(color='darkred', size=12, symbol='diamond'),
            hovertemplate=f'{ticker1} Max DD: {max_drawdown1:.2f}%<br>Date: {max_drawdown_date1.strftime("%Y-%m-%d")}<extra></extra>'
        ))
        
        if ticker2 and df2 is not None:
            fig_dd.add_trace(go.Scatter(
                x=df2.index, y=drawdown2, name=f'{ticker2} Drawdown',
                line=dict(color='#0077B6', width=2)
            ))
            
            # Mark maximum drawdown for stock 2
            fig_dd.add_trace(go.Scatter(
                x=[max_drawdown_date2], y=[max_drawdown2],
                mode='markers', name=f'{ticker2} Max DD',
                marker=dict(color='#003f5c', size=12, symbol='diamond'),
                hovertemplate=f'{ticker2} Max DD: {max_drawdown2:.2f}%<br>Date: {max_drawdown_date2.strftime("%Y-%m-%d")}<extra></extra>'
            ))
        
        title = f"{ticker1} vs {ticker2} - Drawdown Comparison" if ticker2 and df2 is not None else f"{stock_name1} ({ticker1}) - Drawdown Chart"
        
        fig_dd.update_layout(
            title=title,
            xaxis_title="Date", yaxis_title="Drawdown (%)",
            hovermode='x unified', height=450, template='plotly_white',
            yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='black')
        )
        
        st.plotly_chart(fig_dd, use_container_width=True)
        
        # Summary statistics
        with st.expander("📊 Drawdown Statistics"):
            if ticker2 and df2 is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader(ticker1)
                    st.write(f"**Average Drawdown:** {drawdown1[drawdown1 < 0].mean():.2f}%")
                    st.write(f"**Time in Drawdown:** {(drawdown1 < -0.5).sum() / len(drawdown1) * 100:.1f}% of days")
                    st.write(f"**-10%+ Drawdowns:** {(drawdown1 <= -10).sum()} days")
                    st.write(f"**-20%+ Drawdowns:** {(drawdown1 <= -20).sum()} days")
                with col2:
                    st.subheader(ticker2)
                    st.write(f"**Average Drawdown:** {drawdown2[drawdown2 < 0].mean():.2f}%")
                    st.write(f"**Time in Drawdown:** {(drawdown2 < -0.5).sum() / len(drawdown2) * 100:.1f}% of days")
                    st.write(f"**-10%+ Drawdowns:** {(drawdown2 <= -10).sum()} days")
                    st.write(f"**-20%+ Drawdowns:** {(drawdown2 <= -20).sum()} days")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Average Drawdown:** {drawdown1[drawdown1 < 0].mean():.2f}%")
                    st.write(f"**Time in Drawdown:** {(drawdown1 < -0.5).sum() / len(drawdown1) * 100:.1f}% of days")
                with col2:
                    st.write(f"**Number of -10%+ Drawdowns:** {(drawdown1 <= -10).sum()}")
                    st.write(f"**Number of -20%+ Drawdowns:** {(drawdown1 <= -20).sum()}")
        
    else:
        st.error(f"Unable to fetch data for ticker: {ticker1}. Please check the ticker symbol and try again.")
else:
    st.info("Enter a stock ticker in the sidebar to get started!")

# Footer
st.markdown("---")
st.caption("Data provided by Yahoo Finance. Drawdown calculated as percentage decline from peak.")
