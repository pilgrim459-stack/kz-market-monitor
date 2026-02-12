import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
import datetime

# --- Настройка страницы ---
st.set_page_config(page_title="Market Monitor", layout="wide")
st.title("🌏 Оперативный Мониторинг Рынка")
st.markdown("Данные в реальном времени: **USD/KZT | USD/RUB | Нефть | Золото | Серебро**")

# Кнопка обновления
if st.button('Обновить данные 🔄'):
    st.cache_data.clear()

# --- Функция загрузки данных ---
@st.cache_data(ttl=900) 
def load_data():
    tickers = ['KZT=X', 'RUB=X', 'BZ=F', 'GC=F', 'SI=F']
    
    try:
        # Качаем данные
        df = yf.download(tickers, period="max", interval="1d", group_by='ticker', progress=False, auto_adjust=False)
        
        # Превращаем индекс в дату и убираем таймзону
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df.sort_index()
        return df
        
    except Exception as e:
        st.error(f"Ошибка при загрузке с Yahoo Finance: {e}")
        return pd.DataFrame()

# --- Загрузка и Отображение ---
with st.spinner('Загружаю исторические архивы...'):
    main_df = load_data()

if not main_df.empty:
    
    # 1. МЕТРИКИ
    col1, col2, col3, col4, col5 = st.columns(5)
    
    metrics_config = [
        (col1, "🇰🇿 USD/KZT", 'KZT=X', "₸"),
        (col2, "🇷🇺 USD/RUB", 'RUB=X', "₽"),
        (col3, "🛢️ Нефть", 'BZ=F', "$"),
        (col4, "🥇 Золото", 'GC=F', "$"),
        (col5, "🥈 Серебро", 'SI=F', "$")
    ]

    for col, label, ticker, prefix in metrics_config:
        try:
            ticker_df = main_df[ticker].dropna()
            if not ticker_df.empty:
                last_price = ticker_df['Close'].iloc[-1]
                prev_price = ticker_df['Close'].iloc[-2]
                delta = last_price - prev_price
                col.metric(label, f"{prefix}{last_price:.2f}", f"{delta:.2f}")
            else:
                col.metric(label, "Н/Д", "0")
        except:
            col.metric(label, "Н/Д", "0")

    st.divider()

    # 2. ГРАФИКИ
    st.subheader("Динамика рынка (Свечной график)")
    
    # Выбор периода
    timeframe = st.radio(
        "Выберите период:",
        options=["1 Месяц", "3 Месяца", "6 Месяцев", "1 Год", "5 Лет", "Все"],
        index=0, 
        horizontal=True,
        key="tf_selector"
    )

    # --- ЛОГИКА ФИЛЬТРАЦИИ ---
    end_date = main_df.index.max()
    
    if timeframe == "1 Месяц":
        start_date = end_date - pd.Timedelta(days=30)
    elif timeframe == "3 Месяца":
        start_date = end_date - pd.Timedelta(days=90)
    elif timeframe == "6 Месяцев":
        start_date = end_date - pd.Timedelta(days=180)
    elif timeframe == "1 Год":
        start_date = end_date - pd.Timedelta(days=365)
    elif timeframe == "5 Лет":
        start_date = end_date - pd.Timedelta(days=365*5)
    else: 
        start_date = main_df.index.min()
    
    filtered_main_df = main_df[main_df.index >= start_date]

    # --- ПОСТРОЕНИЕ ---
    tabs = st.tabs(["USD/KZT", "USD/RUB", "Нефть", "Золото", "Серебро"])
    
    charts_config = [
        (tabs[0], 'KZT=X', 'Курс USD/KZT'),
        (tabs[1], 'RUB=X', 'Курс USD/RUB'),
        (tabs[2], 'BZ=F',  'Нефть Brent'),
        (tabs[3], 'GC=F',  'Золото'),
        (tabs[4], 'SI=F',  'Серебро')
    ]

    for tab, ticker, title in charts_config:
        with tab:
            try:
                df_ticker = filtered_main_df[ticker].dropna()

                if not df_ticker.empty:
                    
                    # --- ДАТЫ ДЛЯ СКЛЕЙКИ ---
                    all_days = pd.date_range(start=df_ticker.index.min(), end=df_ticker.index.max(), freq='D')
                    missing_dates = all_days.difference(df_ticker.index)
                    dt_breaks = missing_dates.strftime("%Y-%m-%d").tolist()

                    # РИСУЕМ СВЕЧИ
                    fig = go.Figure(data=[go.Candlestick(
                        x=df_ticker.index,
                        open=df_ticker['Open'],
                        high=df_ticker['High'],
                        low=df_ticker['Low'],
                        close=df_ticker['Close'],
                        name=title
                    )])

                    # НАСТРОЙКИ МАКЕТА
                    fig.update_layout(
                        title=title,
                        yaxis_title='Цена',
                        xaxis_title='',
                        dragmode=False, 
                        # ВАЖНО: Возвращаем режим 'x'. Он самый надежный для времени.
                        hovermode='x',
                        margin=dict(l=20, r=20, t=40, b=20),
                        height=500
                    )

                    # ПРИМЕНЯЕМ СКРЫТИЕ ДАТ
                    fig.update_xaxes(
                        rangeslider_visible=False,
                        rangebreaks=[dict(values=dt_breaks)], 
                        # ВКЛЮЧАЕМ ПЕРЕКРЕСТИЕ (SPIKES)
                        showspikes=True, 
                        spikemode='across', 
                        spikesnap='cursor', # Линия бегает за курсором
                        showline=True,
                        spikecolor="gray",
                        spikethickness=1,
                        showgrid=True, 
                        gridcolor='#F0F0F0'
                    )
                    
                    fig.update_yaxes(
                        fixedrange=False,
                        # ВКЛЮЧАЕМ ГОРИЗОНТАЛЬНУЮ ЛИНИЮ
                        showspikes=True, 
                        spikemode='across', 
                        spikesnap='cursor', # Линия бегает за курсором
                        spikecolor="gray",
                        spikethickness=1,
                        showgrid=True, 
                        gridcolor='#F0F0F0'
                    )

                    st.plotly_chart(
                        fig, 
                        use_container_width=True,
                        config={'scrollZoom': False, 'displayModeBar': False} 
                    )

                else:
                    st.warning("Нет данных за этот период")
            except KeyError:
                st.warning(f"Нет данных для {ticker}")

else:
    st.error("Не удалось загрузить данные. Попробуйте нажать кнопку 'Обновить'.")
