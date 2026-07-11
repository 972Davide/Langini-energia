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
def carica_dati():
    try:
        # Caricamento con gestione errori per righe malformate
        df1 = pd.read_csv(URL_METEO, on_bad_lines='skip')
        df2 = pd.read_csv(URL_EOLICO, skiprows=2, on_bad_lines='skip')
        
        # Pulizia nomi colonne (rimuove spazi invisibili)
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        
        # Rinominiamo le colonne chiave per il merge
        # Nel Meteo la colonna è 'Data/Ora', nell'eolico è la prima
        df1.rename(columns={'Data/Ora': 'Tempo'}, inplace=True)
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)
        
        # Conversione date forzata
        df1['Tempo'] = pd.to_datetime(df1['Tempo'], dayfirst=True, errors='coerce')
        df2['Tempo'] = pd.to_datetime(df2['Tempo'], dayfirst=True, errors='coerce')
        
        # Unione dei dati
        df = pd.merge(df1.dropna(subset=['Tempo']), df2.dropna(subset=['Tempo']), on='Tempo', how='inner')
        
        # Pulizia colonne numeriche: rimuove virgole e converte in numeri
        cols_target = ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Mare', 'Umidità']
        for col in cols_target:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        return None

# --- APP ---
st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_dati()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    df_12h = df[df['Tempo'] >= (df['Tempo'].max() - timedelta(hours=12))]
    
    # Metriche
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{ultima.get('Temperatura', 0):.1f} °C")
    c2.metric("Umidità", f"{ultima.get('Umidità', 0):.0f} %")
    c3.metric("Vento", f"{ultima.get('Vento (m/s)', 0):.1f} m/s")
    c4.metric("Produzione", f"{ultima.get('Watt', 0):.0f} W")
    
    st.markdown("---")
    
    # Grafici
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Vento vs Watt (12h)")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Bar(x=df_12h['Tempo'], y=df_12h.get('Vento (m/s)', 0), name="Vento"), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h.get('Watt', 0), name="Watt"), secondary_y=True)
        st.plotly_chart(fig1, use_container_width=True)
        
    with col2:
        st.subheader("Temp vs Umidità (12h)")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h.get('Temperatura', 0), name="Temp", line=dict(color='orange')), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h.get('Umidità', 0), name="Umidità", line=dict(color='cyan')), secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True)

    st.info("Dati aggiornati. La pagina si ricaricherà automaticamente tra 3 minuti.")
    time.sleep(180)
    st.rerun()
else:
    st.warning("Dati non caricati. Verifica che i fogli Google siano pubblici e le colonne esistano.")
    time.sleep(10)
    st.rerun()
