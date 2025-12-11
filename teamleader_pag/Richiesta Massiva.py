import streamlit as st
import pandas as pd
import io
import datetime
from filtro_df import mostra_df_filtrato_home_admin
from excel_funzioni_diff import filtra_cf_massivi

def main(**kwargs):
    st.title("Richiesta Massiva")
    df = kwargs.get('df_full')
    nav = kwargs.get('navigator')

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
    
    # CORREZIONE: Inizializza df_massiva come DataFrame vuoto
    df_massiva = pd.DataFrame()

    if uploaded_file is not None:
        # CORREZIONE: Sposta la definizione qui e rimuovi la chiamata prematura
        df_massiva = pd.read_excel(uploaded_file)
        st.success("File Caricato")
        st.write(df_massiva.head())
        
        buttone = st.selectbox("Seleziona Servizio:", options=[
            "DD PERSONE FISICHE", 
            "DD PERSONE GIURIDICHE",
            "Info lavorativa Full (residenza + telefono + impiego)",
            "Ricerca Anagrafica",
            "Ricerca Telefonica",
            "Ricerca Anagrafica + Telefono",
            "Rintraccio Conto corrente",
            "Ricerca eredi accettanti"
        ])
        
        if buttone:
            if st.button("INVIA", key="invio"):
                oggi = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # CORREZIONE: Ora df_massiva è definita correttamente
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
                    
                    # CORREZIONE: Gestione upload migliorata
                    try:
                        buffer = io.BytesIO()
                        df_finale["COSTO"] = df_finale["COSTO"].replace("", pd.NA)
                        df_finale["COSTO"] = pd.to_numeric(df_finale["COSTO"], errors="coerce")
                        df_finale["INVIATE AL PROVIDER"] = pd.to_datetime(df_finale["INVIATE AL PROVIDER"], errors="coerce", dayfirst=True)
                        df_finale["DATA RICHIESTA"] = pd.to_datetime(df_finale["DATA RICHIESTA"], errors="coerce", dayfirst=True)
                        df_finale["NDG DEBITORE"] = df_finale["NDG DEBITORE"].astype(str)
                        df_finale["MESE"] = df_finale["MESE"].astype(str)
                        df_finale["ANNO"] = df_finale["ANNO"].astype(str)
                        
                        df_finale.to_parquet(buffer, index=False)
                        buffer.seek(0)
                        file_content = buffer.getvalue()
                        
                        # CORREZIONE: Usa il metodo più semplice per l'upload
                        site_id = nav.get_site_id()
                        drive_id, _ = nav.get_drive_id(site_id)
                        file_path = "General/PRENOTAZIONI_BI/prenotazioni.parquet"
                        
                        success = nav.upload_file_direct(site_id, drive_id, file_path, file_content)
                        
                        if success:
                            st.success(f"Aggiunte {len(df_nuove)} nuove richieste.")
                        else:
                            st.error("Errore durante l'upload del file")
                            
                    except Exception as e:
                        st.error(f"Errore durante il salvataggio: {str(e)}")
                else:
                    st.warning("Nessuna nuova richiesta da processare")
    else:
        st.info("Carica un file Excel per procedere con la richiesta massiva")

if __name__ == "__main__":
    main(
        user=None,
        df_full=None,
        df_soggetti=None,
        df_utenza=None,
        df_dt_full=None,
        navigator=None,
        navigator_dt=None
    )