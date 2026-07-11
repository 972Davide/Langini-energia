import streamlit as st
import pandas as pd
import io
import requests # Importante: aggiunta questa riga!

URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

@st.cache_data(ttl=300)
def carica_dati_robusto(url):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return None
        df = pd.read_csv(io.StringIO(response.text))
        # Pulizia nomi colonne
        df.columns = df.columns.str.strip()
        # Cerca la colonna che contiene "Data" o "Tempo"
        col_data = [c for c in df.columns if 'Data' in c or 'Tempo' in c][0]
        df.rename(columns={col_data: "Tempo"}, inplace=True)
        df["Tempo"] = pd.to_datetime(df["Tempo"], dayfirst=True, errors='coerce')
        return df.dropna(subset=["Tempo"])
    except Exception as e:
        st.error(f"Errore caricamento: {e}")
        return None

st.title("🌦️ Langini: Intelligenza Energetica")
df_meteo = carica_dati_robusto(URL_METEO)
df_eolico = carica_dati_robusto(URL_EOLICO)

if df_meteo is not None and df_eolico is not None:
    # Unione dei dati sulla colonna Tempo
    df = pd.merge(df_meteo, df_eolico, on="Tempo", how="inner")
    st.success("Dati caricati correttamente!")
    st.line_chart(df.set_index("Tempo")[["Temperatura", "Watt"]]) # Esempio grafico
else:
    st.error("Dati non caricati. Verifica che i fogli Google siano pubblici e le colonne esistano.")
