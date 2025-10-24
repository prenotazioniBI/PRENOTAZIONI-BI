import streamlit as st
from user import menu_utente
from ottimizzazione import gestisci_nuova_richiesta
import pandas as pd
from filtro_df import mostra_df_filtrato_home_admin
import io 
import datetime

def filtra_cf_massivi(df, df_massiva):
    cf_duplicati = []
    nuove_righe = []

    for idx, riga in df_massiva.iterrows():
        cf = str(riga["C.F."]).strip()
        portafoglio = riga.get("PORTAFOGLIO", "")
        gestore = riga.get("GESTORE", "")
        ndg_debitore = riga.get("NDG DEBITORE", "")
        nominativo_posizione = riga.get("NOMINATIVO POSIZIONE", "")

        # Controllo duplicato su SERVIZIO RICHIESTO
        mask = (
            (df["C.F."].astype(str).str.strip() == cf) &
            (df["SERVIZIO RICHIESTO"].astype(str).str.contains("Richiesta massiva", na=False))
        )
        if mask.any():
            cf_duplicati.append({
                "C.F.": cf,
                "PORTAFOGLIO": portafoglio,
                "NOMINATIVO POSIZIONE": nominativo_posizione,
                "SERVIZIO RICHIESTO": "Richiesta massiva"
            })
        else:
            nuove_righe.append(riga)

    df_duplicati = pd.DataFrame(cf_duplicati)
    df_nuove = pd.DataFrame(nuove_righe)
    return df_duplicati, df_nuove


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
        richieste = [
            "Info lavorativa Full (residenza + telefono + impiego)",
            "Ricerca Anagrafica",
            "Ricerca Telefonica",
            "Ricerca Anagrafica + Telefono",
            "Rintraccio Conto corrente"
        ]
        gestisci_nuova_richiesta(df, df_soggetti, richieste, menu_utente, nav)

    if selezione == "RICHIESTA MASSIVA":
            st.header("1- Scarica Template File Excel")
            st.text("NDG DEBITORE --> NDG POSIZIONE\n" \
            "NOMINATIVO POSIZIONE --> NOMINATIVO RICERCATO (il soggetto anagrafico insomma)")
            df_template = pd.DataFrame({
                "PORTAFOGLIO": pd.Series(dtype="str"),
                "GESTORE": pd.Series(dtype="str"),
                "NDG DEBITORE": pd.Series(dtype="str"),
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
            
            filtra_cf_massivi(df, df_massiva)
        
            if uploaded_file is not None:
                df_massiva = pd.read_excel(uploaded_file)
                st.success("File Caricato")
                st.write(df_massiva.head())
                buttone = st.selectbox("Seleziona Servizio:", options=["DD PERSONE FISICHE", 
                                                                       "DD PERSONE GIURIDICHE",
                                                                       "Info lavorativa Full (residenza + telefono + impiego)",
                                                                        "Ricerca Anagrafica",
                                                                        "Ricerca Telefonica",
                                                                        "Ricerca Anagrafica + Telefono",
                                                                        "Rintraccio Conto corrente",
                                                                        "Ricerca eredi accettanti"])
                if buttone:
                    if st.button("INVIA", key = "invio"):
                        oggi = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                        df_duplicati, df_nuove = filtra_cf_massivi(df, df_massiva)
                        if not df_duplicati.empty:
                            st.warning(f"Saltati {len(df_duplicati)} CF già presenti come 'Richiesta massiva':")
                            st.dataframe(df_duplicati)
                        if not df_nuove.empty:
                            # Prepara le nuove righe
                            df_nuove = df_nuove.copy()
                            df_nuove["DATA RICHIESTA"] = oggi
                            df_nuove["NOME SERVIZIO"] = buttone
                            df_nuove["SERVIZIO RICHIESTO"] = df_nuove["PORTAFOGLIO"].astype(str).str.replace("Lotto", "", regex=False).str.strip().apply(lambda x: f"Richiesta massiva {x}")
                            # Aggiungi colonne mancanti se necessario
                            colonne_mancanti = [
                                "PROVIDER", "INVIATE AL PROVIDER", "COSTO", "MESE", "ANNO",
                                "N. RICHIESTE", "RIFATTURAZIONE", "TOT POSIZIONI",
                                "NDG NOMINATIVO RICERCATO", "NOMINATIVO RICERCA"
                            ]
                            for col in colonne_mancanti:
                                if col not in df_nuove.columns:
                                    df_nuove[col] = ""
                            df_finale = pd.concat([df, df_nuove], ignore_index=True)
                            if "id" in df_finale.columns:
                                df_finale = df_finale.drop(columns="id")
                            df_finale["id"] = range(1, len(df_finale) + 1)
                            buffer = io.BytesIO()
                            df_finale["COSTO"] = df_finale["COSTO"].replace("", pd.NA)
                            df_finale["COSTO"] = pd.to_numeric(df_finale["COSTO"], errors="coerce")
                            df_finale["INVIATE AL PROVIDER"] = pd.to_datetime(df_finale["INVIATE AL PROVIDER"], errors="coerce", dayfirst=True)
                            df_finale["DATA RICHIESTA"] = pd.to_datetime(df_finale["DATA RICHIESTA"], errors="coerce", dayfirst=True)  # <--- AGGIUNGI QUESTA RIGA
                            df_finale["NDG DEBITORE"] = df_finale["NDG DEBITORE"].astype(str)
                            df_finale["MESE"] = df_finale["MESE"].astype(str)
                            df_finale["ANNO"] = df_finale["ANNO"].astype(str)
                            df_finale.to_parquet(buffer, index=False)
                            buffer.seek(0)
                            file_content = buffer.getvalue()
                            file_data = {
                                'filename': "General/PRENOTAZIONI_BI/prenotazioni.parquet",
                                'content': file_content,
                                'size': len(file_content)
                            }
                            nav.file_buffer.append(file_data)
                            nav.upload_file()
                            st.success(f"Aggiunte nuove richieste.")

                        else:
                            st.warning("Nessuna nuova richiesta da processare")