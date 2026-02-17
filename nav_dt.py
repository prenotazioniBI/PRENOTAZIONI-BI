import streamlit as st
import pandas as pd
import io

def carica_richieste_personali_dt(nav):
    """Carica le richieste DT personali dell'utente dal suo file su SharePoint"""
    user = st.session_state.get("user", {})
    email = user.get("email", "")

    if email:
        nome_cognome = email.split("@")[0].replace(".", "_").lower()
        if nome_cognome.endswith("_ext"):
            nome_cognome = nome_cognome[:-4]
        file_name = f"{nome_cognome}_dt.parquet"
    else:
        username = user.get("username", "")
        username_norm = str(username).strip().lower().replace(" ", "_")
        file_name = f"{username_norm}_dt.parquet"
    
    folder = st.secrets.get("DT_FOLDER_PATH", "dt")
    
    site_id = nav.get_site_id()
    drive_id, _ = nav.get_drive_id(site_id)
    
    file_path = f"{folder}/{file_name}"
    
    try:
        file_data = nav.download_file(site_id, drive_id, file_path)
        if isinstance(file_data, dict) and 'content' in file_data:
            content = file_data['content']
        elif isinstance(file_data, (bytes, bytearray)):
            content = bytes(file_data)
        elif hasattr(file_data, "read"):
            content = file_data.read()
        else:
            return pd.DataFrame()  # File non trovato
        
        df_personale = pd.read_parquet(io.BytesIO(content))
        return df_personale
    except Exception as e:
        print(f"Errore caricamento file DT personale: {e}")
        return pd.DataFrame()


