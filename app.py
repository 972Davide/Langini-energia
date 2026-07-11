import streamlit as st
import pandas as pd
import requests
import io

# URL definitivi
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")
st.title("🌦️ Langini: Intelligenza Energetica")

@st.cache_data(ttl=300)
def carica_dati():
    try:
        # Scarichiamo il contenuto come testo puro
        meteo_text = requests.get(URL_METEO, timeout=10).text
        eolico_text = requests.get(URL_EOLICO, timeout=10).text
        
        # Trasformiamo il testo in DataFrame (tabelle)
        df1 = pd.read_csv(io.StringIO(meteo_text))
        df2 = pd.read_csv(io.StringIO(eolico_text))
        
        # Rendiamo i nomi delle colonne uniformi (rimuoviamo spazi extra)
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        
        # Forza la prima colonna a chiamarsi "Tempo"
        df1.rename(columns={df1.columns[0]: "Tempo"}, inplace=True)
        df2.rename(columns={df2.columns[0]: "Tempo"}, inplace=True)
        
        # Convertiamo la colonna Tempo in formato data reale
        df1["Tempo"] = pd.to_datetime(df1["Tempo"], dayfirst=True, errors='coerce')
        df2["Tempo"] = pd.to_datetime(df2["Tempo"], dayfirst=True, errors='coerce')
        
        # Uniamo i due file sulla colonna Tempo
        df = pd.merge(df1, df2, on="Tempo", how="inner")
        
        # Convertiamo tutto il resto in numeri (gestendo le virgole)
        for col in df.columns:
            if col != "Tempo":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df
    except Exception as e:
        return f"Errore: {e}"

# Esecuzione
df = carica_dati()

if isinstance(df, str):
    st.error(f"Qualcosa non va nel caricamento: {df}")
elif df is not None and not df.empty:
    st.success("Dati caricati con successo!")
    st.line_chart(df.set_index("Tempo"))
else:
    st.warning("Nessun dato caricato. Verifica che le colonne si chiamino correttamente.")
