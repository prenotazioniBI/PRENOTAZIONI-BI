from filtro_df import mostra_df_completo_dt
import streamlit as st


def main(**kwargs):

    st.title("Diffide, Welcome Letter e Telegrammi")
    df_dt = kwargs.get('df_dt_full')
    navigator_dt = kwargs.get('navigator_dt')

    st.subheader("Dati Richieste")
    mostra_df_completo_dt(df_dt, key_suffix="1")

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