import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import time
import io
import requests
import socket

# Aumenta il timeout di rete per evitare blocchi con Google Sheets
socket.setdefaulttimeout(15)

URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=300)
def carica_dati_finale():
    try:
        # Leggiamo SENZA skiprows, forzando la pulizia dopo
        df1 = pd.read_csv(URL_METEO, on_bad_lines="skip")
        df2 = pd.read_csv(URL_EOLICO, on_bad_lines="skip")
        
        # Pulisce eventuali spazi nei nomi colonne
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        
        # Identifica la colonna tempo (spesso è la prima, a prescindere dal nome)
        df1.rename(columns={df1.columns[0]: "Tempo"}, inplace=True)
        df2.rename(columns={df2.columns[0]: "Tempo"}, inplace=True)
        
        # Rimuove le righe che non sono date (che contengono intestazioni ripetute)
        df1 = df1[df1["Tempo"].str.contains(r'\d{2}/\d{2}/\d{4}', na=False)]
        df2 = df2.columns[0] # (Solo logica interna di pulizia)
        
        # Conversione sicura
        df1["Tempo"] = pd.to_datetime(df1["Tempo"], dayfirst=True, format='mixed', errors="coerce")
        df2["Tempo"] = pd.to_datetime(df2["Tempo"], dayfirst=True, format='mixed', errors="coerce")

        df = pd.merge(df1.dropna(subset=["Tempo"]), df2.dropna(subset=["Tempo"]), on="Tempo", how="inner")
        
        # Pulizia numerica: forza a float, se fallisce mette NaN
        for col in df.columns:
            if col != "Tempo":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors="coerce")
        
        return df.sort_values("Tempo").tail(2500)
    except Exception as e:
        # Qui vedremo l'errore REALE nel log di Streamlit
        st.error(f"DEBUG ERRORE: {e}")
        return None

# --- UI ---
st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_dati_finale()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    df_12h = df[df["Tempo"] >= (df["Tempo"].max() - timedelta(hours=12))]

    # Metriche
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{ultima.get('Temperatura', 0):.1f} °C")
    c2.metric("Umidità", f"{ultima.get('Umidità', 0):.0f} %")
    c3.metric("Vento", f"{ultima.get('Vento (m/s)', 0):.1f} m/s")
    c4.metric("Watt", f"{ultima.get('Watt', 0):.0f} W")

    # Grafici
    col1, col2 = st.columns(2)
    with col1:
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Bar(x=df_12h["Tempo"], y=df_12h.get("Vento (m/s)", 0), name="Vento"), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df_12h["Tempo"], y=df_12h.get("Watt", 0), name="Watt"), secondary_y=True)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_12h["Tempo"], y=df_12h.get("Temperatura", 0), name="Temp"), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_12h["Tempo"], y=df_12h.get("Umidità", 0), name="Umidità"), secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True)

    time.sleep(180)
    st.rerun()
else:
    st.warning("Dati non disponibili. Verifica la connessione e che i file siano pubblici.")
    time.sleep(10)
    st.rerun()
