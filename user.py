from datetime import datetime
from excel_funzioni import salva_richiesta
import streamlit as st



def menu_utente(df, servizi_scelti, nav):
    user = st.session_state.get("user")
    dati_banner = st.session_state.get("richiesta")
    
    # IMPORTANTE: conservo il DataFrame originale per i casi di errore
    df_originale = df.copy()
    df_corrente = df.copy()
    
    richieste_salvate = 0
    errore = False
    messaggi_errore = []
    messaggi_successo = []
    
    for servizio in servizi_scelti:
        df_temp, ok, msg = salva_richiesta(
            df_corrente,
            portafoglio=dati_banner.get("portafoglio", ""),
            centro_costo="", 
            gestore=dati_banner.get("GESTORE", user.get("username", "")),
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
            nav=nav
        )
        
        if ok:
            df_corrente = df_temp
            richieste_salvate += 1
            messaggi_successo.append(msg)
            st.success(msg)
        else:
            errore = True
            messaggi_errore.append(msg)
            st.error(msg)


    if not errore and richieste_salvate > 0:

        return df_corrente, True, f"Salvate {richieste_salvate} richieste con successo"
    elif richieste_salvate > 0 and errore:

        return df_corrente, True, f"Salvate {richieste_salvate} richieste. Alcune erano duplicate."
    else:

        return df_originale, False, "Nessuna richiesta salvata - tutte erano duplicate o in errore"