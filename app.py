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
        # Carica i file ignorando errori di formattazione
        df1 = pd.read_csv(URL_METEO, on_bad_lines='skip')
        df2 = pd.read_csv(URL_EOLICO, skiprows=2, on_bad_lines='skip')
        
        # Pulizia nomi colonne
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        
        # Rinominiamo le colonne per uniformarle
        df1.rename(columns={'Data/Ora': 'Tempo'}, inplace=True)
        # Assumiamo che la prima colonna dell'eolico sia il tempo
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)
        
        # Conversione date sicura
        df1['Tempo'] = pd.to_datetime(df1['Tempo'], dayfirst=True, errors='coerce')
        df2['Tempo'] = pd.to_datetime(df2['Tempo'], dayfirst=True, errors='coerce')
        
        # Merge
        df = pd.merge(df1.dropna(subset=['Tempo']), df2.dropna(subset=['Tempo']), on='Tempo', how='inner')
        
        # Mappatura testuale (Stato Tempo)
        if 'Stato Tempo' in df.columns:
            mappa = {'Sereno': 1, 'Nuvoloso': 2, 'Pioggia': 3}
            df['Stato Tempo'] = df['Stato Tempo'].map(mappa).fillna(0)
            
        return df.sort_values(by='Tempo')
    except Exception as e:
        return None

# --- APP ---
df = carica_dati()

if df is not None and not df.empty:
    st.title("🌦️ Langini: Intelligenza Energetica")
    ultima = df.iloc[-1]
    
    # Visualizzazione sicura con .get() per evitare crash se la colonna manca
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperatura", f"{ultima.get('Temperatura', 0)} °C")
    c2.metric("Umidità", f"{ultima.get('Umidità', 0)} %")
    c3.metric("Vento", f"{ultima.get('Vento (m/s)', 0)} m/s")
    c4.metric("Watt", f"{ultima.get('Watt', 0)} W")
    
    st.success("Dati caricati correttamente!")
else:
    st.error("Errore: Il formato dei dati non è riconosciuto. Verifica le intestazioni nel foglio Google.")
