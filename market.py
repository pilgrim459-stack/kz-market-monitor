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
@st.cache_data(ttl=900) # Кэшируем данные на 15 минут
def load_data():
    # Тикеры:
    tickers = ['KZT=X', 'RUB=X', 'BZ=F', 'GC=F', 'SI=F']
    
    # Качаем данные за 2 года (чтобы была история)
    # Используем 'yfinance' без корректировок, чтобы ускорить процесс
    try:
        df = yf.download(tickers, period="2y", interval="1d", progress=False, auto_adjust=False)
        
        # Исправляем структуру таблицы
        if isinstance(df.columns, pd.MultiIndex):
            # Если мультииндекс, берем Close или Adj Close
            try:
                df = df['Close']
            except KeyError:
                 # Если нет Close, ищем что-то похожее или берем первый уровень
                 df = df.xs('Close', axis=1, level=1, drop_level=True)

        # Убеждаемся, что индекс - это даты
        df.index = pd.to_datetime(df.index)
        # Сортируем по дате
        df = df.sort_index()
        
        return df
        
    except Exception as e:
        st.error(f"Ошибка при загрузке с Yahoo Finance: {e}")
        return pd.DataFrame()

# --- Загрузка и Отображение ---
with st.spinner('Связываюсь с биржами...'):
    main_df = load_data()

if not main_df.empty and len(main_df) > 2:
    # Получаем последние цены
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
    
    # --- НОВЫЙ ПЕРЕКЛЮЧАТЕЛЬ ТАЙМФРЕЙМОВ (Управление через Streamlit) ---
    timeframe = st.radio(
        "Выберите период:",
        options=["1 Месяц", "3 Месяца", "6 Месяцев", "1 Год", "Все"],
        index=0, # По умолчанию 1 Месяц
        horizontal=True,
        key="tf_selector"
    )

    # --- ЛОГИКА ФИЛЬТРАЦИИ ДАННЫХ ---
    end_date = main_df.index.max()
    start_date = main_df.index.min()

    if timeframe == "1 Месяц":
        start_date = end_date - pd.Timedelta(days=30)
    elif timeframe == "3 Месяца":
        start_date = end_date - pd.Timedelta(days=90)
    elif timeframe == "6 Месяцев":
        start_date = end_date - pd.Timedelta(days=180)
    elif timeframe == "1 Год":
        start_date = end_date - pd.Timedelta(days=365)
    else: # "Все"
        start_date = main_df.index.min()
    
    # Обрезаем датафрейм по выбранной дате
    filtered_df = main_df[main_df.index >= start_date].copy()

    # --- ПОСТРОЕНИЕ ГРАФИКОВ ---
    tabs = st.tabs(["USD/KZT", "USD/RUB", "Нефть", "Золото", "Серебро"])
    CHART_COLOR = '#1f77b4' # Синий

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
                # Строим график на основе УЖЕ ОБРЕЗАННЫХ данных
                fig = px.line(filtered_df, y=ticker, title=title, color_discrete_sequence=[CHART_COLOR])
                
                # Убираем всё лишнее, оставляем чистый график
                fig.update_xaxes(rangeslider_visible=False)
                fig.update_yaxes(fixedrange=False) # Разрешаем зум по вертикали
                fig.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"Нет данных для {title}")

else:
    st.error("Не удалось загрузить данные. Биржа может быть закрыта или данные недоступны. Попробуйте нажать кнопку 'Обновить'.")
