import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Langini: Dashboard", layout="wide")

URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=60)
def carica_dati():
    try:
        # Caricamento
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2)
        
        # Pulizia intestazioni (rimozione spazi bianchi)
        for df in [df1, df2]:
            df.columns = df.columns.str.strip()
            
        # Rename dinamico basato su posizione per sicurezza
        df1 = df1.rename(columns={df1.columns[0]: 'Tempo'})
        df2 = df2.rename(columns={df2.columns[0]: 'Tempo'})
        
        # Conversione tempo
        for df in [df1, df2]:
            df['Tempo'] = pd.to_datetime(df['Tempo'].astype(str).str.replace('.', ':', regex=False), format='mixed', dayfirst=True)
            
        # Merge
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        # Pulizia numerica robusta
        cols_to_fix = ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Mare']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore nel caricamento: {e}")
        return None

# --- INTERFACCIA ---
st.title("🌦️ Langini: Cruscotto Integrato")

if st.button("Aggiorna Dati"):
    st.cache_data.clear()

with st.spinner('Recupero dati in corso...'):
    df = carica_dati()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    
    # Metriche in una riga
    cols = st.columns(4)
    cols[0].metric("Temperatura", f"{ultima.get('Temperatura', 0):.1f} °C")
    cols[1].metric("Vento", f"{ultima.get('Vento (m/s)', 0):.1f} m/s")
    cols[2].metric("Produzione", f"{ultima.get('Watt', 0):.0f} W")
    cols[3].metric("Pressione", f"{ultima.get('Pressione Mare', 0):.0f} hPa")
    
    st.markdown("---")
    
    # Grafico
    st.subheader("📊 Analisi Temporale: Vento vs Watt")
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    df_plot = df.tail(50)
    fig.add_trace(
    go.Bar(
      x=df_plot['Tempo'],
      y=df_plot['Vento (m/s)'],
      name="Vento",
      marker_color='rgba(135, 206, 235, 0.6)'
      ),
      secondary_y=False)
    fig.add_trace(go.Scatter(x=df_plot['Tempo'], y=df_plot['Watt'], name="Watt", line=dict(color='#FFD700', width=3)), secondary_y=True)

    fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=30, b=20))
    fig.update_yaxes(title_text="Vento (m/s)", secondary_y=False)
    fig.update_yaxes(title_text="Potenza (Watt)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Dati non disponibili o errore di sincronizzazione.")
