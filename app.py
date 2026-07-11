import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# I tuoi link (assicurati che siano quelli corretti pubblicati come CSV)
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def carica_dati():
    try:
        # Leggiamo i file come testo puro per vedere se scarichiamo qualcosa
        r1 = requests.get(URL_METEO, timeout=10)
        r2 = requests.get(URL_EOLICO, timeout=10)
        
        # Trasformiamo in dataframe
        df1 = pd.read_csv(io.StringIO(r1.text), header=0, on_bad_lines="skip")
        df2 = pd.read_csv(io.StringIO(r2.text), header=0, on_bad_lines="skip")
        
        # DEBUG: Ritorna il numero di righe invece del dataframe
        return f"Meteo: {len(df1)} righe, Eolico: {len(df2)} righe"
    except Exception as e:
        return f"Errore: {str(e)}"

# --- APP ---
st.title("🌦️ Langini: Intelligenza Energetica")
risultato = carica_dati()

if isinstance(risultato, str):
    st.error(f"Errore caricamento: {risultato}")
    st.info("Controlla che i file Google siano Pubblicati come CSV (non link di condivisione normale).")
elif risultato is not None and not risultato.empty:
    st.success("Dati caricati!")
    st.dataframe(risultato.tail()) # Mostra gli ultimi dati
    
    # Se vedi la tabella, qui puoi rimettere i tuoi grafici
else:
    st.warning("Nessun dato trovato.")
