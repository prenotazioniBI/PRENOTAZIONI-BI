import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder



class Grafici:
    def __init__(self, df):
        user = st.session_state.get("user")
        df = df.copy()
        mappa_gestori = {
        "ANTONELLA COCCO": "Antonella cocco",
        "BEATRICE LAORENZA": "Beatrice Laorenza",
        "Bacchetta ": "Carlo Bacchetta",
        "DANIELA RIZZI": "Daniela Rizzi",
        "FINGEST CREDIT": "Fingest Group",
        "GIUSEPPE NIGRA": "Giuseppe Nigra",
        "LAMYAA HAKIM": "Lamyaa Hakim",
        "MATTEO CATARZI": "Matteo Catarzi",
        "Magnifico Gelsomina ": "Gelsomina Magnifico",
        "Mauro Gualtiero ": "Mauro Gualtiero",
        "Michele  Oranger": "Michele Oranger",
        "RITA NOTO": "Rita Maria Noto",
        "Rita Maria Noto ": "Rita Maria Noto",
        "Rita Noto": "Rita Maria Noto",
        "Rita maria Noto": "Rita Maria Noto",
        "Ruscelli lisa": "Ruscelli Lisa",
        "Tiziana Alibrandi ": "Tiziana Alibrandi",
        "VALENTINA BARTOLO": "Valentina Bartolo",
        "VALERIA NAPOLEONE": "Valeria Napoleone",
        "carmela lanciano": "Carmela Lanciano",
        "silvia stefanelli": "Silvia Stefanelli",
        " AGECREDIT": "AGECREDIT"
    }
        if "GESTORE" in df.columns:
            df["GESTORE"] = df["GESTORE"].replace(mappa_gestori)
        if "COSTO" in df.columns:
            df["COSTO"] = pd.to_numeric(df["COSTO"], errors="coerce").fillna(0)
        
        if user and "username" in user:

            username_norm = user["username"].replace(" ", "").lower()
            df = df[df["GESTORE"].astype(str).str.replace(" ", "").str.lower() == username_norm]
        self.df = df
        self.palette = [
            "#bb5a38",  # primaryColor
            "#3d3a2a",  # textColor
            "#1976d2",  # blu simile
            "#ff9800",  # arancione
            "#f4f3ed",  # backgroundColor
            "#ecebe3",  # secondaryBackgroundColor
            "#d3d2ca",  # borderColor
        ]

    def torta_servizio_costo(self):
        fig = px.pie(
            self.df,
            names="NOME SERVIZIO",
            values="COSTO",
            title="Distribuzione COSTO per NOME SERVIZIO",
            color_discrete_sequence=self.palette
        )
        st.plotly_chart(fig)    
    def pivot_spesa_mensile_aggrid(self):
        df = self.df[self.df["ANNO"].isin([2024, 2025])].copy()
        mesi_ordinati = [
            "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
        ]
        mesi_map = {str(i+1): mese for i, mese in enumerate(mesi_ordinati)}
        mesi_map.update({str(i+1).zfill(2): mese for i, mese in enumerate(mesi_ordinati)})
        df["MESE"] = df["MESE"].astype(str).str.strip()
        df["MESE"] = df["MESE"].map(mesi_map)
        df["COSTO"] = pd.to_numeric(df["COSTO"], errors="coerce").fillna(0)
        df = df[df["MESE"].isin(mesi_ordinati)]
        df["MESE"] = df["MESE"].astype(str)
        pivot = df.groupby(["ANNO", "MESE"], as_index=False)["COSTO"].sum()
        pivot = pivot.sort_values(["ANNO", "MESE"])
        pivot["COSTO"] = pivot["COSTO"].round(2)
    
        pivot_table = pivot.pivot(index="MESE", columns="ANNO", values="COSTO").fillna(0)
        pivot_table.columns = pivot_table.columns.astype(str)
        pivot_table = pivot_table.reindex(mesi_ordinati)
        pivot_table = pivot_table.reset_index()
        pivot_table["MESE"] = pivot_table["MESE"].fillna("").astype(str)
        for anno in ["2024", "2025"]:
            if anno not in pivot_table.columns:
                pivot_table[anno] = 0.0
        pivot_table = pivot_table[pivot_table["MESE"] != ""]
    
        gb = GridOptionsBuilder.from_dataframe(pivot_table)
        gb.configure_default_column(editable=False, groupable=True, sortable=True, resizable=True)
        gb.configure_column("MESE", headerName="Mese", pinned='left', width=120)
        for anno in ["2024", "2025"]:
            gb.configure_column(
                anno,
                headerName=f"Spesa {anno}",
                type="numericColumn",
                valueFormatter="x.toFixed(2)",
                width=120
            )
        gridOptions = gb.build()
    
        st.markdown("### Spesa mensile per gestore (2024-2025)")
        AgGrid(
            pivot_table,
            gridOptions=gridOptions,
            fit_columns_on_grid_load=True,
            height=400,
            theme="streamlit"
        )
        ultimo_anno = pivot["ANNO"].max() if not pivot.empty else ""
        mesi_presenti = pivot[pivot["ANNO"] == ultimo_anno]["MESE"].tolist() if ultimo_anno else []
        mesi_ordinati_presenti = [m for m in mesi_ordinati if m in mesi_presenti]
        if mesi_ordinati_presenti:
            ultimo_mese = mesi_ordinati_presenti[-1]
            spesa_ultimo_mese = pivot[(pivot["ANNO"] == ultimo_anno) & (pivot["MESE"] == ultimo_mese)]["COSTO"].sum()
            st.metric(f"Spesa nell'ultimo mese ({ultimo_mese} {ultimo_anno})", f"{spesa_ultimo_mese:.2f} €")
        else:
            st.metric(f"Spesa nell'ultimo mese", "0.00 €")