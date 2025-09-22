from datetime import datetime
from excel_funzioni import salva_richiesta
import streamlit as st
import time


def menu_utente(df, servizi_scelti, nav):
    user = st.session_state.get("user")
    dati_banner = st.session_state.get("richiesta")
    df = df.copy()
    richieste_salvate = 0
    errore = False
    for servizio in servizi_scelti:
        df, ok, msg = salva_richiesta(
            df,
            portafoglio=dati_banner.get("portafoglio", ""),
            centro_costo="", 
            gestore=user.get("username", ""),
            ndg_debitore=dati_banner.get("ndg_debitore", ""),
            nominativo_posizione=dati_banner.get("nominativo_posizione", ""),
            ndg_nominativo_ricercato=dati_banner.get("ndg_nominativo_ricercato", ""),
            nominativo_ricerca=dati_banner.get("nominativo_ricerca", ""),
            cf=dati_banner.get("cf"),
            nome_servizio=servizio,
            provider="",
            data_invio="",
            costo="",
            mese=datetime.now().month,
            anno=datetime.now().year,
            n_richieste=1,
            rifatturazione="NO",
            tot_posizioni=0,
            data_richiesta=datetime.now().strftime("%d/%m/%Y %H:%M"),
            rifiutata="",
            nav = nav
        )
        if ok:
            richieste_salvate += 1
            st.success(msg)
        else:
            errore = True
            st.error(msg)
            time.sleep(1)
            st.rerun()


    if not errore and richieste_salvate > 0:
        return df, True, msg
    else:
        return df, False, msg