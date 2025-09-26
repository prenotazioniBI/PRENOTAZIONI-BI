import streamlit as st
from filtro_df import  mostra_df_filtrato_home_admin
from grafici import aggrid_pivot, aggrid_pivot_delta
import pandas as pd
import calendar

def refreshino(key_suffix=""):
    refresh = st.button("⟳", key=f"refresh_{key_suffix}")
    if refresh:
        st.cache_data.clear()

def home_analista(df, nav, df_full):
    user = st.session_state.get("user")
    if not user or user.get("ruolo") != "analista":
        st.warning("Sessione scaduta o non autorizzata. Effettua di nuovo il login.")
        st.stop()
    else:
        st.title("Area Analisi")
        sezione = st.sidebar.radio("",["DASHBOARD", "RICHIESTE"])

        if sezione == "RICHIESTE":
            st.subheader("Anteprima richieste")
            if st.button("⟳", key="refresh_pagina_tab1"):
                st.cache_data.clear()
                st.rerun()
            df = mostra_df_filtrato_home_admin(df)
            st.dataframe(df, height =1000)


        if sezione == "DASHBOARD":
            st.subheader("DASHBOARD")
            aggrid_pivot_delta(df,
            group_col="CENTRO DI COSTO",
            sub_col="NOME SERVIZIO",
            value_col="COSTO",
            mese_col="MESE",
            height=500)

            st.subheader("PIVOT")


            df["MESE"] = pd.to_numeric(df["MESE"], errors="coerce").fillna(0).astype(int)
            mesi_numeri = df["MESE"].dropna().unique().tolist()
            mesi_numeri.sort()

            # Mesi in italiano (indice 1=Gennaio, 12=Dicembre)
            mesi_italiani = [
                "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
            ]

            # Crea una mappa {numero: nome italiano}
            mesi_map = {i: mesi_italiani[i] for i in mesi_numeri if 1 <= i <= 12}
            mesi_label = [mesi_map.get(i, str(i)) for i in mesi_numeri]
            mesi_label.insert(0, "Tutti")

            mese_sel = st.pills("Filtra per mese", mesi_label)

            df_filtrato = df 

            if mese_sel != "Tutti":
                mese_num = [k for k, v in mesi_map.items() if v == mese_sel]
                if mese_num:
                    df_filtrato = df[df["MESE"] == mese_num[0]]
            else:
                df_filtrato = df
            col1, spacer, col2 = st.columns([1, 0.1, 1])
            with col1:
                aggrid_pivot(df_filtrato, "GESTORE", "PORTAFOGLIO", "COSTO", value_name="Totale Costo", group_width=80,sub_width=130,value_width=130,height=500)
            with col2:
                aggrid_pivot(df_filtrato, "GESTORE", "NOME SERVIZIO", "COSTO", value_name="Totale Costo", group_width=80,sub_width=120,value_width=100,height=500)
               
            col1, spacer, col2 = st.columns([1, 0.1, 1])
            with col1:
                aggrid_pivot(df_filtrato, "CENTRO DI COSTO", "NOME SERVIZIO", "COSTO", value_name="Totale Costo", group_width=80,sub_width=120,value_width=100,height=500)
            with col2:
                aggrid_pivot(df_filtrato, "CENTRO DI COSTO", "PORTAFOGLIO", "COSTO", value_name="Totale Importo",group_width=80,sub_width=120,value_width=100,height=500)
            
            col1, spacer, col2 = st.columns([1, 0.1, 1])
            with col1:
                aggrid_pivot(df_filtrato, "PORTAFOGLIO", "GESTORE", "COSTO", value_name="Totale Importo",group_width=80,sub_width=120,value_width=100,height=500)