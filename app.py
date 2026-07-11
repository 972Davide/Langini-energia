import streamlit as st
import pandas as pd
import io
import requests

@st.cache_data(ttl=300)
def carica_dati_robusto(url):
    try:
        # Scarica i dati come testo grezzo
        response = requests.get(url)
        if response.status_code != 200:
            return None
        
        # Legge il CSV ignorando errori di formattazione
        df = pd.read_csv(io.StringIO(response.text), on_bad_lines='skip')
        
        # Pulizia: rimuove spazi vuoti dai nomi colonne
        df.columns = df.columns.str.strip()
        
        # Identifica automaticamente la colonna data (cerca 'Data' o 'Tempo')
        col_data = [c for c in df.columns if 'Data' in c or 'Tempo' in c][0]
        df.rename(columns={col_data: "Tempo"}, inplace=True)
        
        # Converte la data
        df["Tempo"] = pd.to_datetime(df["Tempo"], dayfirst=True, errors='coerce')
        
        # Pulisce i dati numerici (sostituisce virgole con punti)
        for col in df.columns:
            if col != "Tempo":
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        return df.dropna(subset=["Tempo"])
    except Exception:
        return None
