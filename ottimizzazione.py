import streamlit as st
from richieste import banner_richiesta_utente
import pandas as pd

def mostra_totale_costi(servizi_scelti):
    costi_servizi = {
        "Ricerca eredi accettanti": 50,
        "Info lavorativa Full (residenza + telefono + impiego)": 10.5,
        "Ricerca Anagrafica + Telefono": 2.9,
        "Ricerca Anagrafica": 0.6,
        "Ricerca Telefonica": 2.3,
        "Rintraccio Conto corrente": 19.5,
    }
    totale = sum(costi_servizi.get(servizio, 0) for servizio in servizi_scelti)
    st.info(f"**Totale costi servizi selezionati: {totale:.2f} €**")

def gestisci_nuova_richiesta(df, df_soggetti, richieste, menu_utente, nav):
    col1, col2, _ = st.columns([0.13, 1, 0.6])
    with col1:
        if st.button("⟳", key="refresh_pagina_tab2"):
            for key in ["richiesta", "servizi_scelti", "inserimento_richiesta"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    with col2:
        if not st.session_state.get("inserimento_richiesta", False):
            if st.button("NUOVA RICHIESTA"):
                st.session_state["inserimento_richiesta"] = True
                st.rerun()
            st.code("NOTA*\n"
                "Per richiedere il rintraccio eredi è necessario rivolgersi tramite email al proprio Team Leader di riferimento.\n" \
                "" )
        else:
            
            if "richiesta" not in st.session_state:
                banner_richiesta_utente(df_soggetti)
            dati_banner = st.session_state.get("richiesta")
            if dati_banner:
                st.title("Riepilogo dati")
                df_banner = pd.DataFrame([dati_banner])
                st.dataframe(df_banner)
                st.divider()
                st.markdown("TIPOLOGIA RICHIESTA:")
                servizi_scelti = st.multiselect(
                    " ",
                    richieste,
                    key="servizi_scelti"
                )
                mostra_totale_costi(servizi_scelti)
                st.divider()
                if st.button("Conferma invio richiesta", key="conferma_richiesta"):
                    df, esito, msg = menu_utente(df, servizi_scelti, nav)
                    if esito:
                        nav.upload_file()
                        for key in ["richiesta", "servizi_scelti", "inserimento_richiesta"]:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.error(msg)
########################################################################################à




def normalizza_gestore(nome, lista_gestori):
    nome_clean = nome.replace(".", "").replace(" ", "").lower()
    for g in lista_gestori:
        g_clean = str(g).replace(".", "").replace(" ", "").lower()
        if nome_clean == g_clean:
            return g
    return nome
