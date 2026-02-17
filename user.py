from datetime import datetime
from excel_funzioni_diff import salva_richiesta_utente_dt
from excel_funzioni import salva_richiesta_utente
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz


def carica_richieste_personali(nav):
    """Carica le richieste personali dell'utente dal suo file su SharePoint"""
    user = st.session_state.get("user", {})
    username = user.get("username", "")
    if not username:
        st.error("Utente non loggato o username mancante")
        return None

    # normalizza username allo stesso modo usato per salvare i file
    username_norm = str(username).strip().lower().replace(" ", "_")
    file_name = f"{username_norm}_prenotazioni.parquet"

    # recupera folder_path/site/drive
    folder = getattr(nav, "folder_path", None) or st.secrets.get("FOLDER_PATH", "General/PRENOTAZIONI_BI")
    try:
        if not nav.login():
            st.error("Errore di autenticazione SharePoint")
            return None

        site_id = nav.get_site_id()
        if not site_id:
            st.error("Impossibile recuperare site_id")
            return None

        drive_id, _ = nav.get_drive_id(site_id)
        if not drive_id:
            st.error("Impossibile recuperare drive_id")
            return None

        file_path = f"{folder}/{file_name}"
        exists = nav.file_exists(site_id, drive_id, file_path)
        if not exists:
            # file non esiste -> ritorna df vuoto con schema standard
            import pandas as pd
            df = pd.DataFrame(columns=[
                'utente', 'portafoglio', 'centro_costo', 'gestore',
                'ndg_debitore', 'nominativo_posizione', 'ndg_nominativo_ricercato',
                'nominativo_ricerca', 'cf', 'nome_servizio', 'provider',
                'data_invio', 'costo', 'mese', 'anno', 'n_richieste',
                'rifatturazione', 'tot_posizioni', 'data_richiesta', 'rifiutata'
            ])
            return df

        # scarica il file (gestendo diversi formati di ritorno)
        file_data = nav.download_file(site_id, drive_id, file_path)
        import pandas as pd, io
        if isinstance(file_data, dict) and 'content' in file_data:
            content = file_data['content']
        elif isinstance(file_data, (bytes, bytearray)):
            content = bytes(file_data)
        elif hasattr(file_data, "read"):
            content = file_data.read()
        else:
            st.error("Download restituito in formato inatteso")
            return None

        df = pd.read_parquet(io.BytesIO(content))
        return df

    except Exception as e:
        st.error(f"Errore nel caricamento delle richieste personali: {e}")
        return None
    


def carica_richieste_personali_dt(nav):
    """Carica le richieste personali dell'utente dal suo file su SharePoint"""
    user = st.session_state.get("user", {})
    username = user.get("username", "")
    if not username:
        st.error("Utente non loggato o username mancante")
        return None

    # normalizza username allo stesso modo usato per salvare i file
    username_norm = str(username).strip().lower().replace(" ", "_")
    file_name = f"{username_norm}_dt.parquet"

    # recupera folder_path/site/drive
    folder = getattr(nav, "folder_path", None) or st.secrets.get("FOLDER_PATH", "General/DIFFIDE_TELEGRAMMI")
    try:
        if not nav.login():
            st.error("Errore di autenticazione SharePoint")
            return None

        site_id = nav.get_site_id()
        if not site_id:
            st.error("Impossibile recuperare site_id")
            return None

        drive_id, _ = nav.get_drive_id(site_id)
        if not drive_id:
            st.error("Impossibile recuperare drive_id")
            return None

        file_path = f"{folder}/{file_name}"

        file_data = nav.download_file(site_id, drive_id, file_path)
        import pandas as pd, io
        if isinstance(file_data, dict) and 'content' in file_data:
            content = file_data['content']
        elif isinstance(file_data, (bytes, bytearray)):
            content = bytes(file_data)
        elif hasattr(file_data, "read"):
            content = file_data.read()
        else:
            st.error("Download restituito in formato inatteso")
            return None

        df = pd.read_parquet(io.BytesIO(content))
        return df

    except Exception as e:
        st.error(f"Errore nel caricamento delle richieste personali: {e}")
        return None
    

