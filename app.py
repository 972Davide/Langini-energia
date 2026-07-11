import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import time

# --- CONFIGURAZIONE ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=300)
def carica_dati():
    try:
        # Carica i CSV da Google Sheets
        df1 = pd.read_csv(URL_METEO, on_bad_lines="skip")
        df2 = pd.read_csv(URL_EOLICO, skiprows=2, on_bad_lines="skip")

        # Rimuove spazi bianchi nei nomi delle colonne
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()

        # Assume che la prima colonna sia sempre il tempo
        df1.rename(columns={df1.columns[0]: "Tempo"}, inplace=True)
        df2.rename(columns={df2.columns[0]: "Tempo"}, inplace=True)

        # Converte la colonna Tempo in datetime
        df1["Tempo"] = pd.to_datetime(df1["Tempo"], dayfirst=True, errors="coerce")
        df2["Tempo"] = pd.to_datetime(df2["Tempo"], dayfirst=True, errors="coerce")

        # Elimina righe con Tempo non valido
        df1 = df1.dropna(subset=["Tempo"])
        df2 = df2.dropna(subset=["Tempo"])

        # Merge sui timestamp comuni
        df = pd.merge(df1, df2, on="Tempo", how="inner")

        # Ordina per Tempo (utile per metrica finale e grafici)
        df = df.sort_values("Tempo")

        return df
    except Exception as e:
        st.error(f"Errore tecnico nel caricamento dati: {e}")
        return None

# --- APP ---
st.title("🌦️ Langini: Intelligenza Energetica")

df = carica_dati()

if df is not None and not df.empty:
    # Ultima riga dopo ordinamento per Tempo
    ultima = df.iloc[-1]

    # Finestra ultime 12 ore
    soglia_12h = df["Tempo"].max() - timedelta(hours=12)
    df_12h = df[df["Tempo"] >= soglia_12h]

    # Metriche principali
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{ultima.get('Temperatura', 0):.1f} °C")
    c2.metric("Umidità", f"{ultima.get('Umidità', 0):.0f} %")
    c3.metric("Vento", f"{ultima.get('Vento (m/s)', 0):.1f} m/s")
    c4.metric("Produzione", f"{ultima.get('Watt', 0):.0f} W")

    st.markdown("---")

    # Grafici
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Vento vs Watt (ultime 12 ore)")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(
            go.Bar(
                x=df_12h["Tempo"],
                y=df_12h.get("Vento (m/s)", 0),
                name="Vento (m/s)",
            ),
            secondary_y=False,
        )
        fig1.add_trace(
            go.Scatter(
                x=df_12h["Tempo"],
                y=df_12h.get("Watt", 0),
                name="Produzione (W)",
                line=dict(color="green"),
            ),
            secondary_y=True,
        )
        fig1.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Temperatura vs Umidità (ultime 12 ore)")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(
            go.Scatter(
                x=df_12h["Tempo"],
                y=df_12h.get("Temperatura", 0),
                name="Temperatura (°C)",
                line=dict(color="orange"),
            ),
            secondary_y=False,
        )
        fig2.add_trace(
            go.Scatter(
                x=df_12h["Tempo"],
                y=df_12h.get("Umidità", 0),
                name="Umidità (%)",
                line=dict(color="cyan"),
            ),
            secondary_y=True,
        )
        fig2.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig2, use_container_width=True)

    st.info("Dati aggiornati. La pagina si ricaricherà automaticamente tra 3 minuti.")
    time.sleep(180)
    # In Streamlit recente è preferibile experimental_rerun
    st.experimental_rerun()
else:
    st.warning("Dati non caricati. Verifica che i fogli Google siano pubblici e che le colonne esistano.")
    time.sleep(10)
    st.experimental_rerun()
