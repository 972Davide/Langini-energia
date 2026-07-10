import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURAZIONE ---
URL_METEO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQvcTq-KenrIWPKg-WK1eTEFwBu70kc-ODtKUMev9JRuZUtC2LWqkzJton8wcTOBnAIVt7KaueuQxjS/pub?gid=0&single=true&output=csv"
URL_EOLICO = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBu3iMBBiAnzESlByyAsLX3W9xPAJB9biFQC8X4O9DEG50XWjWUnM-QRJNXga26_RrM8LWk6vgB34y/pub?gid=0&single=true&output=csv"

def pulisci_dati(df, colonna, min_val, max_val):
    """Filtra i valori fuori range sostituendoli con NaN."""
    if colonna in df.columns:
        df[colonna] = pd.to_numeric(df[colonna].astype(str).str.replace(',', '.'), errors='coerce')
        df.loc[(df[colonna] < min_val) | (df[colonna] > max_val), colonna] = np.nan
    return df

@st.cache_data(ttl=600)
def carica_e_elabora():
    try:
        # 1. Caricamento con gestione righe corrotte
        df1 = pd.read_csv(URL_METEO, on_bad_lines='skip').tail(2000)
        df2 = pd.read_csv(URL_EOLICO, skiprows=2, on_bad_lines='skip').tail(2000)
        
        # 2. Allineamento date
        df1.rename(columns={df1.columns[0]: 'Tempo'}, inplace=True)
        df1['Tempo'] = pd.to_datetime(df1['Tempo'].str.replace('.', ':'), dayfirst=True, errors='coerce').dt.floor('min')
        
        df2.rename(columns={df2.columns[0]: 'Tempo'}, inplace=True)
        df2['Tempo'] = pd.to_datetime(df2['Tempo'], dayfirst=True, errors='coerce').dt.floor('min')
        
        # 3. Pulizia fisica (Filtro dei dati anomali)
        df1 = pulisci_dati(df1, 'Temperatura', -20, 60)
        df1 = pulisci_dati(df1, 'Pressione Locale', 800, 1200)
        df2 = pulisci_dati(df2, 'Vento (m/s)', 0, 50)
        df2 = pulisci_dati(df2, 'Watt', 0, 15000)
        
        # 4. Unione
        df = pd.merge(df1, df2, on='Tempo', how='inner')
        return df.dropna(subset=['Tempo']).sort_values(by='Tempo')
    except Exception as e:
        st.error(f"Errore: {e}")
        return None

# --- INTERFACCIA ---
st.title("⚡ Langini: Intelligenza Energetica")
df = carica_e_elabora()

if df is not None and not df.empty:
    ultima_data = df['Tempo'].max()
    df_24h = df[df['Tempo'] >= (ultima_data - pd.Timedelta(hours=24))]
    
    st.write(f"Dati caricati correttamente. Ultimo aggiornamento: {ultima_data}")
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df_24h['Tempo'], y=df_24h['Vento (m/s)'], name="Vento"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_24h['Tempo'], y=df_24h['Watt'], name="Watt"), secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Dati non trovati. Verifica il formato dei fogli Google.")
