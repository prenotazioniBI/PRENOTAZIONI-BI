import streamlit as st
from richieste_dt import banner_richiesta_utente_dt
from user import menu_utente_dt
import pandas as pd
from seleziona_servizio import seleziona_servizio, conferma_invio_richiesta

def main(**kwargs):
    st.title("Prenotazioni Invio di Diffide, Welcome Letter e Telegrammi")

    # df_dt = kwargs.get('df_dt_full')
    # navigator_dt = kwargs.get('navigator_dt')
    # dt_soggetti = kwargs.get('dt_soggetti')

    
    # col1, col2, _ = st.columns([0.13, 1, 0.6])
    # with col1:
    #     if st.button("⟳", key="refresh_pagina_diff"):
    #         for key in ["richiesta", "servizi_scelti", "inserimento_richiesta", "richiesta_in_corso"]:
    #             if key in st.session_state:
    #                 del st.session_state[key]
    #         st.rerun()
    
    # with col2:
    #     if not st.session_state.get("inserimento_richiesta", False):
    #         if st.button("NUOVA RICHIESTA"):
    #             st.session_state["inserimento_richiesta"] = True
    #             st.rerun()                                       
    #     else:
    #         if "richiesta" not in st.session_state:
    #             banner_richiesta_utente_dt(dt_soggetti)
                            
    #         dati_banner = st.session_state.get("richiesta")
    #         if dati_banner:
    #             st.title("Riepilogo dati")
    #             df_banner = pd.DataFrame([dati_banner])
    #             st.dataframe(df_banner)
    #             st.divider()
                
    #             user = st.session_state.get("user")
    #             if user and user.get("ruolo") == "admin":
    #                 st.warning("**ADMIN MODE**: Inserisci il nome del gestore per cui stai facendo la richiesta")
    #                 nome_gestore = st.text_input(
    #                     "Nome e Cognome del GESTORE", 
    #                     value=st.session_state["richiesta"].get("GESTORE", ""),
    #                     placeholder="Es: Mario Rossi",
    #                     help="Scrivi il nome esattamente come appare nel sistema: Nome Cognome"
    #                 )
                    
    #                 st.session_state["richiesta"]["GESTORE"] = nome_gestore
                    
    #                 if not nome_gestore.strip():
    #                     st.error("Il nome del gestore è obbligatorio!")
    #                     st.stop()
                    
    #                 st.info(f"Richiesta verrà salvata per: **{nome_gestore}**")
    #                 st.divider()
    #             #####################################################################################################
    #             servizi_scelti = seleziona_servizio(dt_soggetti, df_dt, navigator_dt, menu_utente_dt)


    #             if servizi_scelti:
    #                 conferma_invio_richiesta(servizi_scelti, df_dt, navigator_dt, menu_utente_dt)
                    #####################################################################################################
                    
if __name__ == "__main__":
    main()