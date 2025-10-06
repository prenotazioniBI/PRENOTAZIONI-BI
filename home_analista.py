import streamlit as st
from filtro_df import  mostra_df_filtrato_home_admin
from grafici import aggrid_pivot, aggrid_pivot_delta
import pandas as pd
import plotly.graph_objects as go
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
        sezione = st.sidebar.radio("",["PIVOT", "GRAFICI"])

        if sezione == "GRAFICI":
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
                # Raggruppa per portafoglio e somma i costi
                costi_portafoglio = df.groupby("PORTAFOGLIO")["COSTO"].sum().sort_values(ascending=False)
                
                # Colori dal tema Streamlit
                primary_color = st.get_option("theme.primaryColor") or "#1f77b4"
                
                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=costi_portafoglio.index.astype(str),
                            values=costi_portafoglio.values,
                            textinfo='label+percent',
                            hoverinfo='label+value+percent',
                            marker=dict(colors=[primary_color]*len(costi_portafoglio)),
                            hole=0.3  # se vuoi un effetto "donut", altrimenti rimuovi questa riga
                        )
                    ]
                )
                fig.update_layout(
                    title="Distribuzione COSTO per Portafoglio",
                    plot_bgcolor=st.get_option("theme.backgroundColor") or "#fff",
                    paper_bgcolor=st.get_option("theme.backgroundColor") or "#fff",
                    width=500,
                    height=500
                )
                st.plotly_chart(fig, use_container_width=False)




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


        if sezione == "PIVOT":
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