import streamlit as st

@st.dialog("Informazioni sulle richieste")
def dialog_info_richieste():
    st.info("""
**Rintraccio residenza anagrafica**  
*Verifica della validità del codice fiscale, evidenza di eventuali soggetti deceduti e ricerca della residenza attuale del soggetto.*

**Rintraccio utenza telefonica verificato**  
*Ricerca e verifica di utenze telefoniche mobili e fisse intestate al soggetto.*

**Full**  
*Servizio completo: verifica del codice fiscale, evidenza di eventuali soggetti deceduti, ricerca della residenza, identificazione del datore di lavoro e dell’ente erogante, stima del reddito lordo percepito, evidenza di eventuali gravami, controlli catastali, protesti e pregiudizievoli da tribunali e conservatorie.*

**Eredi accettanti**  
*Identificazione dei successibili di un soggetto deceduto con evidenza dei relativi dati anagrafici e verifica dell’accettazione dell’eredità.*

**Rintraccio eredi chiamati con verifica accettazione**  
*Ricerca degli eredi chiamati all’eredità e verifica della loro eventuale accettazione.*

**Rapporti bancari**  
*Verifica del codice fiscale e ricerca degli istituti di credito con i quali il soggetto intrattiene rapporti, con dettaglio di ABI e CAB.*

**Anagrafica + telefono**  
*Combinazione dei servizi di ricerca anagrafica e rintraccio telefonico.*
""")