def menu_utente_dt(df_dt, servizi_scelti, navigator_dt):
    """Gestisce il salvataggio delle richieste DT"""
    try:
        richiesta = st.session_state.get("richiesta", {})

        def pick(*keys, default=""):
            for k in keys:
                v = richiesta.get(k, None)
                if v is None or (isinstance(v, str) and not v.strip()):
                    v = st.session_state.get(k, None)
                if v is not None and (not isinstance(v, str) or v.strip()):
                    return v.strip() if isinstance(v, str) else v
            return default

        is_telegramma = "Telegramma" in servizi_scelti
        
        if is_telegramma:
            indirizzo = pick("indirizzo_telegramma")
            comune = pick("comune_telegramma")
            provincia = pick("provincia_telegramma")
            sigla = pick("sigla_telegramma")
            cap = pick("cap_telegramma")
            regione = pick("regione_telegramma")
            tipoLuogo = pick("tipoLuogo_telegramma", "tipo_luogo_telegramma")
            pec = None
            rapporto = pick("rapporto")
            gbvAttuale = pick("gbvAttuale")
            originator = None
        else:
            indirizzo = pick("indirizzo", "indirizzo_diffida")
            comune = pick("comune", "comune_diffida")
            provincia = pick("provincia", "provincia_diffida")
            sigla = pick("sigla", "sigla_diffida")
            cap = pick("cap", "cap_diffida")
            regione = pick("regione", "regione_diffida")
            tipoLuogo = pick("tipoLuogo", "tipo_luogo_diffida")
            pec = ""
            for pec_key in ["indirizzoPostaElettronica", "pec_destinatario", "PEC DESTINATARIO", "pec_diffida"]:
                pec_value = pick(pec_key)
                if pec_value:
                    pec = pec_value
                    break
            
            rapporto = pick("rapporto")
            gbvAttuale = pick("gbvAttuale")
            originator = pick("originator")

        email_gestore = pick("email_gestore")
        telefono_gestore = pick("telefono_gestore")

        parametri = {
            "cf": richiesta.get("cf", ""),
            "portafoglio": richiesta.get("portafoglio", ""),
            "ndg_debitore": richiesta.get("ndg_debitore", ""),
            "nominativo_posizione": richiesta.get("nominativo_posizione", ""),
            "ndg_nominativo_ricercato": richiesta.get("ndg_nominativo_ricercato", ""),
            "nominativo_ricerca": richiesta.get("nominativo_ricerca", ""),
            "rapporto": rapporto,
            "gbvAttuale": gbvAttuale,
            "indirizzo": indirizzo,
            "comune": comune,
            "provincia": provincia,
            "sigla": sigla,
            "cap": cap,
            "regione": regione,
            "tipoLuogo": tipoLuogo,
            "pec": pec, 
            "originator": originator,
            "telefono_gestore": telefono_gestore,
            "email_gestore": email_gestore,
            "motivazione": richiesta.get("motivazione", "") 
        }
        
        df_result, success, msg = salva_richiesta_utente_dt(
            df_dt=df_dt,
            servizi_scelti=servizi_scelti,
            navigator_dt=navigator_dt,
            **parametri  
        )
        

        return df_result, success, msg
        
    except Exception as e:
        print(f"Errore in menu_utente_dt: {e}")
        import traceback
        traceback.print_exc()
        return df_dt, False, f"Errore durante il salvataggio: {str(e)}"


def menu_utente(df_centralizzato, servizi_scelti, nav):
    user = st.session_state.get("user")
    dati_banner = st.session_state.get("richiesta")
    
    # Carica le richieste personali dell'utente
    df_personale = carica_richieste_personali(nav)
    
    # Lavora sul DataFrame personale
    df_corrente = df_personale.copy()
    
    richieste_salvate = 0
    errore = False
    messaggi_errore = []
    messaggi_successo = []
    
    for servizio in servizi_scelti:
        df_temp, ok, msg = salva_richiesta_utente(
            user.get("username", ""),
            portafoglio=dati_banner.get("portafoglio", ""),
            centro_costo="", 
            gestore=dati_banner.get("GESTORE", user.get("username", "")),
            ndg_debitore=dati_banner.get("ndg_debitore", ""),
            nominativo_posizione=dati_banner.get("nominativo_posizione", ""),
            ndg_nominativo_ricercato=dati_banner.get("ndg_nominativo_ricercato", ""),
            nominativo_ricerca=dati_banner.get("nominativo_ricerca", ""),
            cf=dati_banner.get("cf"),
            nome_servizio=servizio,
            provider="",
            data_invio="",
            costo="",
            mese=datetime.now().month,
            anno=datetime.now().year,
            n_richieste=1,
            rifatturazione="NO",
            tot_posizioni=0,
            data_richiesta=datetime.now(pytz.timezone("Europe/Rome")).strftime("%d/%m/%Y %H:%M"),
            rifiutata="",
            nav=nav
        )
        
        if ok:
            df_corrente = df_temp
            richieste_salvate += 1
            messaggi_successo.append(msg)
            st.success(msg)
        else:
            errore = True
            messaggi_errore.append(msg)
            st.error(msg)

    if not errore and richieste_salvate > 0:
        return df_corrente, True, f"Salvate {richieste_salvate} richieste con successo"
    elif richieste_salvate > 0 and errore:
        return df_corrente, True, f"Salvate {richieste_salvate} richieste. Alcune erano duplicate."
    else:
        return df_personale, False, "Nessuna richiesta salvata - tutte erano duplicate o in errore"



