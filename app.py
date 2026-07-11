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
        # Aggiunto low_memory=False per evitare crash con tipi misti
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2, low_memory=False)
        
        df1 = df1.loc[:, ~df1.columns.str.contains('^Unnamed')]
        df2 = df2.loc[:, ~df2.columns.str.contains('^Unnamed')]
        df1.rename(columns={df1.columns[0]: 'Tempo'}, inplace=True)
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)
        
        for df in [df1, df2]:
            df['Tempo'] = pd.to_datetime(df['Tempo'].astype(str).str.replace('.', ':', regex=False), format='mixed', dayfirst=True).dt.floor('min')
        
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        # Pulizia forzata solo su colonne numeriche note
        for col in df.columns:
            if col not in ['Tempo']:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore caricamento: {e}")
        return None

st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_e_unisci()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    adesso = df['Tempo'].max()
    
    col_temp = next((c for c in df.columns if 'Temperatur' in c), None)
    col_umid = next((c for c in df.columns if 'Umid' in c), None)
    col_vento = next((c for c in df.columns if 'Vento' in c), None)
    col_press = next((c for c in df.columns if 'Pression' in c), None)
    col_watt = next((c for c in df.columns if 'Watt' in c), None)

    df_12h = df[df['Tempo'] >= (adesso - timedelta(hours=12))]
    
    # Metriche e Grafici aggiornati con width='stretch'
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Temperatura", f"{ultima.get(col_temp, 0):.1f} °C")
    c2.metric("Umidità", f"{ultima.get(col_umid, 0):.0f} %")
    c3.metric("Vento", f"{ultima.get(col_vento, 0):.1f} m/s")
    c4.metric("Produzione (Totale)", f"{df[col_watt].sum():,.0f} W")
    c5.metric("Pressione", f"{ultima.get(col_press, 0):.0f} hPa")
    
    st.markdown("---")
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Vento vs Watt (12h)")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Bar(x=df_12h['Tempo'], y=df_12h[col_vento], name="Vento"), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h[col_watt], name="Watt"), secondary_y=True)
        st.plotly_chart(fig1, width='stretch')
    with col_g2:
        st.subheader("🌡️ Temp vs Umidità (12h)")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h[col_temp], name="Temp"), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h[col_umid], name="Umidità"), secondary_y=True)
        st.plotly_chart(fig2, width='stretch')

    bar = st.progress(0)
    for i in range(180):
        time.sleep(1)
        bar.progress((i + 1) / 180)
    st.rerun()
else:
    st.warning("Caricamento in corso o dati non sincronizzati.")
    time.sleep(10)
    st.rerun()
