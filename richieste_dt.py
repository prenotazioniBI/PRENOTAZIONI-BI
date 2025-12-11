import streamlit as st
from stdnum.it import codicefiscale, iva
import pandas as pd

@st.dialog("Inserisci nuova richiesta")
def banner_richiesta_utente_dt(dt_soggetti):
    st.write("Inserisci dati:")
    
    if "codiceFiscale" not in dt_soggetti.columns:
        st.error("Codice Fiscale non trovato")
        if st.button("Chiudi"):
            st.session_state.pop("inserimento_richiesta", None)
            st.rerun()
        st.stop()

    if not st.session_state.get("cf_validato", False):
        cf = st.text_input("CODICE FISCALE o P.IVA *").strip()
        col1, _ = st.columns(2)
        avanti = col1.button("Avanti")
        
        if avanti:
            if not cf:
                st.warning("CODICE FISCALE o P.IVA OBBLIGATORIO")
                st.stop()

            try:
                if len(cf.replace(" ", "")) == 16:
                    cf_clean = codicefiscale.compact(cf)
                    is_valid = codicefiscale.is_valid(cf_clean)
                    tipo_documento = "Codice Fiscale"
                elif len(cf.replace(" ", "")) == 11:
                    cf_clean = iva.compact(cf)
                    is_valid = iva.is_valid(cf_clean)
                    tipo_documento = "Partita IVA"
                else:
                    is_valid = False
                    cf_clean = cf.strip()
                    tipo_documento = "Formato non riconosciuto"
                    
            except Exception as e:
                st.error(f"Errore nella validazione: {str(e)}")
                st.stop()
            
            if not is_valid:
                st.error(f"{tipo_documento} non valido: '{cf}'")
                st.info("Formati accettati:")
                st.info("• Codice Fiscale: 16 caratteri (es. RSSMRA85M01H501Z)")
                st.info("• Partita IVA: 11 cifre (es. 12345670017)")
                st.stop()

            soggetti_cf = dt_soggetti[dt_soggetti["codiceFiscale"].astype(str).str.upper() == cf_clean.upper()]
            
            user = st.session_state.get("user", {})
            ruolo = user.get("ruolo", "")
            

            if "deceduto" in soggetti_cf.columns and not soggetti_cf.empty and (soggetti_cf["deceduto"] == "DECEDUTO").any():
                if ruolo not in ["admin", "team leader"]:
                    st.error("Soggetto risulta deceduto")
                    st.stop()
                else:
                    st.warning("Attenzione: soggetto risulta deceduto (autorizzato per il tuo ruolo)")
            
            if not soggetti_cf.empty:
                st.session_state.soggetti_cf_trovati = soggetti_cf
                st.session_state.cf_validato = cf_clean
                st.session_state.cf_validato_flag = True
                st.rerun()
            else:
                st.error("Soggetto non trovato nel database")
                st.stop()


    else:
        soggetti_cf = st.session_state.get("soggetti_cf_trovati")
        cf_validato = st.session_state.get("cf_validato")
        
        st.success(f"CF validato: **{cf_validato}**")
        
        if len(soggetti_cf) > 1:
            records_unici = []
            seen_combinations = set()
            
            for idx, row in soggetti_cf.iterrows():

                key_combination = (
                    str(row.get('rapporto', '')).strip(),
                    str(row.get('portafoglio', '')).strip(), 
                    str(row.get('ndg', '')).strip()
                )
                
                if key_combination not in seen_combinations:
                    seen_combinations.add(key_combination)
                    records_unici.append({
                        'index': idx,
                        'row': row,
                        'display': f"Rapporto: {row.get('rapporto', 'N/A')} - GBV: {row.get('gbvAttuale', 0):,.2f}€",
                        'rapporto': str(row.get('rapporto', '')).strip(),
                        'gbv': float(row.get('gbvAttuale', 0))
                    })
            
            if len(records_unici) > 1:
                st.write("**Seleziona uno o più rapporti:**")
                
                options_display = [record['display'] for record in records_unici]
                
                selected_indices = st.multiselect(
                    "Rapporti disponibili:",
                    options=list(range(len(options_display))),
                    format_func=lambda x: options_display[x],
                    default=[0] 
                )
                
                if not selected_indices:
                    st.warning("Seleziona almeno un rapporto")
                    st.stop()
                rapporti_selezionati = []
                gbv_totale = 0
                soggetto_base = None
                
                for idx in selected_indices:
                    record = records_unici[idx]
                    rapporti_selezionati.append(record['rapporto'])
                    gbv_totale += record['gbv']
                    if soggetto_base is None:
                        soggetto_base = record['row']
                
                rapporti_stringa = ", ".join(rapporti_selezionati)
                
                st.info(f"**Rapporti selezionati:** {len(selected_indices)}")
                st.info(f"**GBV Totale:** {gbv_totale:,.2f}€")
                
            else:
                soggetto_base = records_unici[0]['row']
                rapporti_stringa = str(soggetto_base.get('rapporto', '')).strip()
                gbv_totale = float(soggetto_base.get('gbvAttuale', 0))
                st.info("Record unico trovato")
        else:
            soggetto_base = soggetti_cf.iloc[0]
            rapporti_stringa = str(soggetto_base.get('rapporto', '')).strip()
            gbv_totale = float(soggetto_base.get('gbvAttuale', 0))
            st.info("Record unico trovato")
        
        st.divider()

        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("Codice Fiscale o P.IVA", value=cf_validato, disabled=True)
            st.text_input("Portafoglio", value=str(soggetto_base.get('portafoglio', '')), disabled=True)
            st.text_input("NDG Debitore", value=str(soggetto_base.get('ndg', '')), disabled=True)
            st.text_area("Rapporti Selezionati", value=rapporti_stringa, disabled=True, height=80)
        
        with col2:
            st.text_input("Intestazione", value=str(soggetto_base.get('intestazione', '')), disabled=True)
            st.text_input("Nome Completo", value=str(soggetto_base.get('nomeCompleto', '')), disabled=True)
            st.text_input("NDG Soggetto", value=str(soggetto_base.get('ndgSoggetto', '')), disabled=True)
            st.number_input("GBV Totale", value=gbv_totale, disabled=True, format="%.2f")
    
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Cambia CF", key="cambia_cf"):
                for key in ["cf_validato", "cf_validato_flag", "soggetti_cf_trovati"]:
                    st.session_state.pop(key, None)
                st.rerun()
        
        with col2:
            if st.button("Conferma Selezione", key="conferma_selezione"):
                st.session_state.richiesta = {
                    "cf": cf_validato,
                    "portafoglio": str(soggetto_base.get('portafoglio', '')).strip(),
                    "ndg_debitore": str(soggetto_base.get('ndg', '')).strip(),
                    "nominativo_posizione": str(soggetto_base.get('intestazione', '')).strip(),
                    "ndg_nominativo_ricercato": str(soggetto_base.get('ndgSoggetto', '')).strip(),
                    "nominativo_ricerca": str(soggetto_base.get('nomeCompleto', '')).strip(),
                    "rapporto": rapporti_stringa, 
                    "gbvAttuale": gbv_totale 
                }
                
                st.success(f"Dati confermati! Rapporti: {len(rapporti_selezionati) if 'rapporti_selezionati' in locals() else 1}")

                for key in ["cf_validato", "cf_validato_flag", "soggetti_cf_trovati"]:
                    st.session_state.pop(key, None)
                
                st.rerun()