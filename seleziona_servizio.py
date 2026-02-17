import streamlit as st
import time
import pandas as pd
from io import BytesIO
import requests
from urllib.parse import quote


def controlla_duplicati_cf(cf_richiesta, servizi_scelti, navigator_dt):
    """
    Controlla se esiste già una richiesta per lo stesso CF con gli stessi servizi,
    anche da altri gestori (diversi portafogli)
    """
    try:
        nav = navigator_dt
        
        # Carica il file centralizzato DT
        dt_folder_path = st.secrets["DT_FOLDER_PATH"]
        file_centrale = f"{dt_folder_path}/dt.parquet"
        
        site_id = nav.get_site_id()
        drive_id, _ = nav.get_drive_id(site_id)
        
        # Scarica il file centrale
        encoded_path = quote(file_centrale)
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
        headers = {"Authorization": f"Bearer {nav.access_token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df_centrale = pd.read_parquet(BytesIO(response.content))
            
            # Converti DATA RICHIESTA in datetime
            df_centrale["DATA RICHIESTA"] = pd.to_datetime(
                df_centrale["DATA RICHIESTA"], errors="coerce", dayfirst=True
            )
            
            # Normalizza CF
            df_centrale["CF"] = df_centrale["CF"].astype(str).str.strip().str.upper()
            cf_richiesta_upper = str(cf_richiesta).strip().upper()
            
            # Filtra per CF
            richieste_cf = df_centrale[df_centrale["CF"] == cf_richiesta_upper].copy()
            
            if not richieste_cf.empty:
                # Controlla se ci sono Diffida o Welcome Letter per questo CF
                servizi_da_controllare = ["DIFFIDA", "WELCOME LETTER"]
                
                for servizio in servizi_scelti:
                    if servizio in ["Diffida", "Welcome Letter"]:
                        # Cerca nel file centrale
                        richieste_simili = richieste_cf[
                            richieste_cf["TIPOLOGIA DOCUMENTO"].str.contains(
                                servizio.upper(), case=False, na=False
                            )
                        ].copy()
                        
                        if not richieste_simili.empty:
                            # Calcola giorni dalla richiesta più recente
                            from datetime import datetime
                            import pytz
                            
                            roma_tz = pytz.timezone("Europe/Rome")
                            oggi = datetime.now(roma_tz).date()
                            
                            richieste_simili["giorni_fa"] = richieste_simili["DATA RICHIESTA"].apply(
                                lambda x: (oggi - x.date()).days if pd.notna(x) else None
                            )
                            
                            # Filtra solo richieste degli ultimi 365 giorni
                            richieste_recenti = richieste_simili[
                                (richieste_simili["giorni_fa"] >= 0) & 
                                (richieste_simili["giorni_fa"] <= 365)
                            ]
                            
                            if not richieste_recenti.empty:
                                # Prendi la più recente
                                richiesta_precedente = richieste_recenti.sort_values(
                                    "DATA RICHIESTA", ascending=False
                                ).iloc[0]
                                
                                giorni_fa = int(richiesta_precedente["giorni_fa"])
                                data_precedente = richiesta_precedente["DATA RICHIESTA"].strftime("%d/%m/%Y")
                                gestore_precedente = richiesta_precedente.get("GESTORE", "Sconosciuto")
                                portafoglio_precedente = richiesta_precedente.get("PORTAFOGLIO", "Sconosciuto")
                                modalita_invio = richiesta_precedente.get("MODALITA INVIO", "Non specificata")
                                
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
                                    f"⚠️ ATTENZIONE - RICHIESTA DUPLICATA\n\n"
                                    f"Il servizio '{servizio}' per il CF **{cf_richiesta_upper}** è già stato richiesto:\n\n"
                                    f" **Data:** {data_precedente} ({tempo_msg})\n"
                                    f" **Gestore:** {gestore_precedente}\n"
                                    f" **Portafoglio:** {portafoglio_precedente}\n"
                                    f" **Modalità invio:** {modalita_invio}\n\n"
                                    f" Puoi richiederlo nuovamente tra **{365 - giorni_fa} giorni**"
                                )
                                
                                st.error(msg_errore)
                                return False
        
        elif response.status_code != 404:
            st.warning(f"Errore durante il controllo duplicati: {response.status_code}")
      
        return True
        
    except Exception as e:
        print(f"Errore controllo duplicati CF: {e}")
        st.warning(f"Impossibile verificare duplicati: {e}")
        return True



