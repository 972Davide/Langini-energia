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
        df1 = pd.read_csv(URL_METEO, dtype=str, on_bad_lines='skip')
        df2 = pd.read_csv(URL_EOLICO, skiprows=2, dtype=str, on_bad_lines='skip')
        
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        df1.rename(columns={df1.columns[0]: 'Tempo'}, inplace=True)
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)
        
        # Mappatura Testo -> Numeri
        mappa_meteo = {'Sereno': 1, 'Nuvoloso': 2, 'Pioggia': 3} # Aggiungi altri stati se necessario
        if 'Stato Tempo' in df1.columns:
            df1['Stato Tempo'] = df1['Stato Tempo'].map(mappa_meteo).fillna(0)
            
        # Conversione date
        df1['Tempo'] = pd.to_datetime(df1['Tempo'], errors='coerce')
        df2['Tempo'] = pd.to_datetime(df2['Tempo'], errors='coerce')
        
        # Merge
        df = pd.merge(df1.dropna(subset=['Tempo']), df2.dropna(subset=['Tempo']), on='Tempo', how='inner')
        
        # Conversione numerica sicura
        cols_numeric = ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Mare', 'Umidità', 'Stato Tempo']
        for col in cols_numeric:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].str.replace(',', '.'), errors='coerce')
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore: {e}")
        return None

# --- APP ---
st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_dati()

if df is not None and not df.empty:
    # Filtriamo le ultime 12 ore basandoci sull'ultima riga disponibile
    ultima = df.iloc[-1]
    df_12h = df[df['Tempo'] >= (df['Tempo'].max() - timedelta(hours=12))]
    
    # Visualizzazione
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{ultima.get('Temp. Est', 0):.1f} °C")
    c2.metric("Umidità", f"{ultima.get('Umid. Est.', 0):.0f} %")
    c3.metric("Vento", f"{ultima.get('Vento (m/s)', 0):.1f} m/s")
    c4.metric("Produzione", f"{ultima.get('Watt', 0):.0f} W")
    
    st.markdown("---")
    
    # Grafici (usiamo width='stretch' per i nuovi standard)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Vento vs Watt (12h)")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Bar(x=df_12h['Tempo'], y=df_12h['Vento (m/s)'], name="Vento"), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h['Watt'], name="Watt"), secondary_y=True)
        st.plotly_chart(fig1, width='stretch')
        
    with col2:
        st.subheader("Temp vs Umidità (12h)")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h['Temp. Est'], name="Temp", line=dict(color='orange')), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h['Umid. Est.'], name="Umidità", line=dict(color='cyan')), secondary_y=True)
        st.plotly_chart(fig2, width='stretch')

    # Timer aggiornamento
    bar = st.progress(0)
    for i in range(180):
        time.sleep(1)
        bar.progress((i + 1) / 180)
    st.rerun()
else:
    st.warning("Dati non leggibili. Verifica che il file Google Sheets sia pubblico.")
    time.sleep(10)
    st.rerun()
