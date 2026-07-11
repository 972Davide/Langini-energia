import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import time

URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=300)
def carica_dati():
    try:
        # skiprows=1: ignora la riga 1, inizia alla riga 2
        df1 = pd.read_csv(URL_METEO, skiprows=1, on_bad_lines="skip", low_memory=False)
        # skiprows=3: ignora le righe 1, 2, 3, inizia alla riga 4
        df2 = pd.read_csv(URL_EOLICO, skiprows=3, on_bad_lines="skip", low_memory=False)

        # Pulizia nomi
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()

        # Rinominiamo la prima colonna in 'Tempo' per entrambi
        df1.rename(columns={df1.columns[0]: "Tempo"}, inplace=True)
        df2.rename(columns={df2.columns[0]: "Tempo"}, inplace=True)

        # Parsing date robusto
        df1["Tempo"] = pd.to_datetime(df1["Tempo"], dayfirst=True, format='mixed', errors="coerce")
        df2["Tempo"] = pd.to_datetime(df2["Tempo"], dayfirst=True, format='mixed', errors="coerce")

        df1 = df1.dropna(subset=["Tempo"])
        df2 = df2.dropna(subset=["Tempo"])

        # Merge
        df = pd.merge(df1, df2, on="Tempo", how="inner")

        # Conversione numerica forzata
        for col in df.columns:
            if col != "Tempo":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors="coerce")

        return df.sort_values("Tempo")
    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        return None

# --- APP ---
st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_dati()

if df is not None and not df.empty:
    ultima = df.iloc[-1]
    
    # Metriche
    c1, c2, c3, c4 = st.columns(4)
    # Cerca il nome della colonna in modo flessibile
    col_temp = next((c for c in df.columns if 'Temp' in c and 'Est' in c), 'Temperatura')
    c1.metric("Temperatura", f"{ultima.get(col_temp, 0):.1f} °C")
    
    col_umid = next((c for c in df.columns if 'Umid' in c), 'Umidità')
    c2.metric("Umidità", f"{ultima.get(col_umid, 0):.0f} %")
    
    col_vento = next((c for c in df.columns if 'Vento' in c), 'Vento (m/s)')
    c3.metric("Vento", f"{ultima.get(col_vento, 0):.1f} m/s")
    
    col_watt = next((c for c in df.columns if 'Watt' in c), 'Watt')
    c4.metric("Produzione", f"{ultima.get(col_watt, 0):.0f} W")

    st.markdown("---")
    
    # Grafici
    df_12h = df[df["Tempo"] >= (df["Tempo"].max() - timedelta(hours=12))]
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Vento vs Watt (12h)")
        fig1 = make_subplots(specs=[[{"secondary_y": True}]])
        fig1.add_trace(go.Bar(x=df_12h["Tempo"], y=df_12h.get(col_vento, 0), name="Vento"), secondary_y=False)
        fig1.add_trace(go.Scatter(x=df_12h["Tempo"], y=df_12h.get(col_watt, 0), name="Watt"), secondary_y=True)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Temp vs Umidità (12h)")
        fig2 = make_subplots(specs=[[{"secondary_y": True}]])
        fig2.add_trace(go.Scatter(x=df_12h["Tempo"], y=df_12h.get(col_temp, 0), name="Temp"), secondary_y=False)
        fig2.add_trace(go.Scatter(x=df_12h["Tempo"], y=df_12h.get(col_umid, 0), name="Umidità"), secondary_y=True)
        st.plotly_chart(fig2, use_container_width=True)

    time.sleep(180)
    st.rerun()
else:
    st.warning("Dati non trovati. Verifica che i fogli siano pubblici e che lo skip righe sia corretto.")
    time.sleep(10)
    st.rerun()
