import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta

# --- URL FOGLI ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-W1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")


@st.cache_data(ttl=300)
def carica_e_unisci():
    """Carica i CSV da Google Sheets, pulisce e unisce i dati."""
    try:
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2)

        # Elimina colonne Unnamed
        df1 = df1.loc[:, ~df1.columns.str.contains('^Unnamed')]
        df2 = df2.loc[:, ~df2.columns.str.contains('^Unnamed')]

        # Rinomina prima colonna in 'Tempo'
        df1.rename(columns={df1.columns[0]: 'Tempo'}, inplace=True)
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)

        # Parsing datetime
        for df in (df1, df2):
            df['Tempo'] = (
                df['Tempo']
                .astype(str)
                .str.replace('.', ':', regex=False)
            )
            df['Tempo'] = pd.to_datetime(
                df['Tempo'],
                format='mixed',
                dayfirst=True,
                errors='coerce'
            ).dt.floor('min')

        # Unione sui timestamp comuni
        df = pd.merge(df1, df2, on='Tempo', how='inner')

        # Convertiamo in float SOLO le colonne numeriche note
        colonne_da_convertire = [
            'Vento (m/s)',
            'Watt',
            'Temperatura',
            'Pressione Mare',
            'Umidità',
            'Umidita',
        ]

        for col in colonne_da_convertire:
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(',', '.'),
                    errors='coerce'
                )

        # Ordina per tempo
        df = df.sort_values(by='Tempo').dropna(subset=['Tempo'])

        return df

    except Exception as e:
        st.error(f"Errore durante il caricamento dati: {e}")
        return pd.DataFrame()


# --- INTERFACCIA ---
st.title("🌦️ Langini: Intelligenza Energetica")

# Opzione per aggiornare manualmente
st.caption("Dati aggiornati ogni massimo 5 minuti (cache).")
if st.button("🔄 Aggiorna ora"):
    # Svuota cache
    carica_e_unisci.clear()

df = carica_e_unisci()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    adesso = df['Tempo'].max()

    # Identificazione dinamica colonne
    col_temp = next((c for c in df.columns if 'Temperatur' in c), None)
    col_umid = next((c for c in df.columns if 'Umid' in c), None)
    col_vento = next((c for c in df.columns if 'Vento' in c), None)
    col_press = next((c for c in df.columns if 'Pression' in c), None)
    col_watt = next((c for c in df.columns if 'Watt' in c), None)

    # Filtro ultime 12 ore
    limite_12h = adesso - timedelta(hours=12)
    df_12h = df[df['Tempo'] >= limite_12h].copy()

    # --- CALCOLO PREVISIONE ---
    limite_3h = adesso - timedelta(hours=3)
    pressione_attuale = float(ultima.get(col_press, 0)) if col_press else 0.0

    if col_press:
        pressione_3h_fa = df[df['Tempo'] <= limite_3h][col_press].tail(1)
        pressione_3h_fa_list = pressione_3h_fa.values
    else:
        pressione_3h_fa_list = []

    previsione = "Stabile"
    if len(pressione_3h_fa_list) > 0 and not pd.isna(pressione_3h_fa_list[0]):
        diff = pressione_attuale - pressione_3h_fa_list[0]
        if diff > 1.5:
            previsione = "Miglioramento"
        elif diff < -1.5:
            previsione = "Instabilità in arrivo"
        else:
            previsione = "Stabile"

    # Produzioni
    if col_watt:
        prod_giornaliera = df[df['Tempo'].dt.date == adesso.date()][col_watt].sum()
        prod_settimanale = df[df['Tempo'] >= (adesso - timedelta(days=7))][col_watt].sum()
        prod_mensile = df[df['Tempo'] >= (adesso - timedelta(days=30))][col_watt].sum()
    else:
        prod_giornaliera = prod_settimanale = prod_mensile = 0

    # --- METRICHE ---
    c1, c2, c3, c4, c5 = st.columns(5)

    # Temperatura
    if col_temp:
        c1.metric(
            "Temperatura",
            f"{ultima.get(col_temp, 0):.1f} °C",
            f"Min {df_12h[col_temp].min():.1f}° / Max {df_12h[col_temp].max():.1f}°",
        )
    else:
        c1.metric("Temperatura", "N/D")

    # Umidità
    if col_umid:
        c2.metric(
            "Umidità",
            f"{ultima.get(col_umid, 0):.0f} %",
            f"Min {df_12h[col_umid].min():.0f}% / Max {df_12h[col_umid].max():.0f}%",
        )
    else:
        c2.metric("Umidità", "N/D")

    # Vento
    if col_vento:
        c3.metric(
            "Vento",
            f"{ultima.get(col_vento, 0):.1f} m/s",
            f"Max 12h: {df_12h[col_vento].max():.1f} m/s",
        )
    else:
        c3.metric("Vento", "N/D")

    # Produzione
    with c4:
        st.metric("Produzione (Oggi)", f"{prod_giornaliera:,.0f} W")
        st.caption(f"Sett: {prod_settimanale:,.0f} W | Mese: {prod_mensile:,.0f} W")

    # Pressione
    if col_press:
        c5.metric("Pressione", f"{pressione_attuale:.0f} hPa", previsione)
    else:
        c5.metric("Pressione", "N/D")

    st.markdown("---")

    # --- Grafico ---
    st.subheader("📊 Analisi Temporale (Ultime 12 ore): Vento vs Watt")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if col_vento:
        fig.add_trace(
            go.Bar(
                x=df_12h['Tempo'],
                y=df_12h[col_vento],
                name="Vento (m/s)",
                marker_color='skyblue',
            ),
            secondary_y=False,
        )

    if col_watt:
        fig.add_trace(
            go.Scatter(
                x=df_12h['Tempo'],
                y=df_12h[col_watt],
                name="Watt",
                line=dict(color='yellow', width=3),
            ),
            secondary_y=True,
        )

    fig.update_layout(
        template="plotly_dark",
        showlegend=True,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    fig.update_yaxes(title_text="Velocità Vento (m/s)", secondary_y=False)
    fig.update_yaxes(title_text="Produzione (Watt)", secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("Caricamento in corso o dati non sincronizzati. Riprovare più tardi.")
