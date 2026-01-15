import streamlit as st
from ottimizzazione import gestisci_nuova_richiesta
from user import menu_utente


def main(**kwargs):
    st.title("Nuova Richiesta Business Information")
    df= kwargs.get('df_full')
    navigator = kwargs.get('navigator')
    df_soggetti = kwargs.get('df_soggetti')
    richieste = [
            "Info lavorativa Full (residenza + telefono + impiego)",
            "Ricerca Anagrafica",
            "Ricerca Telefonica",
            "Ricerca Anagrafica + Telefono",
            "Rintraccio Conto corrente"
        ]
    st.warning("I soggetti censiti sono visibili in app a partire dal giorno successivo.\
                Questo perché il database dell’app è alimentato da un gestionale di terze parti e\
                l’aggiornamento dei dati avviene tramite uno scarico automatico giornaliero programmato da loro.")
    gestisci_nuova_richiesta(df, df_soggetti, richieste, menu_utente, navigator)


if __name__ == "__main__":
    main()