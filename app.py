import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- URL FOGLI ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Cruscotto Integrato", layout="wide")

@st.cache_data(ttl=60)
def carica_e_unisci():
    try:
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2)
        
        # Pulizia colonne
        df1 = df1.loc[:, ~df1.columns.str.contains('^Unnamed')]
        df2 = df2.loc[:, ~df2.columns.str.contains('^Unnamed')]
        df1.rename(columns={df1.columns[0]: 'Tempo'}, inplace=True)
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)
        
        # Formattazione Date
        for df in [df1, df2]:
            df['Tempo'] = pd.to_datetime(df['Tempo'].astype(str).str.replace('.', ':', regex=False), format='mixed', dayfirst=True).dt.floor('min')
        
        # Unione
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        # Pulizia numerica
        for col in ['Vento (m/s)', 'Watt']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
        return df.sort_values(by='Tempo')
    except Exception:
        return None

# --- INTERFACCIA ---
st.title("🌦️ Langini: Cruscotto Integrato")
df = carica_e_unisci()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    
    # Metriche
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{ultima.get('Temperatura', 0)} °C")
    c2.metric("Vento", f"{ultima.get('Vento (m/s)', 0)} m/s")
    c3.metric("Produzione", f"{ultima.get('Watt', 0)} W")
    c4.metric("Pressione", f"{ultima.get('Pressione Mare', 0)} hPa")
    
    st.markdown("---")
    
    # Grafico Combinato
    st.subheader("📊 Analisi Temporale: Vento vs Watt")
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Barre Vento
    fig.add_trace(
        go.Bar(x=df['Tempo'].tail(50), y=df['Vento (m/s)'].tail(50), name="Vento (m/s)", marker_color='skyblue'),
        secondary_y=False,
    )
    # Linea Watt
    fig.add_trace(
        go.Scatter(x=df['Tempo'].tail(50), y=df['Watt'].tail(50), name="Watt", line=dict(color='yellow', width=3)),
        secondary_y=True,
    )

    fig.update_layout(template="plotly_dark", showlegend=True)
    fig.update_yaxes(title_text="Velocità Vento (m/s)", secondary_y=False)
    fig.update_yaxes(title_text="Produzione (Watt)", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(df.tail(10))
else:
    st.warning("Caricamento in corso o dati non sincronizzati.")
