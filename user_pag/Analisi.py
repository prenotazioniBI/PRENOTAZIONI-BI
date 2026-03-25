import streamlit as st
from grafici_utente import Grafici
from gauge_gestore import gauge_spesa_gestore
from gauge_richieste_gestore import  matrice_incassi_post_bi
from graficoPerformance import grafico_conversione_bi
import pandas as pd

def main(**kwargs):
    st.title("Analisi delle tue Richieste")

    df = kwargs.get("df_full")
    user = kwargs.get("user") or {}
    navigator = kwargs.get("navigator")
    dt_performance = kwargs.get("dt_performance") or st.session_state.get("dt_performance")

    username = user.get("username")
    username_norm = " ".join(reversed(username.strip().upper().split()))

    gauge_spesa_gestore(df, gestore_loggato=username)
    dt_performance["assetManager_norm"] = (
        dt_performance["assetManager"]
        .str.strip()
        .str.upper()
    )
    st.divider()
    grafico_conversione_bi(df, dt_performance, username=username_norm)
    
    st.divider()
    matrice_incassi_post_bi(dt_performance, username=username_norm)

if __name__ == "__main__":
    st.info("Questa pagina va aperta dal flusso principale dell'app.")