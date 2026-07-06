import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURAZIONE ---
PREZZO_GSE_KW = 0.15 
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

# --- CSS ---
st.markdown("""
    <style>
    div.stButton button { height: 50px; width: 100%; font-size: 18px; background-color: #ff4b4b; color: white; border-radius: 8px; font-weight: bold; }
    .big-metric { font-size: 20px; color: #888; }
    .big-value { font-size: 40px; font-weight: bold; color: white; margin-bottom: 5px; }
    .small-trend { font-size: 16px; color: #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# --- TESTATA ---
c_title, c_button = st.columns([0.85, 0.15])
with c_title:
    st.title("⚡ Langini: Intelligenza Energetica")
with c_button:
    if st.button('Aggiorna Dati'): st.rerun()
st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")

@st.cache_data(ttl=60)
def carica_e_elabora():
    try:
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2)
        for df in [df1, df2]:
            df.columns = df.columns.str.strip()
            df.rename(columns={df.columns[0]: 'Tempo'}, inplace=True)
            df['Tempo'] = pd.to_datetime(df['Tempo'].astype(str).str.replace('.', ':', regex=False), format='mixed', dayfirst=True).dt.floor('min')
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        for col in ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Locale']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
        return df.sort_values(by='Tempo')
    except Exception: return None

df = carica_e_elabora()

if df is not None and not df.empty:
    now = pd.Timestamp.now()
    df_oggi = df[df['Tempo'].dt.date == now.date()]
    
    # 1. METEO CON FRECCE E MEDIE
    st.subheader("🌡️ Meteo Oggi: Analisi")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="big-metric">Temperatura</div><div class="big-value">{df_oggi["Temperatura"].max():.1f}°C</div><div class="small-trend">↑ Med: {df_oggi["Temperatura"].mean():.1f}°C</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="big-metric">Velocità Vento</div><div class="big-value">{df_oggi["Vento (m/s)"].max():.1f} m/s</div><div class="small-trend">↑ Med: {df_oggi["Vento (m/s)"].mean():.1f} m/s</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="big-metric">Pressione</div><div class="big-value">{df_oggi["Pressione Locale"].max():.0f} hPa</div><div class="small-trend">↑ Med: {df_oggi["Pressione Locale"].mean():.0f} hPa</div>', unsafe_allow_html=True)

    # 2. PRODUZIONE ED ECONOMIA (Logica Separata)
    st.subheader("🔋 Produzione ed Economia (Stima GSE)")
    e_sett = df[df['Tempo'] >= (now - pd.Timedelta(days=7))]['Watt'].sum() / 1000
    e_mese = df[df['Tempo'] >= (now - pd.Timedelta(days=30))]['Watt'].sum() / 1000
    e_anno = (df['Watt'].sum() / 1000 / (df['Tempo'].max() - df['Tempo'].min()).days * 365) if (df['Tempo'].max() - df['Tempo'].min()).days > 0 else e_mese * 12
    
    ee1, ee2, ee3 = st.columns(3)
    ee1.markdown(f'<div class="big-metric">Energia Settimanale</div><div class="big-value">{e_sett:.1f} kWh</div><div class="small-trend">↑ € {e_sett * PREZZO_GSE_KW:.2f}</div>', unsafe_allow_html=True)
    ee2.markdown(f'<div class="big-metric">Energia Mensile</div><div class="big-value">{e_mese:.1f} kWh</div><div class="small-trend">↑ € {e_mese * PREZZO_GSE_KW:.2f}</div>', unsafe_allow_html=True)
    ee3.markdown(f'<div class="big-metric">Stima Annuale</div><div class="big-value">{e_anno:.1f} kWh</div>', unsafe_allow_html=True)

    # ... [Resto del codice per Simulatore e Grafico rimane invariato]
