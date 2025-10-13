import streamlit as st
from user import menu_utente
from ottimizzazione import gestisci_nuova_richiesta
import pandas as pd
from filtro_df import mostra_df_filtrato_utente
from grafici_utente import Grafici


def home_utente(df, df_soggetti, nav):
    """
    Home utente:
    - Visualizza lo storico completo da prenotazioni.parquet (filtrato per gestore)
    - Le nuove richieste vanno nel file personale nomeutente_prenotazioni.parquet
    """
    user = st.session_state.get("user")
    if not user:
        st.stop()
    
    st.title("Area Gestore")
    selezione = st.sidebar.radio("", ["RICHIESTE", "NUOVA RICHIESTA", "ANALISI"])
    
    if selezione == "RICHIESTE":
        st.subheader("Anteprima richieste")
        col1, col2, col3 = st.columns([0.2, 1, 1])
        
        with col1:
            if st.button("⟳", key="refresh_pagina_tab1"):
                st.cache_data.clear()
                st.rerun()
        
        with col2:
            # Normalizza nomi gestori per confronto
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
            }
            
            if "GESTORE" in df.columns:
                df["GESTORE"] = df["GESTORE"].replace(mappa_gestori)
            
            # Filtra per gestore corrente (VISUALIZZA STORICO COMPLETO)
            username_norm = user["username"].replace(" ", "").lower()
            df_gestore = df[df["GESTORE"].astype(str).str.replace(" ", "").str.lower() == username_norm]
            
            totale = df_gestore["COSTO"].sum() if "COSTO" in df_gestore.columns else 0
            st.info(f"**Costo totale richieste: {totale:.2f} €**")
        
        with col3:
            st.info(f"**Numero richieste: {len(df_gestore)}**")
        
        # Mostra storico completo filtrato
        mostra_df_filtrato_utente(df_gestore)
    
    elif selezione == "NUOVA RICHIESTA":
        richieste = [
            "Info lavorativa Full (residenza + telefono + impiego)",
            "Ricerca Anagrafica",
            "Ricerca Telefonica",
            "Ricerca Anagrafica + Telefono",
            "Rintraccio Conto corrente"
        ]
        # Le nuove richieste andranno nel file personale
        gestisci_nuova_richiesta(df, df_soggetti, richieste, menu_utente, nav)
    
    elif selezione == "ANALISI":
        col1, col2 = st.columns(2)
        
        # Filtra per gestore per le analisi
        username_norm = user["username"].replace(" ", "").lower()
        df_gestore = df[df["GESTORE"].astype(str).str.replace(" ", "").str.lower() == username_norm]
        
        grafici = Grafici(df_gestore)
        
        with col1:
            grafici.pivot_spesa_mensile_aggrid()
        with col2:
            grafici.torta_servizio_costo()