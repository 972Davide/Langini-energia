import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURAZIONE ---
PREZZO_GSE_KW = 0.15 
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

st.markdown("""
    <style>
    /* Pulsante Aggiorna */
    div.stButton button { height: 50px; width: 100%; font-size: 18px; background-color: #ff4b4b; color: white; border-radius: 8px; }
    
    /* Box Personalizzato per dati grandi */
    .big-metric { font-size: 20px; color: #888; margin-bottom: -10px; }
    .big-value { font-size: 42px; font-weight: bold; color: white; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- TESTATA ---
c_title, c_button = st.columns([0.85, 0.15])
with c_title:
    st.title("⚡ Langini: Intelligenza Energetica")
with c_button:
    if st.button('Aggiorna Dati'):
        st.rerun()
st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")

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
df = carica_e_elabora()

if df is not None and not df.empty:
    now = pd.Timestamp.now()
    df_oggi = df[df['Tempo'].dt.date == now.date()]
    
    st.subheader("🌡️ Meteo Oggi")
    c1, c2, c3 = st.columns(3)
    c1.metric("Temperatura", f"{df_oggi['Temperatura'].max():.1f}°C")
    c2.metric("Velocità Vento", f"{df_oggi['Vento (m/s)'].max():.1f} m/s")
    c3.metric("Pressione", f"{df_oggi['Pressione Locale'].max():.0f} hPa")

st.subheader("🔋 Produzione ed Economia")
    
    # Filtro preciso per gli ultimi 7 giorni
    mask_week = df['Tempo'] >= (now - pd.Timedelta(days=7))
    e_kw = df[mask_week]['Watt'].sum() / 1000
    
    # Filtro preciso per gli ultimi 30 giorni
    mask_month = df['Tempo'] >= (now - pd.Timedelta(days=30))
    e_mo = df[mask_month]['Watt'].sum() / 1000
    
    # Calcolo Stima Annuale (media giornaliera * 365)
    giorni_disponibili = (df['Tempo'].max() - df['Tempo'].min()).days
    if giorni_disponibili > 0:
        stima_annuale = (df['Watt'].sum() / 1000 / giorni_disponibili) * 365
    else:
        stima_annuale = e_mo * 12 # fallback se abbiamo pochi giorni
    
    ee1, ee2, ee3 = st.columns(3)
    
    # Usiamo le nostre classi personalizzate per le dimensioni corrette
    with ee1:
        st.markdown('<div class="big-metric">Energia Settimanale</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-value">{e_kw:.1f} kWh</div>', unsafe_allow_html=True)
        
    with ee2:
        st.markdown('<div class="big-metric">Energia Mensile</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-value">{e_mo:.1f} kWh</div>', unsafe_allow_html=True)
        
    with ee3:
        st.markdown('<div class="big-metric">Stima Annuale</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-value">{stima_annuale:.1f} kWh</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🔮 Simulatore e Tendenza")
    col_pred, col_meteo = st.columns(2)
    
    with col_pred:
        st.markdown('<div class="card"><h4>Simulatore</h4>', unsafe_allow_html=True)
        m, q = np.polyfit(df['Vento (m/s)'].dropna(), df['Watt'].dropna(), 1)
        vento_in = st.slider("Velocità Vento (m/s)", 0.0, 20.0, 5.0)
        st.metric("Produzione Stimata", f"{max(0, (m * vento_in) + q):.2f} W")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_meteo:
        st.markdown('<div class="card"><h4>Tendenza Meteo</h4>', unsafe_allow_html=True)
        if len(df) > 180:
            var = df['Pressione Locale'].iloc[-1] - df['Pressione Locale'].iloc[-180]
            st.metric("Variazione Pressione (3h)", f"{var:.2f} hPa")
            if var > 0.5: st.success("Stato: In miglioramento")
            elif var < -0.5: st.error("Stato: Instabilità in arrivo")
            else: st.info("Stato: Stabile")
        st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("📊 Analisi Vento vs Watt (Oggi)")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df_oggi['Tempo'], y=df_oggi['Vento (m/s)'], name="Vento", marker_color='skyblue'), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_oggi['Tempo'], y=df_oggi['Watt'], name="Watt", line=dict(color='yellow', width=3)), secondary_y=True)
    fig.update_layout(template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Dati non disponibili.")
