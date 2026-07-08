import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURAZIONE ---
PREZZO_GSE_KW = 0.15
# Link garantiti come "Pubblicati come CSV"
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?output=csv"

DELTA_ORE = 1.0 / 60.0

# --- CARICAMENTO DATI ROBUSTO ---
@st.cache_data(ttl=60)
def carica_e_elabora():
    try:
        # Caricamento con gestione automatica delle intestazioni
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO)
        
        for df in [df1, df2]:
            # Pulisce spazi bianchi dai nomi colonne
            df.columns = df.columns.str.strip()
            # Forza la prima colonna a chiamarsi 'Tempo'
            df.rename(columns={df.columns[0]: 'Tempo'}, inplace=True)
            # Converte Tempo in datetime gestendo eventuali errori
            df['Tempo'] = pd.to_datetime(df['Tempo'], format='mixed', dayfirst=True, errors='coerce')
            df.dropna(subset=['Tempo'], inplace=True)
        
        # Merge basato sul Tempo (Inner Join)
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        
        # Pulizia numerica: gestisce virgole e punti
        for col in ['Vento (m/s)', 'Watt', 'Temperatura', 'Pressione Locale']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(',', '.').replace('nan', '0').astype(float)
        
        return df.sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore critico di lettura dati: {e}")
        return None

# Il resto del tuo codice segue esattamente come lo abbiamo scritto...
