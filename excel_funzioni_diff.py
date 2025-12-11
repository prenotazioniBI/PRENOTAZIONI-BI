import pandas as pd
import streamlit as st
from io import BytesIO
import requests
from urllib.parse import quote
from filtro_df import mostra_df_filtrato_home_admin_dt



def salva_richiesta_utente_dt(df_dt, servizi_scelti, navigator_dt, cf=None, portafoglio=None, ndg_debitore=None, 
                             nominativo_posizione=None, ndg_nominativo_ricercato=None,
                             nominativo_ricerca=None, rapporto=None, gbvAttuale=None,
                             indirizzo=None, numeroCivico=None, comune=None, 
                             provincia=None, sigla=None, cap=None, regione=None,
                             tipoLuogo=None, pec=None,
                             originator=None, telefono_gestore=None,
                             email_gestore=None, **kwargs):
    
    try:
        nav = navigator_dt
        user = st.session_state.get("user", {})
        gestore = user.get("username", "Sconosciuto")

        if ndg_debitore is not None:
            if isinstance(ndg_debitore, (int, float)):
                if isinstance(ndg_debitore, float) and ndg_debitore.is_integer():
                    ndg_debitore = str(int(ndg_debitore))
                else:
                    ndg_debitore = str(ndg_debitore)
            else:
                ndg_debitore = str(ndg_debitore).strip()
        else:
            ndg_debitore = ""
        
        if ndg_nominativo_ricercato is not None:
            if isinstance(ndg_nominativo_ricercato, (int, float)):
                if isinstance(ndg_nominativo_ricercato, float) and ndg_nominativo_ricercato.is_integer():
                    ndg_nominativo_ricercato = str(int(ndg_nominativo_ricercato))
                else:
                    ndg_nominativo_ricercato = str(ndg_nominativo_ricercato)
            else:
                ndg_nominativo_ricercato = str(ndg_nominativo_ricercato).strip()
        else:
            ndg_nominativo_ricercato = ""
        
        data_richiesta = pd.Timestamp.now()
        modalita_invio = "PEC" if pec else "RACCOMANDATA"
        tipologia_documento = ", ".join(servizi_scelti) if isinstance(servizi_scelti, list) else servizi_scelti
        
        is_telegramma = "Telegramma" in servizi_scelti
        
 
        
        email = user.get("email", "")
        if email:
            nome_cognome = email.split("@")[0].replace(".", "_")
            if nome_cognome.endswith("_ext"):
                nome_cognome = nome_cognome[:-4]
            nome_file = f"{nome_cognome}_dt.parquet"
        else:
            nome_file = f"{gestore.replace(' ', '_')}_dt.parquet"
        nome_file = nome_file.lower()
        
        dt_folder_path = st.secrets["DT_FOLDER_PATH"]
        file_path = f"{dt_folder_path}/{nome_file}"
        
        site_id = nav.get_site_id()
        if site_id is None:
            return df_dt, False, "Errore: impossibile ottenere site_id"
        
        drive_result = nav.get_drive_id(site_id)
        if drive_result is None or len(drive_result) != 2:
            return df_dt, False, "Errore: impossibile ottenere drive_id"
        
        drive_id, _ = drive_result
        if drive_id is None:
            return df_dt, False, "Errore: drive_id è None"
        
        df_originale = pd.DataFrame()
        encoded_path = quote(file_path)
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
        headers = {"Authorization": f"Bearer {nav.access_token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df_originale = pd.read_parquet(BytesIO(response.content))
            if not df_originale.empty and "DATA RICHIESTA" in df_originale.columns:
                df_originale["DATA RICHIESTA"] = pd.to_datetime(df_originale["DATA RICHIESTA"], errors="coerce")
        elif response.status_code != 404:
            return df_dt, False, f"Errore caricamento file: {response.status_code}"
        
        riga = {
            "id": (df_originale["id"].max() + 1) if not df_originale.empty and "id" in df_originale.columns else 1,
            "CF": cf,  
            "PORTAFOGLIO": portafoglio,
            "NOMINATIVO POSIZIONE": nominativo_posizione,
            "NDG DEBITORE": ndg_debitore,
            "NDG NOMINATIVO RICERCATO": ndg_nominativo_ricercato,
            "GESTORE": gestore,
            "ORIGINATOR": originator if not is_telegramma else None,  
            "DESTINATARIO": nominativo_ricerca,
            "RAPPORTO": rapporto if not is_telegramma else None,       
            "GBV ATTUALE": gbvAttuale if not is_telegramma else None,  
            "PEC DESTINATARIO": pec,
            "INDIRIZZO": indirizzo,
            "NUMERO CIVICO": numeroCivico,
            "CITTA": comune,
            "PROVINCIA": provincia,
            "SIGLA": sigla,
            "CAP": cap,
            "REGIONE": regione,
            "TIPO LUOGO": tipoLuogo,
            "EMAIL GESTORE": email_gestore,
            "TELEFONO GESTORE": telefono_gestore,
            "MODALITA INVIO": modalita_invio,
            "TIPOLOGIA DOCUMENTO": tipologia_documento,
            "DATA RICHIESTA": data_richiesta,
            "INVIATE AL PROVIDER": None,
            "COSTO": None
        }
        
        
        df_nuovo = pd.concat([df_originale, pd.DataFrame([riga])], ignore_index=True)
        
        if "DATA RICHIESTA" in df_nuovo.columns:
            df_nuovo["DATA RICHIESTA"] = pd.to_datetime(df_nuovo["DATA RICHIESTA"], errors="coerce")
        
        if 'NDG DEBITORE' in df_nuovo.columns:
            df_nuovo['NDG DEBITORE'] = df_nuovo['NDG DEBITORE'].astype(str)
            df_nuovo['NDG DEBITORE'] = df_nuovo['NDG DEBITORE'].str.replace(r'\.0$', '', regex=True)
        
        if 'NDG NOMINATIVO RICERCATO' in df_nuovo.columns:
            df_nuovo['NDG NOMINATIVO RICERCATO'] = df_nuovo['NDG NOMINATIVO RICERCATO'].astype(str)
            df_nuovo['NDG NOMINATIVO RICERCATO'] = df_nuovo['NDG NOMINATIVO RICERCATO'].str.replace(r'\.0$', '', regex=True)
        
        buffer_out = BytesIO()
        df_nuovo.to_parquet(buffer_out, index=False)
        buffer_out.seek(0)
        
        success = nav.upload_file_direct(site_id, drive_id, file_path, buffer_out.getvalue())
        
        if success:
            if is_telegramma:
                return df_nuovo, True, f"Richiesta Telegramma salvata per {nominativo_ricerca}"
            else:
                return df_nuovo, True, f"Richiesta salvata: Rapporto {rapporto}"
        else:
            return df_originale, False, f"Errore salvataggio per {nominativo_ricerca}"
            
    except Exception as e:
        print(f"Errore completo: {e}")
        import traceback
        traceback.print_exc()
        return df_dt, False, f"Errore durante il salvataggio: {str(e)}"
def unifica_file_utenti_dt(nav, folder_path):
    """Unifica tutti i file DT personali nel file centrale dt.parquet"""
    
    site_id = nav.get_site_id()
    drive_id, _ = nav.get_drive_id(site_id)
    
    file_path_centrale = f"{folder_path}/dt.parquet"
    
    try:
        file_data = nav.download_file(site_id, drive_id, file_path_centrale)
        if isinstance(file_data, dict) and "content" in file_data:
            content = file_data["content"]
        elif isinstance(file_data, (bytes, bytearray)):
            content = bytes(file_data)
        elif hasattr(file_data, "read"):
            content = file_data.read()
        else:
            content = None
        
        if content:
            df_centrale = pd.read_parquet(BytesIO(content))
        else:
            df_centrale = pd.DataFrame()
    except Exception as e:
        df_centrale = pd.DataFrame()
    
    try:
        if hasattr(nav, 'list_files'):
            folder_items = nav.list_files(site_id, drive_id, folder_path)
        else:
            from urllib.parse import quote
            encoded_folder = quote(folder_path)
            url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_folder}:/children"
            headers = {"Authorization": f"Bearer {nav.access_token}"}
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                folder_items = response.json().get("value", [])
            else:
                return df_centrale, 0, f"Errore lettura cartella {folder_path}: {response.status_code}"
                
    except Exception as e:
        return df_centrale, 0, f"Errore lettura cartella {folder_path}: {e}"
    
    user_files_dt = []
    for item in folder_items:
        nome_file = item.get("name", "")
        if nome_file.endswith("_dt.parquet"):
            user_files_dt.append(nome_file)
    

    
    if not user_files_dt:
        return df_centrale, 0, f"Nessun file DT personale (*_dt.parquet) trovato in {folder_path}"
    
    df_list = []
    righe_caricate_per_file = {}

    for user_file in user_files_dt:
        try:
            file_path_user = f"{folder_path}/{user_file}"
            file_data = nav.download_file(site_id, drive_id, file_path_user)
            
            if isinstance(file_data, dict) and "content" in file_data:
                content = file_data["content"]
            elif isinstance(file_data, (bytes, bytearray)):
                content = bytes(file_data)
            elif hasattr(file_data, "read"):
                content = file_data.read()
            else:
                continue
            
            df_user = pd.read_parquet(BytesIO(content))
            
            if not df_user.empty:
                righe_caricate_per_file[user_file] = len(df_user)
                df_list.append(df_user)
            else:
                print(f"DEBUG: File {user_file} - vuoto")
                
        except Exception as e:
            continue
    
    if not df_list:
        return df_centrale, 0, "Nessun dato trovato nei file DT personali"

    
    df_nuovi = pd.concat(df_list, ignore_index=True)

    # Pulizia dataframe PRIMA del controllo duplicati
    df_nuovi = pulisci_dataframe(df_nuovi)
    df_centrale = pulisci_dataframe(df_centrale)
    

    # Normalizzazione per controllo duplicati
    for df in [df_nuovi, df_centrale]:
        if not df.empty:
            if "TIPOLOGIA DOCUMENTO" in df.columns:
                df["TIPOLOGIA DOCUMENTO"] = df["TIPOLOGIA DOCUMENTO"].astype(str).str.strip().str.upper()

    # CORREZIONE: Rimozione duplicati meno aggressiva
    duplicate_cols = ["CF", "DESTINATARIO", "TIPOLOGIA DOCUMENTO"]
    duplicate_cols = [col for col in duplicate_cols if col in df_nuovi.columns and col in df_centrale.columns]
    

    
    if duplicate_cols and not df_centrale.empty:
        # Prima conta i duplicati
        df_merged = pd.merge(
            df_nuovi[duplicate_cols], 
            df_centrale[duplicate_cols], 
            on=duplicate_cols, 
            how='inner'
        )
        duplicati_trovati = len(df_merged)

        
        # Rimuovi solo duplicati ESATTI
        df_nuovi_puliti = df_nuovi.merge(
            df_centrale[duplicate_cols], 
            on=duplicate_cols, 
            how='left', 
            indicator=True
        )
        df_nuovi_puliti = df_nuovi_puliti[df_nuovi_puliti['_merge'] == 'left_only']
        df_nuovi_puliti = df_nuovi_puliti.drop('_merge', axis=1)
        
    else:
        df_nuovi_puliti = df_nuovi.copy()
    
    # Unione finale
    if df_centrale.empty:
        df_finale = df_nuovi_puliti.copy()
        righe_aggiunte = len(df_finale)
    else:
        df_finale = pd.concat([df_centrale, df_nuovi_puliti], ignore_index=True)
        righe_aggiunte = len(df_nuovi_puliti)
    
    
    # Assegnazione ID
    df_finale["id"] = range(1, len(df_finale) + 1)
    
    # Pulizia finale
    df_finale = pulisci_dataframe(df_finale)
    df_finale = df_finale.dropna(how='all')
    
    
    try:
        buffer_out = BytesIO()
        df_finale.to_parquet(buffer_out, index=False)
        buffer_out.seek(0)
        success = nav.upload_file_direct(site_id, drive_id, file_path_centrale, buffer_out.getvalue())
        
        if success:
            msg = (
                f"Unificazione DT completata: {righe_aggiunte} nuove righe aggiunte "
                f"(totale: {len(df_finale)}) da {len(user_files_dt)} file personali"
            )
            return df_finale, righe_aggiunte, msg
        else:
            return df_centrale, 0, "Errore durante l'unificazione"
            
    except Exception as e:
        print(f"Errore salvataggio parquet: {e}")
        return df_centrale, 0, f"Errore conversione parquet: {str(e)}"


