import streamlit as st
from stdnum.it import codicefiscale, iva
import pandas as pd



@st.dialog("Inserisci nuova richiesta")
def banner_richiesta_utente(df_soggetti):
    portafogli = [
            "",
            "Lotto Acero 1",
            "Lotto Banca di Imola 2",
            "Lotto Banca Imola",
            "Lotto Banca Pop Valconca",
            "Lotto Banca Pop Valconca - Acquisto",
            "Lotto Banco di Lucca",
            "Lotto BAPS 1",
            "Lotto BAPS 2",
            "Lotto BAPS 3",
            "Lotto BAPS 4",
            "Lotto Benetton 1",
            "Lotto Blu Banca",
            "Lotto BP Lazio",
            "Lotto BPER 1",
            "Lotto BPER 2",
            "Lotto BPER 3",
            "Lotto BPER 4",
            "Lotto CF Plus",
            "Lotto Clessidra",
            "Lotto Climb 3",
            "Lotto ex Bramito",
            "Lotto Giamarca",
            "Lotto Giasone",
            "Lotto Girasole",
            "Lotto IRFIS",
            "Lotto La Cassa di Ravenna",
            "Lotto Libra",
            "Lotto Platinum",
            "Lotto Pop Npl 2018",
            "Lotto Pop Npl 2018 2",
            "Lotto Pop Npl 2018 3",
            "Lotto Ragusa",
            "Lotto Ragusa 2",
            "Lotto Ragusa 3",
            "Lotto Ragusa 4",
            "Lotto UnipolRec 1"
            ]
    st.write(f"Inserisci dati:")
    cf = st.text_input("CODICE FISCALE o P.IVA *")
    # ndg_debitore = st.text_input("NDG DEBITORE")
    # nominativo_posizione = st.text_input("NOMINATIVO POSIZIONE")
    # ndg_nominativo_ricercato = st.text_input("NDG NOMINATIVO RICERCATO")
    # nominativo_ricerca = st.text_input("NOMINATIVO RICERCA")
    # portafoglio = st.selectbox("PORTAFOGLIO", portafogli)
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




