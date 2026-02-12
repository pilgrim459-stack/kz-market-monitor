import streamlit as st
import yfinance as yf
import plotly.express as px
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
        df = yf.download(tickers, period="max", interval="1d", progress=False, auto_adjust=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            try:
                df = df['Close']
            except KeyError:
                 df = df.xs('Close', axis=1, level=1, drop_level=True)

        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        return df
        
    except Exception as e:
        st.error(f"Ошибка при загрузке с Yahoo Finance: {e}")
        return pd.DataFrame()

# --- Загрузка и Отображение ---
with st.spinner('Загружаю исторические архивы...'):
    main_df = load_data()

if not main_df.empty and len(main_df) > 2:
    last_prices = main_df.iloc[-1]
    prev_prices = main_df.iloc[-2]
    
    # 1. МЕТРИКИ
    col1, col2, col3, col4, col5 = st.columns(5)
    
    def show_metric(col, label, ticker, prefix="", suffix=""):
        if ticker in last_prices:
            val = last_prices[ticker]
            delta = val - prev_prices[ticker]
            col.metric(label, f"{prefix}{val:.2f}{suffix}", f"{delta:.2f}")
        else:
            col.metric(label, "Н/Д", "0")

    show_metric(col1, "🇰🇿 USD/KZT", 'KZT=X', "₸")
    show_metric(col2, "🇷🇺 USD/RUB", 'RUB=X', "₽")
    show_metric(col3, "🛢️ Нефть", 'BZ=F', "$")
    show_metric(col4, "🥇 Золото", 'GC=F', "$")
    show_metric(col5, "🥈 Серебро", 'SI=F', "$")

    st.divider()

    # 2. ГРАФИКИ
    st.subheader("Динамика рынка")
    
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
    
    filtered_df = main_df[main_df.index >= start_date].copy()

    # --- ПОСТРОЕНИЕ ---
    tabs = st.tabs(["USD/KZT", "USD/RUB", "Нефть", "Золото", "Серебро"])
    CHART_COLOR = '#1f77b4' 

    charts_config = [
        (tabs[0], 'KZT=X', 'Курс USD/KZT'),
        (tabs[1], 'RUB=X', 'Курс USD/RUB'),
        (tabs[2], 'BZ=F',  'Нефть Brent'),
        (tabs[3], 'GC=F',  'Золото'),
        (tabs[4], 'SI=F',  'Серебро')
    ]

    for tab, ticker, title in charts_config:
        with tab:
            if ticker in filtered_df.columns:
                series = filtered_df[ticker].dropna()
                
                if not series.empty:
                    fig = px.line(x=series.index, y=series.values, title=title)
                    fig.update_traces(
                        line_color=CHART_COLOR,
                        line_width=2,
                        # МАГИЯ 1: Чистый тултип. 
                        # %{y:.2f} - цена с 2 знаками. %{x} - дата.
                        # <extra></extra> скрывает название трассы (trace 0)
                        hovertemplate="<b>Цена: %{y:.2f}</b><br>Дата: %{x|%d.%m.%Y}<extra></extra>"
                    )
                    
                    # МАГИЯ 2: TradingView стиль (Перекрестия и метки на осях)
                    fig.update_xaxes(
                        rangeslider_visible=False,
                        showspikes=True,      # Показать линию (шип)
                        spikemode='across',   # Линия через весь график
                        spikesnap='cursor',   # Прилипать к курсору
                        showline=False,       # Скрыть линию оси
                        showgrid=True,        # Сетка
                        spikethickness=1,     # Толщина линии
                        spikecolor="gray",    # Цвет линии
                        showlabel=True        # ПОКАЗАТЬ МЕТКУ ДАТЫ НА ОСИ X
                    )
                    
                    fig.update_yaxes(
                        fixedrange=False,
                        showspikes=True,      # Показать линию
                        spikemode='across',
                        spikesnap='cursor',
                        spikethickness=1,
                        spikecolor="gray",
                        showlabel=True        # ПОКАЗАТЬ МЕТКУ ЦЕНЫ НА ОСИ Y
                    )

                    fig.update_layout(
                        hovermode="x", # Важно: просто "x", чтобы пере
