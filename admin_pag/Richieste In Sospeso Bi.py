import streamlit as st
from excel_funzioni import visualizza_richieste_per_stato_invio_provider



def main(**kwargs):
    df = kwargs.get('df_full')
    st.subheader("Richieste in Attesa di Invio al Provider")
    
    col1, col2 = st.columns([0.1, 1])
    with col1:
        if st.button("⟳", key="refresh_attesa"):
            st.cache_data.clear()
            st.rerun()
    
    df_attesa = visualizza_richieste_per_stato_invio_provider(df)
    
    with col2:
        st.info(f"**Richieste in attesa: {len(df_attesa)}**")
    
    if not df_attesa.empty:
        st.dataframe(
            df_attesa,
            use_container_width=True,
            height=600,
            hide_index=True
        )
    else:
        st.success("Nessuna richiesta in attesa")

if __name__ == "__main__":
    main()