import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import timedelta
import time
import io
import requests

URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def carica_dati_intelligente():
    def fetch_df(url):
        # Scarichiamo il file come testo per cercare la riga giusta
        r = requests.get(url)
        lines = r.text.splitlines()
        # Cerchiamo la prima riga che contiene i nomi colonne (es. ha la parola 'Tempo' o 'Data')
        start_idx = 0
        for i, line in enumerate(lines):
            if 'Data' in line or 'Tempo' in line:
                start_idx = i
                break
        
        # Leggiamo da quella riga in poi
        data = "\n".join(lines[start_idx:])
        return pd.read_csv(io.StringIO(data))

    try:
        df1 = fetch_df(URL_METEO)
        df2 = fetch_df(URL_EOLICO)
        
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        
        # Merge basato sulla colonna che contiene "Data" o "Tempo"
        col_tempo1 = [c for c in df1.columns if 'Data' in c or 'Tempo' in c][0]
        col_tempo2 = [c for c in df2.columns if 'Data' in c or 'Tempo' in c][0]
        
        df1.rename(columns={col_tempo1: 'Tempo'}, inplace=True)
        df2.rename(columns={col_tempo2: 'Tempo'}, inplace=True)
        
        df1['Tempo'] = pd.to_datetime(df1['Tempo'], dayfirst=True, format='mixed', errors='coerce')
        df2['Tempo'] = pd.to_datetime(df2['Tempo'], dayfirst=True, format='mixed', errors='coerce')
        
        df = pd.merge(df1.dropna(subset=['Tempo']), df2.dropna(subset=['Tempo']), on='Tempo', how='inner')
        return df
    except Exception as e:
        st.error(f"Errore: {e}")
        return None

st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_dati_intelligente()

if df is not None:
    st.write("Dati caricati con successo!")
    st.dataframe(df.head()) # Se vedi questa tabella, abbiamo vinto!
else:
    st.error("Non riesco a trovare i dati. Assicurati che i file siano CSV pubblici.")
