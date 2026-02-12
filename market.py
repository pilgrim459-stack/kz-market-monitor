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
def load_data():
    tickers = ['KZT=X', 'RUB=X', 'BZ=F', 'GC=F', 'SI=F']
    
    # Качаем данные за 2 года
    df = yf.download(tickers, period="2y", interval="1d", progress=False)
    
    # Исправляем структуру таблицы
    if isinstance(df.columns, pd.MultiIndex):
        try:
            df = df['Close']
        except:
            df = df.iloc[:, 0]
            
    return df

# --- Загрузка и Отображение ---
with st.spinner('Связываюсь с биржами...'):
    df = load_data()

if not df.empty:
    last_prices = df.iloc[-1]
    prev_prices = df.iloc[-2]
    
    # 1. МЕТРИКИ
    col1, col2, col3, col4, col5 = st.columns(5)
    
    def show_metric(col, label, ticker, prefix="", suffix=""):
        val = last_prices[ticker]
        delta = val - prev_prices[ticker]
        col.metric(label, f"{prefix}{val:.2f}{suffix}", f"{delta:.2f}")

    show_metric(col1, "🇰🇿 USD/KZT", 'KZT=X', "₸")
    show_metric(col2, "🇷🇺 USD/RUB", 'RUB=X', "₽")
    show_metric(col3, "🛢️ Нефть", 'BZ=F', "$")
    show_metric(col4, "🥇 Золото", 'GC=F', "$")
    show_metric(col5, "🥈 Серебро", 'SI=F', "$")

    st.divider()

    # 2. ГРАФИКИ
    st.subheader("Динамика рынка")
    
    tabs = st.tabs(["USD/KZT", "USD/RUB", "Нефть", "Золото", "Серебро"])
    
    # Цвет графиков (Синий)
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
            fig = px.line(df, y=ticker, title=title, color_discrete_sequence=[CHART_COLOR])
            
            # --- НАСТРОЙКА ОСЕЙ ---
            fig.update_xaxes(
                rangeslider_visible=False, # ВАЖНО: Выключаем слайдер, чтобы работал авто-зум
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1м", step="month", stepmode="backward"),
                        dict(count=3, label="3м", step="month", stepmode="backward"),
                        dict(count=6, label="6м", step="month", stepmode="backward"),
                        dict(count=12, label="12м", step="month", stepmode="backward"),
                        dict(step="all", label="Все")
                    ])
                )
            )
            
            # Включаем автомасштабирование по оси Y
            fig.update_yaxes(autorange=True, fixedrange=False)
            
            fig.update_layout(hovermode="x unified") 
            st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Не удалось загрузить данные. Попробуйте позже.")
