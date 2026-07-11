import streamlit as st
import pandas as pd
import io
import requests

# URL dei tuoi fogli (assicurati che siano corretti)
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def carica_dati_robusto(url):
    try:
        # Scarica il CSV
        response = requests.get(url)
        if response.status_code != 200:
            return None
        
        # Legge il CSV
        df = pd.read_csv(io.StringIO(response.text))
        
        # Pulizia nomi: rimuove spazi extra
        df.columns = df.columns.str.strip()
        
        # Forza la prima colonna a chiamarsi "Tempo"
        df.rename(columns={df.columns[0]: "Tempo"}, inplace=True)
        
        # Converte la colonna Tempo in formato data
        df["Tempo"] = pd.to_datetime(df["Tempo"], dayfirst=True, errors='coerce')
        
        return df.dropna(subset=["Tempo"])
    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        return None

st.title("🌦️ Langini: Intelligenza Energetica")

# Caricamento dati
df_meteo = carica_dati_robusto(URL_METEO)
df_eolico = carica_dati_robusto(URL_EOLICO)

if df_meteo is not None and df_eolico is not None:
    # Merge basato sulla colonna 'Tempo'
    df = pd.merge(df_meteo, df_eolico, on="Tempo", how="inner")
    
    if not df.empty:
        st.success("Dati caricati correttamente!")
        # Esempio di visualizzazione: serie temporale
        df = df.set_index("Tempo")
        st.line_chart(df[["Temperatura", "Watt"]]) 
    else:
        st.warning("Il merge non ha trovato date corrispondenti. Controlla che i formati data siano identici.")
else:
    st.error("Dati non caricati. Verifica che i fogli siano Pubblici come CSV.")
