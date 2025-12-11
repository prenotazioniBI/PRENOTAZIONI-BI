import streamlit as st
import pandas as pd
from excel_funzioni import (
    modifica_celle_excel, unifica_file_utenti
)
from io import BytesIO
import re
import unicodedata


def main(**kwargs):
    st.title("Business Information")
    df = kwargs.get('df_full')
    user = kwargs.get('user')
    nav = kwargs.get('navigator')
    df_soggetti = kwargs.get('df_soggetti')

    st.subheader("Convalida e Modifica Dati")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("🔄 AGGIORNA", help="Unifica tutti i file utente (incluso admin) in prenotazioni.parquet"):
            with st.spinner("Unificazione file in corso..."):
                folder_path = st.secrets["FOLDER_PATH"]
                df_unificato, righe_aggiunte, msg = unifica_file_utenti(nav, folder_path)
                
                if righe_aggiunte > 0:
                    st.success(msg)
                    st.session_state['df_full'] = df_unificato
                    st.cache_data.clear()
                    st.rerun()
                elif righe_aggiunte == 0:
                    st.info("Nessuna nuova richiesta da aggiungere")
                else:
                    st.error(msg)
    
    with col2:
        st.info(f"**Totale righe nel database: {len(st.session_state['df_full'])}**")
    
    with col3:
        if st.button("⟳ Refresh"):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    
    edited_df = modifica_celle_excel(df, mostra_editor=True)
    
    if edited_df is not None and not edited_df.empty:

        if "🗑️ ELIMINA" in edited_df.columns:
            righe_da_eliminare = edited_df[edited_df["🗑️ ELIMINA"] == True]
            num_da_eliminare = len(righe_da_eliminare)
        else:
            num_da_eliminare = 0
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 SALVA MODIFICHE", type="primary"):
                with st.spinner("Salvataggio in corso..."):

                    if "🗑️ ELIMINA" in edited_df.columns:
                        df_to_save = edited_df[edited_df["🗑️ ELIMINA"] == False].copy()
                        df_to_save = df_to_save.drop(columns=["🗑️ ELIMINA"])
                    else:
                        df_to_save = edited_df.copy()

                    df_full_updated = st.session_state['df_full'].copy()

                    if num_da_eliminare > 0:
                        ids_da_eliminare = righe_da_eliminare['id'].tolist()
                        df_full_updated = df_full_updated[~df_full_updated['id'].isin(ids_da_eliminare)]
                        try:
                            site_id = nav.get_site_id()
                            drive_id, _ = nav.get_drive_id(site_id)
                            folder_path = st.secrets["FOLDER_PATH"]
                            gestore_col = next((c for c in ['GESTORE', 'UTENTE', 'gestore', 'utente'] if c in righe_da_eliminare.columns), None)
                            if gestore_col is None:
                                st.warning("Colonna gestore/utente non trovata nelle righe da eliminare: impossibile aggiornare file personali.")
                            else:
                                        # lista gestori coinvolti
                                        gestori = righe_da_eliminare[gestore_col].astype(str).str.strip().unique().tolist()
    
                                        # helper per trovare prima colonna utile
                                        def _find_col(df_obj, candidates):
                                            for c in candidates:
                                                if c in df_obj.columns:
                                                    return c
                                            return None
    
                                        # colonne attese nel file centrale / righe_da_eliminare
                                        central_date_col = _find_col(righe_da_eliminare, ["DATA RICHIESTA", "data_richiesta", "data_richiesta_dt"])
                                        central_servizio_col = _find_col(righe_da_eliminare, ["NOME SERVIZIO", "nome_servizio", "nome servizio", "servizio"])
                                        central_cf_col = _find_col(righe_da_eliminare, ["C.F.", "cf", "CF"])
    
                                        for g in gestori:
                                            if not g:
                                                continue
                                            # crea nome file normalizzato: nome_cognome_prenotazioni.parquet
                                            slug = unicodedata.normalize("NFKD", str(g)).encode("ascii", "ignore").decode("ascii")
                                            slug = slug.strip().lower()
                                            slug = re.sub(r'\s+', '_', slug)
                                            slug = re.sub(r'[^a-z0-9_]', '_', slug)
                                            slug = re.sub(r'_+', '_', slug).strip('_')
                                            if not slug:
                                                continue
                                            personal_filename = f"{slug}_prenotazioni.parquet"
                                            personal_path = f"{folder_path.rstrip('/')}/{personal_filename}"
                                            try:
                                                if not nav.file_exists(site_id, drive_id, personal_path):
                                                    st.info(f"File personale non trovato per '{g}': {personal_filename}")
                                                    continue
                                                # scarica file personale
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
                                                    st.warning(f"Impossibile leggere il file personale di {g}")
                                                    continue
                                                df_personal = pd.read_parquet(BytesIO(content))
                                                # trova colonne nel file personale
                                                personal_date_col = _find_col(df_personal, ["DATA RICHIESTA", "data_richiesta", "data_richiesta_dt"])
                                                personal_servizio_col = _find_col(df_personal, ["NOME SERVIZIO", "nome_servizio", "nome servizio", "servizio"])
                                                personal_cf_col = _find_col(df_personal, ["C.F.", "cf", "CF"])
                                                if personal_date_col is None or personal_servizio_col is None or personal_cf_col is None:
                                                    st.warning(f"Colonne chiave mancanti in {personal_filename}; skipping.")
                                                    continue
    
                                                # estrai le righe da eliminare relative a questo gestore
                                                mask_g = righe_da_eliminare[gestore_col].astype(str).str.strip().str.lower() == str(g).strip().lower()
                                                to_remove = righe_da_eliminare.loc[mask_g].copy()
                                                if to_remove.empty:
                                                    st.info(f"Nessuna riga da rimuovere per {g}")
                                                    continue
                                                # build key function (normalizza)
                                                def _build_key(df_obj, date_col, svc_col, cf_col):
                                                    dates = pd.to_datetime(df_obj[date_col], errors='coerce', dayfirst=True)
                                                    dates_s = dates.dt.strftime("%Y-%m-%d %H:%M:%S").fillna("")
                                                    svc_s = df_obj[svc_col].astype(str).str.strip().str.lower().fillna("")
                                                    cf_s = df_obj[cf_col].astype(str).str.strip().str.upper().fillna("")
                                                    return dates_s + "||" + svc_s + "||" + cf_s
    
                                                # chiavi da rimuovere (dal centrale per questo gestore)
                                                if central_date_col and central_servizio_col and central_cf_col:
                                                    keys_to_remove = set(_build_key(to_remove, central_date_col, central_servizio_col, central_cf_col).tolist())
                                                else:
                                                    # fallback: prova con colonne 'data_richiesta','nome_servizio','cf' se presenti in righe_da_eliminare
                                                    keys_to_remove = set(_build_key(to_remove, to_remove.columns[0], to_remove.columns[0], to_remove.columns[0]).tolist()) if not to_remove.empty else set()
    
                                                # costruisci chiave per file personale e rimuovi matching
                                                df_personal['_del_key'] = _build_key(df_personal, personal_date_col, personal_servizio_col, personal_cf_col)
                                                before_count = len(df_personal)
                                                df_personal_updated = df_personal[~df_personal['_del_key'].isin(keys_to_remove)].copy()
                                                df_personal_updated = df_personal_updated.drop(columns=['_del_key'], errors='ignore')
                                                removed = before_count - len(df_personal_updated)
                                                if removed <= 0:
                                                    st.info(f"Nessuna riga rimossa in {personal_filename} (nessun match su data/servizio/cf)")
                                                    continue
                                                # riscrivi file personale
                                                buf = BytesIO()
                                                df_personal_updated.to_parquet(buf, index=False)
                                                buf.seek(0)
                                                ok = nav.upload_file_direct(site_id, drive_id, personal_path, buf.getvalue())
                                                if ok:
                                                    st.success(f"Aggiornato file personale: {personal_filename} — rimosse {removed} righe")
                                                else:
                                                    st.warning(f"Errore caricamento file personale: {personal_filename}")
                                            except Exception as _e:
                                                st.warning(f"Errore aggiornando file personale {personal_filename}: {_e}")

                        except Exception as _e:
                                        st.write("che ne so")
                    for idx, row in df_to_save.iterrows():
                        if 'id' in row:
                            mask = df_full_updated['id'] == row['id']
                            if mask.any():
                                for col in df_to_save.columns:
                                    if col in df_full_updated.columns:
                                        df_full_updated.loc[mask, col] = row[col]
                    
                    folder_path = st.secrets["FOLDER_PATH"]
                    file_path = f"{folder_path}/prenotazioni.parquet"
                    
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
                        st.session_state['df_full'] = df_full_updated
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Errore durante il salvataggio")
        
        with col2:
        
            df_export = edited_df.copy()
            if "🗑️ ELIMINA" in df_export.columns:
                df_export = df_export.drop(columns=["🗑️ ELIMINA"])
            
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Dati')
            buffer.seek(0)
            
            st.download_button(
                label="📥 SCARICA EXCEL",
                data=buffer,
                file_name="prenotazioni_modificate.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col3:
            if num_da_eliminare > 0:
                st.warning(f"⚠️ {num_da_eliminare} righe selezionate per eliminazione")


if __name__ == "__main__":
    main()