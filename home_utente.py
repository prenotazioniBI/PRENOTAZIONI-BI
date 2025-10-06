import streamlit as st
from user import menu_utente
from ottimizzazione import gestisci_nuova_richiesta
import pandas as pd
from filtro_df import mostra_df_filtrato_utente


def home_utente(df, df_soggetti, nav):
    user = st.session_state.get("user")
    if not user:
        st.stop()
    st.title("Area Gestore")

    selezione = st.sidebar.radio ("", [ "RICHIESTE", "NUOVA RICHIESTA"])
    if selezione == "RICHIESTE":
        st.subheader("Anteprima richieste")
        col1, col2, col3 = st.columns([0.2,1,1])
        with col1:
            if st.button("⟳", key="refresh_pagina_tab1"):
                st.cache_data.clear()
        with col2:
            costi_servizi = {
                "Rintraccio Conto corrente": 19.5,
                "Info lavorativa Full (residenza + telefono + impiego)": 10.5,
                "Ricerca eredi accettanti": 50,
                "Ricerca Anagrafica + Telefono": 2.9,
                "Ricerca Anagrafica": 0.6,
                "Ricerca Telefonica": 2.3,
            }
            richieste_utente = df[df["GESTORE"] == user["username"]]
            richieste_utente["COSTO_SERVIZIO"] = richieste_utente["NOME SERVIZIO"].map(costi_servizi).fillna(0)
            totale = richieste_utente["COSTO_SERVIZIO"].sum()

            st.info(f"**Costo delle richieste: {totale:.2f} €**")
        mostra_df_filtrato_utente(df)

    if selezione == "NUOVA RICHIESTA":
        
        richieste = [
            "Info lavorativa Full (residenza + telefono + impiego)",
            "Ricerca Anagrafica",
            "Ricerca Telefonica",
            "Ricerca Anagrafica + Telefono",
            "Rintraccio Conto corrente"
        ]
        gestisci_nuova_richiesta(df, df_soggetti, richieste, menu_utente, nav)
                



