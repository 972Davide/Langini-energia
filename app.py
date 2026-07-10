import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURAZIONE ---
PREZZO_GSE_KW = 0.15
# URL presi dai tuoi screenshot (assicurati che siano corretti)
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

# --- CARICAMENTO ROBUSTO ---
@st.cache_data(ttl=60)
def carica_dati():
    try:
        # Carica i dati
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO)
        
        # Rinominazione sicura della prima colonna come 'Tempo'
        for df in [df1, df2]:
            df.columns = [c.strip() for c in df.columns]
            df.rename(columns={df.columns[0]: 'Tempo'}, inplace=True)
            df['Tempo'] = pd.to_datetime(df['Tempo'], errors='coerce')
        
        # Unione
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        return df
    except Exception as e:
        return f"Errore caricamento: {e}"

# --- ESECUZIONE ---
df = carica_dati()

if isinstance(df, str):
    st.error(df)
elif df is not None and not df.empty:
    st.success("Dati caricati correttamente!")
    st.dataframe(df.head()) # Mostra un'anteprima per verificare la struttura
    
    # Esempio di grafico
    if 'Watt' in df.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Tempo'], y=df['Watt'], name="Watt"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Colonna 'Watt' non trovata. Colonne disponibili: " + str(list(df.columns)))
else:
    st.warning("Dati vuoti o non trovati.")
