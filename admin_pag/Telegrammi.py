import streamlit as st
from excel_funzioni_diff import  unifica_file_utenti_dt, modifica_celle_excel_dt
from io import BytesIO
import pandas as pd

def main(**kwargs):
    st.title("Telegrammi")
    df_dt = kwargs.get('df_dt')
    
    if df_dt is None or df_dt.empty:
        nav = kwargs.get('navigator_dt') or st.session_state.get('navigator_dt')
        colonne_attese = [
            "PORTAFOGLIO", "CF", "NOMINATIVO POSIZIONE", "NDG DEBITORE", 
            "NDG NOMINATIVO RICERCATO", "GESTORE", "ORIGINATOR", "DESTINATARIO",
            "RAPPORTO", "GBV ATTUALE", "PEC DESTINATARIO", "INDIRIZZO",
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
                
                st.session_state['df_dt_full'] = df_dt
            else:
                st.warning("File dt.parquet non trovato o vuoto")
                df_dt = pd.DataFrame(columns=colonne_attese)
                
        except Exception as e:
            st.error(f"Errore caricamento dt.parquet: {e}")
            df_dt = pd.DataFrame(columns=colonne_attese)

    if not df_dt.empty and 'id' not in df_dt.columns:
        df_dt['id'] = range(1, len(df_dt) + 1)
    
    # CORREZIONE: Filtra per mostrare SOLO i telegrammi
    if not df_dt.empty and "TIPOLOGIA DOCUMENTO" in df_dt.columns:
        # Filtra per tutto quello che contiene "TELEGRAMMA"
        mask_telegrammi = df_dt["TIPOLOGIA DOCUMENTO"].astype(str).str.contains(
            "TELEGRAMMA", case=False, na=False
        )
        
        df_dt = df_dt[mask_telegrammi]
        
        st.info(f"**Totale righe (solo Telegrammi): {len(df_dt)}**")
    
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
                            nav = st.session_state.get('navigator_dt')
                            
                            if nav is None:
                                st.error("Navigator non disponibile")
                                st.stop()
                            
                            site_id = nav.get_site_id()
                            drive_id, _ = nav.get_drive_id(site_id)
                            
                            if "ELIMINA" in edited_df.columns:
                                df_to_save = edited_df[edited_df["ELIMINA"] == False].copy()
                                righe_eliminate = edited_df[edited_df["ELIMINA"] == True].copy()
                                df_to_save = df_to_save.drop(columns=["ELIMINA"])
                            else:
                                df_to_save = edited_df.copy()
                                righe_eliminate = pd.DataFrame()

                            if 'NDG DEBITORE' in df_to_save.columns:
                                df_to_save['NDG DEBITORE'] = df_to_save['NDG DEBITORE'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
                            
                            if 'NDG NOMINATIVO RICERCATO' in df_to_save.columns:
                                df_to_save['NDG NOMINATIVO RICERCATO'] = df_to_save['NDG NOMINATIVO RICERCATO'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')

                            df_full_updated = st.session_state.get('df_dt_full')
                            
                            if df_full_updated is None:
                                st.error("Database non caricato")
                                st.stop()
                            
                            df_full_updated = df_full_updated.copy()
                            
                            if 'id' not in df_full_updated.columns:
                                df_full_updated['id'] = range(1, len(df_full_updated) + 1)

                            if not righe_eliminate.empty:
                                num_da_eliminare = len(righe_eliminate)
                                
                                folder_path = st.secrets["DT_FOLDER_PATH"]
                                
                                def _find_col(df_obj, candidates):
                                    for c in candidates:
                                        if c in df_obj.columns:
                                            return c
                                    return None
                                
                                central_date_col = _find_col(righe_eliminate, ["DATA RICHIESTA", "data_richiesta"])
                                central_servizio_col = _find_col(righe_eliminate, ["TIPOLOGIA DOCUMENTO", "tipologia_documento"])
                                central_cf_col = _find_col(righe_eliminate, ["CF", "cf"])
                                gestore_col = _find_col(righe_eliminate, ["GESTORE", "gestore"])
                                
                                if not all([central_date_col, central_servizio_col, gestore_col]):
                                    st.warning("Colonne necessarie mancanti per l'eliminazione")
                                else:
                                    gestori = righe_eliminate[gestore_col].astype(str).str.strip().unique().tolist()
                                    
                                    for g in gestori:
                                        if not g or g.lower() == 'nan':
                                            continue
                                        
                                        slug = str(g).strip().lower().replace(" ", "_").replace(".", "_")
                                        personal_filename = f"{slug}_dt.parquet"
                                        personal_path = f"{folder_path.rstrip('/')}/{personal_filename}"
                                        
                                        file_exists = nav.file_exists(site_id, drive_id, personal_path)
                                        
                                        if not file_exists:
                                            continue
                                        
                                        file_data = nav.download_file(site_id, drive_id, personal_path)
                                        if isinstance(file_data, dict) and "content" in file_data:
                                            content = file_data["content"]
                                        elif isinstance(file_data, (bytes, bytearray)):
                                            content = bytes(file_data)
                                        elif hasattr(file_data, "read"):
                                            content = file_data.read()
                                        else:
                                            content = None
                                        
                                        if not content:
                                            continue
                                        
                                        df_personal = pd.read_parquet(BytesIO(content))
                                        
                                        personal_date_col = _find_col(df_personal, ["DATA RICHIESTA", "data_richiesta"])
                                        personal_servizio_col = _find_col(df_personal, ["TIPOLOGIA DOCUMENTO", "tipologia_documento"])
                                      
                                        
                                        if not all([personal_date_col, personal_servizio_col]):
                                            continue
                                        
                                        before_count = len(df_personal)
                                        
                                        righe_gestore = righe_eliminate[righe_eliminate[gestore_col].astype(str).str.strip() == g]

                                        for _, riga in righe_gestore.iterrows():
                                                data_completa = riga[central_date_col]
                                                servizio = str(riga[central_servizio_col]) if pd.notna(riga[central_servizio_col]) else ""
                                                gestore_riga = str(riga[gestore_col]) if pd.notna(riga[gestore_col]) else ""  # AGGIUNGI QUESTA
                                                
                                                if pd.notna(data_completa):
                                                    data_str = str(data_completa)
                                                    data_senza_micro = data_str.split('.')[0] if '.' in data_str else data_str
                                                else:
                                                    data_str = ""
                                                    data_senza_micro = ""
                                                
                                                servizio_lower = servizio.lower()
                                                
                                                # VECCHIO MATCH (senza gestore)
                                                # mask = (df_personal[personal_date_col].astype(str).str.split('.').str[0] == data_senza_micro) & \
                                                #        (df_personal[personal_servizio_col].astype(str).str.lower() == servizio_lower)
                                                
                                                # NUOVO MATCH - CON GESTORE ✅
                                                personal_gestore_col = _find_col(df_personal, ["GESTORE", "gestore"])
                                                
                                                mask = (df_personal[personal_date_col].astype(str).str.split('.').str[0] == data_senza_micro) & \
                                                    (df_personal[personal_servizio_col].astype(str).str.lower() == servizio_lower)
                                                
                                                if personal_gestore_col and gestore_riga:
                                                    mask = mask & (df_personal[personal_gestore_col].astype(str).str.strip() == gestore_riga)  # AGGIUNGI QUESTA
                                                
                                                
                                                df_personal = df_personal[~mask]

                                        removed = before_count - len(df_personal)

                                        if removed > 0:
                                            buf = BytesIO()
                                            df_personal.to_parquet(buf, index=False)
                                            buf.seek(0)
                                            ok = nav.upload_file_direct(site_id, drive_id, personal_path, buf.getvalue())
                                            
                                            if ok:
                                                st.success(f"Aggiornato {personal_filename} — rimosse {removed} righe")
                                            else:
                                                st.error(f"Errore caricamento {personal_filename}")
                                        
                                
                                        for _, riga in righe_eliminate.iterrows():
                                            data_completa = riga[central_date_col]
                                            servizio = str(riga[central_servizio_col]) if pd.notna(riga[central_servizio_col]) else ""
                                            cf = str(riga[central_cf_col]) if central_cf_col and pd.notna(riga[central_cf_col]) else ""
                                            gestore_riga = str(riga[gestore_col]) if pd.notna(riga[gestore_col]) else ""  # AGGIUNGI
                                            
                                            if pd.notna(data_completa):
                                                data_str = str(data_completa)
                                                data_senza_micro = data_str.split('.')[0] if '.' in data_str else data_str
                                            else:
                                                data_str = ""
                                                data_senza_micro = ""
                                            
                                            servizio_lower = servizio.lower()
                                            
                                            mask = (df_full_updated[central_date_col].astype(str).str.split('.').str[0] == data_senza_micro) & \
                                                (df_full_updated[central_servizio_col].astype(str).str.lower() == servizio_lower)
                                            
   
                                            if gestore_col and gestore_riga:
                                                mask = mask & (df_full_updated[gestore_col].astype(str).str.strip() == gestore_riga)
                                            
                                            if central_cf_col and cf:
                                                mask = mask & (df_full_updated[central_cf_col].astype(str) == cf)
                                            
                                            df_full_updated = df_full_updated[~mask]

                                    st.info(f"Database centrale: eliminate {num_da_eliminare} righe")

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
                            
                            buffer = BytesIO()
                            df_full_updated.to_parquet(buffer, index=False)
                            buffer.seek(0)
                            
                            success = nav.upload_file_direct(site_id, drive_id, file_path, buffer.getvalue())
                            
                            if success:
                                msg_success = "Modifiche salvate con successo"
                                if num_da_eliminare > 0:
                                    msg_success += f" ({num_da_eliminare} righe eliminate)"
                                st.success(msg_success)
                                st.session_state['df_dt_full'] = df_full_updated
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Errore durante il salvataggio del file centrale")

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
                        file_name="telegrammi_letter.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                with col3:
                    if num_da_eliminare > 0:
                        st.warning(f"{num_da_eliminare} righe selezionate per eliminazione")
        
        else:
            st.warning("Database vuoto o nessun telegramma trovato")
    
 