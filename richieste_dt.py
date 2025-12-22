import streamlit as st
from stdnum.it import codicefiscale, iva
import pandas as pd

@st.dialog("Inserisci nuova richiesta")
def banner_richiesta_utente_dt(dt_soggetti):
    st.write("Inserisci dati:")
    
    # Validazione iniziale colonna
    if "codiceFiscale" not in dt_soggetti.columns:
        st.error("Codice Fiscale non trovato")
        if st.button("Chiudi"):
            st.session_state.pop("inserimento_richiesta", None)
            st.rerun()
        st.stop()

    # FASE 1: Validazione CF/P.IVA
    if not st.session_state.get("cf_validato_flag", False):
        cf = st.text_input("CODICE FISCALE o P.IVA *").strip()
        col1, _ = st.columns(2)
        
        if col1.button("Avanti"):
            if not cf:
                st.warning("CODICE FISCALE o P.IVA OBBLIGATORIO")
                st.stop()

            # Validazione rapida
            cf_len = len(cf.replace(" ", ""))
            if cf_len == 16:
                cf_clean = codicefiscale.compact(cf)
                is_valid = codicefiscale.is_valid(cf_clean)
                tipo_documento = "Codice Fiscale"
            elif cf_len == 11:
                cf_clean = iva.compact(cf)
                is_valid = iva.is_valid(cf_clean)
                tipo_documento = "Partita IVA"
            else:
                st.error(f"Formato non riconosciuto: '{cf}'")
                st.info("• Codice Fiscale: 16 caratteri (es. RSSMRA85M01H501Z)\n• Partita IVA: 11 cifre (es. 12345670017)")
                st.stop()
            
            if not is_valid:
                st.error(f"{tipo_documento} non valido: '{cf}'")
                st.stop()

            # Ricerca soggetto (ottimizzata con upper() una sola volta)
            cf_upper = cf_clean.upper()
            soggetti_cf = dt_soggetti[dt_soggetti["codiceFiscale"].str.upper() == cf_upper]
            
            if soggetti_cf.empty:
                st.error("Soggetto non trovato nel database")
                st.stop()
            
            # Check deceduto
            user_ruolo = st.session_state.get("user", {}).get("ruolo", "")
            if "deceduto" in soggetti_cf.columns and (soggetti_cf["deceduto"] == "DECEDUTO").any():
                if user_ruolo not in ["admin", "team leader"]:
                    st.error("Soggetto risulta deceduto")
                    st.stop()
                else:
                    st.warning("Attenzione: soggetto risulta deceduto (autorizzato per il tuo ruolo)")
            
            # Salva e procedi
            st.session_state.soggetti_cf_data = soggetti_cf.to_dict('records')
            st.session_state.cf_validato = cf_clean
            st.session_state.cf_validato_flag = True
            st.rerun()

    # FASE 2: Selezione portafoglio e rapporti
    else:
        soggetti_cf_data = st.session_state.get("soggetti_cf_data")
        if not soggetti_cf_data:
            st.session_state.pop("cf_validato_flag", None)
            st.rerun()
            st.stop()
            
        soggetti_cf = pd.DataFrame(soggetti_cf_data)
        st.success(f"CF validato: **{st.session_state.cf_validato}**")
        
        # Gestione portafogli multipli
        portafogli_unici = soggetti_cf['portafoglio'].unique()
        
        if len(portafogli_unici) > 1:
            st.warning(f"Trovati {len(portafogli_unici)} portafogli diversi per questo CF")
            
            if "portafoglio_selezionato" not in st.session_state:
                st.write("**Seleziona il portafoglio:**")
                
                # Calcolo aggregato ottimizzato
                portafoglio_options = []
                for i, portafoglio in enumerate(portafogli_unici):
                    records_pf = soggetti_cf[soggetti_cf['portafoglio'] == portafoglio]
                    portafoglio_options.append({
                        'index': i,
                        'portafoglio': portafoglio,
                        'display': f"Portafoglio: {portafoglio} - Rapporti: {len(records_pf)} - GBV: {records_pf['gbvAttuale'].sum():,.2f}€"
                    })
                
                selected_index = st.selectbox(
                    "Portafogli disponibili:",
                    options=[opt['index'] for opt in portafoglio_options],
                    format_func=lambda x: portafoglio_options[x]['display']
                )
                
                if st.button("Conferma Portafoglio"):
                    selected_pf = portafoglio_options[selected_index]['portafoglio']
                    st.session_state.portafoglio_selezionato = selected_pf
                    records_filtrati = soggetti_cf[soggetti_cf['portafoglio'] == selected_pf]
                    st.session_state.soggetti_cf_filtrati_data = records_filtrati.to_dict('records')
                    st.rerun()
                st.stop()
            else:
                # Portafoglio già selezionato
                soggetti_cf_filtrati_data = st.session_state.get("soggetti_cf_filtrati_data")
                if not soggetti_cf_filtrati_data:
                    st.session_state.pop("portafoglio_selezionato", None)
                    st.rerun()
                    st.stop()
                
                soggetti_cf = pd.DataFrame(soggetti_cf_filtrati_data)
                st.info(f"Portafoglio selezionato: **{st.session_state.portafoglio_selezionato}**")
                
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("Cambia Portafoglio"):
                        st.session_state.pop("portafoglio_selezionato", None)
                        st.session_state.pop("soggetti_cf_filtrati_data", None)
                        st.rerun()
        
        # FASE 3: Selezione rapporti
        if len(soggetti_cf) > 1:
            # Deduplica rapporti ottimizzata
            records_unici = []
            seen = set()
            
            for idx, row in soggetti_cf.iterrows():
                key = (str(row.get('rapporto', '')).strip(), 
                       str(row.get('portafoglio', '')).strip(), 
                       str(row.get('ndg', '')).strip())
                
                if key not in seen:
                    seen.add(key)
                    records_unici.append({
                        'index': len(records_unici),
                        'row_data': row.to_dict(),
                        'display': f"Rapporto: {row.get('rapporto', 'N/A')} - GBV: {row.get('gbvAttuale', 0):,.2f}€",
                        'rapporto': key[0],
                        'gbv': float(row.get('gbvAttuale', 0))
                    })
            
            if len(records_unici) > 1:
                st.write("**Seleziona uno o più rapporti:**")
                
                selected_indices = st.multiselect(
                    "Rapporti disponibili:",
                    options=[r['index'] for r in records_unici],
                    format_func=lambda x: records_unici[x]['display'],
                    default=[0]
                )
                
                if not selected_indices:
                    st.warning("Seleziona almeno un rapporto")
                    st.stop()
                
                rapporti_selezionati = [records_unici[i]['rapporto'] for i in selected_indices]
                gbv_totale = sum(records_unici[i]['gbv'] for i in selected_indices)
                soggetto_base_data = records_unici[selected_indices[0]]['row_data']
                rapporti_stringa = ", ".join(rapporti_selezionati)
                
                st.info(f"**Rapporti selezionati:** {len(selected_indices)}")
                st.info(f"**GBV Totale:** {gbv_totale:,.2f}€")
            else:
                soggetto_base_data = records_unici[0]['row_data']
                rapporti_stringa = soggetto_base_data.get('rapporto', '')
                gbv_totale = soggetto_base_data.get('gbvAttuale', 0)
                st.info("Record unico trovato")
        else:
            soggetto_base_data = soggetti_cf.iloc[0].to_dict()
            rapporti_stringa = str(soggetto_base_data.get('rapporto', '')).strip()
            gbv_totale = float(soggetto_base_data.get('gbvAttuale', 0))
            st.info("Record unico trovato")
        
        st.write("---")
        gbv_editabile = st.number_input(
            "GBV Attuale (editabile):",
            min_value=0.0,
            value=float(gbv_totale),
            step=0.01,
            format="%.2f"
        )
        
        col1, col2 = st.columns(2)
        with col2:
            if st.button("Conferma Selezione", key="conferma_selezione"):
                st.session_state.richiesta = {
                    "cf": st.session_state.cf_validato,
                    "portafoglio": str(soggetto_base_data.get('portafoglio', '')).strip(),
                    "ndg_debitore": str(soggetto_base_data.get('ndg', '')).strip(),
                    "nominativo_posizione": str(soggetto_base_data.get('intestazione', '')).strip(),
                    "ndg_nominativo_ricercato": str(soggetto_base_data.get('ndgSoggetto', '')).strip(),
                    "nominativo_ricerca": str(soggetto_base_data.get('nomeCompleto', '')).strip(),
                    "rapporto": rapporti_stringa,
                    "gbvAttuale": gbv_editabile
                }
                
                st.success(f"Dati confermati! Rapporti: {len(rapporti_selezionati) if 'rapporti_selezionati' in locals() else 1}")

                # Pulizia session state
                for key in ["cf_validato", "cf_validato_flag", "soggetti_cf_data", 
                           "portafoglio_selezionato", "soggetti_cf_filtrati_data"]:
                    st.session_state.pop(key, None)
                
                st.rerun()