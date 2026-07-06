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

# --- CSS DEFINITIVO (SCALABILE E GRANDE) ---
st.markdown("""
    <style>
    div.stButton button { height: 60px; width: 100%; font-size: 20px !important; background-color: #ff4b4b; color: white; border-radius: 10px; font-weight: bold; }
    .big-metric { font-size: 26px !important; color: #aaaaaa; margin-bottom: 10px; font-weight: 600; }
    .big-value { font-size: 55px !important; font-weight: 900 !important; color: white; margin-bottom: 25px; }
    .card { background-color: #262730; padding: 30px; border-radius: 15px; border: 1px solid #454545; margin-bottom: 20px; }
    .card h4 { font-size: 32px !important; margin-bottom: 20px; }
    div[role="alert"] { font-size: 24px !important; font-weight: bold !important; padding: 25px !important; }
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
    
    # SEZIONE METEO
    st.subheader("🌡️ Meteo Oggi: Analisi")
    c1, c2, c3 = st.columns(3)
    dati_meteo = [("Temperatura", f"{df_oggi['Temperatura'].max():.1f}°C"), 
                  ("Velocità Vento", f"{df_oggi['Vento (m/s)'].max():.1f} m/s"), 
                  ("Pressione", f"{df_oggi['Pressione Locale'].max():.0f} hPa")]
    for col, (label, val) in zip([c1, c2, c3], dati_meteo):
        with col:
            st.markdown(f'<div class="big-metric">{label}</div><div class="big-value">{val}</div>', unsafe_allow_html=True)

    # SEZIONE PRODUZIONE
    st.subheader("🔋 Produzione ed Economia (Stima GSE)")
    e_kw = df[df['Tempo'] >= (now - pd.Timedelta(days=7))]['Watt'].sum() / 1000
    e_mo = df[df['Tempo'] >= (now - pd.Timedelta(days=30))]['Watt'].sum() / 1000
    giorni = (df['Tempo'].max() - df['Tempo'].min()).days
    stima_ann = (df['Watt'].sum() / 1000 / giorni * 365) if giorni > 0 else e_mo * 12
    
    ee1, ee2, ee3 = st.columns(3)
    dati_prod = [("Energia Settimanale", f"{e_kw:.1f} kWh"), ("Energia Mensile", f"{e_mo:.1f} kWh"), ("Stima Annuale", f"{stima_ann:.1f} kWh")]
    for col, (label, val) in zip([ee1, ee2, ee3], dati_prod):
        with col:
            st.markdown(f'<div class="big-metric">{label}</div><div class="big-value">{val}</div>', unsafe_allow_html=True)

    # SIMULATORE E TENDENZA
    st.markdown("---")
    st.subheader("🔮 Simulatore e Tendenza Meteo 🌦️")
    col_pred, col_meteo = st.columns(2)
    with col_pred:
        st.markdown('<div class="card"><h4>Simulatore</h4>', unsafe_allow_html=True)
        m, q = np.polyfit(df['Vento (m/s)'].dropna(), df['Watt'].dropna(), 1)
        v_in = st.slider("Velocità Vento (m/s)", 0.0, 20.0, 5.0)
        st.markdown(f'<div class="big-metric">Produzione Stimata</div><div class="big-value">{max(0, (m * v_in) + q):.2f} W</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_meteo:
        st.markdown('<div class="card"><h4>Tendenza Barometrica</h4>', unsafe_allow_html=True)
        var = df['Pressione Locale'].iloc[-1] - df['Pressione Locale'].iloc[-180] if len(df) > 180 else 0
        st.markdown(f'<div class="big-metric">Variazione (3h)</div><div class="big-value">{var:.2f} hPa</div>', unsafe_allow_html=True)
        if var > 0.5: st.success("Stato: In miglioramento")
        elif var < -0.5: st.error("Stato: Instabilità in arrivo")
        else: st.info("Stato: Stabile")
        st.markdown('</div>', unsafe_allow_html=True)

    # GRAFICO
    st.subheader("📊 Analisi Vento vs Watt (Oggi)")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df_oggi['Tempo'], y=df_oggi['Vento (m/s)'], name="Vento", marker_color='skyblue'), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_oggi['Tempo'], y=df_oggi['Watt'], name="Watt", line=dict(color='yellow', width=3)), secondary_y=True)
    fig.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Dati non disponibili.")
