import streamlit as st
import pandas as pd
import plotly.express as px

# Percorsi dei tuoi file CSV in locale
FILE_METEO = "Meteo.csv"   # Assicurati che il file si chiami così e sia nella stessa cartella
FILE_EOLICO = "Eolico.csv" # Assicurati che il file si chiami così e sia nella stessa cartella

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")
st.title("🌦️ Langini: Intelligenza Energetica (Localhost)")

def carica_dati_locale():
    try:
        # Leggiamo i CSV
        df1 = pd.read_csv(FILE_METEO)
        df2 = pd.read_csv(FILE_EOLICO)
        
        # Pulizia nomi colonne (rimuove spazi)
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        
        # Rinominiamo la prima colonna in 'Tempo'
        df1.rename(columns={df1.columns[0]: "Tempo"}, inplace=True)
        df2.rename(columns={df2.columns[0]: "Tempo"}, inplace=True)
        
        # Conversione date
        df1["Tempo"] = pd.to_datetime(df1["Tempo"], dayfirst=True)
        df2["Tempo"] = pd.to_datetime(df2["Tempo"], dayfirst=True)
        
        # Unione
        df = pd.merge(df1, df2, on="Tempo")
        
        # Pulizia numerica: sostituisce virgole con punti
        for col in df.columns:
            if col != "Tempo":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Errore nel caricamento: {e}")
        return None

# Caricamento e Visualizzazione
df = carica_dati_locale()

if df is not None:
    st.success("Dati caricati correttamente in locale!")
    st.dataframe(df.tail())
    
    # Grafico veloce
    st.line_chart(df.set_index("Tempo")[["Temperatura", "Watt"]])
else:
    st.warning("Non trovo i file CSV nella cartella. Verifica i nomi dei file!")
