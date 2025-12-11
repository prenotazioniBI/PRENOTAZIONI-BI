import streamlit as st
import time
import pandas as pd
from io import BytesIO
import requests
from urllib.parse import quote


def controlla_duplicati_cf(cf_richiesta, servizi_scelti, navigator_dt):
    """
    Controlla se esiste già una richiesta per lo stesso CF con gli stessi servizi
    """
    try:
        nav = navigator_dt
        user = st.session_state.get("user", {})
        email = user.get("email", "")
        
        # Crea nome file come in salva_richiesta_utente_dt
        if email:
            nome_cognome = email.split("@")[0].replace(".", "_").lower()
            if nome_cognome.endswith("_ext"):
                nome_cognome = nome_cognome[:-4]
            nome_file = f"{nome_cognome}_dt.parquet"
        else:
            gestore = user.get("username", "Sconosciuto")
            nome_file = f"{gestore.replace(' ', '_').lower()}_dt.parquet"
        
        dt_folder_path = st.secrets["DT_FOLDER_PATH"]
        file_path = f"{dt_folder_path}/{nome_file}"
        
        site_id = nav.get_site_id()
        drive_id, _ = nav.get_drive_id(site_id)
        
        # Carica il file esistente
        encoded_path = quote(file_path)
        url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
        headers = {"Authorization": f"Bearer {nav.access_token}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            df_esistente = pd.read_parquet(BytesIO(response.content))
            
            if not df_esistente.empty and "CF" in df_esistente.columns:
                # Converti data richiesta
                if "DATA RICHIESTA" in df_esistente.columns:
                    df_esistente["DATA RICHIESTA"] = pd.to_datetime(df_esistente["DATA RICHIESTA"], errors="coerce")
                
                # Filtra per CF
                richieste_cf = df_esistente[
                    df_esistente["CF"].astype(str).str.upper() == cf_richiesta.upper()
                ].copy()
                
                if not richieste_cf.empty:
                    # Controlla ogni servizio richiesto
                    servizi_str = ", ".join(sorted(servizi_scelti))
                    
                    for _, riga in richieste_cf.iterrows():
                        tipologia_esistente = str(riga.get("TIPOLOGIA DOCUMENTO", ""))
                        
                        # Controlla se c'è overlap nei servizi
                        servizi_esistenti = [s.strip() for s in tipologia_esistente.split(",")]
                        overlap = set(servizi_scelti) & set(servizi_esistenti)
                        
                        if overlap:
                            data_esistente = riga.get("DATA RICHIESTA")
                            if pd.notna(data_esistente):
                                # Calcola giorni fa
                                oggi = pd.Timestamp.now()
                                giorni_fa = (oggi - data_esistente).days
                                
            
                                if 0 <= giorni_fa <= 30:
                                    data_str = data_esistente.strftime("%d/%m/%Y")
                                    
                                    if giorni_fa == 0:
                                        tempo_msg = "oggi"
                                    elif giorni_fa == 1:
                                        tempo_msg = "1 giorno fa"
                                    else:
                                        tempo_msg = f"{giorni_fa} giorni fa"
                                    
                                    servizi_duplicati = ", ".join(overlap)
                                    
                                    msg_errore = (
                                        f"RICHIESTA DUPLICATA PER CF {cf_richiesta}\n\n"
                                        f"Servizi già richiesti: {servizi_duplicati}\n"
                                        f"Data richiesta precedente: {data_str} ({tempo_msg})\n\n"
                                        f"Puoi richiedere nuovamente tra {30 - giorni_fa} giorni"
                                    )
                                    
                                    return False, msg_errore
                
        elif response.status_code != 404:
            return False, f"Errore caricamento file: {response.status_code}"
        
      
        return True, "Nessun duplicato trovato"
        
    except Exception as e:
        print(f"Errore controllo duplicati CF: {e}")
        return False, f"Errore controllo duplicati: {str(e)}"



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
                        
                        numero_civico_raw = soggetto_completo.get('numeroCivico', '')
                        numero_civico_value = "" if pd.isna(numero_civico_raw) or numero_civico_raw is None else str(numero_civico_raw)
                        
                        comune_raw = soggetto_completo.get('comune', '')
                        comune_value = "" if pd.isna(comune_raw) or comune_raw is None else str(comune_raw)
                        
                        provincia_raw = soggetto_completo.get('provincia', '')
                        provincia_value = "" if pd.isna(provincia_raw) or provincia_raw is None else str(provincia_raw)
                        
                        indirizzo_mod = st.text_input("Indirizzo *", 
                            value=indirizzo_value, 
                            key="indirizzo_diffida")
                        numero_civico_mod = st.text_input("Numero Civico *", 
                            value=numero_civico_value, 
                            key="numero_civico_diffida")
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
                    
                    numero_civico_raw = soggetto_completo.get('numeroCivico', '')
                    numero_civico_value = "" if pd.isna(numero_civico_raw) or numero_civico_raw is None else str(numero_civico_raw)
                    
                    comune_raw = soggetto_completo.get('comune', '')
                    comune_value = "" if pd.isna(comune_raw) or comune_raw is None else str(comune_raw)
                    
                    provincia_raw = soggetto_completo.get('provincia', '')
                    provincia_value = "" if pd.isna(provincia_raw) or provincia_raw is None else str(provincia_raw)
                    
                    indirizzo_mod = st.text_input("Indirizzo *", 
                        value=indirizzo_value, 
                        key="indirizzo_telegramma")
                    numero_civico_mod = st.text_input("Numero Civico *", 
                        value=numero_civico_value, 
                        key="numero_civico_telegramma")
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
                "numero_civico_diffida": "Numero Civico", 
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
            "numero_civico_telegramma": "Numero Civico",
            "comune_telegramma": "Comune", 
            "cap_telegramma": "CAP"
        }
        
        for key, nome_campo in campi_telegramma.items():
            valore = st.session_state.get(key, "").strip()
            if not valore:
                errori.append(f"{nome_campo} è obbligatorio per Telegramma")
    
    return errori

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

        cf_richiesta = st.session_state.get("richiesta", {}).get("cf", "")
        if cf_richiesta:
            duplicato_ok, msg_duplicato = controlla_duplicati_cf(cf_richiesta, servizi_scelti, navigator_dt)
            if not duplicato_ok:
                st.error(msg_duplicato)
                st.stop()
    
        if servizi_scelti:
            if any(servizio in ["Diffida", "Welcome Letter"] for servizio in servizi_scelti):
                tipo_invio = st.session_state.get("tipo_invio_diffida", "")
                
                st.session_state["richiesta"]["tipo_invio_diffida"] = tipo_invio
                
                if tipo_invio == "PEC":
                    pec_value = st.session_state.get("pec_diffida", "").strip()
                    
                    if pec_value:
                        st.session_state["richiesta"]["PEC DESTINATARIO"] = pec_value

                    
                elif tipo_invio == "RACCOMANDATA":
                    st.session_state["richiesta"].update({
                        "indirizzo": st.session_state.get("indirizzo_diffida", "").strip(),
                        "numeroCivico": st.session_state.get("numero_civico_diffida", "").strip(),
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
                    "numeroCivico_telegramma": st.session_state.get("numero_civico_telegramma", "").strip(),
                    "comune_telegramma": st.session_state.get("comune_telegramma", "").strip(),
                    "provincia_telegramma": st.session_state.get("provincia_telegramma", "").strip(),
                    "sigla_telegramma": st.session_state.get("sigla_telegramma", "").strip(),
                    "cap_telegramma": st.session_state.get("cap_telegramma", "").strip(),
                    "regione_telegramma": st.session_state.get("regione_telegramma", "").strip(),
                    "tipoLuogo_telegramma": st.session_state.get("tipo_luogo_telegramma", "").strip()
                })
        
            st.session_state["richiesta"].update({
                "email_gestore": st.session_state.get("email_gestore", "").strip(),
                "telefono_gestore": st.session_state.get("telefono_gestore", "").strip()
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