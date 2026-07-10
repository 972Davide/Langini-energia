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
        # Carica
        df1 = pd.read_csv(URL_METEO, on_bad_lines='skip').tail(5000)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2, on_bad_lines='skip').tail(5000)
        
        # Pulizia colonna Data/Ora
        # Formato Meteo: 10/07/2026 19.26.05 -> sostituiamo punti con due punti
        df1.rename(columns={df1.columns[0]: 'Tempo'}, inplace=True)
        df1['Tempo'] = pd.to_datetime(df1['Tempo'].str.replace('.', ':'), dayfirst=True)
        
        # Formato Eolico
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)
        df2['Tempo'] = pd.to_datetime(df2['Tempo'], dayfirst=True)
        
        # Arrotondiamo al MINUTO per permettere l'unione
        df1['Tempo'] = df1['Tempo'].dt.floor('min')
        df2['Tempo'] = df2['Tempo'].dt.floor('min')
        
        # Merge basato sul minuto
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        # Conversione numeri (gestione virgola/punto)
        for col in ['Temperatura', 'Vento (m/s)', 'Watt']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore: {e}")
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
