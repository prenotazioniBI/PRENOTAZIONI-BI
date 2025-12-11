import streamlit as st
from richieste import banner_richiesta_utente
import pandas as pd
from informazioni import dialog_info_richieste

def mostra_totale_costi(servizi_scelti):
    costi_servizi = {
        "Ricerca eredi accettanti": 15,
        "Rintraccio eredi chiamati con verifica accettazione" : 35,
        "Info lavorativa Full (residenza + telefono + impiego)": 10.5,
        "Ricerca Anagrafica + Telefono": 2.9,
        "Ricerca Anagrafica": 0.6,
        "Ricerca Telefonica": 2.3,
        "Rintraccio Conto corrente": 19.5,
    }
    totale = sum(costi_servizi.get(servizio, 0) for servizio in servizi_scelti)
    st.info(f"**Totale costi servizi selezionati: {totale:.2f} €**")

def gestisci_nuova_richiesta(df, df_soggetti, richieste, menu_funzione, nav, nome_gestore=None):
    """
    Gestisce il flusso di creazione di una nuova richiesta
    menu_funzione: può essere menu_utente o menu_admin
    """
    col1, col2, _ = st.columns([0.13, 1, 0.6])
    with col1:
        if st.button("⟳", key="refresh_pagina_tab2"):
            for key in ["richiesta", "servizi_scelti", "inserimento_richiesta", "richiesta_in_corso"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    with col2:
        if not st.session_state.get("inserimento_richiesta", False):
            if st.button("NUOVA RICHIESTA"):
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
                st.divider()
                
                # SE È ADMIN, CHIEDI IL NOME DEL GESTORE
                user = st.session_state.get("user")
                if user and user.get("ruolo") == "admin":
                    st.warning("**ADMIN MODE**: Inserisci il nome del gestore per cui stai facendo la richiesta")
                    nome_gestore = st.text_input(
                        "Nome e Cognome del GESTORE", 
                        value=st.session_state["richiesta"].get("GESTORE", ""),
                        placeholder="Es: Mario Rossi",
                        help="Scrivi il nome esattamente come appare nel sistema: Nome Cognome"
                    )
                    
                    # Aggiorna sempre il valore nel dizionario richiesta
                    st.session_state["richiesta"]["GESTORE"] = nome_gestore
                    
                    if not nome_gestore.strip():
                        st.error("Il nome del gestore è obbligatorio!")
                        st.stop()
                    
                    st.info(f"📝 Richiesta verrà salvata per: **{nome_gestore}**")
                    st.divider()
                
                st.markdown("TIPOLOGIA RICHIESTA:")
                servizi_scelti = st.multiselect(
                    " ",
                    richieste,
                    key="servizi_scelti"
                )
                
                if servizi_scelti:
                    mostra_totale_costi(servizi_scelti)
                
                clicked = st.button("*?*", key="info_richieste", help="Informazioni sulle richieste")
                if clicked:
                    dialog_info_richieste()
                
                st.divider()
                
                # PROTEZIONE CONTRO DOPPIO CLIC
                if "richiesta_in_corso" not in st.session_state:
                    st.session_state["richiesta_in_corso"] = False
                
                # Mostra messaggio se la richiesta è in corso
                if st.session_state["richiesta_in_corso"]:
                    st.warning("⏳ Richiesta in elaborazione, attendere...")
                
                if st.button("Conferma invio richiesta", key="conferma_richiesta", disabled=st.session_state["richiesta_in_corso"]):
                    if not servizi_scelti:
                        st.warning("⚠️ Seleziona almeno un servizio!")
                        st.stop()
                    
                    # Blocca il pulsante durante l'elaborazione
                    st.session_state["richiesta_in_corso"] = True
                    
                    # Chiama la funzione menu appropriata (utente o admin)
                    df, esito, msg = menu_funzione(df, servizi_scelti, nav)
                    
                    if esito:
                        st.success(msg)
                        # Pulisci lo stato
                        for key in ["richiesta", "servizi_scelti", "inserimento_richiesta", "richiesta_in_corso"]:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.rerun()
                    else:
                        st.error(msg)
                        # Riabilita il pulsante in caso di errore
                        st.session_state["richiesta_in_corso"] = False