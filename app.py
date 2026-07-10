import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAZIONE ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

@st.cache_data(ttl=300)
def load_and_merge():
    try:
        # Caricamento
        df_m = pd.read_csv(URL_METEO)
        df_e = pd.read_csv(URL_EOLICO)
        
        # Pulizia nomi colonne (rimuove spazi)
        df_m.columns = df_m.columns.str.strip()
        df_e.columns = df_e.columns.str.strip()
        
        # Rinominazione prima colonna in 'Tempo'
        df_m.rename(columns={df_m.columns[0]: 'Tempo'}, inplace=True)
        df_e.rename(columns={df_e.columns[0]: 'Tempo'}, inplace=True)
        
        # Conversione Tempo
        df_m['Tempo'] = pd.to_datetime(df_m['Tempo'], errors='coerce')
        df_e['Tempo'] = pd.to_datetime(df_e['Tempo'], errors='coerce')
        
        # Merge
        df = pd.merge(df_m, df_e, on='Tempo', how='inner')
        return df
    except Exception as e:
        return str(e)

st.title("⚡ Langini: Intelligenza Energetica")

data = load_and_merge()

if isinstance(data, str):
    st.error(f"Errore tecnico: {data}")
    st.info("Verifica che i file CSV abbiano una colonna data/ora comune.")
else:
    st.success("Dati caricati correttamente!")
    
    # Debug: mostriamo le colonne trovate per assicurarci di usarne i nomi giusti
    st.write("Colonne disponibili nel database unificato:", list(data.columns))
    
    # Mostriamo solo le prime 5 righe
    st.dataframe(data.head())
    
    # Se trovi la colonna Watt, disegniamo il grafico
    target_col = 'Watt' # O il nome esatto che vedrai nella lista colonne
    if target_col in data.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['Tempo'], y=data[target_col], name="Produzione"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"La colonna '{target_col}' non è stata trovata. Controlla il nome esatto nell'elenco sopra.")
