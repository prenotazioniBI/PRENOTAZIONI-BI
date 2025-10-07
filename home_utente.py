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
            mappa_gestori = {
            "ANTONELLA COCCO": "Antonella cocco",
            "BEATRICE LAORENZA": "Beatrice Laorenza",
            "Bacchetta ": "Carlo Bacchetta",
            "DANIELA RIZZI": "Daniela Rizzi",
            "FINGEST CREDIT": "Fingest Group",
            "GIUSEPPE NIGRA": "Giuseppe Nigra",
            "LAMYAA HAKIM": "Lamyaa Hakim",
            "MATTEO CATARZI": "Matteo Catarzi",
            "Magnifico Gelsomina ": "Gelsomina Magnifico",
            "Mauro Gualtiero ": "Mauro Gualtiero",
            "Michele  Oranger": "Michele Oranger",
            "RITA NOTO": "Rita Maria Noto",
            "Rita Maria Noto ": "Rita Maria Noto",
            "Rita Noto": "Rita Maria Noto",
            "Rita maria Noto": "Rita Maria Noto",
            "Ruscelli lisa": "Ruscelli Lisa",
            "Tiziana Alibrandi ": "Tiziana Alibrandi",
            "VALENTINA BARTOLO": "Valentina Bartolo",
            "VALERIA NAPOLEONE": "Valeria Napoleone",
            "carmela lanciano": "Carmela Lanciano",
            "silvia stefanelli": "Silvia Stefanelli",
            " AGECREDIT": "AGECREDIT"
            # aggiungi qui altre normalizzazioni se servono
            }
            if "GESTORE" in df.columns:
                df["GESTORE"] = df["GESTORE"].replace(mappa_gestori)
            username_norm = user["username"].replace(" ", "").lower()
            df = df[df["GESTORE"].astype(str).str.replace(" ", "").str.lower() == username_norm]
            totale = df["COSTO"].sum()

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
                



