import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURAZIONE ---
PREZZO_GSE_KW = 0.15 
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

DELTA_ORE = 1.0 / 60.0

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

# --- CARICAMENTO "AUTO-ADATTIVO" ---
@st.cache_data(ttl=60)
def carica_e_elabora():
    try:
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO)
        
        for df in [df1, df2]:
            df.columns = df.columns.str.strip()
            df.rename(columns={df.columns[0]: 'Tempo'}, inplace=True)
            df['Tempo'] = pd.to_datetime(df['Tempo'], format='mixed', dayfirst=True, errors='coerce')
            df.dropna(subset=['Tempo'], inplace=True)

        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        # TROVA I NOMI DELLE COLONNE REALI
        # Cerchiamo colonne che contengono parole chiave, ignorando maiuscole/minuscole
        col_map = {}
        for col in df.columns:
            c_low = col.lower()
            if 'watt' in c_low: col_map[col] = 'Watt'
            elif 'vento' in c_low: col_map[col] = 'Vento'
            elif 'temp' in c_low: col_map[col] = 'Temperatura'
            elif 'pression' in c_low: col_map[col] = 'Pressione'
        
        df.rename(columns=col_map, inplace=True)
        
        # Pulizia numerica basata sui nuovi nomi
        for col in ['Watt', 'Vento', 'Temperatura', 'Pressione']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore caricamento: {e}")
        return None

df = carica_e_elabora()

# --- INTERFACCIA ---
if df is not None and not df.empty:
    # Verifichiamo che la colonna Watt esista dopo la rinomina
    if 'Watt' not in df.columns:
        st.error(f"Colonne trovate nel foglio: {list(df.columns)}. Non trovo una colonna valida per i Watt.")
    else:
        now = pd.Timestamp.now()
        e_sett = df[df['Tempo'] >= (now - pd.Timedelta(days=7))]['Watt'].sum() * DELTA_ORE / 1000.0
        
        st.subheader("🔋 Produzione Energetica")
        st.metric("Energia Settimanale", f"{e_sett:.1f} kWh")
        
        # Grafico
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Tempo'], y=df['Watt'], name="Watt"))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Dati non trovati. Controlla la pubblicazione su Google Sheets.")
