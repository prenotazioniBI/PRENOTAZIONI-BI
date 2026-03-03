import streamlit as st
from stdnum.it import codicefiscale, iva
import pandas as pd


@st.dialog("Inserisci nuova richiesta")
def banner_richiesta_utente(df_soggetti):
    st.write("Inserisci dati:")
    cf = st.text_input("CODICE FISCALE o P.IVA *").strip().upper()
    col1, _ = st.columns(2)
    avanti = col1.button("Avanti", key="btn_avanti_cf")

    if df_soggetti is None:
        st.warning("Nessun dato disponibile. Carica prima i dati dei soggetti.")
        return

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

        soggetti_cf = df_soggetti[df_soggetti["codiceFiscale"].astype(str).str.upper() == cf]
        user = st.session_state.get("user", {})
        ruolo = user.get("ruolo", "")

        if "deceduto" in soggetti_cf.columns and (soggetti_cf["deceduto"] == "DECEDUTO").any():
            if ruolo not in ["admin", "team leader"]:
                st.error("Soggetto deceduto")
                st.stop()

        if soggetti_cf.empty:
            st.error("Soggetto mai censito")
            st.stop()

        portafogli = soggetti_cf["portafoglio"].dropna().astype(str).unique().tolist()
        st.session_state.soggetti_cf = soggetti_cf.to_dict("records")
        st.session_state.portafogli = portafogli
        st.session_state.cf_salvato = cf
        st.session_state.cf_ok = True

        # reset selezioni precedenti
        st.session_state.pop("portafoglio_sel", None)
        st.session_state.pop("ndg_sel", None)
        st.rerun()

    if st.session_state.get("cf_ok", False):
        soggetti_cf = pd.DataFrame(st.session_state.get("soggetti_cf", []))
        portafogli = st.session_state.get("portafogli", [])
        cf = st.session_state.get("cf_salvato", "")

        if soggetti_cf.empty or not portafogli:
            st.error("Dati soggetto non disponibili.")
            st.stop()

        # ---- SELEZIONE PORTAFOGLIO (fix) ----
        if len(portafogli) > 1 and "portafoglio_sel" not in st.session_state:
            scelta = st.selectbox("Seleziona portafoglio", portafogli, key="sb_portafoglio")
            if st.button("Conferma selezione portafoglio", key="btn_conf_portafoglio"):
                st.session_state.portafoglio_sel = scelta
                st.session_state.pop("ndg_sel", None)  # reset eventuale NDG
                st.rerun()
            st.stop()
        elif len(portafogli) == 1 and "portafoglio_sel" not in st.session_state:
            st.session_state.portafoglio_sel = portafogli[0]

        portafoglio_sel = st.session_state.get("portafoglio_sel")
        soggetti_pf = soggetti_cf[soggetti_cf["portafoglio"].astype(str) == str(portafoglio_sel)]

        if soggetti_pf.empty:
            st.error("Nessun soggetto trovato nel portafoglio selezionato.")
            st.stop()

        ndg_unici = soggetti_pf["ndg"].astype(str).dropna().unique().tolist() if "ndg" in soggetti_pf.columns else []

        # ---- SELEZIONE NDG ----
        if len(ndg_unici) > 1 and "ndg_sel" not in st.session_state:
            st.warning(
                f"Il codice fiscale è associato a **{len(ndg_unici)} posizioni diverse**. "
                "Seleziona quella di interesse:"
            )
            ndg_options = {}
            for ndg in ndg_unici:
                rec = soggetti_pf[soggetti_pf["ndg"].astype(str) == ndg].iloc[0]
                ndg_options[ndg] = f"{rec.get('intestazione', 'N/A')} — NDG: {ndg}"

            ndg_sel = st.selectbox(
                "Posizioni disponibili:",
                options=list(ndg_options.keys()),
                format_func=lambda x: ndg_options[x],
                key="sb_ndg"
            )
            if st.button("Conferma posizione", key="btn_conf_ndg"):
                st.session_state.ndg_sel = ndg_sel
                st.rerun()
            st.stop()
        elif len(ndg_unici) == 1 and "ndg_sel" not in st.session_state:
            st.session_state.ndg_sel = ndg_unici[0]

        if "ndg_sel" in st.session_state:
            soggetti_pf = soggetti_pf[soggetti_pf["ndg"].astype(str) == str(st.session_state.ndg_sel)]

        if soggetti_pf.empty:
            st.error("Nessun dettaglio disponibile per la posizione selezionata.")
            st.stop()

        soggetto = soggetti_pf.iloc[0]
        st.session_state.richiesta = {
            "cf": cf,
            "portafoglio": soggetto.get("portafoglio"),
            "ndg_debitore": soggetto.get("ndg"),
            "nominativo_posizione": soggetto.get("intestazione"),
            "ndg_nominativo_ricercato": soggetto.get("ndgSoggetto"),
            "nominativo_ricerca": soggetto.get("nomeCompleto"),
        }

        st.success("Dati inseriti correttamente.")
        st.session_state["active_tab"] = 1
        for key in ["cf_ok", "soggetti_cf", "portafogli", "portafoglio_sel", "ndg_sel", "cf_salvato"]:
            st.session_state.pop(key, None)
        st.rerun()
# ...existing code...