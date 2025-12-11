from datetime import datetime
from excel_funzioni import salva_richiesta_utente
import streamlit as st


def menu_admin(df, servizi_scelti, nav):
    """
    Gestisce il salvataggio delle richieste per l'admin
    L'admin ha un suo file personale admin_prenotazioni.parquet
    """
    user = st.session_state.get("user")
    dati_banner = st.session_state.get("richiesta")
    
    # Conservo il DataFrame originale per i casi di errore totale
    df_originale = df.copy()
    
    richieste_salvate = 0
    errore = False
    messaggi_errore = []
    messaggi_successo = []
    
    # L'admin deve specificare per chi sta facendo la richiesta
    nome_gestore = dati_banner.get("GESTORE", "")
    
    if not nome_gestore:
        st.error("ERRORE: Nome gestore non specificato!")
        return df_originale, False, "Nome gestore obbligatorio"
    
    for idx, servizio in enumerate(servizi_scelti):
        df_temp, ok, msg = salva_richiesta_utente(
            username=nome_gestore, 
            portafoglio=dati_banner.get("portafoglio", ""),
            centro_costo="", 
            gestore=nome_gestore, 
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
            richieste_salvate += 1
            messaggi_successo.append(msg)
            st.success(f"{msg} per **{nome_gestore}**")
        else:
            errore = True
            messaggi_errore.append(msg)
            with st.expander(f"Errore servizio: {servizio}", expanded=True):
                st.error(msg)

    if richieste_salvate > 0 and not errore:
        return df_temp, True, f"Salvate {richieste_salvate} richieste per {nome_gestore}"
    elif richieste_salvate > 0 and errore:
        return df_temp, True, f"Salvate {richieste_salvate}/{len(servizi_scelti)} richieste per {nome_gestore}. Alcune erano duplicate."
    else:
        return df_originale, False, f"❌ Nessuna richiesta salvata per {nome_gestore} - tutte erano duplicate o in errore"