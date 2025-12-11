
import streamlit as st
import pandas as pd
import io

def carica_richieste_personali(nav):
    """Carica le richieste personali dell'utente dal suo file su SharePoint"""
    user = st.session_state.get("user", {})
    username = user.get("username", "")

    username_norm = str(username).strip().lower().replace(" ", "_")
    file_name = f"{username_norm}_prenotazioni.parquet"

    folder = getattr(nav, "folder_path", None) or st.secrets.get("FOLDER_PATH", "General/PRENOTAZIONI_BI")


    site_id = nav.get_site_id()
    drive_id, _ = nav.get_drive_id(site_id)

    file_path = f"{folder}/{file_name}"


    file_data = nav.download_file(site_id, drive_id, file_path)
    if isinstance(file_data, dict) and 'content' in file_data:
        content = file_data['content']
    elif isinstance(file_data, (bytes, bytearray)):
        content = bytes(file_data)
    elif hasattr(file_data, "read"):
        content = file_data.read()


    df_personale = pd.read_parquet(io.BytesIO(content))
    return df_personale


def visualizza_richieste_personali(nav, df_centralizzato=None):

    col1, col2, col3 = st.columns([0.2, 1, 1])
    with col1:
        if st.button("⟳", key="refresh_richieste_personali"):
            st.cache_data.clear()
            st.rerun()

    df_personale = carica_richieste_personali(nav)


    if df_centralizzato is None:
        try:
            folder = getattr(nav, "folder_path", None) or st.secrets.get("FOLDER_PATH", "General/PRENOTAZIONI_BI")
            central_filename = "prenotazioni_bi.parquet"
            central_path = f"{folder}/{central_filename}"
            if nav.login():
                site_id = nav.get_site_id()
                drive_id, _ = nav.get_drive_id(site_id)
                if site_id and drive_id and nav.file_exists(site_id, drive_id, central_path):
                    file_data = nav.download_file(site_id, drive_id, central_path)
                    import io
                    if isinstance(file_data, dict) and "content" in file_data:
                        content = file_data["content"]
                    elif isinstance(file_data, (bytes, bytearray)):
                        content = bytes(file_data)
                    elif hasattr(file_data, "read"):
                        content = file_data.read()
                    else:
                        content = None
                    if content:
                        df_centralizzato = pd.read_parquet(io.BytesIO(content))
        except Exception as e:
            st.warning(f"Impossibile caricare prenotazioni_bi.parquet: {e}")
            df_centralizzato = None

    try:

        column_mapping = {
            'utente': 'UTENTE','portafoglio': 'PORTAFOGLIO','centro_costo': 'CENTRO DI COSTO',
            'gestore': 'GESTORE','ndg_debitore': 'NDG DEBITORE','nominativo_posizione': 'NOMINATIVO POSIZIONE',
            'ndg_nominativo_ricercato': 'NDG NOMINATIVO RICERCATO','nominativo_ricerca': 'NOMINATIVO RICERCA',
            'cf': 'C.F.','nome_servizio': 'NOME SERVIZIO','provider': 'PROVIDER',
            'data_invio': 'INVIATE AL PROVIDER','costo': 'COSTO','mese': 'MESE','anno': 'ANNO',
            'n_richieste': 'N. RICHIESTE','rifatturazione': 'RIFATTURAZIONE','tot_posizioni': 'TOT POSIZIONI',
            'data_richiesta': 'DATA RICHIESTA','rifiutata': 'RIFIUTATA'
        }


        df = df_personale.copy()
        for old, new in column_mapping.items():
            if old in df.columns:
                df = df.rename(columns={old: new})


        if "C.F." in df.columns:
            df["C.F."] = df["C.F."].fillna("").astype(str).str.strip().str.upper()
        if "NOME SERVIZIO" in df.columns:
            df["NOME SERVIZIO"] = df["NOME SERVIZIO"].fillna("").astype(str).str.strip()

        if "DATA RICHIESTA" in df.columns:
            df["DATA RICHIESTA"] = pd.to_datetime(df["DATA RICHIESTA"], errors="coerce", dayfirst=True)
        else:
            df["DATA RICHIESTA"] = pd.NaT

        user = st.session_state.get("user", {}) or {}
        gestore_corrente = (user.get("username") or "").strip().lower()
        gestore_col = None
        for candidate in ["GESTORE", "UTENTE"]:
            if candidate in df.columns:
                gestore_col = candidate
                break

        if gestore_col:
            df["_gestore_lc"] = df[gestore_col].astype(str).str.strip().str.lower()
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

        if "DATA RICHIESTA" in df_gestore.columns:
            df_gestore["DATA_only"] = df_gestore["DATA RICHIESTA"].dt.date
            df_settimanale = df_gestore[(df_gestore["DATA_only"] >= lunedi) & (df_gestore["DATA_only"] <= venerdi)].copy()
            df_settimanale.drop(columns=["DATA_only"], inplace=True, errors="ignore")
        else:
            df_settimanale = df_gestore.iloc[0:0].copy()

        # prepara storico dal centralizzato se disponibile
        if df_centralizzato is not None and not df_centralizzato.empty:
            df_cent = df_centralizzato.copy()
            for old, new in column_mapping.items():
                if old in df_cent.columns:
                    df_cent = df_cent.rename(columns={old: new})
            if "C.F." in df_cent.columns:
                df_cent["C.F."] = df_cent["C.F."].fillna("").astype(str).str.strip().str.upper()
            if "DATA RICHIESTA" in df_cent.columns:
                df_cent["DATA RICHIESTA"] = pd.to_datetime(df_cent["DATA RICHIESTA"], errors="coerce", dayfirst=True)
            else:
                df_cent["DATA RICHIESTA"] = pd.NaT

            cent_gestore_col = None
            for candidate in ["GESTORE", "UTENTE"]:
                if candidate in df_cent.columns:
                    cent_gestore_col = candidate
                    break
            if cent_gestore_col:
                df_cent["_gestore_lc"] = df_cent[cent_gestore_col].astype(str).str.strip().str.lower()
                df_storico = df_cent[df_cent["_gestore_lc"] == gestore_corrente].copy()
                df_storico.drop(columns=["_gestore_lc"], inplace=True, errors="ignore")
            else:
                df_storico = df_cent.copy()
        else:
            df_storico = pd.DataFrame(columns=df.columns)  # vuoto se non c'è central


        if "DATA RICHIESTA" in df_settimanale.columns:
            df_settimanale = df_settimanale.sort_values("DATA RICHIESTA", ascending=False)
        if "DATA RICHIESTA" in df_storico.columns:
            df_storico = df_storico.sort_values("DATA RICHIESTA", ascending=False)

        # colonne e visualizzazione
        colonne_vista = [
            "DATA RICHIESTA","C.F.","NOME SERVIZIO","INVIATE AL PROVIDER",
            "PORTAFOGLIO","NDG DEBITORE","NOMINATIVO POSIZIONE","NOMINATIVO RICERCA", "COSTO"
        ]
        colonne_sett = [c for c in colonne_vista if c in df_settimanale.columns]
        colonne_stor = [c for c in colonne_vista if c in df_storico.columns]

        df_sett_vis = df_settimanale.copy()
        if "DATA RICHIESTA" in df_sett_vis.columns:
            df_sett_vis["DATA RICHIESTA"] = df_sett_vis["DATA RICHIESTA"].dt.strftime("%d/%m/%Y %H:%M")

        df_stor_vis = df_storico.copy()
        if "DATA RICHIESTA" in df_stor_vis.columns:
            df_stor_vis["DATA RICHIESTA"] = df_stor_vis["DATA RICHIESTA"].dt.strftime("%d/%m/%Y %H:%M")

        # mostra settimanale
        st.subheader("Richieste di questa settimana (Lun-Ven)")
        if df_sett_vis.empty:
            st.info("Nessuna richiesta questa settimana")
        else:
            st.dataframe(df_sett_vis[colonne_sett], use_container_width=True, height=600)

        st.subheader("Storico")
        if df_stor_vis.empty:
            st.info("Storico centralizzato non disponibile o vuoto")
        else:
            st.dataframe(df_stor_vis[colonne_stor], use_container_width=True, height=800)

        return df_settimanale

    except Exception as e:
        st.error(f"Errore nella visualizzazione: {e}")
        st.dataframe(df_personale, use_container_width=True, hide_index=True)
        return None