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

@st.cache_data(ttl=600) # Aumentiamo la cache a 10 minuti
def carica_dati_intelligente():
    try:
        # Usiamo un timeout per evitare che il server si blocchi aspettando Google
        session = requests.Session()
        
        def fetch_df(url):
            r = session.get(url, timeout=10) 
            if r.status_code != 200:
                raise Exception(f"Errore HTTP {r.status_code}")
            
            lines = r.text.splitlines()
            # Pulizia: cerca la prima riga che contiene dati (inizia con una data o 'Data')
            start_idx = 0
            for i, line in enumerate(lines):
                if 'Data' in line or 'Tempo' in line or '/' in line:
                    start_idx = i
                    break
            
            data = "\n".join(lines[start_idx:])
            return pd.read_csv(io.StringIO(data))

        df1 = fetch_df(URL_METEO)
        df2 = fetch_df(URL_EOLICO)
        
        # ... (il resto del tuo codice di merge rimane uguale)
        
    except Exception as e:
        # Logghiamo l'errore per capire cosa succede sul server
        st.error(f"DEBUG: Non riesco a scaricare il file. Dettaglio: {e}")
        return None

st.title("🌦️ Langini: Intelligenza Energetica")
df = carica_dati_intelligente()

if df is not None:
    st.write("Dati caricati con successo!")
    st.dataframe(df.head()) # Se vedi questa tabella, abbiamo vinto!
else:
    st.error("Non riesco a trovare i dati. Assicurati che i file siano CSV pubblici.")
