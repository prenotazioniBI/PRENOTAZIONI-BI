import streamlit as st
from excel_funzioni import visualizza_richieste_Evase




def main(**kwargs):
    df = kwargs.get('df_full')

    st.subheader("Richieste Evase")
    
    col1, col2 = st.columns([0.1, 1])
    with col1:
        if st.button("⟳", key="refresh_evase"):
            st.cache_data.clear()
            st.rerun()
    
    df_evase = visualizza_richieste_Evase(df)
    
    with col2:
        totale_costo = df_evase["COSTO"].sum() if "COSTO" in df_evase.columns else 0
        st.info(f"**Richieste evase: {len(df_evase)} | Costo totale: {totale_costo:.2f} €**")
    
    if not df_evase.empty:
        st.dataframe(
            df_evase,
            use_container_width=True,
            height=600,
            hide_index=True
        )
    else:
        st.info("Nessuna richiesta evasa")


if __name__ == "__main__":
    main()