def visualizza_richieste_personali(nav, df_centralizzato=None):
    """
    Visualizza le richieste personali dell'utente:
      - richieste di questa settimana (lun -> ven) dal file personale (Europe/Rome)
      - sotto: storico completo preso da prenotazioni_bi.parquet (se disponibile)
    Lo storico viene caricato ad ogni chiamata e mostrato senza bisogno di refresh.
    Ritorna il DataFrame settimanale.
    """
    col1, col2, col3 = st.columns([0.2, 1, 1])
    with col1:
        if st.button("⟳", key="refresh_richieste_personali"):
            st.cache_data.clear()
            st.rerun()

    # Carica le richieste personali
    df_personale = carica_richieste_personali(nav)
    if df_personale is None:
        st.error("Impossibile caricare le richieste personali")
        return None

    # Se vuoto, mostriamo messaggio ma proseguiamo per visualizzare comunque lo storico centralizzato
    if df_personale.empty:
        st.info("Non hai ancora effettuato richieste")

    # Carica il centralizzato (prenotazioni_bi.parquet) se non passato
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
        # mapping colonne compatibilità
        column_mapping = {
            'utente': 'UTENTE','portafoglio': 'PORTAFOGLIO','centro_costo': 'CENTRO DI COSTO',
            'gestore': 'GESTORE','ndg_debitore': 'NDG DEBITORE','nominativo_posizione': 'NOMINATIVO POSIZIONE',
            'ndg_nominativo_ricercato': 'NDG NOMINATIVO RICERCATO','nominativo_ricerca': 'NOMINATIVO RICERCA',
            'cf': 'C.F.','nome_servizio': 'NOME SERVIZIO','provider': 'PROVIDER',
            'data_invio': 'INVIATE AL PROVIDER','costo': 'COSTO','mese': 'MESE','anno': 'ANNO',
            'n_richieste': 'N. RICHIESTE','rifatturazione': 'RIFATTURAZIONE','tot_posizioni': 'TOT POSIZIONI',
            'data_richiesta': 'DATA RICHIESTA'
        }

        # prepara df personale
        df = df_personale.copy()
        for old, new in column_mapping.items():
            if old in df.columns:
                df = df.rename(columns={old: new})

        # pulizie minime su personale
        if "C.F." in df.columns:
            df["C.F."] = df["C.F."].fillna("").astype(str).str.strip().str.upper()
        if "NOME SERVIZIO" in df.columns:
            df["NOME SERVIZIO"] = df["NOME SERVIZIO"].fillna("").astype(str).str.strip()

        # DATA RICHIESTA -> datetime
        if "DATA RICHIESTA" in df.columns:
            df["DATA RICHIESTA"] = pd.to_datetime(df["DATA RICHIESTA"], errors="coerce", dayfirst=True)
        else:
            df["DATA RICHIESTA"] = pd.NaT

        # filtro per gestore loggato
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

        # calcola intervallo settimana corrente in Europe/Rome
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

        # ordina settimanale e storico
        if "DATA RICHIESTA" in df_settimanale.columns:
            df_settimanale = df_settimanale.sort_values("DATA RICHIESTA", ascending=False)
        if "DATA RICHIESTA" in df_storico.columns:
            df_storico = df_storico.sort_values("DATA RICHIESTA", ascending=False)

        # colonne e visualizzazione
        colonne_vista = [
            "DATA RICHIESTA","C.F.","NOME SERVIZIO","INVIATE AL PROVIDER",
            "PORTAFOGLIO","NDG DEBITORE","NOMINATIVO POSIZIONE","NOMINATIVO RICERCA"
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

        # mostra storico (sempre, se presente) senza bisogno di refresh
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
