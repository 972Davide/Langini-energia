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

# Campionamento fisso: 1 minuto = 1/60 ore
DELTA_ORE = 1.0 / 60.0

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

# --- CSS DEFINITIVO ---
st.markdown("""
    <style>
    .big-metric { font-size: 16px; color: #b0c4de; text-transform: uppercase; }
    .big-value { font-size: 32px; font-weight: 800; color: #ffcc00; }
    .small-trend { font-size: 14px; color: #32cd32; font-weight: bold; }

    .card {
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 12px;
    }

    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            margin-bottom: 15px !important;
            background: rgba(255, 255, 255, 0.05);
            padding: 15px !important;
            border-radius: 12px;
        }
        .big-value { font-size: 28px !important; }
    }
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

# --- CARICAMENTO DATI ---
@st.cache_data(ttl=60)
def carica_e_elabora():
    try:
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2)

        # Normalizza colonne e tempo
        for df in [df1, df2]:
            df.columns = df.columns.str.strip()
            df.rename(columns={df.columns[0]: 'Tempo'}, inplace=True)
            df['Tempo'] = pd.to_datetime(
                df['Tempo'].astype(str).str.replace('.', ':', regex=False),
                format='mixed',
                dayfirst=True,
                errors='coerce'
            ).dt.floor('min')
            df.dropna(subset=['Tempo'], inplace=True)

        # Merge sui timestamp
        df = pd.merge(df1, df2, on='Tempo', how='inner')

        # Conversioni numeriche
        for col in ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Locale']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').astype(float)

        return df.sort_values(by='Tempo')
    except Exception:
        return None

df = carica_e_elabora()

if df is not None and not df.empty:
    # --- DEBUG PANEL PER VERIFICARE LO STORICO ---
    with st.expander("🛠️ Debug Dati (Verifica Storico)", expanded=False):
        st.write(f"Data primo dato registrato: {df['Tempo'].min()}")
        st.write(f"Data ultimo dato registrato: {df['Tempo'].max()}")
        st.write(f"Numero totale righe: {len(df)}")

    now = pd.Timestamp.now()
    df_oggi = df[df['Tempo'].dt.date == now.date()]

    # --- METEO OGGI ---
    st.subheader("🌡️ Meteo Oggi: Analisi")
    if not df_oggi.empty:
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f'<div class="big-metric">Temperatura</div>'
            f'<div class="big-value">{df_oggi["Temperatura"].max():.1f}°C</div>'
            f'<div class="small-trend">↑ Med: {df_oggi["Temperatura"].mean():.1f}°C</div>',
            unsafe_allow_html=True
        )
        c2.markdown(
            f'<div class="big-metric">Velocità Vento</div>'
            f'<div class="big-value">{df_oggi["Vento (m/s)"].max():.1f} m/s</div>'
            f'<div class="small-trend">↑ Med: {df_oggi["Vento (m/s)"].mean():.1f} m/s</div>',
            unsafe_allow_html=True
        )
        c3.markdown(
            f'<div class="big-metric">Pressione</div>'
            f'<div class="big-value">{df_oggi["Pressione Locale"].max():.0f} hPa</div>'
            f'<div class="small-trend">↑ Med: {df_oggi["Pressione Locale"].mean():.0f} hPa</div>',
            unsafe_allow_html=True
        )
    else:
        st.info("Nessun dato meteo per oggi nei fogli Google.")

    # --- PRODUZIONE ED ECONOMIA ---
    st.subheader("🔋 Produzione ed Economia (Stima GSE)")

    # Intervalli per settimana/mese basati sull'ultimo dato
    end_time = df['Tempo'].max()
    start_sett = end_time - pd.Timedelta(days=7)
    start_mese = end_time - pd.Timedelta(days=30)

    mask_sett = (df['Tempo'] >= start_sett) & (df['Tempo'] <= end_time)
    mask_mese = (df['Tempo'] >= start_mese) & (df['Tempo'] <= end_time)

    # Energia settimanale/mensile (kWh) con campionamento 1 min
    e_sett = df.loc[mask_sett, 'Watt'].sum() * DELTA_ORE / 1000.0
    e_mese = df.loc[mask_mese, 'Watt'].sum() * DELTA_ORE / 1000.0

    # --- STIMA ANNUA (PROIEZIONE SU DATI ATTUALI) ---
    energia_tot = df['Watt'].sum() * DELTA_ORE / 1000.0
    giorni_totali = max((df['Tempo'].max() - df['Tempo'].min()).days, 1)

    media_giornaliera = energia_tot / giorni_totali
    stima_annua_media = media_giornaliera * 365.0

    # Proiezioni da settimana / mese
    stima_annua_da_sett = e_sett * (365.0 / 7.0) if mask_sett.any() else None
    stima_annua_da_mese = e_mese * (365.0 / 30.0) if mask_mese.any() else None

    # Intervalli Da / A
    if mask_sett.any():
        data_sett_da = df.loc[mask_sett, 'Tempo'].min().date()
        data_sett_a = df.loc[mask_sett, 'Tempo'].max().date()
        intervallo_sett = f"Da {data_sett_da} a {data_sett_a}"
    else:
        intervallo_sett = "Intervallo non disponibile"

    if mask_mese.any():
        data_mese_da = df.loc[mask_mese, 'Tempo'].min().date()
        data_mese_a = df.loc[mask_mese, 'Tempo'].max().date()
        intervallo_mese = f"Da {data_mese_da} a {data_mese_a}"
    else:
        intervallo_mese = "Intervallo non disponibile"

    ee1, ee2, ee3 = st.columns(3)

    # Energia Settimanale
    ee1.markdown(
        f'<div class="big-metric">Energia Settimanale</div>'
        f'<div class="big-value">{e_sett:.1f} kWh</div>'
        f'<div class="small-trend">{intervallo_sett} · € {e_sett * PREZZO_GSE_KW:.2f}</div>',
        unsafe_allow_html=True
    )

    # Energia Mensile
    ee2.markdown(
        f'<div class="big-metric">Energia Mensile</div>'
        f'<div class="big-value">{e_mese:.1f} kWh</div>'
        f'<div class="small-trend">{intervallo_mese} · € {e_mese * PREZZO_GSE_KW:.2f}</div>',
        unsafe_allow_html=True
    )

    # Stima annua principale (proiezione su dati attuali)
    ee3.markdown(
        f'<div class="big-metric">Stima annua (proiezione)</div>'
        f'<div class="big-value">{stima_annua_media:.1f} kWh</div>'
        f'<div class="small-trend">Basata su {giorni_totali} giorni di storico</div>',
        unsafe_allow_html=True
    )

    # PANNELLO DI DETTAGLIO STIMA ANNUA
    with st.expander("🔍 Dettaglio stima annua (teorica)", expanded=False):
        st.markdown(
            f"- Media giornaliera attuale: **{media_giornaliera:.2f} kWh/giorno**"
        )
        st.markdown(
            f"- Proiezione annua da storico complessivo: **{stima_annua_media:.1f} kWh**"
        )
        if stima_annua_da_sett is not None:
            st.markdown(
                f"- Proiezione annua da ultima settimana: ~{stima_annua_da_sett:.1f} kWh"
            )
        if stima_annua_da_mese is not None:
            st.markdown(
                f"- Proiezione annua da ultimo mese: ~{stima_annua_da_mese:.1f} kWh"
            )
        st.info(
            "Valori indicativi: la produzione reale dipende da stagionalità, vento e condizioni "
            "non modellate (non sono dati ufficiali GSE)."
        )

    st.markdown("---")

    # --- STORICO GIORNALIERO ---
    st.subheader("📅 Storico Giornaliero Energia / €")

    df_energy = df.copy()
    df_energy['Giorno'] = df_energy['Tempo'].dt.date

    daily = (
        df_energy
        .groupby('Giorno', as_index=False)
        .agg(kWh_giorno=('Watt', lambda x: x.sum() * DELTA_ORE / 1000.0))
    )
    daily['Euro_giorno'] = daily['kWh_giorno'] * PREZZO_GSE_KW
    daily = daily.sort_values('Giorno', ascending=False)

    st.dataframe(
        daily.style.format({
            'kWh_giorno': '{:.2f}',
            'Euro_giorno': '{:.2f}'
        }),
        use_container_width=True
    )

    tot_kwh = daily['kWh_giorno'].sum()
    tot_euro = daily['Euro_giorno'].sum()
    st.markdown(
        f"Totale periodo registrato: **{tot_kwh:.2f} kWh** · € {tot_euro:.2f}"
    )

    st.markdown("---")

    # --- SIMULATORE E TENDENZA ---
    col_pred, col_meteo = st.columns(2)

    with col_pred:
        st.markdown('<div class="card"><h4>🔮 Simulatore Produzione</h4>', unsafe_allow_html=True)
        valid = df[['Vento (m/s)', 'Watt']].dropna()
        if len(valid) >= 5 and valid['Vento (m/s)'].std() > 0:
            m, q = np.polyfit(valid['Vento (m/s)'], valid['Watt'], 1)
        else:
            m, q = 0, valid['Watt'].mean() if len(valid) > 0 else 0

        v_in = st.slider("Velocità Vento (m/s)", 0.0, 20.0, 5.0)
        produzione_stimata_watt = max(0, (m * v_in) + q)
        st.markdown(
            f'<div class="big-metric">Produzione Stimata</div>'
            f'<div class="big-value">{produzione_stimata_watt:.2f} W</div>',
            unsafe_allow_html=True
        )

    with col_meteo:
        st.markdown('<div class="card"><h4>🌦️ Tendenza Barometrica</h4>', unsafe_allow_html=True)
        ultimo_tempo = df['Tempo'].iloc[-1]
        tre_ore_prima = ultimo_tempo - pd.Timedelta(hours=3)
        df_prev = df[df['Tempo'] <= tre_ore_prima]

        if not df_prev.empty:
            var = df['Pressione Locale'].iloc[-1] - df_prev['Pressione Locale'].iloc[-1]
        else:
            var = 0.0

        st.markdown(
            f'<div class="big-metric">Variazione (3h)</div>'
            f'<div class="big-value">{var:.2f} hPa</div>',
            unsafe_allow_html=True
        )

        if var > 0.5:
            st.success("Stato: In miglioramento")
        elif var < -0.5:
            st.error("Stato: Instabilità in arrivo")
        else:
            st.info("Stato: Stabile")

    # --- GRAFICO VENTO vs WATT OGGI ---
    st.subheader("📊 Analisi Vento vs Watt (Oggi)")
    if not df_oggi.empty:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(
                x=df_oggi['Tempo'],
                y=df_oggi['Vento (m/s)'],
                name="Vento",
                marker_color='rgba(135, 206, 235, 0.6)'
            ),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(
                x=df_oggi['Tempo'],
                y=df_oggi['Watt'],
                name="Watt",
                line=dict(color='#FFD700', width=3)
            ),
            secondary_y=True
        )

        fig.update_layout(
            template="plotly_dark",
            height=450,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Tempo",
            yaxis_title="Vento (m/s)",
            legend_title="Variabili"
        )
        fig.update_yaxes(title_text="Watt", secondary_y=True)

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nessun dato di vento/Watt per oggi disponibili nei fogli Google.")

else:
    st.warning("Dati non ancora disponibili. Verifica il collegamento ai fogli Google.")
