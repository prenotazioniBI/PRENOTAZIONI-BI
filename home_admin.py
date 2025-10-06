import streamlit as st
from filtro_df import  mostra_df_filtrato
from excel_funzioni import modifica_celle_excel
from grafici import aggrid_pivot, aggrid_pivot_delta
from io import BytesIO
import pandas as pd
from ottimizzazione import gestisci_nuova_richiesta
from user import menu_utente

def refreshino(key_suffix=""):
    refresh = st.button("⟳", key=f"refresh_{key_suffix}")
    if refresh:
        st.cache_data.clear()

def home_admin(df, df_soggetti, nav, df_full):
    user = st.session_state.get("user")
    if not user or user.get("ruolo") != "admin":
        st.warning("Sessione scaduta o non autorizzata. Effettua di nuovo il login.")
        st.stop()
    else:
        st.title("Area Admin")
        sezione = st.sidebar.radio("",["AGGIORNA", "DA INVIARE","NUOVA RICHIESTA", "DASHBOARD"])

        if sezione == "DA INVIARE":
            col1, col2, _ = st.columns([0.04, 1, 0.1])
            with col1:
                refreshino(key_suffix="1")
            with col2:
                st.subheader("DA INVIARE")
                mostra_df_filtrato(df_full)


        if sezione == "AGGIORNA":
            col1, col2, col3 = st.columns([0.04, 1, 0.2])
            with col1:
                refreshino(key_suffix="2")
            with col2:
                st.subheader("AGGIORNA")
            with col3: 
                st.write("") 
                salva = st.button("Salva modifiche", key="salva_modifiche_excel")
            if "RIFATTURAZIONE" in st.session_state['df_full'].columns:
                    st.session_state['df_full']["RIFATTURAZIONE"] = (
                        st.session_state['df_full']["RIFATTURAZIONE"]
                        .fillna("")
                        .replace({"NO": ""})
                        .astype(str)
                    )
            edited_df = modifica_celle_excel(st.session_state['df_full'])
            if salva:
                if edited_df is None or edited_df.empty:
                    st.warning("Nessuna modifica da salvare.")
                else:
                    st.session_state['df_full'].update(edited_df)
                buffer = BytesIO()
                st.session_state['df_full'].to_parquet(buffer, index=False)
                buffer.seek(0)
                file_content = buffer.getvalue()
                file_data = {
                    'filename': "General/PRENOTAZIONI_BI/prenotazioni.parquet",
                    'content': file_content,
                    'size': len(file_content)
                }
                nav.file_buffer.append(file_data)
                nav.upload_file()
                st.cache_data.clear()
                st.rerun()
        if sezione == "NUOVA RICHIESTA":
            st.subheader("NUOVA RICHIESTA")
            richieste = [
                    "Ricerca eredi accettanti"
                ]
            gestisci_nuova_richiesta(df, df_soggetti, richieste, menu_utente, nav)

        if sezione == "DASHBOARD":
            st.subheader("DASHBOARD")
            aggrid_pivot_delta(df,
            group_col="CENTRO DI COSTO",
            sub_col="NOME SERVIZIO",
            value_col="COSTO",
            mese_col="MESE",
            height=500)
            

            st.subheader("PIVOT")

            df = df[df["INVIATE AL PROVIDER"].notnull()]
            mesi_italiani = [
                "Tutti", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
            ]
            df["MESE_IT"] = df["MESE"].apply(lambda x: mesi_italiani[int(x)] if pd.notnull(x) and str(x).isdigit() and 0 < int(x) <= 12 else "")
            mesi_unici = sorted(set(df["MESE_IT"].dropna().unique()) - {""})
            mesi = ["Tutti"] + mesi_unici
            anni = df["ANNO"].dropna().unique().tolist()
            anni.sort()
            anni.insert(0, "Tutti")

            col_mese, col_anno = st.columns(2)
            with col_mese:
                mese_sel = st.pills("Filtra per mese", mesi)
            with col_anno:
                anno_sel = st.pills("Filtra per anno", anni)

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