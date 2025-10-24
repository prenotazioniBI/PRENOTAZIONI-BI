import streamlit as st
import pandas as pd
from excel_funzioni import (
    modifica_celle_excel, 
    visualizza_richieste_per_stato_invio_provider,
    visualizza_richieste_Evase,
    unifica_file_utenti
)
from io import BytesIO
from ottimizzazione import gestisci_nuova_richiesta
from admin_menu import menu_admin


def home_admin(df, df_soggetti, nav, df_full):
    st.title("Area Admin")
    
    selezione = st.sidebar.radio("", [
        "NUOVA RICHIESTA",
        "CONVALIDA DATI",
        "RICHIESTE IN ATTESA", 
        "RICHIESTE EVASE"
    ])
    
    if selezione == "NUOVA RICHIESTA":
        st.subheader("Nuova Richiesta - Admin")
        st.info("Come admin puoi richiedere anche il servizio **Ricerca eredi accettanti** e **Rintraccio eredi chiamati con verifica accettazione**")
        
        # Lista completa servizi inclusi eredi
        richieste_admin = [
            "Ricerca eredi accettanti",
            "Rintraccio eredi chiamati con verifica accettazione",
            "Info lavorativa Full (residenza + telefono + impiego)",
            "Ricerca Anagrafica",
            "Ricerca Telefonica",
            "Ricerca Anagrafica + Telefono",
            "Rintraccio Conto corrente"
        ]
        
        # Usa la stessa funzione ma con menu_admin
        gestisci_nuova_richiesta(df, df_soggetti, richieste_admin, menu_admin, nav)
    
    elif selezione == "CONVALIDA DATI":
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

    elif selezione == "RICHIESTE IN ATTESA":
        st.subheader("Richieste in Attesa di Invio al Provider")
        
        col1, col2 = st.columns([0.1, 1])
        with col1:
            if st.button("⟳", key="refresh_attesa"):
                st.cache_data.clear()
                st.rerun()
        
        df_attesa = visualizza_richieste_per_stato_invio_provider(df)
        
        with col2:
            st.info(f"**Richieste in attesa: {len(df_attesa)}**")
        
        if not df_attesa.empty:
            st.dataframe(
                df_attesa,
                use_container_width=True,
                height=600,
                hide_index=True
            )
        else:
            st.success("Nessuna richiesta in attesa")
    
    elif selezione == "RICHIESTE EVASE":
        st.subheader("Richieste Evase")
        
        col1, col2 = st.columns([0.1, 1])
        with col1:
            if st.button("⟳", key="refresh_evase"):
                st.cache_data.clear()
                st.rerun()
        
        df_evase = visualizza_richieste_Evase(df)
        
        with col2:
            totale_costo = df_evase["COSTO"].sum() if "COSTO" in df_evase.columns else 0
            st.info(f"**Richieste evase: {len(df_evase)} | Costo totale: {totale_costo:.2f} €**")
        
        if not df_evase.empty:
            st.dataframe(
                df_evase,
                use_container_width=True,
                height=600,
                hide_index=True
            )
        else:
            st.info("Nessuna richiesta evasa")