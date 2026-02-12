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
    # Тикеры Yahoo Finance:
    # KZT=X -> USD/KZT
    # RUB=X -> USD/RUB (Новый)
    # BZ=F  -> Нефть Brent
    # GC=F  -> Золото
    # SI=F  -> Серебро (Новый)
    tickers = ['KZT=X', 'RUB=X', 'BZ=F', 'GC=F', 'SI=F']
    
    # Качаем данные за последний год
    df = yf.download(tickers, period="1y", interval="1d", progress=False)
    
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
    # Получаем последние цены
    last_prices = df.iloc[-1]
    prev_prices = df.iloc[-2]
    
    # 1. МЕТРИКИ (5 штук в ряд)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Функция для красивого отображения метрики
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

    # 2. ГРАФИКИ С УЛУЧШЕННЫМ ЗУМОМ
    st.subheader("Динамика за 1 год")
    
    # Создаем вкладки
    tabs = st.tabs(["USD/KZT", "USD/RUB", "Нефть", "Золото", "Серебро"])
    
    # Словарь настроек для каждого графика
    charts_config = [
        (tabs[0], 'KZT=X', 'Курс USD/KZT', 'green'),
        (tabs[1], 'RUB=X', 'Курс USD/RUB', 'red'),
        (tabs[2], 'BZ=F',  'Нефть Brent',  'black'),
        (tabs[3], 'GC=F',  'Золото',       'gold'),
        (tabs[4], 'SI=F',  'Серебро',      'silver')
    ]

    for tab, ticker, title, color in charts_config:
        with tab:
            # Строим график
            fig = px.line(df, y=ticker, title=title, color_discrete_sequence=[color])
            
            # --- МАГИЯ: ДОБАВЛЯЕМ СЛАЙДЕР И УБИРАЕМ "ПРЫЖКИ" ---
            fig.update_xaxes(
                rangeslider_visible=True,  # Включаем нижний бегунок
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1м", step="month", stepmode="backward"),
                        dict(count=6, label="6м", step="month", stepmode="backward"),
                        dict(label="Все", step="all")
                    ])
                )
            )
            # Фиксируем ось Y, чтобы она не скакала слишком сильно, но подстраивалась
            fig.update_layout(hovermode="x unified") 
            
            st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Не удалось загрузить данные. Попробуйте позже.")