def pulisci_dataframe(df):
    if df.empty:
        return df
    
    # Solo GBV ATTUALE numerico
    numeric_cols = ["GBV ATTUALE"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # NDG, NUMERO CIVICO, CAP devono rimanere stringhe
    string_cols = ["NDG DEBITORE", "NDG NOMINATIVO RICERCATO", "NUMERO CIVICO", "CAP"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].str.replace(r'\.0$', '', regex=True)
            df[col] = df[col].replace('nan', '')
    
    # Altri campi di testo
    text_cols = ["CF", "TIPOLOGIA DOCUMENTO", "DESTINATARIO", "GESTORE", 
                "PORTAFOGLIO", "NOMINATIVO POSIZIONE", "ORIGINATOR"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('nan', '')
            
    # Date
    date_cols = ["DATA RICHIESTA", "INVIATE AL PROVIDER"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    
    return df
def modifica_celle_excel_dt(df_dt, mostra_editor=True, key_suffix=""):
    if 'NDG DEBITORE' in df_dt.columns:
        df_dt['NDG DEBITORE'] = df_dt['NDG DEBITORE'].astype(str)
    
    # CORREZIONE: Usa la funzione mostra_df_filtrato_home_admin_dt
    df_filtered = mostra_df_filtrato_home_admin_dt(df_dt, key_suffix=key_suffix)
    
    if df_filtered is None or df_filtered.empty:
        st.warning("Nessun dato dopo i filtri")
        return None

    colonne = [
        "id",
        "PORTAFOGLIO",
        "NDG DEBITORE", 
        "NOMINATIVO POSIZIONE",
        "RAPPORTO",
        "NDG NOMINATIVO RICERCATO",
        "GBV ATTUALE",
        "DESTINATARIO",
        "GESTORE",
        "TELEFONO GESTORE",
        "EMAIL GESTORE", 
        "DATA RICHIESTA",
        "INVIATE AL PROVIDER",
        "TIPO LUOGO",
        "SIGLA",
        "REGIONE",
        "PEC DESTINATARIO",
        "INDIRIZZO",
        "NUMERO CIVICO",
        "CITTA",
        "CAP",
        "PROVINCIA",
        "TIPOLOGIA DOCUMENTO",
        "MODALITA INVIO",
        "ORIGINATOR"
    ]

    cols_to_show = [col for col in colonne if col in df_filtered.columns]
    df_filtered = df_filtered[cols_to_show]

    if mostra_editor:
        df_copy = df_filtered.copy().reset_index(drop=True)
        df_copy.insert(0, "ELIMINA", False)
        df_copy = df_copy.loc[:, ~df_copy.columns.duplicated()]
        
        if 'NDG DEBITORE' in df_copy.columns:
            df_copy['NDG DEBITORE'] = df_copy['NDG DEBITORE'].astype(str)
        if "INVIATE AL PROVIDER" in df_copy.columns:
            df_copy["INVIATE AL PROVIDER"] = pd.to_datetime(
                df_copy["INVIATE AL PROVIDER"], format="mixed", dayfirst=True, errors="coerce"
            )

        editor_key = f"editor_admin_dt_{key_suffix}" if key_suffix else "editor_admin_dt"
        
        edited_df = st.data_editor(
            df_copy,
            num_rows="dynamic",
            height=2000,
            use_container_width=True,
            key=editor_key,
            column_config={
                "ELIMINA": st.column_config.CheckboxColumn(
                    "ELIMINA",
                    help="Seleziona per eliminare la riga",
                    default=False,
                ),
            }
        )
        
        return edited_df
    
    return df_filtered

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