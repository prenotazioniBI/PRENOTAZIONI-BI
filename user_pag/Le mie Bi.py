import streamlit as st
import pandas as pd
from nav import visualizza_richieste_personali
def main(**kwargs):

    st.title("Le Mie Richieste Bi")
    df_full = kwargs.get('df_full')
    navigator = kwargs.get('navigator')

    st.subheader("Dati Richieste")
    st.info("per visualizzare tutte le richieste clicca sull'icona di aggiornamento e attendi qualche secondo.")
    visualizza_richieste_personali(navigator, df_full)

    st.divider()


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