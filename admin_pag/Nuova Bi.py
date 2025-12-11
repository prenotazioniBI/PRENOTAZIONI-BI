import streamlit as st
import pandas as pd
from excel_funzioni import (
    modifica_celle_excel, 
    visualizza_richieste_per_stato_invio_provider,
    visualizza_richieste_Evase
)
from io import BytesIO
from ottimizzazione import gestisci_nuova_richiesta
from admin_menu import menu_admin
import re
import unicodedata


def main(**kwargs):

    df = kwargs.get('df_full')
    user = kwargs.get('user')
    nav = kwargs.get('navigator')
    df_soggetti = kwargs.get('df_soggetti')

    st.title("Area Admin")


    st.subheader("Nuova Richiesta - Admin")
    st.info("Come admin puoi richiedere anche il servizio **Ricerca eredi accettanti** e **Rintraccio eredi chiamati con verifica accettazione**")
    
    # Lista completa servizi inclusi eredi
    richieste_admin = [
        "Ricerca eredi accettanti",
        "Rintraccio eredi chiamati con verifica accettazione",
        "Info lavorativa Full (residenza + telefono + impiego)",
        "Ricerca Anagrafica",
        "Ricerca Telefonica",
        "Ricerca Anagrafica + Telefono",
        "Rintraccio Conto corrente"
    ]
    
    gestisci_nuova_richiesta(df, df_soggetti, richieste_admin, menu_admin, nav)
    


if __name__ == "__main__":
    main()