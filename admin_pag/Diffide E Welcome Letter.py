import streamlit as st
from excel_funzioni_diff import  unifica_file_utenti_dt, modifica_celle_excel_dt
import re
from io import BytesIO
import pandas as pd
def main(**kwargs):
    st.title("Diffide e Welcome Letter")
    df_dt = kwargs.get('df_dt')
    
    if df_dt is None or df_dt.empty:
        nav = kwargs.get('navigator_dt') or st.session_state.get('navigator_dt')
        colonne_attese = [
            "PORTAFOGLIO", "CF", "NOMINATIVO POSIZIONE", "NDG DEBITORE", 
            "NDG NOMINATIVO RICERCATO", "GESTORE", "ORIGINATOR", "DESTINATARIO",
            "RAPPORTO", "GBV ATTUALE",  "PEC DESTINATARIO", "INDIRIZZO", 
            "NUMERO CIVICO", "CITTA", "PROVINCIA", "SIGLA", "CAP", "REGIONE",
            "TIPO LUOGO", "EMAIL GESTORE", "TELEFONO GESTORE", "MODALITA INVIO",
            "TIPOLOGIA DOCUMENTO", "DATA RICHIESTA", "INVIATE AL PROVIDER", "id"
        ]
        df_dt = pd.DataFrame(columns=colonne_attese)
        
        try:
            site_id = nav.get_site_id()
            drive_id, _ = nav.get_drive_id(site_id)
            
            folder_path = st.secrets['DT_FOLDER_PATH']
            file_path = f"{folder_path}/dt.parquet"
            
            file_data = nav.download_file(site_id, drive_id, file_path)
            
            if isinstance(file_data, dict) and "content" in file_data:
                content = file_data["content"]
            elif isinstance(file_data, (bytes, bytearray)):
                content = bytes(file_data)
            elif hasattr(file_data, "read"):
                content = file_data.read()
            else:
                content = None
            
            if content:
                df_dt = pd.read_parquet(BytesIO(content))
 
                if 'id' not in df_dt.columns:
                    df_dt['id'] = range(1, len(df_dt) + 1)
                
                if 'NDG DEBITORE' in df_dt.columns:
                    df_dt['NDG DEBITORE'] = df_dt['NDG DEBITORE'].astype(str)
                    # Rimuovi ".0" finale se presente
                    df_dt['NDG DEBITORE'] = df_dt['NDG DEBITORE'].str.replace(r'\.0$', '', regex=True)
                    # Sostituisci "nan" con stringa vuota
                    df_dt['NDG DEBITORE'] = df_dt['NDG DEBITORE'].replace('nan', '')
                
                if 'NDG NOMINATIVO RICERCATO' in df_dt.columns:
                    df_dt['NDG NOMINATIVO RICERCATO'] = df_dt['NDG NOMINATIVO RICERCATO'].astype(str)
                    df_dt['NDG NOMINATIVO RICERCATO'] = df_dt['NDG NOMINATIVO RICERCATO'].str.replace(r'\.0$', '', regex=True)
                    df_dt['NDG NOMINATIVO RICERCATO'] = df_dt['NDG NOMINATIVO RICERCATO'].replace('nan', '')
                

                if 'CF' in df_dt.columns:
                    df_dt['CF'] = df_dt['CF'].astype(str).replace('nan', '')
                
                if 'RAPPORTO' in df_dt.columns:
                    df_dt['RAPPORTO'] = df_dt['RAPPORTO'].astype(str).replace('nan', '')
                

                
                st.session_state['df_dt_full'] = df_dt
            else:
                st.warning("File dt.parquet non trovato o vuoto")
                df_dt = pd.DataFrame(columns=colonne_attese)
                
        except Exception as e:
            st.error(f"Errore caricamento dt.parquet: {e}")
            df_dt = pd.DataFrame(columns=colonne_attese)

    if not df_dt.empty:
        if 'id' not in df_dt.columns:
            df_dt['id'] = range(1, len(df_dt) + 1)
        
        if 'NDG DEBITORE' in df_dt.columns:
            df_dt['NDG DEBITORE'] = df_dt['NDG DEBITORE'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
        
        if 'NDG NOMINATIVO RICERCATO' in df_dt.columns:
            df_dt['NDG NOMINATIVO RICERCATO'] = df_dt['NDG NOMINATIVO RICERCATO'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    
    if not df_dt.empty and "TIPOLOGIA DOCUMENTO" in df_dt.columns:
        mask_diffida_welcome = df_dt["TIPOLOGIA DOCUMENTO"].astype(str).str.contains(
            "DIFFIDA|DIFFDA|WELCOME LETTER|WL", case=False, na=False
        )

        mask_no_telegramma_solo = ~df_dt["TIPOLOGIA DOCUMENTO"].astype(str).str.contains(
            "^TELEGRAMMA$", case=False, na=False
        )
        
        df_dt = df_dt[mask_diffida_welcome & mask_no_telegramma_solo]
        
        st.info(f"**Totale righe (Diffide e Welcome Letter): {len(df_dt)}**")
    
    if not df_dt.empty:
        folder_path = st.secrets['DT_FOLDER_PATH']
        user = st.session_state.get('user')
        nav = st.session_state.get('navigator_dt')
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("AGGIORNA", help="Unifica tutti i file utente in dt.parquet"):
                with st.spinner("Unificazione file in corso..."):
                    try:
                        df_unificato, righe_aggiunte, msg = unifica_file_utenti_dt(nav, folder_path)
                        
                        if righe_aggiunte > 0:
                            st.success(msg)
                            
                            if 'id' not in df_unificato.columns:
                                df_unificato['id'] = range(1, len(df_unificato) + 1)
                            
                            if 'NDG DEBITORE' in df_unificato.columns:
                                df_unificato['NDG DEBITORE'] = df_unificato['NDG DEBITORE'].astype(str)
                                df_unificato['NDG DEBITORE'] = df_unificato['NDG DEBITORE'].str.replace(r'\.0$', '', regex=True).replace('nan', '')
                            
                            if 'NDG NOMINATIVO RICERCATO' in df_unificato.columns:
                                df_unificato['NDG NOMINATIVO RICERCATO'] = df_unificato['NDG NOMINATIVO RICERCATO'].astype(str)
                                df_unificato['NDG NOMINATIVO RICERCATO'] = df_unificato['NDG NOMINATIVO RICERCATO'].str.replace(r'\.0$', '', regex=True).replace('nan', '')
                            
                            st.session_state['df_dt_full'] = df_unificato
                            st.cache_data.clear()
                            st.rerun()
                        elif righe_aggiunte == 0:
                            st.info("Nessuna nuova richiesta da aggiungere")
                        else:
                            st.error(msg)
                            
                    except Exception as e:
                        st.error(f"Errore durante unificazione: {e}")
        
        with col2:
            pass
        
        with col3:
            if st.button("⟳ Refresh"):
                st.cache_data.clear()
                st.rerun()
       
        edited_df = modifica_celle_excel_dt(df_dt, mostra_editor=True)
    
    else:
        edited_df = None
        st.warning("Database vuoto o nessuna Diffida/Welcome Letter trovata")

    if edited_df is not None and not edited_df.empty:

        if "ELIMINA" in edited_df.columns:
            righe_da_eliminare = edited_df[edited_df["ELIMINA"] == True]
            num_da_eliminare = len(righe_da_eliminare)
        else:
            num_da_eliminare = 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("SALVA MODIFICHE", type="primary"):
                with st.spinner("Salvataggio in corso..."):
                    if "ELIMINA" in edited_df.columns:
                        df_to_save = edited_df[edited_df["ELIMINA"] == False].copy()
                        df_to_save = df_to_save.drop(columns=["ELIMINA"])
                    else:
                        df_to_save = edited_df.copy()

                    if 'NDG DEBITORE' in df_to_save.columns:
                        df_to_save['NDG DEBITORE'] = df_to_save['NDG DEBITORE'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
                    
                    if 'NDG NOMINATIVO RICERCATO' in df_to_save.columns:
                        df_to_save['NDG NOMINATIVO RICERCATO'] = df_to_save['NDG NOMINATIVO RICERCATO'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')

                    df_full_updated = st.session_state['df_dt_full'].copy()
                    if 'id' not in df_full_updated.columns:
                        df_full_updated['id'] = range(1, len(df_full_updated) + 1)

                    if num_da_eliminare > 0:
                        if 'id' in righe_da_eliminare.columns:
                            ids_da_eliminare = righe_da_eliminare['id'].tolist()
                            df_full_updated = df_full_updated[~df_full_updated['id'].isin(ids_da_eliminare)]
                            st.info(f"Eliminate {num_da_eliminare} righe dal database centrale")
                        else:
                            st.error("Colonna 'id' non trovata nelle righe da eliminare")

                    for idx, row in df_to_save.iterrows():
                        if 'id' in row and pd.notna(row['id']):
                            mask = df_full_updated['id'] == row['id']
                            if mask.any():
                                for col in df_to_save.columns:
                                    if col in df_full_updated.columns:
                                        df_full_updated.loc[mask, col] = row[col]
                    
                    if 'NDG DEBITORE' in df_full_updated.columns:
                        df_full_updated['NDG DEBITORE'] = df_full_updated['NDG DEBITORE'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
                    
                    if 'NDG NOMINATIVO RICERCATO' in df_full_updated.columns:
                        df_full_updated['NDG NOMINATIVO RICERCATO'] = df_full_updated['NDG NOMINATIVO RICERCATO'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
                    
                    folder_path = st.secrets["DT_FOLDER_PATH"]
                    file_path = f"{folder_path}/dt.parquet"
                    
                    site_id = nav.get_site_id()
                    drive_id, _ = nav.get_drive_id(site_id)
                    
                    buffer = BytesIO()
                    df_full_updated.to_parquet(buffer, index=False)
                    buffer.seek(0)
                    
                    success = nav.upload_file_direct(site_id, drive_id, file_path, buffer.getvalue())
                    
                    if success:
                        msg_success = "Modifiche salvate con successo!"
                        if num_da_eliminare > 0:
                            msg_success += f" ({num_da_eliminare} righe eliminate)"
                        st.success(msg_success)
                        st.session_state['df_dt_full'] = df_full_updated
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Errore durante il salvataggio")
        
        with col2:
            df_export = edited_df.copy()
            if "ELIMINA" in df_export.columns:
                df_export = df_export.drop(columns=["ELIMINA"])
            
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Dati')
            buffer.seek(0)
            
            st.download_button(
                label="SCARICA EXCEL",
                data=buffer,
                file_name="diffide_welcome_letter.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col3:
            if num_da_eliminare > 0:
                st.warning(f"⚠️ {num_da_eliminare} righe selezionate per eliminazione")