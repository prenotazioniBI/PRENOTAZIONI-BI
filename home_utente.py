import streamlit as st
from user import menu_utente
from ottimizzazione import gestisci_nuova_richiesta
from user import visualizza_richieste_personali
import pandas as pd
from grafici_utente import Grafici


def home_utente(df, df_soggetti, nav):
    """
    Home utente:
    - Visualizza le richieste personali dal file nomeutente_prenotazioni.parquet
    - Lo storico completo da prenotazioni.parquet viene usato solo per i grafici
    - Le nuove richieste vanno nel file personale nomeutente_prenotazioni.parquet
    """
    user = st.session_state.get("user")
    if not user:
        st.stop()
    
    st.title("Area Gestore")
    selezione = st.sidebar.radio("", ["RICHIESTE", "NUOVA RICHIESTA", "ANALISI"])
    
    if selezione == "RICHIESTE":
        st.subheader("📋 Le Mie Richieste")
        st.info("Abbiamo aggiornato la logica di visualizzazione per permetterti " \
"di vedere subito le richieste appena inviate. Clicca sull’icona di " \
"aggiornamento e attendi qualche secondo per caricare i dati aggiornati.")
        
        # Visualizza le richieste personali dal file personale
        visualizza_richieste_personali(nav, df)


    
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
        
        # Per i grafici usiamo lo storico completo filtrato per gestore
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
            "Ritamaria Noto": "Rita Maria Noto",
            "Mariagiulia Berardi": "Maria Giulia Berardi",
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
        
        # Filtra per gestore corrente (VISUALIZZA STORICO COMPLETO per i grafici)
        username_norm = user["username"].replace(" ", "").lower()
        df_gestore = df[df["GESTORE"].astype(str).str.replace(" ", "").str.lower() == username_norm]
        
        grafici = Grafici(df_gestore)
        
        with col1:
            grafici.pivot_spesa_mensile_aggrid()
        with col2:
            grafici.torta_servizio_costo()