import streamlit as st

@st.dialog("Informazioni sulle richieste")
def dialog_info_richieste():
    st.info("""
**Rintraccio residenza anagrafica**  
*Verifica esistenza CF, evidenza dei soggetti deceduti, rintraccio residenza del soggetto.*

**Rintraccio utenza telefonica verificato**  
*Rintraccio utenze mobili e fisse.*

**Full**  
*Esistenza CF, evidenza soggetti deceduti, ricerca residenza del soggetto, identificazione datore lavoro e ente erogante, stima del reddito lordo percepito, evidenza di eventuali gravami, check di catasto, protesti, pregiudizievoli da tribunale e conservatorie.*

**Eredi accettanti**  
*Identificazione dei successibili di un soggetto deceduto con evidenza dei dati anagrafici.*

**Rintraccio eredi chiamati con verifica accettazione**

**Rapporti bancari**  
*Verifica esistenza CF, ricerca istituti di credito con i quali il debitore intrattiene rapporti raccogliendo ABI e CAB.*

**Anagrafica + telefono**  
*La somma delle due cose.*
""")