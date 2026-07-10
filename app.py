import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURAZIONE ---
PREZZO_GSE_KW = 0.15 
# Link uniformati per garantire lettura corretta su Cloud e Locale
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

DELTA_ORE = 1.0 / 60.0

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

# --- CARICAMENTO E PULIZIA ---
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
            df['Tempo'] = df['Tempo'].dt.floor('min')
        
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        # Pulizia numerica
        for col in ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Locale']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        # FILTRO REALTÀ (Esclude i valori anomali visti negli screenshot)
        df = df[
            (df['Temperatura'] > -20) & (df['Temperatura'] < 50) &
            (df['Pressione Locale'] > 900) & (df['Pressione Locale'] < 1100) &
            (df['Watt'] >= 0) & (df['Watt'] < 10000)
        ]
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore caricamento: {e}")
        return None

df = carica_e_elabora()

# --- INTERFACCIA ---
if df is not None and not df.empty:
    now = pd.Timestamp.now()
    
    # Calcoli Statistici depurati
    df_2026 = df[df['Tempo'].dt.year == 2026]
    energia_anno_corrente = df_2026['Watt'].sum() * DELTA_ORE / 1000.0
    giorni_passati = max((now - pd.Timestamp(year=2026, month=1, day=1)).days, 1)
    media_giornaliera = energia_anno_corrente / giorni_passati
    giorni_rimanenti = max((pd.Timestamp(year=2026, month=12, day=31) - now).days, 0)
    stima_annua_finire = energia_anno_corrente + (media_giornaliera * giorni_rimanenti)
    
    e_sett = df[df['Tempo'] >= (now - pd.Timedelta(days=7))]['Watt'].sum() * DELTA_ORE / 1000.0
    e_mese = df[df['Tempo'] >= (now - pd.Timedelta(days=30))]['Watt'].sum() * DELTA_ORE / 1000.0

    st.subheader("🔋 Produzione ed Economia (Dati Depurati)")
    ee1, ee2, ee3 = st.columns(3)
    ee1.metric("Energia Settimanale", f"{e_sett:.1f} kWh", f"€ {e_sett * PREZZO_GSE_KW:.2f}")
    ee2.metric("Energia Mensile (30gg)", f"{e_mese:.1f} kWh", f"€ {e_mese * PREZZO_GSE_KW:.2f}")
    ee3.metric("Stima Annua (A finire)", f"{stima_annua_finire:.1f} kWh", f"Media: {media_giornaliera:.2f} kWh/gg")

    # Grafico pulito
    df_oggi = df[df['Tempo'].dt.date == now.date()]
    if not df_oggi.empty:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=df_oggi['Tempo'], y=df_oggi['Vento (m/s)'], name="Vento"), secondary_y=False)
        fig.add_trace(go.Scatter(x=df_oggi['Tempo'], y=df_oggi['Watt'], name="Watt"), secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Dati non trovati o filtrati. Verifica che i fogli contengano dati validi.")
