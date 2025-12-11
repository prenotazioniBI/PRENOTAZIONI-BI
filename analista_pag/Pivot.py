import streamlit as st
from grafici import aggrid_pivot, aggrid_pivot_delta
import pandas as pd
import plotly.graph_objects as go


def main(**kwargs):
        df = kwargs.get('df_full')
        navigator = kwargs.get('navigator')
        st.subheader("DASHBOARD")
        aggrid_pivot_delta(df,
        group_col="CENTRO DI COSTO",
        sub_col="NOME SERVIZIO",
        value_col="COSTO",
        mese_col="MESE",
        height=500)

        st.header("PIVOT")

        df = df[df["INVIATE AL PROVIDER"].notnull()]
        mesi_italiani = [
            "Tutti", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
        ]
        df["MESE_IT"] = df["MESE"].apply(lambda x: mesi_italiani[int(x)] if pd.notnull(x) and str(x).isdigit() and 0 < int(x) <= 12 else "")
        mesi_italiani_ordinati = mesi_italiani[1:]
        mesi_presenti = [m for m in mesi_italiani_ordinati if m in df["MESE_IT"].values]
        mesi = ["Tutti"] + mesi_presenti
        anni = df["ANNO"].dropna().unique().tolist()
        anni.sort()
        anni.insert(0, "Tutti")
        col1, col2 = st.columns(2)
        with col1:
            anno_sel = st.segmented_control("Filtra per anno", anni)
            mese_sel = st.selectbox("Filtra per mese", mesi)

        st.divider()
        df_filtrato = df
        if mese_sel != "Tutti":
            df_filtrato = df_filtrato[df_filtrato["MESE_IT"] == mese_sel]
        if anno_sel != "Tutti":
            df_filtrato = df_filtrato[df_filtrato["ANNO"] == anno_sel]
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
    

if __name__ == "__main__":
    main()