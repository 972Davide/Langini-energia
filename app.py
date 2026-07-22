import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import time

# --- URL FOGLI ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

# --- PARAMETRO GSE (Tariffa stimata in € per kWh prodotto) ---
TARIFFA_GSE_EURO_KWH = 0.20  # Modificalo qui se hai una tariffa diversa (es. 0.15, 0.25, ecc.)

st.set_page_config(page_title="Langini: Monitoraggio Impianto Eolico 1kW & Meteo", layout="wide")

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
        
        # Conversione numerica robusta
        colonne_da_convertire = ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Mare', 'Umidità', 'Umidita']
        for col in colonne_da_convertire:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df.sort_values(by='Tempo')
    
    except Exception as e:
        st.error(f"Errore durante il caricamento dati: {e}")
        return None

# --- INTERFACCIA ---
st.title("⚡ Langini: Monitoraggio Impianto Eolico 1kW & Meteo")
df = carica_e_unisci()

if df is not None and not df.empty:
    # Identificazione dinamica colonne
    col_temp = next((c for c in df.columns if 'Temperatur' in c), None)
    col_umid = next((c for c in df.columns if 'Umid' in c), None)
    col_vento = next((c for c in df.columns if 'Vento' in c), None)
    col_press = next((c for c in df.columns if 'Pression' in c), None)
    col_watt = next((c for c in df.columns if 'Watt' in c), None)

    # --- FILTRO 12 ORE SENZA BUCHI ---
    adesso = df['Tempo'].max()
    limite_12h = adesso - timedelta(hours=12)
    df_12h = df[df['Tempo'] >= limite_12h].copy()
    
    ultima = df_12h.iloc[-1] if not df_12h.empty else df.iloc[-1]
    
    # --- CALCOLO PREVISIONE PRESSIONE ---
    limite_3h = adesso - timedelta(hours=3)
    pressione_attuale = ultima.get(col_press, 0)
    pressione_3h_fa_list = df[df['Tempo'] <= limite_3h][col_press].tail(1).values if col_press else []
    
    previsione = "Stabile"
    if len(pressione_3h_fa_list) > 0:
        diff = pressione_attuale - pressione_3h_fa_list[0]
        if diff > 1.5: previsione = "Miglioramento"
        elif diff < -1.5: previsione = "Instabilità in arrivo"
        else: previsione = "Stabile"

    # --- CALCOLO PRODUZIONI E PROIEZIONE ANNUALE ---
    giorni_passati = (adesso - df['Tempo'].min()).days + 1
    prod_totale = df[col_watt].sum() if col_watt else 0
    
    prod_settimanale = df[df['Tempo'] >= (adesso - timedelta(days=7))][col_watt].sum() if col_watt else 0
    prod_mensile = df[df['Tempo'] >= (adesso - timedelta(days=30))][col_watt].sum() if col_watt else 0
    
    media_giornaliera = prod_totale / giorni_passati if giorni_passati > 0 else 0
    proiezione_anno = media_giornaliera * 365
    
    # --- METRICHE ---
    c1, c2, c3, c4, c5 = st.columns(5)
    
    c1.metric("Temperatura", f"{ultima.get(col_temp, 0):.1f} °C", 
              f"Min {df_12h[col_temp].min():.1f}° / Max {df_12h[col_temp].max():.1f}°" if col_temp is not None and not df_12h[col_temp].empty else "")
    
    c2.metric("Umidità", f"{ultima.get(col_umid, 0):.0f} %", 
              f"Min {df_12h[col_umid].min():.0f}% / Max {df_12h[col_umid].max():.0f}%" if col_umid is not None and not df_12h[col_umid].empty else "")
    
    c3.metric("Vento", f"{ultima.get(col_vento, 0):.1f} m/s", 
              f"Max 12h: {df_12h[col_vento].max():.1f} m/s" if col_vento is not None and not df_12h[col_vento].empty else "")
    
    with c4:
        st.metric("Produzione (Totale)", f"{prod_totale:,.0f} W")
        st.caption(f"Sett: {prod_settimanale:,.0f} W | Mese: {prod_mensile:,.0f} W")
        st.caption(f"Proiezione anno: {proiezione_anno:,.0f} W")
        
    c5.metric("Pressione", f"{pressione_attuale:.0f} hPa", previsione)
    
    st.markdown("---")
    
    # --- PRIMA RIGA DI GRAFICI (Vento vs Watt & Temp vs Umidità) ---
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.subheader("📊 Vento vs Watt (Ultime 12h)")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Bar(x=df_12h['Tempo'], y=df_12h[col_vento], name="Vento", marker_color='skyblue'), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h[col_watt], name="Watt", line=dict(color='yellow', width=3)), secondary_y=True)
        fig1.update_layout(template="plotly_dark", showlegend=True, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig1, use_container_width=True)
        
    with col_g2:
        st.subheader("🌡️ Temp vs Umidità (Ultime 12h)")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h[col_temp], name="Temp (°C)", line=dict(color='orange', width=3)), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h[col_umid], name="Umidità (%)", line=dict(color='cyan', width=3, dash='dot')), secondary_y=True)
        fig2.update_layout(template="plotly_dark", showlegend=True, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig2, use_container_width=True)

    # --- SECONDA RIGA DI GRAFICI (Pressione Zoomata & Produzione Giornaliera Storica) ---
    col_g3, col_g4 = st.columns(2)
    
    with col_g3:
        st.subheader("🌐 Pressione Atmosferica (Ultime 12h - Zoom)")
        fig3 = go.Figure()
        if col_press and not df_12h.empty:
            fig3.add_trace(go.Scatter(x=df_12h['Tempo'], y=df_12h[col_press], name="Pressione (hPa)", line=dict(color='magenta', width=3), fill='tozeroy'))
            p_min = df_12h[col_press].min() - 1
            p_max = df_12h[col_press].max() + 1
            fig3.update_yaxes(range=[p_min, p_max])
        fig3.update_layout(template="plotly_dark", showlegend=True, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig3, use_container_width=True)
        
    with col_g4:
        st.subheader("📈 Produzione Energetica Giornaliera")
        fig4 = go.Figure()
        if col_watt:
            df_giornaliero = df.copy()
            df_giornaliero['Data'] = df_giornaliero['Tempo'].dt.date
            df_storico_giorni = df_giornaliero.groupby('Data')[col_watt].sum().reset_index()
            fig4.add_trace(go.Bar(x=df_storico_giorni['Data'], y=df_storico_giorni[col_watt], name="Watt / Giorno", marker_color='limegreen'))
        fig4.update_layout(template="plotly_dark", showlegend=True, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig4, use_container_width=True)

    # --- TERZA RIGA: NUOVO GRAFICO DI MONETIZZAZIONE GSE ---
    st.subheader("💶 Monetizzazione Giornaliera GSE (Stima in €)")
    fig5 = go.Figure()
    if col_watt:
        df_giornaliero = df.copy()
        df_giornaliero['Data'] = df_giornaliero['Tempo'].dt.date
        df_storico_giorni = df_giornaliero.groupby('Data')[col_watt].sum().reset_index()
        
        # Conversione da Watt a kWh (ipotizzando registrazioni cumulative o normalizzate) e calcolo euro
        # Nota: Se i Watt sul foglio sono letture istantanee o totalizzatori, la stima si adatta moltiplicando per la tariffa
        df_storico_giorni['Euro'] = (df_storico_giorni[col_watt] / 1000.0) * TARIFFA_GSE_EURO_KWH
        
        fig5.add_trace(go.Bar(
            x=df_storico_giorni['Data'], 
            y=df_storico_giorni['Euro'], 
            name="Guadagno (€)", 
            marker_color='gold',
            text=df_storico_giorni['Euro'].apply(lambda x: f"€ {x:.2f}"),
            textposition='auto'
        ))
    fig5.update_layout(template="plotly_dark", showlegend=False, margin=dict(l=20, r=20, t=30, b=20))
    fig5.update_yaxes(title_text="Euro (€)")
    st.plotly_chart(fig5, use_container_width=True)
    
    # --- TIMER E BARRA DI AGGIORNAMENTO ---
    st.caption("Prossimo aggiornamento automatico tra:")
    bar = st.progress(0)
    for i in range(180):
        time.sleep(1)
        bar.progress((i + 1) / 180)
    st.rerun()
    
else:
    st.warning("Caricamento in corso o dati non sincronizzati.")
    time.sleep(10)
    st.rerun()
