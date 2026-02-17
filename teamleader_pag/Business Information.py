import streamlit as st
from filtro_df import mostra_df_filtrato_home_admin

def main(**kwargs):
    st.subheader("Anteprima richieste")
 
    if st.button("⟳", key="refresh_pagina_tab1"):
        st.cache_data.clear()
        st.rerun()
    df_full = kwargs.get('df_full')
    navigator = kwargs.get('navigator')
    df =  mostra_df_filtrato_home_admin(st.session_state['df_full'])


    st.dataframe(df, height =1000)
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