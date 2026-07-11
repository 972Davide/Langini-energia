import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import time

# --- CONFIGURAZIONE URL ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=300)
def carica_dati():
    try:
        # Carica i dati ignorando le righe corrotte
        df1 = pd.read_csv(URL_METEO, on_bad_lines="skip")
        df2 = pd.read_csv(URL_EOLICO, skiprows=2, on_bad_lines="skip")

        # 1. Pulisce i nomi delle colonne (rimuove spazi vuoti a inizio/fine)
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()

        # 2. Identifica il tempo usando la posizione (la colonna 0)
        df1.rename(columns={df1.columns[0]: "Tempo"}, inplace=True)
        df2.rename(columns={df2.columns[0]: "Tempo"}, inplace=True)

        # 3. Conversione date robusta
        df1["Tempo"] = pd.to_datetime(df1["Tempo"], dayfirst=True, errors="coerce")
        df2["Tempo"] = pd.to_datetime(df2["Tempo"], dayfirst=True, errors="coerce")

        # 4. Merge flessibile
        df = pd.merge(df1.dropna(subset=["Tempo"]), df2.dropna(subset=["Tempo"]), on="Tempo", how="inner")

        # 5. Pulizia numerica: forza la conversione di TUTTE le colonne (eccetto Tempo) in numeri
        for col in df.columns:
            if col != "Tempo":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce")

        return df.sort_values("Tempo")
    except Exception as e:
        return None

# --- INTERFACCIA ---
st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_dati()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    df_12h = df[df["Tempo"] >= (df["Tempo"].max() - timedelta(hours=12))]

    # Mappatura "intelligente": cerca tra i nomi probabili
    def get_val(nome_lista):
        for n in nome_lista:
            if n in df.columns: return ultima[n]
        return 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{get_val(['Temperatura', 'Temp. Est']):.1f} °C")
    c2.metric("Umidità", f"{get_val(['Umidità', 'Umid. Est.']):.0f} %")
    c3.metric("Vento", f"{get_val(['Vento (m/s)']):.1f} m/s")
    c4.metric("Produzione", f"{get_val(['Watt']):.0f} W")

    st.markdown("---")

    # Grafici
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Vento vs Watt (12h)")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Bar(x=df_12h["Tempo"], y=df_12h.get("Vento (m/s)", 0), name="Vento"), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df_12h["Tempo"], y=df_12h.get("Watt", 0), name="Watt"), secondary_y=True)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Temp vs Umidità (12h)")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_12h["Tempo"], y=df_12h.get("Temperatura", df_12h.get("Temp. Est", 0)), name="Temp"), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_12h["Tempo"], y=df_12h.get("Umidità", df_12h.get("Umid. Est.", 0)), name="Umidità"), secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True)

    time.sleep(180)
    st.rerun()
else:
    st.warning("Dati non disponibili. Controlla che i fogli siano pubblicati come CSV.")
    time.sleep(10)
    st.rerun()
