import streamlit as st
from grafici import aggrid_pivot, aggrid_pivot_delta
import pandas as pd
import plotly.graph_objects as go


def main(**kwargs):
        df = kwargs.get('df_full')
        navigator = kwargs.get('navigator')
        st.subheader("DASHBOARD")
        col1, col2 = st.columns(2)
        with col1:
            # Filtra solo i dati con ANNO 2024 e 2025
            df_bar = df[df["ANNO"].isin([2024, 2025])]

            # Raggruppa per anno e somma i costi
            costi_per_anno = df_bar.groupby("ANNO")["COSTO"].sum().reindex([2024, 2025]).fillna(0)

            # Ottieni i colori dal tema Streamlit
            primary_color = st.get_option("theme.primaryColor") or "#1f77b4"
            secondary_color = "#22577A"

            fig = go.Figure(
                data=[
                    go.Bar(
                        x=costi_per_anno.index.astype(str),
                        y=costi_per_anno.values,
                        marker_color=[secondary_color, primary_color],
                        text=[f"{v:,.2f} €" for v in costi_per_anno.values],
                        textposition="auto"
                    )
                ])
            fig.update_layout(
                title="Confronto COSTO tra 2024 e 2025",
                xaxis_title="Anno",
                yaxis_title="Totale Costo (€)",
                plot_bgcolor=st.get_option("theme.backgroundColor") or "#fff",
                paper_bgcolor=st.get_option("theme.backgroundColor") or "#fff",
                width=550,
                height=600   # Imposta la larghezza desiderata (puoi ridurre ancora se vuoi)
            )
            
            st.plotly_chart(fig, use_container_width=False)
        with col2: 
            # Mappatura per normalizzare i nomi dei servizi
            mappa_servizi = {
                "Ricerca Telefonica": "Ricerca Telefonica",
                "Ricerca Telefonica ": "Ricerca Telefonica",
                "Ricerca telefonica ": "Ricerca Telefonica",
                "Ricerca Telefonica (verificato)": "Ricerca Telefonica",
                "Anagrafica+Telefono" : "Ricerca Anagrafica + Telefono",
                "Rintraccio Eredi Chiamati con verifica accettazione" : "Ricerca eredi",
                "Ricerca eredi accettanti" : "Ricerca eredi"
            }
            # Filtra solo i dati del 2025
            df_2025 = df[df["ANNO"] == 2025].copy()
            
            # Normalizza i nomi dei servizi
            df_2025["NOME SERVIZIO"] = df_2025["NOME SERVIZIO"].replace(mappa_servizi)
            
            # Raggruppa per NOME SERVIZIO e somma i costi
            costi_servizio = df_2025.groupby("NOME SERVIZIO")["COSTO"].sum().sort_values(ascending=True)
            
            # Colori dal tema Streamlit
            primary_color = st.get_option("theme.primaryColor") or "#1f77b4"
            
            fig = go.Figure(
                data=[
                    go.Bar(
                        y=costi_servizio.index.astype(str),  # Asse Y: NOME SERVIZIO normalizzato
                        x=costi_servizio.values,             # Asse X: COSTO
                        orientation="h",                     # Barre orizzontali
                        marker_color=primary_color,
                        text=[f"{v:,.2f} €" for v in costi_servizio.values],
                        textposition="auto"
                    )
                ]
            )
            fig.update_layout(
                title="Costo totale per NOME SERVIZIO (2025)",
                xaxis_title="Totale Costo (€)",
                yaxis_title="Nome Servizio",
                plot_bgcolor=st.get_option("theme.backgroundColor") or "#fff",
                paper_bgcolor=st.get_option("theme.backgroundColor") or "#fff",
                width=550,
                height=600
            )
            st.plotly_chart(fig, use_container_width=True)


        df_line = df[df["ANNO"].isin([2024, 2025])].copy()
        df_line["MESE"] = pd.to_numeric(df_line["MESE"], errors="coerce")

        # Raggruppa per anno e mese, somma i costi
        costi_mensili = (
            df_line.groupby(["ANNO", "MESE"])["COSTO"]
            .sum()
            .unstack("ANNO")
            .reindex(index=range(1, 13), fill_value=0)
        )

        # Nomi mesi italiani
        mesi_italiani = [
            "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
        ]

        # Ottieni i colori dal tema Streamlit
        primary_color = st.get_option("theme.primaryColor") or "#1f77b4"
        secondary_color = "#22577A"

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=mesi_italiani,
            y=costi_mensili[2024] if 2024 in costi_mensili else [0]*12,
            mode="lines+markers+text",
            name="2024",
            line=dict(color=secondary_color, width=3),
            text=[f"{v:,.2f} €" for v in (costi_mensili[2024] if 2024 in costi_mensili else [0]*12)],
            textposition="top center"
        ))
        fig.add_trace(go.Scatter(
            x=mesi_italiani,
            y=costi_mensili[2025] if 2025 in costi_mensili else [0]*12,
            mode="lines+markers+text",
            name="2025",
            line=dict(color=primary_color, width=3),
            text=[f"{v:,.2f} €" for v in (costi_mensili[2025] if 2025 in costi_mensili else [0]*12)],
            textposition="top center"
        ))
        fig.update_layout(
            title="Andamento mensile del COSTO: confronto 2024 vs 2025",
            xaxis_title="Mese",
            yaxis_title="Totale Costo (€)",
            plot_bgcolor=st.get_option("theme.backgroundColor") or "#fff",
            paper_bgcolor=st.get_option("theme.backgroundColor") or "#fff",
            width=1000,
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)




    

if __name__ == "__main__":
    main()