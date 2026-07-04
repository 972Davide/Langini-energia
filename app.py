import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURAZIONE ---
PREZZO_GSE_KW = 0.15 # Stima media valore GSE per kWh
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=60)
def carica_e_elabora():
    try:
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2)
        for df in [df1, df2]:
            df.columns = df.columns.str.strip()
            df.rename(columns={df.columns[0]: 'Tempo'}, inplace=True)
            df['Tempo'] = pd.to_datetime(df['Tempo'].astype(str).str.replace('.', ':', regex=False), format='mixed', dayfirst=True).dt.floor('min')
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        for col in ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Locale']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
        return df.sort_values(by='Tempo')
    except Exception:
        return None

# --- INTERFACCIA ---
st.title("⚡ Langini: Intelligenza Energetica")
df = carica_e_elabora()

if df is not None and not df.empty:
    now = pd.Timestamp.now()
    df_oggi = df[df['Tempo'].dt.date == now.date()]
    
    # 1. Metriche Meteo (Massima e Media)
    st.subheader("🌡️ Meteo Oggi: Analisi")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperatura", f"Max: {df_oggi['Temperatura'].max():.1f}°C", f"Med: {df_oggi['Temperatura'].mean():.1f}°C")
    c2.metric("Vento", f"Max: {df_oggi['Vento (m/s)'].max():.1f} m/s", f"Med: {df_oggi['Vento (m/s)'].mean():.1f} m/s")
    c3.metric("Pressione", f"Max: {df_oggi['Pressione Locale'].max():.0f} hPa", f"Med: {df_oggi['Pressione Locale'].mean():.0f} hPa")

    # 2. Metriche Energia & GSE
    st.subheader("🔋 Produzione ed Economia (Stima GSE)")
    e_kw = df[df['Tempo'] >= (now - pd.Timedelta(days=7))]['Watt'].sum()/1000
    e_mo = df[df['Tempo'] >= (now - pd.Timedelta(days=30))]['Watt'].sum()/1000
    
    ee1, ee2, ee3 = st.columns(3)
    ee1.metric("Energia Settimanale", f"{e_kw:.1f} kWh", f"€ {e_kw * PREZZO_GSE_KW:.2f}")
    ee2.metric("Energia Mensile", f"{e_mo:.1f} kWh", f"€ {e_mo * PREZZO_GSE_KW:.2f}")
    ee3.metric("Stima Annuale", f"{df[df['Tempo'] >= (now - pd.Timedelta(days=365))]['Watt'].sum()/1000:.1f} kWh")

    # 3. Previsioni e Tendenza
    st.markdown("---")
    st.subheader("🔮 Simulatore e Tendenza Meteo")
    col_pred, col_meteo = st.columns(2)
    
    with col_pred:
        m, q = np.polyfit(df['Vento (m/s)'].dropna(), df['Watt'].dropna(), 1)
        vento_in = st.slider("Simula velocità vento (m/s)", 0.0, 20.0, 5.0)
        st.metric("Produzione Stimata", f"{max(0, (m * vento_in) + q):.2f} W")
    
    with col_meteo:
        if len(df) > 180:
            var = df['Pressione Locale'].iloc[-1] - df['Pressione Locale'].iloc[-180]
            st.metric("Variazione Pressione (3h)", f"{var:.2f} hPa")
            if var > 0.5: st.info("Tendenza: In miglioramento")
            elif var < -0.5: st.warning("Tendenza: Instabilità in arrivo")
            else: st.success("Tendenza: Stabile")

    # 4. Grafico
    st.subheader("📊 Analisi Vento vs Watt (Oggi)")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df_oggi['Tempo'], y=df_oggi['Vento (m/s)'], name="Vento", marker_color='skyblue'), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_oggi['Tempo'], y=df_oggi['Watt'], name="Watt", line=dict(color='yellow', width=3)), secondary_y=True)
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Dati non disponibili.")
