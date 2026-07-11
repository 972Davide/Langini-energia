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
        # Carica senza saltare righe (header=0 prende la prima riga come nomi colonne)
        df1 = pd.read_csv(URL_METEO, header=0, on_bad_lines="skip")
        df2 = pd.read_csv(URL_EOLICO, header=0, on_bad_lines="skip")
        
        # Rinominazione forzata della prima colonna in "Tempo"
        df1.rename(columns={df1.columns[0]: "Tempo"}, inplace=True)
        df2.rename(columns={df2.columns[0]: "Tempo"}, inplace=True)
        
        # Converte in date
        df1["Tempo"] = pd.to_datetime(df1["Tempo"], dayfirst=True, errors="coerce")
        df2["Tempo"] = pd.to_datetime(df2["Tempo"], dayfirst=True, errors="coerce")
        
        # Unisce i due file
        df = pd.merge(df1.dropna(subset=["Tempo"]), df2.dropna(subset=["Tempo"]), on="Tempo", how="inner")
        
        # Forza i valori numerici (pulisce virgole e spazi)
        for col in df.columns:
            if col != "Tempo":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors="coerce").fillna(0)
        
        return df.sort_values("Tempo").tail(2500)
    except Exception as e:
        return str(e) # Restituisce l'errore come testo

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
