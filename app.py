import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import time

# --- URL FOGLI ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=300)
def carica_e_unisci():
    try:
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2)
        
        df1 = df1.loc[:, ~df1.columns.str.contains('^Unnamed')]
        df2 = df2.loc[:, ~df2.columns.str.contains('^Unnamed')]
        df1.rename(columns={df1.columns[0]: 'Tempo'}, inplace=True)
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)
        
        for df in [df1, df2]:
            df['Tempo'] = pd.to_datetime(df['Tempo'].astype(str).str.replace('.', ':', regex=False), format='mixed', dayfirst=True).dt.floor('min')
        
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        colonne_da_convertire = ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Mare', 'Umidità', 'Umidita']
        for col in colonne_da_convertire:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore caricamento dati: {e}")
        return None

# --- INTERFACCIA ---
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

    # Filtri
    limite_12h = adesso - timedelta(hours=12)
    df_12h = df[df['Tempo'] >= limite_12h]
    
    # Previsione
    limite_3h = adesso - timedelta(hours=3)
    pressione_attuale = ultima.get(col_press, 0)
    pressione_3h_fa_list = df[df['Tempo'] <= limite_3h][col_press].tail(1).values if col_press else []
    previsione = "Stabile"
    if len(pressione_3h_fa_list) > 0:
        diff = pressione_attuale - pressione_3h_fa_list[0]
        if diff > 1.5: previsione = "Miglioramento"
        elif diff < -1.5: previsione = "Instabilità in arrivo"
    
    # Produzioni
    prod_giornaliera = df[df['Tempo'].dt.date == adesso.date()][col_watt].sum() if col_watt else 0
    prod_settimanale = df[df['Tempo'] >= (adesso - timedelta(days=7))][col_watt].sum() if col_watt else 0
    prod_mensile = df[df['Tempo'] >= (adesso - timedelta(days=30))][col_watt].sum() if col_watt else 0
    
    # --- METRICHE ---
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Temperatura", f"{ultima.get(col_temp, 0):.1f} °C", f"Min {df_12h[col_temp].min():.1f}° / Max {df_12h[col_temp].max():.1f}°" if col_temp else "")
    c2.metric("Umidità", f"{ultima.get(col_umid, 0):.0f} %", f"Min {df_12h[col_umid].min():.0f}% / Max {df_12h[col_umid].max():.0f}%" if col_umid else "")
    c3.metric("Vento", f"{ultima.get(col_vento, 0):.1f} m/s", f"Max 12h: {df_12h[col_vento].max():.1f} m/s" if col_vento else "")
    with c4:
        st.metric("Produzione (Oggi)", f"{prod_giornaliera:,.0f} W")
        st.caption(f"Sett: {prod_settimanale:,.0f} W | Mese: {prod_mensile:,.0f} W")
    c5.metric("Pressione", f"{pressione_attuale:.0f} hPa", previsione)
    
    st.markdown("---")
    
    # Grafici
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Vento vs Watt (12h)")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Bar(x=df_12h['Tempo'], y=df_12h[col_vento], name="Vento", marker_color='skyblue'), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h[col_watt], name="Watt", line=dict(color='yellow', width=3)), secondary_y=True)
        fig1.update_layout(template="plotly_dark")
        st.plotly_chart(fig1, use_container_width=True)
    with col_g2:
        st.subheader("🌡️ Temp vs Umidità (12h)")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h[col_temp], name="Temp (°C)", line=dict(color='orange', width=3)), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h[col_umid], name="Umidità (%)", line=dict(color='cyan', width=3, dash='dot')), secondary_y=True)
        fig2.update_layout(template="plotly_dark")
        st.plotly_chart(fig2, use_container_width=True)

    # --- BARRA DI PROGRESSO ---
    st.caption("Prossimo aggiornamento tra:")
    bar = st.progress(0)
    for i in range(180):
        time.sleep(1)
        # Calcola percentuale (1 - tempo_trascorso/totale)
        progress = (i + 1) / 180
        bar.progress(progress)
    st.rerun()

else:
    st.warning("Caricamento in corso o dati non sincronizzati.")
    time.sleep(10)
    st.rerun()
