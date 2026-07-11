import streamlit as st
import pandas as pd
import requests
import io
import plotly.express as px

# URL confermati dai tuoi screenshot
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")
st.title("🌦️ Langini: Intelligenza Energetica")

@st.cache_data(ttl=300)
def scarica_e_pulisci(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        
        # Legge il file CSV
        df = pd.read_csv(io.StringIO(response.text))
        
        # Pulisce nomi colonne
        df.columns = df.columns.str.strip()
        
        # Trova la colonna Tempo (cerca "Data" o "Tempo")
        col_tempo = [c for c in df.columns if 'Data' in c or 'Tempo' in c]
        if not col_tempo:
            return None
        
        df.rename(columns={col_tempo[0]: "Tempo"}, inplace=True)
        df["Tempo"] = pd.to_datetime(df["Tempo"], dayfirst=True, errors='coerce')
        return df.dropna(subset=["Tempo"])
    except Exception:
        return None

# Caricamento
df_meteo = scarica_e_pulisci(URL_METEO)
df_eolico = scarica_e_pulisci(URL_EOLICO)

if df_meteo is not None and df_eolico is not None:
    # Unione sicura
    df = pd.merge(df_meteo, df_eolico, on="Tempo", how="inner")
    
    if not df.empty:
        st.success("Dati caricati con successo!")
        # Visualizzazione sicura: verifichiamo che le colonne esistano prima di plottare
        colonne_da_mostrare = [c for c in ['Temperatura', 'Watt', 'Vento'] if c in df.columns]
        if colonne_da_mostrare:
            st.line_chart(df.set_index("Tempo")[colonne_da_mostrare])
        else:
            st.warning("Dati caricati, ma non trovo le colonne 'Temperatura' o 'Watt'.")
    else:
        st.warning("I file sono stati letti, ma non trovo date corrispondenti per l'unione (merge).")
else:
    st.error("Impossibile scaricare i dati. Verifica che i fogli siano Pubblici come CSV.")
