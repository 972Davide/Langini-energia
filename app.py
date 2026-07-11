import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import time

URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=300)
def carica_e_unisci():
    try:
        # Carica CSV
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2, low_memory=False)
        
        # Pulisce colonne vuote
        df1 = df1.loc[:, ~df1.columns.str.contains('^Unnamed')]
        df2 = df2.loc[:, ~df2.columns.str.contains('^Unnamed')]
        
        # Rinomina la colonna dei tempi in 'Tempo' per poter fare il merge
        df1.rename(columns={df1.columns[0]: 'Tempo'}, inplace=True)
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)
        
        # Formattazione data
        for df in [df1, df2]:
            df['Tempo'] = pd.to_datetime(df['Tempo'].astype(str).str.replace('.', ':', regex=False), format='mixed', dayfirst=True).dt.floor('min')
        
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        # Conversione sicura in numeri (gestisce errori come 'Sereno')
        # Usiamo i nomi esatti che appaiono nella tua tabella
        cols_to_clean = ['Vento (m/s)', 'Temp. Est', 'Umid. Est.', 'Watt']
        for col in cols_to_clean:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
        return None

# --- INTERFACCIA ---
st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_e_unisci()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    adesso = df['Tempo'].max()
    df_12h = df[df['Tempo'] >= (adesso - timedelta(hours=12))]
    
    # Calcolo proiezione annuale
    giorni_passati = (adesso - df['Tempo'].min()).days + 1
    media_giornaliera = df['Watt'].sum() / giorni_passati
    proiezione = media_giornaliera * 365
    
    # --- METRICHE ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{ultima.get('Temp. Est', 0):.1f} °C")
    c2.metric("Umidità", f"{ultima.get('Umid. Est.', 0):.0f} %")
    c3.metric("Vento", f"{ultima.get('Vento (m/s)', 0):.1f} m/s")
    c4.metric("Produzione (Totale)", f"{df['Watt'].sum():,.0f} W", f"Proj: {proiezione:,.0f} W")
    
    st.markdown("---")
    
    # Grafici
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Vento vs Watt (12h)")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Bar(x=df_12h['Tempo'], y=df_12h['Vento (m/s)'], name="Vento"), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h['Watt'], name="Watt"), secondary_y=True)
        fig1.update_layout(template="plotly_dark")
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_g2:
        st.subheader("🌡️ Temp vs Umidità (12h)")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h['Temp. Est'], name="Temp (°C)", line=dict(color='orange')), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h['Umid. Est.'], name="Umidità (%)", line=dict(color='cyan', dash='dot')), secondary_y=True)
        fig2.update_layout(template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

    # Countdown
    st.caption("Prossimo aggiornamento tra:")
    bar = st.progress(0)
    for i in range(180):
        time.sleep(1)
        bar.progress((i + 1) / 180)
    st.rerun()
else:
    st.warning("Caricamento in corso o dati non sincronizzati.")
    time.sleep(10)
    st.rerun()
