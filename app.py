import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import time

# --- CONFIGURAZIONE ---
URL_METEO = "..." # (i tuoi URL)
URL_EOLICO = "..." # (i tuoi URL)

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=300)
def carica_dati():
    try:
        df1 = pd.read_csv(URL_METEO, on_bad_lines="skip")
        df2 = pd.read_csv(URL_EOLICO, skiprows=2, on_bad_lines="skip")
        
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        
        df1.rename(columns={df1.columns[0]: "Tempo"}, inplace=True)
        df2.rename(columns={df2.columns[0]: "Tempo"}, inplace=True)
        
        # Conversione sicura
        df1["Tempo"] = pd.to_datetime(df1["Tempo"], dayfirst=True, errors="coerce")
        df2["Tempo"] = pd.to_datetime(df2["Tempo"], dayfirst=True, errors="coerce")
        
        # Pulisci i nulli prima del merge
        df1 = df1.dropna(subset=["Tempo"])
        df2 = df2.dropna(subset=["Tempo"])
        
        # MERGE "SMART": se il merge esatto fallisce, qui avresti 0 righe.
        # Per ora teniamo inner, ma se non vedi grafici, il problema è qui.
        df = pd.merge(df1, df2, on="Tempo", how="inner")
        
        # Conversione numerica forzata per evitare errori nei grafici
        for col in df.columns:
            if col != "Tempo":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors="coerce")
        
        return df.sort_values("Tempo")
    except Exception as e:
        st.error(f"Errore: {e}")
        return None

# --- APP ---
st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_dati()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    df_12h = df[df["Tempo"] >= (df["Tempo"].max() - timedelta(hours=12))]

    # [Inserisci qui le tue metriche e grafici come li avevi scritti, sono corretti]

    st.info("Aggiornamento tra 3 minuti...")
    time.sleep(180)
    st.rerun() # <-- Modifica fondamentale qui
else:
    st.warning("Dati non trovati. Verifica le colonne e che il foglio sia pubblico.")
    time.sleep(10)
    st.rerun() # <-- Modifica fondamentale qui
