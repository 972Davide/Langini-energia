import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURAZIONE ---
PREZZO_GSE_KW = 0.15 
# Inserisci qui i tuoi link definitivi (pubblicati come CSV da Google Sheets)
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

# --- TESTATA ---
c_title, c_button = st.columns([0.85, 0.15])
with c_title:
    st.title("⚡ Langini: Intelligenza Energetica")
with c_button:
    if st.button('Aggiorna Dati'):
        st.cache_data.clear()
        st.rerun()

st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")

@st.cache_data(ttl=600)
def carica_e_elabora():
    try:
        # Leggiamo solo le ultime 5000 righe per non saturare la RAM
        df1 = pd.read_csv(URL_METEO).tail(5000)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2).tail(5000)
        
        for df in [df1, df2]:
            df.columns = df.columns.str.strip()
            df.rename(columns={df.columns[0]: 'Tempo'}, inplace=True)
            df['Tempo'] = pd.to_datetime(df['Tempo'], format='mixed', dayfirst=True, errors='coerce')
        
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        # Conversione in numeri
        for col in ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Locale']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        # --- FILTRO PULIZIA (Sanity Check) ---
        df.loc[(df['Temperatura'] < -20) | (df['Temperatura'] > 60), 'Temperatura'] = np.nan
        df.loc[(df['Vento (m/s)'] < 0) | (df['Vento (m/s)'] > 50), 'Vento (m/s)'] = np.nan
        df.loc[(df['Watt'] < 0) | (df['Watt'] > 15000), 'Watt'] = np.nan
        df.loc[(df['Pressione Locale'] < 800) | (df['Pressione Locale'] > 1200), 'Pressione Locale'] = np.nan
        
        return df.dropna(subset=['Tempo']).sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore caricamento: {e}")
        return None

# --- INTERFACCIA ---
df = carica_e_elabora()

if df is not None and not df.empty:
    # Filtro 24 ore basato sull'ultimo dato presente
    ultima_data = df['Tempo'].max()
    df_24h = df[df['Tempo'] >= (ultima_data - pd.Timedelta(hours=24))]
    
    # 1. Metriche
    st.subheader("🌡️ Meteo Ultime 24h")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperatura Media", f"{df_24h['Temperatura'].mean():.1f}°C")
    c2.metric("Vento Massimo", f"{df_24h['Vento (m/s)'].max():.1f} m/s")
    c3.metric("Pressione", f"{df_24h['Pressione Locale'].mean():.0f} hPa")

    # 2. Grafico
    st.subheader("📊 Analisi Vento vs Watt (24h)")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df_24h['Tempo'], y=df_24h['Vento (m/s)'], name="Vento (m/s)"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_24h['Tempo'], y=df_24h['Watt'], name="Watt", line=dict(width=3)), secondary_y=True)
    fig.update_layout(template="plotly_dark", height=500)
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Dati non disponibili o corruzione rilevata nei fogli.")
