import streamlit as st
from user import menu_utente
from richieste import banner_richiesta_utente
import pandas as pd
from filtro_df import mostra_df_filtrato_home_admin
import io 
import datetime
from datetime import timedelta



def home_Teamleader(df, df_soggetti, nav):
    user = st.session_state.get("user")
    if not user or user.get("ruolo") != "team leader":
        st.stop()
    st.title("Area Team Leader")
    selezione = st.sidebar.radio("", ["RICHIESTE", "NUOVA RICHIESTA", "RICHIESTA MASSIVA"])

    if selezione == "RICHIESTE":
        st.subheader("Anteprima richieste")
        if st.button("⟳", key="refresh_pagina_tab1"):
            st.cache_data.clear()
            st.rerun()
        df = mostra_df_filtrato_home_admin(df)
        st.dataframe(df, height =1000)


    if selezione == "NUOVA RICHIESTA":
        col1, col2, _ = st.columns([0.13, 1, 0.1])
        with col1:
            if st.button("⟳", key="refresh_pagina_tab2"):
                for key in ["richiesta", "servizi_scelti", "inserimento_richiesta"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        with col2:
            if not st.session_state.get("inserimento_richiesta", False):
                if st.button("Aggiungi una richiesta"):
                    st.session_state["inserimento_richiesta"] = True
                    st.rerun()
            else:
                if "richiesta" not in st.session_state:
                    banner_richiesta_utente(df_soggetti)
                dati_banner = st.session_state.get("richiesta")
                if dati_banner:
                    st.title("Riepilogo dati")
                    df_banner = pd.DataFrame([dati_banner])
                    st.dataframe(df_banner)
                    richieste = [
                        "Ricerca eredi accettanti",
                        "Info lavorativa Full (residenza + telefono + impiego)",
                        "Ricerca Anagrafica",
                        "Ricerca Telefonica",
                        "Ricerca Anagrafica + Telefono",
                        "Visura camerale",
                        "Bilancio",
                        "Rintraccio Conto corrente",
                        "Visura Camerale storica",
                        "Rintraccio Eredi Chiamati con verifica accettazione"
                    ]
                    st.divider()
                    st.markdown("SELEZIONA RICHIESTA BI:")
                    servizi_scelti = st.multiselect(
                        " ",
                        richieste,
                        key="servizi_scelti"
                    )
                    st.divider()
                    if st.button("Conferma invio richiesta", key="conferma_richiesta"):
                        df, esito, msg = menu_utente(df, servizi_scelti, nav)
                        if esito:
                            nav.upload_file()
                            for key in ["richiesta", "servizi_scelti", "inserimento_richiesta"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                        else:
                            st.error(msg)
    if selezione == "RICHIESTA MASSIVA":
        st.header("1- Scarica Template File Excel")
        df_template = pd.DataFrame({
            "PORTAFOGLIO": pd.Series(dtype="str"),
            "GESTORE": pd.Series(dtype="str"),
            "NDG DEBITORE": pd.Series(dtype="int"),
            "NOMINATIVO POSIZIONE": pd.Series(dtype="str"),
            "C.F.": pd.Series(dtype="str"),
        })
        buffer = io.BytesIO()
        df_template.to_excel(buffer, index=False)
        buffer.seek(0)

        st.download_button(
            label="Excel Richiesta Massiva",
            data=buffer,
            file_name="template_richiesta.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.header("2- Carica File Excel per Richiesta Massiva")
        uploaded_file = st.file_uploader("", type=['xlsx'])

        if uploaded_file is not None:
            df_massiva = pd.read_excel(uploaded_file)
            st.success("File Caricato")
            st.write(df_massiva.head())
            buttone = st.selectbox("Seleziona Servizio:",options =["DD PERSONE FISICHE", "DD PERSONE GIURIDICHE"])
            if buttone:
                if st.button("INVIA"):
                    oggi = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                    oggi_per_confronto = datetime.datetime.now()
                    tre_mesi_fa = oggi_per_confronto - timedelta(days=90)

                    cf_duplicati = []
                    nuove_righe = []

                    for idx, riga in df_massiva.iterrows():
                        cf = str(riga["C.F."]).strip()
                        portafoglio = riga.get("PORTAFOGLIO", "")
                        gestore = riga.get("GESTORE", "")
                        ndg_debitore = riga.get("NDG DEBITORE", "")
                        nominativo_posizione = riga.get("NOMINATIVO POSIZIONE", "")

                        mask = (
                            (df["C.F."].astype(str).str.strip() == cf) &
                            (df["NOME SERVIZIO"].astype(str).str.strip() == str(buttone).strip())
                        )
                        
                        duplicato = False
                        for data_str in df.loc[mask, "DATA RICHIESTA"]:
                            data_richiesta = pd.to_datetime(data_str, dayfirst=True, errors="coerce")
                            if pd.notnull(data_richiesta) and data_richiesta >= tre_mesi_fa:
                                cf_duplicati.append({
                                    "C.F.": cf,
                                    "PORTAFOGLIO": portafoglio,
                                    "NOMINATIVO POSIZIONE": nominativo_posizione,
                                    "NOME SERVIZIO": buttone,
                                    "DATA_ESISTENTE": data_richiesta.strftime("%d/%m/%Y")
                                })
                                duplicato = True
                                break 
                        if not duplicato:
                            nuova_riga = {
                                "PORTAFOGLIO": portafoglio,
                                "GESTORE": gestore,
                                "NDG DEBITORE": ndg_debitore,
                                "NOMINATIVO POSIZIONE": nominativo_posizione,
                                "C.F.": cf,
                                "DATA RICHIESTA": oggi,
                                "SERVIZIO RICHIESTO": f"Richiesta massiva {portafoglio}",
                                "NOME SERVIZIO": buttone,
                                "PROVIDER": "",
                                "INVIATE AL PROVIDER": "",
                                "COSTO": "",
                                "MESE": "",
                                "ANNO": "",
                                "N. RICHIESTE": "",
                                "RIFATTURAZIONE": "",
                                "TOT POSIZIONI": "",
                                "RIFIUTATA": "",
                                "NDG NOMINATIVO RICERCATO": "",
                                "NOMINATIVO RICERCA": ""
                            }
                            nuove_righe.append(nuova_riga)
                    if cf_duplicati:
                        st.warning(f"Saltati {len(cf_duplicati)} CF con richieste duplicate negli ultimi 3 mesi:")
                        df_duplicati = pd.DataFrame(cf_duplicati)
                        st.dataframe(df_duplicati)
                    if nuove_righe:

                        df_nuove = pd.DataFrame(nuove_righe)
                        df_finale = pd.concat([df, df_nuove], ignore_index=True)

                        if "id" in df_finale.columns:
                            df_finale = df_finale.drop(columns="id")
                        df_finale["id"] = range(1, len(df_finale) + 1)

                        buffer = io.BytesIO()
                        df_finale.to_excel(buffer, index=False)
                        buffer.seek(0)
                        file_content = buffer.getvalue()
                        file_data = {
                            'filename': "General/REPORT INCASSI/SOFTWARE INCASSI/prenotazioni.xlsx",
                            'content': file_content,
                            'size': len(file_content)
                        }
                        nav.file_buffer.append(file_data)
                        upload_esito = nav.upload_file()
                        
                        if upload_esito:
                            st.success(f"Aggiunte nuove richieste.")                                  
                    else:
                        st.warning("Nessuna nuova richiesta da processare")