def seleziona_servizio(dt_soggetti, df_dt, navigator_dt, menu_utente_dt):
    richieste = [
        "Diffida",
        "Welcome Letter",
        "Telegramma"
    ]
    st.markdown("TIPOLOGIA RICHIESTA:")
    servizi_scelti = st.multiselect(
        " ",
        richieste,
        key="servizi_scelti"
    )

    if servizi_scelti:
        if "Telegramma" in servizi_scelti and len(servizi_scelti) > 1:
            st.error("ATTENZIONE: Telegramma NON può essere richiesto insieme ad altri servizi!")
            st.info("Rimuovi Telegramma per continuare con Diffida/Welcome Letter, oppure seleziona solo Telegramma.")
            return []  
        
        if "Telegramma" in servizi_scelti and any(serv in ["Diffida", "Welcome Letter"] for serv in servizi_scelti):
            st.error("Telegramma è incompatibile con Diffida e Welcome Letter")
            return []

    if servizi_scelti:
        st.divider()
        st.subheader("Dettagli aggiuntivi richiesti")

        cf_richiesta = st.session_state["richiesta"]["cf"]
        soggetti_completi = dt_soggetti[dt_soggetti["codiceFiscale"].astype(str).str.upper() == cf_richiesta.upper()]
        
        if not soggetti_completi.empty:
            soggetto_completo = soggetti_completi.iloc[0]
            
            user = st.session_state.get("user", {})
            email_gestore_default = user.get("email", "") 
            nome_gestore = user.get("nome", user.get("username", ""))

            # DIFFIDA e WELCOME LETTER: Possono scegliere PEC o RACCOMANDATA
            if any(servizio in ["Diffida", "Welcome Letter"] for servizio in servizi_scelti):
                st.markdown("**Tipo di invio per Diffida/Welcome Letter:**")
                
                tipo_invio = st.selectbox(
                    "Seleziona modalità di invio:",
                    ["PEC", "RACCOMANDATA"],
                    key="tipo_invio_diffida"
                )
                
                st.divider()
                
                if tipo_invio == "PEC":
                    st.markdown("**Dati PEC Destinatario:**")
                    pec_raw = soggetto_completo.get('indirizzoPostaElettronica', '')
                    if pd.isna(pec_raw) or pec_raw is None or str(pec_raw).lower() in ['none', 'null', 'nan']:
                        pec_default = ""
                    else:
                        pec_default = str(pec_raw).strip()
                    pec_mod = st.text_input("PEC Destinatario *", 
                        value=pec_default,
                        key="pec_diffida",
                        help="Indirizzo PEC del destinatario")
                

                elif tipo_invio == "RACCOMANDATA":
                    st.markdown("**Dati indirizzo per invio postale:**")
                    
                    col1, col2 = st.columns(2)

                    with col1:
                        indirizzo_raw = soggetto_completo.get('indirizzo', '')
                        indirizzo_value = "" if pd.isna(indirizzo_raw) or indirizzo_raw is None else str(indirizzo_raw)
                        
                        comune_raw = soggetto_completo.get('comune', '')
                        comune_value = "" if pd.isna(comune_raw) or comune_raw is None else str(comune_raw)
                        
                        provincia_raw = soggetto_completo.get('provincia', '')
                        provincia_value = "" if pd.isna(provincia_raw) or provincia_raw is None else str(provincia_raw)
                        
                        indirizzo_mod = st.text_input("Indirizzo (via e numero civico) *", 
                            value=indirizzo_value, 
                            key="indirizzo_diffida",
                            help="Inserisci via e numero civico insieme (es: Via Roma 10)")
                        comune_mod = st.text_input("Comune *", 
                            value=comune_value, 
                            key="comune_diffida")
                        provincia_mod = st.text_input("Provincia", 
                            value=provincia_value, 
                            key="provincia_diffida")
                    
                    with col2:
                        sigla_raw = soggetto_completo.get('sigla', '')
                        sigla_value = "" if pd.isna(sigla_raw) or sigla_raw is None else str(sigla_raw)
                        
                        cap_raw = soggetto_completo.get('cap', '')
                        cap_value = "" if pd.isna(cap_raw) or cap_raw is None else str(cap_raw)
                        
                        regione_raw = soggetto_completo.get('regione', '')
                        regione_value = "" if pd.isna(regione_raw) or regione_raw is None else str(regione_raw)
                        
                        tipo_luogo_raw = soggetto_completo.get('tipoLuogo', '')
                        tipo_luogo_value = "" if pd.isna(tipo_luogo_raw) or tipo_luogo_raw is None else str(tipo_luogo_raw)
                        
                        sigla_mod = st.text_input("Sigla Provincia", 
                            value=sigla_value, 
                            key="sigla_diffida")
                        cap_mod = st.text_input("CAP *", 
                            value=cap_value, 
                            key="cap_diffida")
                        regione_mod = st.text_input("Regione", 
                            value=regione_value, 
                            key="regione_diffida")
                        tipo_luogo_mod = st.text_input("Tipo Luogo", 
                            value=tipo_luogo_value, 
                            key="tipo_luogo_diffida")
                        originator_raw = soggetto_completo.get('fonteRecapito', '')
                        if pd.isna(originator_raw) or originator_raw is None or str(originator_raw).lower() in ['none', 'null', 'nan']:
                            originator_default = ""
                        else:
                            originator_default = str(originator_raw).strip()
                        
                        originator = st.text_input("Originator *", 
                            value=originator_default, 
                            key="originator",
                            help="Nome dell'Originator")

       
            if "Telegramma" in servizi_scelti:
                st.markdown("**Dati indirizzo di spedizione Telegramma:**")
                
                st.session_state["tipo_invio_telegramma"] = "RACCOMANDATA"
                
                col1, col2 = st.columns(2)
                
                with col1:
                    indirizzo_raw = soggetto_completo.get('indirizzo', '')
                    indirizzo_value = "" if pd.isna(indirizzo_raw) or indirizzo_raw is None else str(indirizzo_raw)
                    
                    comune_raw = soggetto_completo.get('comune', '')
                    comune_value = "" if pd.isna(comune_raw) or comune_raw is None else str(comune_raw)
                    
                    provincia_raw = soggetto_completo.get('provincia', '')
                    provincia_value = "" if pd.isna(provincia_raw) or provincia_raw is None else str(provincia_raw)
                    
                    indirizzo_mod = st.text_input("Indirizzo *", 
                        value=indirizzo_value, 
                        key="indirizzo_telegramma")
                    comune_mod = st.text_input("Comune *", 
                        value=comune_value, 
                        key="comune_telegramma")
                    provincia_mod = st.text_input("Provincia", 
                        value=provincia_value, 
                        key="provincia_telegramma")
                
                with col2:
                    sigla_raw = soggetto_completo.get('sigla', '')
                    sigla_value = "" if pd.isna(sigla_raw) or sigla_raw is None else str(sigla_raw)
                    
                    cap_raw = soggetto_completo.get('cap', '')
                    cap_value = "" if pd.isna(cap_raw) or cap_raw is None else str(cap_raw)
                    
                    regione_raw = soggetto_completo.get('regione', '')
                    regione_value = "" if pd.isna(regione_raw) or regione_raw is None else str(regione_raw)
                    
                    tipo_luogo_raw = soggetto_completo.get('tipoLuogo', '')
                    tipo_luogo_value = "" if pd.isna(tipo_luogo_raw) or tipo_luogo_raw is None else str(tipo_luogo_raw)
                    
                    sigla_mod = st.text_input("Sigla Provincia", 
                        value=sigla_value, 
                        key="sigla_telegramma")
                    cap_mod = st.text_input("CAP *", 
                        value=cap_value, 
                        key="cap_telegramma")
                    regione_mod = st.text_input("Regione", 
                        value=regione_value, 
                        key="regione_telegramma")
                    tipo_luogo_mod = st.text_input("Tipo Luogo", 
                        value=tipo_luogo_value, 
                        key="tipo_luogo_telegramma")

            
            st.divider()


            st.markdown("**Dati Obbligatori:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
    
                
                email_gestore = st.text_input("Email Gestore *", 
                    value=email_gestore_default, 
                    key="email_gestore",
                    help="La tua email di contatto (precompilata dal login)")
            
            with col2:
                telefono_gestore = st.text_input("Numero Telefono *", 
                    value="", 
                    key="telefono_gestore",
                    placeholder="Es: +39 123 456 7890",
                    help="Il tuo numero di telefono")
                
                if nome_gestore:
                    st.text_input("Nome Gestore", 
                        value=nome_gestore, 
                        disabled=True,
                        help="Nome del gestore loggato")
            st.divider()


            st.markdown("**Seleziona Motivazione:**")

            st.selectbox(
                    "Seleziona il motivo:",
                    ["STIMOLARE CONTATTO", "INTERROMPERE PRESCRIZIONE","AVVIO ATTI"],
                    key="motivazione"
                )
                
        else:
            st.error("Impossibile recuperare i dati completi del soggetto")
            st.stop()

    st.divider()

    if "richiesta_in_corso" not in st.session_state:
        st.session_state["richiesta_in_corso"] = False

    return servizi_scelti


def valida_campi_obbligatori(servizi_scelti):
    errori = []

    email_gestore = st.session_state.get("email_gestore", "").strip()
    telefono_gestore = st.session_state.get("telefono_gestore", "").strip()
    
    if not email_gestore:
        errori.append("Email Gestore è obbligatorio")
    if not telefono_gestore:
        errori.append("Numero Telefono è obbligatorio")
 
    if any(servizio in ["Diffida", "Welcome Letter"] for servizio in servizi_scelti):
        tipo_invio = st.session_state.get("tipo_invio_diffida", "")
        
        if not tipo_invio:
            errori.append("Seleziona il tipo di invio (PEC o RACCOMANDATA)")
        
        elif tipo_invio == "PEC":
            pec = st.session_state.get("pec_diffida", "").strip()
            if not pec:
                errori.append("PEC Destinatario è obbligatorio per invio PEC")
            elif "@" not in pec or "." not in pec:
                errori.append("Inserisci un indirizzo PEC valido")
        
        elif tipo_invio == "RACCOMANDATA":
            campi_raccomandata = {
                "indirizzo_diffida": "Indirizzo",
                "comune_diffida": "Comune",
                "cap_diffida": "CAP",
                "originator": "Originator"
            }
            
            for key, nome_campo in campi_raccomandata.items():
                valore = st.session_state.get(key, "").strip()
                if not valore:
                    errori.append(f"{nome_campo} è obbligatorio per invio RACCOMANDATA")
    
    if "Telegramma" in servizi_scelti:
        campi_telegramma = {
            "indirizzo_telegramma": "Indirizzo",
            "comune_telegramma": "Comune", 
            "cap_telegramma": "CAP"
        }
        
        for key, nome_campo in campi_telegramma.items():
            valore = st.session_state.get(key, "").strip()
            if not valore:
                errori.append(f"{nome_campo} è obbligatorio per Telegramma")
    
    return errori

def controlla_limite_mensile_gestore(navigator_dt):
    """
    Controlla se il gestore ha già raggiunto il limite di 50 richieste mensili
    tra Diffida, Welcome Letter e Telegramma
    """
    try:
        nav = navigator_dt
        user = st.session_state.get("user", {})
        gestore_corrente = user.get("username", "").strip()
        
        if not gestore_corrente:
            st.warning("Impossibile identificare il gestore corrente")
            return True
        
        # Carica il file centralizzato DT
        dt_folder_path = st.secrets["DT_FOLDER_PATH"]
        file_centrale = f"{dt_folder_path}/dt.parquet"
        
        site_id = nav.get_site_id()
        drive_id, _ = nav.get_drive_id(site_id)
        
        # Scarica il file centrale
        encoded_path = quote(file_centrale)
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
        headers = {"Authorization": f"Bearer {nav.access_token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df_centrale = pd.read_parquet(BytesIO(response.content))
            
            # Converti DATA RICHIESTA in datetime
            df_centrale["DATA RICHIESTA"] = pd.to_datetime(
                df_centrale["DATA RICHIESTA"], errors="coerce", dayfirst=True
            )
            
            # Normalizza GESTORE
            df_centrale["GESTORE"] = df_centrale["GESTORE"].astype(str).str.strip().str.lower()
            gestore_lower = gestore_corrente.lower()
            
            # Calcola mese e anno corrente
            from datetime import datetime
            import pytz
            
            roma_tz = pytz.timezone("Europe/Rome")
            ora_corrente = datetime.now(roma_tz)
            mese_corrente = ora_corrente.month
            anno_corrente = ora_corrente.year
            
            # Filtra richieste del gestore nel mese corrente
            richieste_gestore_mensili = df_centrale[
                (df_centrale["GESTORE"] == gestore_lower) &
                (df_centrale["DATA RICHIESTA"].dt.month == mese_corrente) &
                (df_centrale["DATA RICHIESTA"].dt.year == anno_corrente)
            ].copy()
            
            # Conta solo Diffida, Welcome Letter e Telegramma
            servizi_conteggiati = ["DIFFIDA", "WELCOME LETTER", "TELEGRAMMA"]
            
            conteggio = 0
            for _, row in richieste_gestore_mensili.iterrows():
                tipologia = str(row.get("TIPOLOGIA DOCUMENTO", "")).upper()
                for servizio in servizi_conteggiati:
                    if servizio in tipologia:
                        conteggio += 1
                        break  # Conta ogni richiesta una sola volta
            
            LIMITE_MENSILE = 50
            
            if conteggio >= LIMITE_MENSILE:
                msg_errore = (
                    f"🚫 LIMITE MENSILE RAGGIUNTO\n\n"
                    f"Hai già effettuato **{conteggio}/{LIMITE_MENSILE}** richieste questo mese "
                    f"({mese_corrente}/{anno_corrente}).\n\n"
                    f"Il limite mensile per Diffida, Welcome Letter e Telegramma è di **{LIMITE_MENSILE} richieste** per gestore.\n\n"
                    f"⏳ Potrai effettuare nuove richieste dal mese prossimo."
                )
                st.error(msg_errore)
                return False
            
            # Mostra info rimanenti
            rimanenti = LIMITE_MENSILE - conteggio
            st.info(f"ℹ️ Hai effettuato **{conteggio}/{LIMITE_MENSILE}** richieste questo mese. Ti rimangono **{rimanenti}** richieste disponibili.")
            return True
        
        elif response.status_code != 404:
            st.warning(f"Errore durante il controllo limite mensile: {response.status_code}")
      
        return True
        
    except Exception as e:
        print(f"Errore controllo limite mensile: {e}")
        st.warning(f"Impossibile verificare limite mensile: {e}")
        return True
def conferma_invio_richiesta(servizi_scelti, df_dt, navigator_dt, menu_utente_dt):
    if st.button("Conferma invio richiesta", key="conferma_richiesta", disabled=st.session_state["richiesta_in_corso"]):
        if not servizi_scelti:
            st.warning("Seleziona almeno un servizio!")
            st.stop()

        errori_validazione = valida_campi_obbligatori(servizi_scelti)
        if errori_validazione:
            st.error("Completa tutti i campi obbligatori:")
            for errore in errori_validazione:
                st.error(f"• {errore}")
            st.stop()

        # CONTROLLO LIMITE MENSILE GESTORE
        if not controlla_limite_mensile_gestore(navigator_dt):
            st.stop()  # Blocca l'invio se limite raggiunto

        cf_richiesta = st.session_state.get("richiesta", {}).get("cf", "")
        
        # CONTROLLO DUPLICATI CROSS-GESTORE
        if cf_richiesta and any(serv in ["Diffida", "Welcome Letter"] for serv in servizi_scelti):
            if not controlla_duplicati_cf(cf_richiesta, servizi_scelti, navigator_dt):
                st.stop()  # Blocca l'invio se trovato duplicato
    
        if servizi_scelti:
            if any(servizio in ["Diffida", "Welcome Letter"] for servizio in servizi_scelti):
                tipo_invio = st.session_state.get("tipo_invio_diffida", "")
                st.session_state["richiesta"]["tipo_invio_diffida"] = tipo_invio

                if tipo_invio == "RACCOMANDATA":
                    indirizzo_completo = st.session_state.get("indirizzo_diffida", "").strip()
                    
                    st.session_state["richiesta"].update({
                        "indirizzo": indirizzo_completo,
                        "comune": st.session_state.get("comune_diffida", "").strip(),
                        "provincia": st.session_state.get("provincia_diffida", "").strip(),
                        "sigla": st.session_state.get("sigla_diffida", "").strip(),
                        "cap": st.session_state.get("cap_diffida", "").strip(),
                        "regione": st.session_state.get("regione_diffida", "").strip(),
                        "tipoLuogo": st.session_state.get("tipo_luogo_diffida", "").strip(),
                        "originator": st.session_state.get("originator", "").strip()
                    })

            if "Telegramma" in servizi_scelti: 
                st.session_state["richiesta"].update({
                    "tipo_invio_telegramma": "RACCOMANDATA",
                    "indirizzo_telegramma": st.session_state.get("indirizzo_telegramma", "").strip(),
                    "comune_telegramma": st.session_state.get("comune_telegramma", "").strip(),
                    "provincia_telegramma": st.session_state.get("provincia_telegramma", "").strip(),
                    "sigla_telegramma": st.session_state.get("sigla_telegramma", "").strip(),
                    "cap_telegramma": st.session_state.get("cap_telegramma", "").strip(),
                    "regione_telegramma": st.session_state.get("regione_telegramma", "").strip(),
                    "tipoLuogo_telegramma": st.session_state.get("tipo_luogo_telegramma", "").strip()
                })
        
            st.session_state["richiesta"].update({
                "email_gestore": st.session_state.get("email_gestore", "").strip(),
                "telefono_gestore": st.session_state.get("telefono_gestore", "").strip(),
                "motivazione": st.session_state.get("motivazione", "").strip()
            })
            
            if any(servizio in ["Diffida", "Welcome Letter"] for servizio in servizi_scelti):
                originator_value = st.session_state.get("originator", "").strip()
                if originator_value:
                    st.session_state["richiesta"]["originator"] = originator_value
        
            st.session_state["richiesta_in_corso"] = True
            
            for key in ["pec_diffida", "indirizzoPostaElettronica", "pec_destinatario", "PEC DESTINATARIO"]:
                valore_session = st.session_state.get(key, "NON TROVATO")
                valore_richiesta = st.session_state.get("richiesta", {}).get(key, "NON TROVATO")
                print(f"  {key}: session='{valore_session}', richiesta='{valore_richiesta}'")

            st.json(st.session_state["richiesta"])
                
        try:
            df_result, success, msg = menu_utente_dt(
                df_dt,          
                servizi_scelti, 
                navigator_dt    
            )
            
            if success:
                st.success(msg)
                
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.03) 
                    progress_bar.progress(i + 1)
                
                for key in ["richiesta", "servizi_scelti", "inserimento_richiesta", "richiesta_in_corso"]:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.rerun()
                
        except Exception as e:
            st.error(f"Errore durante il salvataggio: {str(e)}")
            st.session_state["richiesta_in_corso"] = False