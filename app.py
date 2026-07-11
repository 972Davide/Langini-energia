import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import time

# --- CONFIGURAZIONE ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=300)
def carica_e_unisci():
    try:
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2)
        df1.rename(columns={df1.columns[0]: 'Tempo'}, inplace=True)
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)
        for df in [df1, df2]:
            df['Tempo'] = pd.to_datetime(df['Tempo'].astype(str).str.replace('.', ':', regex=False), format='mixed', dayfirst=True).dt.floor('min')
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        for col in df.columns:
            if col != 'Tempo':
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        return df.sort_values(by='Tempo')
    except: return None

# --- UI PRINCIPALE ---
st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_e_unisci()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    adesso = df['Tempo'].max()
    
    # Identificazione colonne dinamica
    col_temp = next((c for c in df.columns if 'Temperatur' in c), None)
    col_umid = next((c for c in df.columns if 'Umid' in c), None)
    col_vento = next((c for c in df.columns if 'Vento' in c), None)
    col_press = next((c for c in df.columns if 'Pression' in c), None)
    col_watt = next((c for c in df.columns if 'Watt' in c), None)

    # Metriche e Grafici (stessa logica di prima)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Temperatura", f"{ultima.get(col_temp, 0):.1f} °C")
    c2.metric("Umidità", f"{ultima.get(col_umid, 0):.0f} %")
    c3.metric("Vento", f"{ultima.get(col_vento, 0):.1f} m/s")
    c4.metric("Produzione", f"{df[col_watt].sum():,.0f} W")
    c5.metric("Pressione", f"{ultima.get(col_press, 0):.0f} hPa")
    
    # --- AGGIORNAMENTO SICURO ---
    st.markdown("---")
    st.caption("Aggiornamento automatico in corso...")
    bar = st.progress(0)
    
    # Ciclo di attesa senza bloccare l'interfaccia con errori
    for i in range(180):
        time.sleep(1)
        bar.progress((i + 1) / 180)
    
    st.rerun()
else:
    st.warning("Caricamento in corso...")
    time.sleep(5)
    st.rerun()
