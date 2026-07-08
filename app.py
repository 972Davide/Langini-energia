import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURAZIONE ---
PREZZO_GSE_KW = 0.15  # € / kWh
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?output=csv"

DELTA_ORE = 1.0 / 60.0

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

# --- CSS DEFINITIVO ---
st.markdown("""
    <style>
    .big-metric { font-size: 16px; color: #b0c4de; text-transform: uppercase; }
    .big-value { font-size: 32px; font-weight: 800; color: #ffcc00; }
    .small-trend { font-size: 14px; color: #32cd32; font-weight: bold; }
    .card { background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 12px; }
    @media (max-width: 768px) {
        [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; margin-bottom: 15px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- TESTATA ---
c_title, c_button = st.columns([0.85, 0.15])
with c_title:
    st.title("⚡ Langini: Intelligenza Energetica")
with c_button:
    if st.button('Aggiorna Dati'): st.rerun()
st.caption(f"Ultimo aggiornamento: {datetime.now().strftime('%H:%M:%S')}")

# --- CARICAMENTO DATI ---
@st.cache_data(ttl=60)
def carica_e_elabora():
    try:
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2)
        for df in [df1, df2]:
            df.columns = df.columns.str.strip()
            df.rename(columns={df.columns[0]: 'Tempo'}, inplace=True)
            df['Tempo'] = pd.to_datetime(df['Tempo'].astype(str).str.replace('.', ':', regex=False), format='mixed', dayfirst=True, errors='coerce').dt.floor('min')
            df.dropna(subset=['Tempo'], inplace=True)
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        for col in ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Locale']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').astype(float)
        return df.sort_values(by='Tempo')
    except Exception: return None

df = carica_e_elabora()

if df is not None and not df.empty:
    now = pd.Timestamp.now()
    
    # --- CALCOLI ENERGETICI DINAMICI ---
    # 1. Storico 2026
    df_2026 = df[df['Tempo'].dt.year == 2026]
    energia_anno_corrente = df_2026['Watt'].sum() * DELTA_ORE / 1000.0
    giorno_inizio_anno = pd.Timestamp(year=2026, month=1, day=1)
    giorni_passati = max((now - giorno_inizio_anno).days, 1)
    media_giornaliera_storica = energia_anno_corrente / giorni_passati
    
    # 2. Proiezione a finire
    fine_anno = pd.Timestamp(year=2026, month=12, day=31)
    giorni_rimanenti = max((fine_anno - now).days, 0)
    stima_annua_finire = energia_anno_corrente + (media_giornaliera_storica * giorni_rimanenti)
    
    # 3. Settimanale e Mensile
    e_sett = df[df['Tempo'] >= (now - pd.Timedelta(days=7))]['Watt'].sum() * DELTA_ORE / 1000.0
    e_mese = df[df['Tempo'] >= (now - pd.Timedelta(days=30))]['Watt'].sum() * DELTA_ORE / 1000.0

    # --- UI PRODUZIONE ---
    st.subheader("🔋 Produzione ed Economia")
    ee1, ee2, ee3 = st.columns(3)
    
    ee1.markdown(f'<div class="big-metric">Energia Settimanale</div><div class="big-value">{e_sett:.1f} kWh</div><div class="small-trend">€ {e_sett * PREZZO_GSE_KW:.2f}</div>', unsafe_allow_html=True)
    ee2.markdown(f'<div class="big-metric">Energia Mensile (30gg)</div><div class="big-value">{e_mese:.1f} kWh</div><div class="small-trend">€ {e_mese * PREZZO_GSE_KW:.2f}</div>', unsafe_allow_html=True)
    ee3.markdown(f'<div class="big-metric">Stima Annua (A finire)</div><div class="big-value">{stima_annua_finire:.1f} kWh</div><div class="small-trend">Media 2026: {media_giornaliera_storica:.2f} kWh/gg</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # --- SIMULATORE E METEO ---
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="card"><h4>🔮 Simulatore Produzione</h4>', unsafe_allow_html=True)
        valid = df[['Vento (m/s)', 'Watt']].dropna()
        m, q = np.polyfit(valid['Vento (m/s)'], valid['Watt'], 1) if len(valid) > 5 else (0, 0)
        v_in = st.slider("Velocità Vento (m/s)", 0.0, 20.0, 5.0)
        st.markdown(f'<div class="big-metric">Produzione Stimata</div><div class="big-value">{max(0, (m * v_in) + q):.2f} W</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card"><h4>🌦️ Tendenza Barometrica</h4>', unsafe_allow_html=True)
        var = df['Pressione Locale'].iloc[-1] - df[df['Tempo'] <= (now - pd.Timedelta(hours=3))]['Pressione Locale'].iloc[-1]
        st.markdown(f'<div class="big-metric">Variazione (3h)</div><div class="big-value">{var:.2f} hPa</div>', unsafe_allow_html=True)
        if var > 0.5: st.success("Stato: In miglioramento")
        elif var < -0.5: st.error("Stato: Instabilità in arrivo")
        else: st.info("Stato: Stabile")

    # --- GRAFICO ---
    st.subheader("📊 Analisi Vento vs Watt (Oggi)")
    df_oggi = df[df['Tempo'].dt.date == now.date()]
    if not df_oggi.empty:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Bar(x=df_oggi['Tempo'], y=df_oggi['Vento (m/s)'], name="Vento", marker_color='rgba(135, 206, 235, 0.6)'), secondary_y=False)
        fig.add_trace(go.Scatter(x=df_oggi['Tempo'], y=df_oggi['Watt'], name="Watt", line=dict(color='#FFD700', width=3)), secondary_y=True)
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Dati non disponibili.")
