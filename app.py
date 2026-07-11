import streamlit as st
import pandas as pd
import requests
import io

# Inserisci qui i link ottenuti da "Pubblica sul web" (formato CSV)
# --- URL FOGLI ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"


st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")
st.title("🌦️ Langini: Intelligenza Energetica")

@st.cache_data(ttl=300)
def carica_dati():
    try:
        # Scarica i dati
        r1 = requests.get(URL_METEO).text
        r2 = requests.get(URL_EOLICO).text
        
        # Leggi come DataFrame
        df1 = pd.read_csv(io.StringIO(r1))
        df2 = pd.read_csv(io.StringIO(r2))
        
        # Converte la colonna Tempo in formato data
        df1["Tempo"] = pd.to_datetime(df1["Tempo"], dayfirst=True)
        df2["Tempo"] = pd.to_datetime(df2["Tempo"], dayfirst=True)
        
        # Unisce i due file sulla colonna Tempo
        df = pd.merge(df1, df2, on="Tempo", how="inner")
        
        return df.sort_values("Tempo")
    except Exception as e:
        return f"Errore: {e}"

# Esecuzione
risultato = carica_dati()

if isinstance(risultato, str):
    st.error(risultato)
    st.info("Assicurati che la prima colonna si chiami 'Tempo' e che i file siano pubblici.")
else:
    st.success("Dati caricati!")
    st.dataframe(risultato.tail(10)) # Mostra gli ultimi dati
    
    # Grafico veloce
    if 'Temperatura' in risultato.columns and 'Watt' in risultato.columns:
        st.line_chart(risultato.set_index("Tempo")[["Temperatura", "Watt"]])
    else:
        st.warning("Assicurati che le colonne si chiamino 'Temperatura' e 'Watt'.")
