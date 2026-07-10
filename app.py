import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy import stats

# --- CONFIGURAZIONE ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="Langini: Intelligenza Energetica", layout="wide")

# --- MOTORE DI PULIZIA ---
@st.cache_data(ttl=60)
def carica_e_elabora():
    try:
        df1 = pd.read_csv(URL_METEO)
        df2 = pd.read_csv(URL_EOLICO)
        
        # Rinominazione colonne sicura
        for df in [df1, df2]:
            df.columns = df.columns.str.strip()
            df.rename(columns={df.columns[0]: 'Tempo'}, inplace=True)
            df['Tempo'] = pd.to_datetime(df['Tempo'], format='mixed', dayfirst=True, errors='coerce')
        
        # Merge
        df = pd.merge(df1, df2, on='Tempo', how='inner').set_index('Tempo')
        
        # Pulizia tipi numerici
        for col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')

        # 1. FILTRI FISICI (Sanity Check)
        # Nota: adatta i nomi se nel file si chiamano diversamente
        if 'Temperatura' in df.columns:
            df = df[(df['Temperatura'] > -30) & (df['Temperatura'] < 60)]
        if 'Pressione Locale' in df.columns:
            df = df[(df['Pressione Locale'] > 900) & (df['Pressione Locale'] < 1100)]
        if 'Watt' in df.columns:
            df = df[(df['Watt'] >= 0) & (df['Watt'] < 10000)]

        # 2. FILTRI STATISTICI (Z-Score su Vento e Watt)
        for col in ['Vento (m/s)', 'Watt']:
            if col in df.columns and len(df) > 20:
                z_scores = np.abs(stats.zscore(df[col].fillna(0)))
                df = df[z_scores < 3]

        return df.reset_index()
    except Exception as e:
        return str(e)

# --- INTERFACCIA ---
st.title("⚡ Langini: Intelligenza Energetica")
df = carica_e_elabora()

if isinstance(df, str):
    st.error(f"Errore caricamento: {df}")
elif df is not None and not df.empty:
    st.success("Dati puliti e pronti!")
    
    # Regressione sicura
    if {'Vento (m/s)', 'Watt'}.issubset(df.columns):
        valid = df[['Vento (m/s)', 'Watt']].dropna()
        if len(valid) > 5:
            m, q = np.polyfit(valid['Vento (m/s)'], valid['Watt'], 1)
            st.metric("Modello Regressione", f"Watt = {m:.2f} * Vento + {q:.2f}")
    
    # Grafico
    fig = go.Figure()
    if 'Watt' in df.columns:
        fig.add_trace(go.Scatter(x=df['Tempo'], y=df['Watt'], name="Produzione"))
        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Nessun dato valido disponibile dopo i filtri.")
