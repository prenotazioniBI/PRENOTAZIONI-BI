import pandas as pd
import streamlit as st
from filtro_df import mostra_df_filtrato_home_admin
from io import BytesIO
import os

TENANT_ID = st.secrets["TENANT_ID"] 
CLIENT_ID = st.secrets["CLIENT_ID"] 
CLIENT_SECRET = st.secrets["CLIENT_SECRET"] 


def crea_file_utente_se_non_esiste(username, nav, folder_path):
    """Crea file parquet personale per l'utente se non esiste"""
    filename = f"{username.lower().replace(' ', '_')}_prenotazioni.parquet"
    file_path = f"{folder_path}/{filename}"
    
    site_id = nav.get_site_id()
    drive_id, _ = nav.get_drive_id(site_id)
    
    # Verifica se esiste
    if not nav.file_exists(site_id, drive_id, file_path):
        print(f"📝 Creazione file personale per {username}")
        
        # Crea DataFrame vuoto con tutte le colonne
        colonne = [
            "PORTAFOGLIO", "CENTRO DI COSTO", "GESTORE", "NDG DEBITORE", 
            "NOMINATIVO POSIZIONE", "NDG NOMINATIVO RICERCATO", "C.F.", 
            "SERVIZIO RICHIESTO", "NOME SERVIZIO", "PROVIDER",
            "INVIATE AL PROVIDER", "COSTO", "MESE", "ANNO", "N. RICHIESTE",
            "RIFATTURAZIONE", "TOT POSIZIONI", "DATA RICHIESTA", "NOMINATIVO RICERCA", "id"
        ]
        
        df_vuoto = pd.DataFrame(columns=colonne)
        
        # Converti in parquet
        buffer = BytesIO()
        df_vuoto.to_parquet(buffer, index=False)
        buffer.seek(0)
        
        # Upload su SharePoint
        success = nav.upload_file_direct(site_id, drive_id, file_path, buffer.getvalue())
        
        if success:
            print(f"File {filename} creato con successo")
            return True
        else:
            print(f"Errore creazione file {filename}")
            return False
    else:
        print(f"✓ File personale già esistente per {username}")
        return True


