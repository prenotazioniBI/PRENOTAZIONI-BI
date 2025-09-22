import streamlit as st
from stdnum.it import codicefiscale, iva
import pandas as pd



@st.dialog("Inserisci nuova richiesta")
def banner_richiesta_utente(df_soggetti):
    st.write(f"Inserisci dati:")
    cf = st.text_input("CODICE FISCALE o P.IVA *")
    col1, _ = st.columns(2)
    avanti = col1.button("Avanti")
    df_soggetti = df_soggetti.copy()


    if avanti:
        if not cf:
            st.warning("CODICE FISCALE o P.IVA OBBLIGATORIO")
            st.stop()
        is_cf = codicefiscale.is_valid(cf)
        is_iva = iva.is_valid(cf)
        if not (is_cf or is_iva):
            st.warning("CODICE FISCALE o P.IVA NON VALIDO.")
            st.stop()
        if cf in df_soggetti["codiceFiscale"].astype(str).values:
            st.success("Soggetto già censito")
            soggetto = df_soggetti[df_soggetti["codiceFiscale"].astype(str) == cf].iloc[0]
            st.session_state.richiesta = {
                "cf": cf,
                "portafoglio": soggetto["portafoglio"],
                "ndg_debitore": soggetto["ndg"],
                "nominativo_posizione": soggetto["intestazione"],
                "ndg_nominativo_ricercato": soggetto["ndg_Soggetto"],
                "nominativo_ricerca": soggetto["nomeCompleto"]
            }
            st.success("Dati inseriti correttamente.")
            st.session_state["active_tab"] = 1
            st.rerun()
        else:
            st.error("Soggetto mai censito")
            st.stop()




