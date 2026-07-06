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

# --- CSS DEFINITIVO ---
st.markdown("""
    <style>
    /* Pulsanti e Card */
    div.stButton button { height: 50px; width: 100%; font-size: 18px; background-color: #ff4b4b; color: white; border-radius: 8px; font-weight: bold; }
    .card { background-color: #262730; padding: 25px; border-radius: 15px; border: 1px solid #454545; margin-bottom: 20px; }
    
    /* Metriche Grandi */
    .big-metric { font-size: 20px; color: #aaaaaa; margin-bottom: 5px; }
    .big-value { font-size: 45px; font-weight: 900; color: white; margin-bottom: 10px; }
    .small-trend { font-size: 18px; color: #00ff00; font-weight: bold; }
    
    /* Alert */
    div[role="alert"] { font-size: 20px !important; font-weight: bold !important; padding: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- TESTATA ---
c_title, c_button = st.columns([0.85, 0.15])
with c_title:
    st.title("⚡ Langini: Intelligenza Energetica")
with c_button:
    if st.button('Aggiorna Dati'): st.rerun()
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
    except Exception: return None

df = carica_e_elabora()

if df is not None and not df.empty:
    #st.sidebar.write("Data più vecchia nel DB:", df['Tempo'].min())
    now = pd.Timestamp.now()
    df_oggi = df[df['Tempo'].dt.date == now.date()]
    
    # 1. METEO
    st.subheader("🌡️ Meteo Oggi: Analisi")
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="big-metric">Temperatura</div><div class="big-value">{df_oggi["Temperatura"].max():.1f}°C</div><div class="small-trend">↑ Med: {df_oggi["Temperatura"].mean():.1f}°C</div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="big-metric">Velocità Vento</div><div class="big-value">{df_oggi["Vento (m/s)"].max():.1f} m/s</div><div class="small-trend">↑ Med: {df_oggi["Vento (m/s)"].mean():.1f} m/s</div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="big-metric">Pressione</div><div class="big-value">{df_oggi["Pressione Locale"].max():.0f} hPa</div><div class="small-trend">↑ Med: {df_oggi["Pressione Locale"].mean():.0f} hPa</div>', unsafe_allow_html=True)

    # 2. PRODUZIONE ED ECONOMIA (Calcolo Reale)
    st.subheader("🔋 Produzione ed Economia (Stima GSE)")
    
    # Filtro temporale rigoroso
    mask_sett = (df['Tempo'] >= (now - pd.Timedelta(days=7)))
    mask_mese = (df['Tempo'] >= (now - pd.Timedelta(days=30)))
    
    # Calcolo dei kWh reali dai dati
    e_sett = df.loc[mask_sett, 'Watt'].sum() / 1000
    e_mese = df.loc[mask_mese, 'Watt'].sum() / 1000
    
    # Calcolo Annuale basato sulla media giornaliera reale dei dati disponibili
    giorni_totali = (df['Tempo'].max() - df['Tempo'].min()).days
    if giorni_totali > 0:
        media_giornaliera = (df['Watt'].sum() / 1000) / giorni_totali
        e_anno = media_giornaliera * 365
    else:
        e_anno = e_mese * 12

    ee1, ee2, ee3 = st.columns(3)
    
    # Display con Valori in Euro e kWh
    ee1.markdown(f'<div class="big-metric">Energia Settimanale</div><div class="big-value">{e_sett:.1f} kWh</div><div class="small-trend">↑ € {e_sett * PREZZO_GSE_KW:.2f}</div>', unsafe_allow_html=True)
    ee2.markdown(f'<div class="big-metric">Energia Mensile</div><div class="big-value">{e_mese:.1f} kWh</div><div class="small-trend">↑ € {e_mese * PREZZO_GSE_KW:.2f}</div>', unsafe_allow_html=True)
    ee3.markdown(f'<div class="big-metric">Stima Annuale</div><div class="big-value">{e_anno:.1f} kWh</div>', unsafe_allow_html=True)
    # 3. SIMULATORE E TENDENZA
    st.markdown("---")
    col_pred, col_meteo = st.columns(2)
    with col_pred:
        st.markdown('<div class="card"><h4>🔮 Simulatore Produzione</h4>', unsafe_allow_html=True)
        m, q = np.polyfit(df['Vento (m/s)'].dropna(), df['Watt'].dropna(), 1)
        v_in = st.slider("Velocità Vento (m/s)", 0.0, 20.0, 5.0)
        st.markdown(f'<div class="big-metric">Produzione Stimata</div><div class="big-value">{max(0, (m * v_in) + q):.2f} W</div>', unsafe_allow_html=True)
    with col_meteo:
        st.markdown('<div class="card"><h4>🌦️ Tendenza Barometrica</h4>', unsafe_allow_html=True)
        var = df['Pressione Locale'].iloc[-1] - df['Pressione Locale'].iloc[-180] if len(df) > 180 else 0
        st.markdown(f'<div class="big-metric">Variazione (3h)</div><div class="big-value">{var:.2f} hPa</div>', unsafe_allow_html=True)
        if var > 0.5: st.success("Stato: In miglioramento")
        elif var < -0.5: st.error("Stato: Instabilità in arrivo")
        else: st.info("Stato: Stabile")

    # 4. GRAFICO (Ottimizzato)
    st.subheader("📊 Analisi Vento vs Watt (Oggi)")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df_oggi['Tempo'], y=df_oggi['Vento (m/s)'], name="Vento", marker_color='rgba(135, 206, 235, 0.6)'), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_oggi['Tempo'], y=df_oggi['Watt'], name="Watt", line=dict(color='#FFD700', width=3)), secondary_y=True)
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Dati non ancora disponibili. Verifica il collegamento ai fogli Google.")