def salva_richiesta_utente(
    username,
    portafoglio,
    centro_costo,
    gestore,
    ndg_debitore,
    nominativo_posizione,
    ndg_nominativo_ricercato,
    nominativo_ricerca,
    cf,
    nome_servizio,
    provider,
    data_invio,
    costo,
    mese,
    anno,
    n_richieste,
    rifatturazione,
    tot_posizioni,
    data_richiesta, 
    rifiutata,
    nav
):
    """Salva richiesta nel file personale dell'utente dopo aver controllato duplicati nel file centrale"""
    from io import BytesIO
    import pandas as pd
    from datetime import datetime, timedelta
    from urllib.parse import quote
    import requests
    
    folder_path = st.secrets["FOLDER_PATH"]
    site_id = nav.get_site_id()
    drive_id, _ = nav.get_drive_id(site_id)
    
    # STEP 1: CONTROLLA DUPLICATI NEL FILE CENTRALE (prenotazioni.parquet)
    file_centrale = f"{folder_path}/prenotazioni.parquet"
    
    try:
        encoded_path = quote(file_centrale)
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
        headers = {"Authorization": f"Bearer {nav.access_token}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df_centrale = pd.read_parquet(BytesIO(response.content))
            print(f"✓ File centrale caricato per controllo: {len(df_centrale)} righe")
            
            # Converti data_richiesta in datetime
            if isinstance(data_richiesta, str):
                data_richiesta_dt = pd.to_datetime(data_richiesta, errors="coerce", dayfirst=True)
            else:
                data_richiesta_dt = pd.to_datetime(data_richiesta, errors="coerce")
            
            # Converti colonna DATA RICHIESTA in datetime
            df_centrale["DATA RICHIESTA"] = pd.to_datetime(df_centrale["DATA RICHIESTA"], errors="coerce", dayfirst=True)
            
            # Filtra richieste con stesso CF e stesso servizio
            richieste_simili = df_centrale[
                (df_centrale["C.F."] == cf) & 
                (df_centrale["NOME SERVIZIO"] == nome_servizio)
            ].copy()
            
            if not richieste_simili.empty:
                # Calcola differenza in giorni
                richieste_simili["giorni_fa"] = (data_richiesta_dt - richieste_simili["DATA RICHIESTA"]).dt.days
                
                # Filtra solo quelle degli ultimi 365 giorni
                richieste_recenti = richieste_simili[
                    (richieste_simili["giorni_fa"] >= 0) & 
                    (richieste_simili["giorni_fa"] <= 365)
                ]
                
                if not richieste_recenti.empty:
                    # Prendi la più recente
                    richiesta_precedente = richieste_recenti.sort_values("DATA RICHIESTA", ascending=False).iloc[0]
                    
                    giorni_fa = int(richiesta_precedente["giorni_fa"])
                    data_precedente = richiesta_precedente["DATA RICHIESTA"].strftime("%d/%m/%Y")
                    gestore_precedente = richiesta_precedente["GESTORE"]
                    
                    # Formatta messaggio
                    if giorni_fa == 0:
                        tempo_msg = "oggi"
                    elif giorni_fa == 1:
                        tempo_msg = "1 giorno fa"
                    elif giorni_fa < 30:
                        tempo_msg = f"{giorni_fa} giorni fa"
                    elif giorni_fa < 365:
                        mesi = giorni_fa // 30
                        tempo_msg = f"{mesi} {'mese' if mesi == 1 else 'mesi'} fa ({giorni_fa} giorni)"
                    else:
                        tempo_msg = f"{giorni_fa} giorni fa"
                    
                    msg_errore = (
                        f"RICHIESTA DUPLICATA\n"
                        f"Servizio '{nome_servizio}' per CF {cf} già richiesto:\n"
                        f"📅 Data: {data_precedente} ({tempo_msg})\n"
                        f"👤 Gestore: {gestore_precedente}\n"
                        f"⏳ Puoi richiederlo nuovamente tra {365 - giorni_fa} giorni"
                    )
                    
                    return pd.DataFrame(), False, msg_errore
        else:
            print(f"File centrale non trovato, procedo senza controllo duplicati")
            
    except Exception as e:
        print(f"Errore controllo duplicati: {e}")
    
    # STEP 2: SE NON CI SONO DUPLICATI, SALVA NEL FILE PERSONALE
    filename = f"{gestore.lower().replace(' ', '_')}_prenotazioni.parquet"
    file_path = f"{folder_path}/{filename}"
    
    # Assicurati che il file personale esista
    crea_file_utente_se_non_esiste(gestore, nav, folder_path)
    
    # Carica file personale
    try:
        encoded_path = quote(file_path)
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
        headers = {"Authorization": f"Bearer {nav.access_token}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df_personale = pd.read_parquet(BytesIO(response.content))
            print(f"✓ File personale caricato: {len(df_personale)} righe")
        else:
            raise Exception(f"File non trovato")
    except Exception as e:
        print(f"Creo nuovo file personale: {e}")
        df_personale = pd.DataFrame(columns=[
            "PORTAFOGLIO", "CENTRO DI COSTO", "GESTORE", "NDG DEBITORE", 
            "NOMINATIVO POSIZIONE", "NDG NOMINATIVO RICERCATO", "NOMINATIVO RICERCA",
            "C.F.", "NOME SERVIZIO", "PROVIDER", "INVIATE AL PROVIDER", "COSTO", 
            "MESE", "ANNO", "N. RICHIESTE", "RIFATTURAZIONE", "TOT POSIZIONI", 
            "DATA RICHIESTA", "SERVIZIO RICHIESTO", "id"
        ])
    # Crea nuova riga
    riga = {
        "PORTAFOGLIO": portafoglio,
        "CENTRO DI COSTO": centro_costo,
        "GESTORE": gestore,
        "NDG DEBITORE": ndg_debitore,
        "NOMINATIVO POSIZIONE": nominativo_posizione,
        "NDG NOMINATIVO RICERCATO": ndg_nominativo_ricercato,
        "NOMINATIVO RICERCA": nominativo_ricerca,
        "C.F.": cf,
        "NOME SERVIZIO": nome_servizio,
        "PROVIDER": provider,
        "INVIATE AL PROVIDER": pd.to_datetime(data_invio, errors="coerce", dayfirst=True) if data_invio else pd.NaT,
        "COSTO": costo,
        "MESE": mese,
        "ANNO": anno,
        "N. RICHIESTE": n_richieste,
        "RIFATTURAZIONE": rifatturazione,
        "TOT POSIZIONI": tot_posizioni,
        "DATA RICHIESTA": data_richiesta,
        "SERVIZIO RICHIESTO": "Richiesta singola gestore"
    }
    
    # Genera ID progressivo solo per questo file utente
    riga["id"] = df_personale["id"].max() + 1 if not df_personale.empty and "id" in df_personale.columns else 1
    
    # Aggiungi al DataFrame personale
    df_completo = pd.concat([df_personale, pd.DataFrame([riga])], ignore_index=True)
    
    # Conversioni tipo
    df_completo["COSTO"] = pd.to_numeric(df_completo["COSTO"], errors="coerce")
    df_completo["DATA RICHIESTA"] = pd.to_datetime(df_completo["DATA RICHIESTA"], errors="coerce", dayfirst=True)
    
    # Salva su SharePoint
    buffer_out = BytesIO()
    df_completo.to_parquet(buffer_out, index=False)
    buffer_out.seek(0)
    
    success = nav.upload_file_direct(site_id, drive_id, file_path, buffer_out.getvalue())
    
    if success:
        return df_completo, True, f"Richiesta salvata: {nome_servizio}"
    else:
        return df_personale, False, f"Errore salvataggio: {nome_servizio}"

def unifica_file_utenti(nav, folder_path):
    """
    Unifica tutti i file *_prenotazioni.parquet in un unico file 'prenotazioni.parquet'.
    Mantiene lo storico e aggiunge solo le nuove righe che:
      - NON sono già presenti nello stesso file (deduplicazione interna)
      - NON sono duplicate rispetto al file centrale (stesso CF + servizio entro 1 anno o stessa data)
    """
    import pandas as pd
    from datetime import datetime
    from io import BytesIO

    site_id = nav.get_site_id()
    drive_id, _ = nav.get_drive_id(site_id)

    # 📁 File centrale (storico)
    file_path_centrale = f"{folder_path}/prenotazioni.parquet"

    try:
        file_data = nav.download_file(site_id, drive_id, file_path_centrale)
        df_centrale = pd.read_parquet(BytesIO(file_data["content"]))
        print(f"📂 File centrale caricato: {len(df_centrale)} righe")
    except Exception as e:
        print(f"⚠️ File centrale non trovato, creo nuovo: {e}")
        df_centrale = pd.DataFrame()

    # 📋 Lista file utente
    user_files = nav.list_user_files(site_id, drive_id)
    print(f"📋 Trovati {len(user_files)} file utente")

    df_list = []

    for user_file in user_files:
        try:
            file_path_user = f"{folder_path}/{user_file}"
            file_data = nav.download_file(site_id, drive_id, file_path_user)
            df_user = pd.read_parquet(BytesIO(file_data["content"]))

            if not df_user.empty:
                print(f"  ✓ {user_file}: {len(df_user)} righe")
                df_list.append(df_user)
            else:
                print(f"  ⊘ {user_file}: vuoto")
        except Exception as e:
            print(f"  ✗ Errore lettura {user_file}: {e}")

    if not df_list:
        return df_centrale, 0, "Nessun file utente da unificare"

    # 🔄 Unisci tutti i DataFrame utente
    df_nuovi = pd.concat(df_list, ignore_index=True)
    print(f"\n📊 Totale righe dai file utente: {len(df_nuovi)}")

    # --- 🧹 Normalizzazione dati ---
    for df in [df_nuovi, df_centrale]:
        if not df.empty:
            for col in ["C.F.", "NOME SERVIZIO"]:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip().str.lower()

    # 🕓 Conversione date
    for df in [df_nuovi, df_centrale]:
        if not df.empty and "DATA RICHIESTA" in df.columns:
            df["DATA RICHIESTA"] = pd.to_datetime(
                df["DATA RICHIESTA"], errors="coerce", dayfirst=True
            )

    # --- 1️⃣ Rimuovi duplicati interni (stesso CF + servizio + data) ---
    df_nuovi = df_nuovi.drop_duplicates(
        subset=["C.F.", "NOME SERVIZIO", "DATA RICHIESTA"],
        keep="first",
    )

    # Se il centrale è vuoto → usa tutti i nuovi dati
    if df_centrale.empty:
        df_finale = df_nuovi.copy()
        df_finale["id"] = range(1, len(df_finale) + 1)
        righe_aggiunte = len(df_finale)
        righe_duplicate = 0
    else:
        # --- 2️⃣ Confronta con centrale per duplicati entro 1 anno ---
        righe_da_aggiungere = []
        righe_duplicate = 0

        for idx, riga_nuova in df_nuovi.iterrows():
            cf_nuovo = riga_nuova["C.F."]
            servizio_nuovo = riga_nuova["NOME SERVIZIO"]
            data_nuovo = riga_nuova["DATA RICHIESTA"]

            if pd.isna(data_nuovo):
                # Se la data è mancante, considerala nuova ma loggala
                print(f"⚠️ Riga senza DATA RICHIESTA: {cf_nuovo}, {servizio_nuovo}")
                righe_da_aggiungere.append(riga_nuova)
                continue

            richieste_simili = df_centrale[
                (df_centrale["C.F."] == cf_nuovo)
                & (df_centrale["NOME SERVIZIO"] == servizio_nuovo)
            ].copy()

            e_duplicato = False

            if not richieste_simili.empty:
                richieste_simili["giorni_diff"] = (
                    data_nuovo - richieste_simili["DATA RICHIESTA"]
                ).dt.days

                # Duplice condizione: stessa data oppure entro 365 giorni
                duplicati_recenti = richieste_simili[
                    (richieste_simili["giorni_diff"].abs() <= 365)
                ]
                duplicato_stesso_giorno = richieste_simili[
                    richieste_simili["DATA RICHIESTA"] == data_nuovo
                ]

                if not duplicati_recenti.empty or not duplicato_stesso_giorno.empty:
                    e_duplicato = True
                    righe_duplicate += 1
                    print(
                        f"⚠️ Duplicato ignorato: CF={cf_nuovo}, "
                        f"SERVIZIO={servizio_nuovo}, DATA={data_nuovo.date()}"
                    )

            if not e_duplicato:
                righe_da_aggiungere.append(riga_nuova)

        print(f"✨ Righe nuove da aggiungere: {len(righe_da_aggiungere)}")
        print(f"Righe duplicate ignorate: {righe_duplicate}")

        if righe_da_aggiungere:
            df_da_aggiungere = pd.DataFrame(righe_da_aggiungere)
            df_finale = pd.concat([df_centrale, df_da_aggiungere], ignore_index=True)
            righe_aggiunte = len(df_da_aggiungere)
        else:
            df_finale = df_centrale.copy()
            righe_aggiunte = 0

        # Rigenera ID progressivi
        df_finale["id"] = range(1, len(df_finale) + 1)

    # --- 🔢 Conversioni di tipo ---
    for col in ["N. RICHIESTE", "TOT POSIZIONI", "MESE", "ANNO"]:
        if col in df_finale.columns:
            df_finale[col] = df_finale[col].astype(str)

    if "COSTO" in df_finale.columns:
        df_finale["COSTO"] = pd.to_numeric(df_finale["COSTO"], errors="coerce")
    if "C.F." in df_finale.columns:
        df_finale["C.F."] = df_finale["C.F."].astype(str).str.upper()
    for col in ["DATA RICHIESTA", "INVIATE AL PROVIDER"]:
        if col in df_finale.columns:
            df_finale[col] = pd.to_datetime(df_finale[col], errors="coerce", dayfirst=True)

    if "NOME SERVIZIO" in df_finale.columns:
        df_finale["NOME SERVIZIO"] = df_finale["NOME SERVIZIO"].astype(str).str.strip().str.upper()
    
    chiavi = ["C.F.", "NOME SERVIZIO", "DATA RICHIESTA"]
    df_finale = df_finale.drop_duplicates(subset=chiavi, keep="last").reset_index(drop=True)

    
    buffer_out = BytesIO()
    df_finale.to_parquet(buffer_out, index=False)
    buffer_out.seek(0)
    success = nav.upload_file_direct(site_id, drive_id, file_path_centrale, buffer_out.getvalue())

    if success:
        msg = (
            f"✅ Unificazione completata: {righe_aggiunte} nuove righe aggiunte "
            f"(totale: {len(df_finale)})"
        )
        if righe_duplicate > 0:
            msg += f"\n⚠️ {righe_duplicate} duplicati ignorati"
        return df_finale, righe_aggiunte, msg
    else:
        return df_centrale, 0, "❌ Errore durante l'unificazione"


def visualizza_richieste_per_gestore(df, username):
    df_gestore = df.copy()
    richieste_utente = df_gestore[df_gestore["GESTORE"] == username]
    colonne_da_mostrare = [
        "DATA RICHIESTA",
        "C.F.",
        "NOME SERVIZIO",
        "INVIATE AL PROVIDER",
        "PORTAFOGLIO",
        "NDG DEBITORE",
        "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO",
        "NOMINATIVO RICERCA"
    ]
    
    colonne_presenti = [col for col in colonne_da_mostrare if col in richieste_utente.columns]
    richieste_utente = richieste_utente.sort_values("DATA RICHIESTA", ascending=False)
    richieste_utente[colonne_da_mostrare] = richieste_utente[colonne_da_mostrare].fillna("   -    ")
    return richieste_utente[colonne_presenti]


def visualizza_richieste_per_stato_invio_provider(df):
    df = df[df["INVIATE AL PROVIDER"].isnull()]
    colonne_principali = [
        "GESTORE",
        "C.F.",
        "DATA RICHIESTA",
        "NOME SERVIZIO",
        "PORTAFOGLIO",
        "NDG DEBITORE",
        "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO",
        "NOMINATIVO RICERCA",
        "INVIATE AL PROVIDER"
    ]

    df = df[colonne_principali] 
    df["DATA RICHIESTA"] = pd.to_datetime(df["DATA RICHIESTA"], errors="coerce", dayfirst=False)
    ordino_per_stato = df.sort_values("DATA RICHIESTA", ascending=False)
    return ordino_per_stato


def visualizza_richieste_Evase(df):
    df = df.copy()
    df = df[df["INVIATE AL PROVIDER"].notnull()]
    colonne_principali = [
        "GESTORE",
        "C.F.",
        "DATA RICHIESTA",
        "INVIATE AL PROVIDER",
        "COSTO",
        "NOME SERVIZIO",
        "PORTAFOGLIO",
        "NDG DEBITORE",
        "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO",
        "NOMINATIVO RICERCA"
    ]
    df = df[colonne_principali] 
    ordino_per_stato = df.sort_values("DATA RICHIESTA", ascending=False)
    return ordino_per_stato


def modifica_celle_excel(df, mostra_editor=True):
    df_filtered = mostra_df_filtrato_home_admin(st.session_state['df_full'])
    if df_filtered is None or df_filtered.empty:
        st.warning("Nessun dato disponibile dopo l'applicazione dei filtri.")
        return None

    colonne = ["C.F.", "DATA RICHIESTA", "GESTORE", "COSTO", "INVIATE AL PROVIDER", "PORTAFOGLIO",
               "CENTRO DI COSTO", "NDG DEBITORE", "NOMINATIVO POSIZIONE", 
               "NDG NOMINATIVO RICERCATO", "NOMINATIVO RICERCA", "SERVIZIO RICHIESTO",
               "NOME SERVIZIO", "PROVIDER", "RIFATTURAZIONE"]

    cols_to_show = [col for col in colonne if col in df_filtered.columns]
    if 'id' in df_filtered.columns and 'id' not in cols_to_show:
        cols_to_show.append('id')

    df_filtered = df_filtered[cols_to_show]

    if mostra_editor:
        df_copy = df_filtered.copy().reset_index(drop=True)
        df_copy = df_copy.loc[:, ~df_copy.columns.duplicated()]
        if 'NDG DEBITORE' in df_copy.columns:
            df_copy['NDG DEBITORE'] = df_copy['NDG DEBITORE'].astype(str)
        if 'C.F.' in df_copy.columns:
            df_copy['C.F.'] = df_copy['C.F.'].astype(str)
        if 'NDG NOMINATIVO RICERCATO' in df_copy.columns:
            df_copy['NDG NOMINATIVO RICERCATO'] = df_copy['NDG NOMINATIVO RICERCATO'].fillna('').astype(str)
        if 'COSTO' in df_copy.columns:
            df_copy["COSTO"] = pd.to_numeric(df_copy["COSTO"].replace('', 0), errors="coerce")
        df_copy["INVIATE AL PROVIDER"] = pd.to_datetime(df_copy["INVIATE AL PROVIDER"], format="mixed", dayfirst=True, errors="coerce")        
        edited_df = st.data_editor(
            df_copy,
            num_rows="dynamic",
            height=2000,
            use_container_width=True,
            key="editor_admin",
            column_config={
                "PROVIDER": st.column_config.SelectboxColumn(
                    "PROVIDER", options=["AZ", "Abbrevia", "CreditVision", "BD", "Europa"], required=False),
                "NOMINATIVO RICERCA": st.column_config.TextColumn("NOMINATIVO RICERCA", required=False), 
                "NDG NOMINATIVO RICERCATO": st.column_config.TextColumn("NDG NOMINATIVO RICERCATO", required=False),
                "NOMINATIVO POSIZIONE": st.column_config.TextColumn("NOMINATIVO POSIZIONE", required=False), 
                "NDG DEBITORE": st.column_config.TextColumn("NDG DEBITORE", required=False),
                "RIFATTURAZIONE": st.column_config.SelectboxColumn("RIFATTURAZIONE", options=["", "SI", "NO"], required=False),
                "INVIATE AL PROVIDER": st.column_config.DateColumn("INVIATE AL PROVIDER", format="DD.MM.YYYY", required=False),
                "CENTRO DI COSTO": st.column_config.SelectboxColumn("CENTRO DI COSTO", options=["ACERO SPV", "CLESSIDRA", "CF PLUS", "FBS"], required=False), 
                "COSTO": st.column_config.NumberColumn("COSTO", required=False, format="%.2f"),
                "PORTAFOGLIO": st.column_config.SelectboxColumn("PORTAFOGLIO", options=[
                    "", "Lotto Acero 1", "Lotto Banca di Imola 2", "Lotto Banca Imola", 
                    "Lotto Banca Pop Valconca", "Lotto Banca Pop Valconca - Acquisto", 
                    "Lotto Banco di Lucca", "Lotto BAPS 1", "Lotto BAPS 2", "Lotto BAPS 3",
                    "Lotto BAPS 4", "Lotto Benetton 1", "Lotto Blu Banca", "Lotto BP Lazio", 
                    "Lotto BPER 1", "Lotto BPER 2", "Lotto BPER 3", "Lotto BPER 4", 
                    "Lotto CF Plus", "Lotto Clessidra", "Lotto Climb 3", "Lotto ex Bramito", 
                    "Lotto Giamarca", "Lotto Giasone", "Lotto Girasole", "Lotto IRFIS",
                    "Lotto La Cassa di Ravenna", "Lotto Libra", "Lotto Platinum", 
                    "Lotto Pop Npl 2018", "Lotto Pop Npl 2018 2", "Lotto Pop Npl 2018 3",
                    "Lotto Ragusa", "Lotto Ragusa 2", "Lotto Ragusa 3", "Lotto Ragusa 4", 
                    "Lotto UnipolRec 1"], required=False)
            }
        )
        
            
        return edited_df
    
    return df_filtered


def visualizza_richieste_TeamLeader(df):
    df = df.copy()
    colonne_principali = [
        "GESTORE",
        "C.F.",
        "SERVIZIO RICHIESTO",
        "DATA RICHIESTA",
        "INVIATE AL PROVIDER",
        "COSTO",
        "NOME SERVIZIO",
        "PORTAFOGLIO",
        "NDG DEBITORE",
        "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO",
        "NOMINATIVO RICERCA"
    ]
    df = df[colonne_principali] 
    ordino_per_stato = df.sort_values("DATA RICHIESTA", ascending=False)
    return ordino_per_stato