def visualizza_richieste_personali_dt(nav, df_centralizzato_dt=None):
    """Visualizza le richieste DT personali dell'utente"""
    
    col1, col2, col3 = st.columns([0.2, 1, 1])
    with col1:
        if st.button("⟳", key="refresh_richieste_personali_dt"):
            st.cache_data.clear()
            st.rerun()
    
    df_personale = carica_richieste_personali_dt(nav)
    
    if df_personale.empty:
        st.info("Nessuna richiesta trovata")
        return pd.DataFrame()
    
    # Carica il file centralizzato dt.parquet se non fornito
    if df_centralizzato_dt is None:
        try:
            folder = st.secrets.get("DT_FOLDER_PATH", "dt")
            central_filename = "dt.parquet"
            central_path = f"{folder}/{central_filename}"
            if nav.login():
                site_id = nav.get_site_id()
                drive_id, _ = nav.get_drive_id(site_id)
                if site_id and drive_id and nav.file_exists(site_id, drive_id, central_path):
                    file_data = nav.download_file(site_id, drive_id, central_path)
                    if isinstance(file_data, dict) and "content" in file_data:
                        content = file_data["content"]
                    elif isinstance(file_data, (bytes, bytearray)):
                        content = bytes(file_data)
                    elif hasattr(file_data, "read"):
                        content = file_data.read()
                    else:
                        content = None
                    if content:
                        df_centralizzato_dt = pd.read_parquet(io.BytesIO(content))
        except Exception as e:
            st.warning(f"Impossibile caricare dt.parquet centralizzato: {e}")
            df_centralizzato_dt = None
    
    try:
        df = df_personale.copy()

        if "DATA RICHIESTA" in df.columns:
            df["DATA RICHIESTA"] = pd.to_datetime(df["DATA RICHIESTA"], errors="coerce")
            df = df.dropna(subset=["DATA RICHIESTA"])
        else:
            st.warning("Colonna DATA RICHIESTA non trovata nel file personale")
            return pd.DataFrame()
        if "CF" in df.columns:
            df["CF"] = df["CF"].fillna("").astype(str).str.strip().str.upper()
        if "TIPOLOGIA DOCUMENTO" in df.columns:
            df["TIPOLOGIA DOCUMENTO"] = df["TIPOLOGIA DOCUMENTO"].fillna("").astype(str).str.strip()

        user = st.session_state.get("user", {}) or {}
        gestore_corrente = (user.get("username") or "").strip().lower()
        
        if "GESTORE" in df.columns:
            df["_gestore_lc"] = df["GESTORE"].astype(str).str.strip().str.lower()
            df_gestore = df[df["_gestore_lc"] == gestore_corrente].copy()
            df_gestore.drop(columns=["_gestore_lc"], inplace=True, errors="ignore")
        else:
            df_gestore = df.copy()
        

        from datetime import datetime, timedelta
        import pytz
        roma_tz = pytz.timezone("Europe/Rome")
        now_rome = datetime.now(roma_tz)
        oggi_rome = now_rome.date()
        lunedi = oggi_rome - timedelta(days=oggi_rome.weekday())
        venerdi = lunedi + timedelta(days=4)
        

        if not df_gestore.empty and "DATA RICHIESTA" in df_gestore.columns:
            if pd.api.types.is_datetime64_any_dtype(df_gestore["DATA RICHIESTA"]):
                df_gestore["DATA_only"] = df_gestore["DATA RICHIESTA"].dt.date
                df_settimanale = df_gestore[
                    (df_gestore["DATA_only"] >= lunedi) & 
                    (df_gestore["DATA_only"] <= venerdi)
                ].copy()
                df_settimanale.drop(columns=["DATA_only"], inplace=True, errors="ignore")
            else:
                st.error("Errore: DATA RICHIESTA non è in formato datetime")
                df_settimanale = pd.DataFrame()
        else:
            df_settimanale = pd.DataFrame()
        
        df_storico = pd.DataFrame()
        if df_centralizzato_dt is not None and not df_centralizzato_dt.empty:
            df_cent = df_centralizzato_dt.copy()
            
            if "CF" in df_cent.columns:
                df_cent["CF"] = df_cent["CF"].fillna("").astype(str).str.strip().str.upper()
            if "DATA RICHIESTA" in df_cent.columns:
                df_cent["DATA RICHIESTA"] = pd.to_datetime(df_cent["DATA RICHIESTA"], errors="coerce")
                df_cent = df_cent.dropna(subset=["DATA RICHIESTA"])
            
            if "GESTORE" in df_cent.columns:
                df_cent["_gestore_lc"] = df_cent["GESTORE"].astype(str).str.strip().str.lower()
                df_storico = df_cent[df_cent["_gestore_lc"] == gestore_corrente].copy()
                df_storico.drop(columns=["_gestore_lc"], inplace=True, errors="ignore")
            else:
                df_storico = df_cent.copy()
        if not df_settimanale.empty and "DATA RICHIESTA" in df_settimanale.columns:
            df_settimanale = df_settimanale.sort_values("DATA RICHIESTA", ascending=False)
        if not df_storico.empty and "DATA RICHIESTA" in df_storico.columns:
            df_storico = df_storico.sort_values("DATA RICHIESTA", ascending=False)

        colonne_vista_dt = ["PORTAFOGLIO",
                "NOMINATIVO POSIZIONE",
                "NDG DEBITORE",
                "NDG NOMINATIVO RICERCATO",
                "GESTORE",
                "ORIGINATOR",
                "DESTINATARIO",
                "RAPPORTO",
                "GBV ATTUALE",
                "PEC DESTINATARIO",
                "INDIRIZZO",
                "CITTA",
                "PROVINCIA",
                "CAP",
                "EMAIL GESTORE",
                "TELEFONO GESTORE",
                "MODALITA INVIO",
                "TIPOLOGIA DOCUMENTO",
                "DATA RICHIESTA",
                "id",
                "INVIATE AL PROVIDER",
                "MOTIVAZIONE"]

        # Controlla quali colonne esistono effettivamente
        colonne_sett = [c for c in colonne_vista_dt if c in df_settimanale.columns]
        colonne_stor = [c for c in colonne_vista_dt if c in df_storico.columns]
        
        # Formatta date per visualizzazione
        df_sett_vis = df_settimanale.copy()
        if not df_sett_vis.empty and "DATA RICHIESTA" in df_sett_vis.columns:
            if pd.api.types.is_datetime64_any_dtype(df_sett_vis["DATA RICHIESTA"]):
                df_sett_vis["DATA RICHIESTA"] = df_sett_vis["DATA RICHIESTA"].dt.strftime("%d/%m/%Y %H:%M")
        
        df_stor_vis = df_storico.copy()
        if not df_stor_vis.empty and "DATA RICHIESTA" in df_stor_vis.columns:
            if pd.api.types.is_datetime64_any_dtype(df_stor_vis["DATA RICHIESTA"]):
                df_stor_vis["DATA RICHIESTA"] = df_stor_vis["DATA RICHIESTA"].dt.strftime("%d/%m/%Y %H:%M")

        # Mostra richieste settimanali
        st.subheader("Richieste di questa settimana (Lun-Ven)")
        if df_sett_vis.empty:
            st.info("Nessuna richiesta DT questa settimana")
        else:
            st.dataframe(df_sett_vis[colonne_sett], use_container_width=True, height=600)
        
        # Mostra storico
        st.subheader("Storico")
        if df_stor_vis.empty:
            st.info("Storico centralizzato non disponibile o vuoto")
        else:
            st.dataframe(df_stor_vis[colonne_stor], use_container_width=True, height=800)
        
        return df_settimanale
    
    except Exception as e:
        st.error(f"Errore nella visualizzazione DT: {e}")
        import traceback
        st.code(traceback.format_exc())
        if not df_personale.empty:
            st.write("**Dati raw del file personale:**")
            st.dataframe(df_personale, use_container_width=True, hide_index=True)
        return pd.DataFrame()