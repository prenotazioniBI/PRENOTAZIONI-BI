import streamlit as st
from user import menu_utente
from excel_funzioni import visualizza_richieste_per_gestore
from richieste import banner_richiesta_utente
import pandas as pd
from filtro_df import mostra_df_filtrato_utente
from sharepoint_utils import SharePointNavigator


def home_utente(df, df_soggetti, nav):
    user = st.session_state.get("user")
    if not user:
        st.stop()
    st.title("Area Gestore")
    selezione = st.sidebar.radio ("", [ "RICHIESTE", "NUOVA RICHIESTA"])
    if selezione == "RICHIESTE":
        st.subheader("Anteprima richieste")
        if st.button("⟳", key="refresh_pagina_tab1"):
            st.cache_data.clear()
        mostra_df_filtrato_utente(df)
    if selezione == "NUOVA RICHIESTA":
        col1, col2, _ = st.columns([0.13, 1, 0.1])
        with col1:
            if st.button("⟳", key="refresh_pagina_tab2"):
                for key in ["richiesta", "servizi_scelti", "inserimento_richiesta"]:
                    if key in st.session_state:
                        del st.session_state[key]
                        st.rerun()               
        with col2:
            if not st.session_state.get("inserimento_richiesta", False):
                if st.button("Aggiungi una richiesta"):
                    st.session_state["inserimento_richiesta"] = True
                    st.rerun()
            else:
                if "richiesta" not in st.session_state:
                    banner_richiesta_utente(df_soggetti)
                dati_banner = st.session_state.get("richiesta")
                if dati_banner:
                    st.title("Riepilogo dati")
                    df_banner = pd.DataFrame([dati_banner])
                    st.dataframe(df_banner)
                    richieste = [
                            "Ricerca eredi accettanti",
                            "Info lavorativa Full (residenza + telefono + impiego)",
                            "Ricerca Anagrafica",
                            "Ricerca Telefonica",
                            "Ricerca Anagrafica + Telefono",
                            "Visura camerale",
                            "Bilancio",
                            "Rintraccio Conto corrente",
                            "Visura Camerale storica",
                            "Rintraccio Eredi Chiamati con verifica accettazione"
                    ]
                    
                    st.divider()
                    st.markdown("SELEZIONA RICHIESTA BI:")
                    servizi_scelti = st.multiselect(
                        " ",
                        richieste,
                        key="servizi_scelti"
                    )
                    
                    st.divider()
                                    
                    if st.button("Conferma invio richiesta", key="conferma_richiesta"):
                        df, esito, msg = menu_utente(df, servizi_scelti, nav)
                        if esito:
                            nav.upload_file()
                            for key in ["richiesta", "servizi_scelti", "inserimento_richiesta"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.rerun()       

                



