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

    gestisci_nuova_richiesta(df, df_soggetti, richieste, menu_utente, navigator)


if __name__ == "__main__":
    main()