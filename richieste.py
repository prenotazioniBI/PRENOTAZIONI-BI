import streamlit as st
from stdnum.it import codicefiscale, iva
import pandas as pd

@st.dialog("Inserisci nuova richiesta")
def banner_richiesta_utente(df_soggetti):
    st.write(f"Inserisci dati:")
    cf = st.text_input("CODICE FISCALE o P.IVA *").strip()
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
        soggetti_cf = df_soggetti[df_soggetti["codiceFiscale"].astype(str) == cf]
        user = st.session_state.get("user", {})
        ruolo = user.get("ruolo", "")
        if "deceduto" in soggetti_cf.columns and (soggetti_cf["deceduto"] == "DECEDUTO").any():
            if ruolo not in ["admin", "team leader"]:
                st.error("Soggetto deceduto")
                st.stop()
        if not soggetti_cf.empty:
            portafogli = soggetti_cf["portafoglio"].unique().tolist()
            st.session_state.soggetti_cf = soggetti_cf
            st.session_state.portafogli = portafogli
            st.session_state.cf_ok = True
            st.rerun()
        else:
            st.error("Soggetto mai censito")
            st.stop()

    if st.session_state.get("cf_ok", False):
        soggetti_cf = st.session_state.soggetti_cf
        portafogli = st.session_state.portafogli
        if len(portafogli) > 1:
            portafoglio_sel = st.selectbox("Seleziona portafoglio", portafogli)
            conferma = st.button("Conferma selezione portafoglio")
            if conferma:
                soggetto = soggetti_cf[soggetti_cf["portafoglio"] == portafoglio_sel].iloc[0]
                st.session_state.richiesta = {
                    "cf": cf,
                    "portafoglio": portafoglio_sel,
                    "ndg_debitore": soggetto["ndg"],
                    "nominativo_posizione": soggetto["intestazione"],
                    "ndg_nominativo_ricercato": soggetto["ndgSoggetto"],
                    "nominativo_ricerca": soggetto["nomeCompleto"]
                }
                st.success("Dati inseriti correttamente.")
                st.session_state["active_tab"] = 1
                del st.session_state.cf_ok
                del st.session_state.soggetti_cf
                del st.session_state.portafogli
                st.rerun()
        else:
            soggetto = soggetti_cf.iloc[0]
            portafoglio_sel = soggetto["portafoglio"]
            st.session_state.richiesta = {
                "cf": cf,
                "portafoglio": portafoglio_sel,
                "ndg_debitore": soggetto["ndg"],
                "nominativo_posizione": soggetto["intestazione"],
                "ndg_nominativo_ricercato": soggetto["ndgSoggetto"],
                "nominativo_ricerca": soggetto["nomeCompleto"]
            }
            st.success("Dati inseriti correttamente.")
            st.session_state["active_tab"] = 1
            del st.session_state.cf_ok
            del st.session_state.soggetti_cf
            del st.session_state.portafogli
            st.rerun()