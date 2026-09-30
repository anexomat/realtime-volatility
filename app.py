import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# Cài đặt giao diện trang web
st.set_page_config(page_title="Real-Time Market Volatility", layout="wide", page_icon="📈")

# Tự động refresh mỗi 30 giây (30000 milliseconds) để tạo tính năng Real-time
st_autorefresh(interval=30000, limit=1000, key="data_refresh")

st.title("📈 Real-Time Stock & Crypto Volatility Dashboard")
st.markdown("""
**Hàm lượng khoa học:** Ứng dụng tính toán Log-Returns, Rolling Volatility (Độ biến động trượt) và EWMA (Exponentially Weighted Moving Average) theo thời gian thực để đo lường mức độ rủi ro của tài sản.
""")

# Sidebar cấu hình
st.sidebar.header("⚙️ Tùy chỉnh tham số")
ticker = st.sidebar.text_input("Nhập mã tài sản (Ticker)", value="BTC-USD")
period = st.sidebar.selectbox("Khung thời gian", ["1d", "5d", "1mo"], index=1)
interval = st.sidebar.selectbox("Độ phân giải (Interval)", ["1m", "5m", "15m", "1h"], index=1)
window = st.sidebar.slider("Cửa sổ tính Volatility (Rolling Window)", 5, 50, 20)

@st.cache_data(ttl=15) # Cache data trong 15s để tránh gọi API liên tục
def get_live_data(ticker, period, interval):
    data = yf.download(tickers=ticker, period=period, interval=interval, progress=False)
    if not data.empty:
        # Xử lý format MultiIndex của yfinance bản mới
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
            
        # Tính Log Return
        data['Log_Return'] = np.log(data['Close'] / data['Close'].shift(1))
        # Tính Rolling Volatility
        data['Rolling_Vol'] = data['Log_Return'].rolling(window=window).std() * np.sqrt(252*78) 
        # Tính EWMA Volatility
        data['EWMA_Vol'] = data['Log_Return'].ewm(span=window).std() * np.sqrt(252*78)
    return data

# Main layout
try:
    df = get_live_data(ticker, period, interval)
    
    if df.empty:
        st.error("Không tìm thấy dữ liệu. Vui lòng kiểm tra lại mã Ticker.")
    else:
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        price_change = current_price - prev_price
        pct_change = (price_change / prev_price) * 100
        
        current_vol = df['Rolling_Vol'].iloc[-1]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Giá hiện tại", f"{current_price:,.2f}", f"{price_change:,.2f} ({pct_change:.2f}%)")
        col2.metric("Độ biến động (Rolling)", f"{current_vol:.4f}")
        col3.metric("Số điểm dữ liệu", f"{len(df)} điểm")
        col4.metric("Lần cập nhật cuối", datetime.now().strftime("%H:%M:%S"))

        st.divider()

        # Biểu đồ giá
        st.subheader("1. Diễn biến giá tài sản (Real-time)")
        fig_price = go.Figure()
        fig_price.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="Nến giá"
        ))
        fig_price.update_layout(height=400, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_price, use_container_width=True)

        # Biểu đồ Volatility
        st.subheader(f"2. Phân tích Độ biến động ({window}-period)")
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Scatter(x=df.index, y=df['Rolling_Vol'], mode='lines', name='Rolling Volatility', line=dict(color='orange')))
        fig_vol.add_trace(go.Scatter(x=df.index, y=df['EWMA_Vol'], mode='lines', name='EWMA Volatility', line=dict(color='cyan')))
        fig_vol.update_layout(height=300, template="plotly_dark", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_vol, use_container_width=True)

except Exception as e:
    st.error(f"Đã xảy ra lỗi khi lấy dữ liệu: {e}")

st.caption("Ứng dụng tự động lấy dữ liệu và làm mới trang web mỗi 30 giây.")
