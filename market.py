import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
import datetime

# --- Настройка страницы ---
st.set_page_config(page_title="Market Monitor", layout="wide")
st.title("🌏 Оперативный Мониторинг Рынка")
st.markdown("Данные в реальном времени: **USD/KZT | Нефть Brent | Золото**")

# Кнопка обновления
if st.button('Обновить данные 🔄'):
    st.cache_data.clear()

# --- Функция загрузки данных ---
def load_data():
    # Тикеры Yahoo Finance:
    # KZT=X -> Курс доллара к тенге
    # BZ=F  -> Нефть Brent (Futures)
    # GC=F  -> Золото (Gold Futures)
    tickers = ['KZT=X', 'BZ=F', 'GC=F']
    
    # Качаем данные за последний год
    df = yf.download(tickers, period="1y", interval="1d", progress=False)
    
    # Исправляем структуру таблицы (как мы делали раньше)
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
    # Получаем последние цены и изменения
    last_prices = df.iloc[-1]
    prev_prices = df.iloc[-2]
    
    # 1. МЕТРИКИ (Крупные цифры)
    col1, col2, col3 = st.columns(3)
    
    # Доллар/Тенге
    kzt_change = last_prices['KZT=X'] - prev_prices['KZT=X']
    col1.metric("🇺🇸🇰🇿 USD/KZT", f"₸{last_prices['KZT=X']:.2f}", f"{kzt_change:.2f}")

    # Нефть Brent
    brent_change = last_prices['BZ=F'] - prev_prices['BZ=F']
    col2.metric("🛢️ Нефть (Brent)", f"${last_prices['BZ=F']:.2f}", f"{brent_change:.2f}")

    # Золото
    gold_change = last_prices['GC=F'] - prev_prices['GC=F']
    col3.metric("🏆 Золото (Gold)", f"${last_prices['GC=F']:.2f}", f"{gold_change:.2f}")

    st.divider()

    # 2. ГРАФИКИ
    st.subheader("Динамика за 1 год")
    
    tab1, tab2, tab3 = st.tabs(["USD/KZT", "Нефть Brent", "Золото"])
    
    with tab1:
        fig_kzt = px.line(df, y='KZT=X', title='Курс Тенге', color_discrete_sequence=['green'])
        st.plotly_chart(fig_kzt, use_container_width=True)
        
    with tab2:
        fig_oil = px.line(df, y='BZ=F', title='Цена на Нефть (Brent)', color_discrete_sequence=['black'])
        st.plotly_chart(fig_oil, use_container_width=True)
        
    with tab3:
        fig_gold = px.line(df, y='GC=F', title='Цена на Золото', color_discrete_sequence=['gold'])
        st.plotly_chart(fig_gold, use_container_width=True)

else:
    st.error("Не удалось загрузить данные. Попробуйте позже.")