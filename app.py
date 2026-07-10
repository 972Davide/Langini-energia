import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURAZIONE ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=600)
def carica_e_elabora():
    try:
        # Leggiamo i dati
        df1 = pd.read_csv(URL_METEO).tail(100)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2).tail(100)
        
        # DEBUG: Stampiamo le colonne per vedere se sono giuste
        st.write("Colonne Meteo:", df1.columns.tolist())
        st.write("Colonne Eolico:", df2.columns.tolist())
        
        # Procediamo come prima
        for df in [df1, df2]:
            df.columns = df.columns.str.strip()
            df.rename(columns={df.columns[0]: 'Tempo'}, inplace=True)
            df['Tempo'] = pd.to_datetime(df['Tempo'], format='mixed', errors='coerce')
        
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        # DEBUG: Vediamo se dopo il merge il file è vuoto
        st.write("Righe dopo il merge:", len(df))
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        return None

# --- INTERFACCIA ---
st.title("⚡ Langini: Intelligenza Energetica")
df = carica_e_elabora()

if df is not None and not df.empty:
    ultima_data = df['Tempo'].max()
    df_24h = df[df['Tempo'] >= (ultima_data - pd.Timedelta(hours=24))]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperatura", f"{df_24h['Temperatura'].mean():.1f}°C")
    c2.metric("Watt (Media)", f"{df_24h['Watt'].mean():.0f} W")
    c3.metric("Pressione", f"{df_24h['Pressione Locale'].mean():.0f} hPa")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df_24h['Tempo'], y=df_24h['Vento (m/s)'], name="Vento"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_24h['Tempo'], y=df_24h['Watt'], name="Watt"), secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Dati non trovati o formato non compatibile. Controlla il foglio Google.")
