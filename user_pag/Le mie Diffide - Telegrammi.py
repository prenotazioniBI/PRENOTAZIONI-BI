import streamlit as st
import pandas as pd
from nav_dt import visualizza_richieste_personali_dt

def main(**kwargs):

    st.title("Diffide, Welcome Letter e Telegrammi Inviati")
    st.success("------------------ IN ATTESA DI APPROVAZIONE -------------------      \n\n" \
    "Nuova funzionalità per richiedere l'invio di Diffide, Welcome Letter e Telegrammi")
    # df_dt = kwargs.get('df_dt_full')
    # navigator_dt = kwargs.get('navigator_dt')

    # st.subheader("Dati Richieste")
    # st.info("per visualizzare tutte le richieste clicca sull'icona di aggiornamento e attendi qualche secondo.")
    # visualizza_richieste_personali_dt(navigator_dt, df_dt)
    # st.divider()


if __name__ == "__main__":

    
    main(
        user=None,
        df_full=None,
        df_soggetti=None,
        df_utenza=None,
        df_dt_full=None,
        navigator=None,
        navigator_dt=None
    )