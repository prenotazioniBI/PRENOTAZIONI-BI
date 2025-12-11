import streamlit as st
from grafici_utente import Grafici
from grafici import aggrid_spesa_per_portafoglio


def main(**kwargs):
    st.title("Analisi delle tue Richieste")
    df= kwargs.get('df_full')
    user = kwargs.get('user')
    navigator = kwargs.get('navigator')
    df_soggetti = kwargs.get('df_soggetti')
    mappa_gestori = {
            "ANTONELLA COCCO": "Antonella cocco",
            "BEATRICE LAORENZA": "Beatrice Laorenza",
            "Bacchetta ": "Carlo Bacchetta",
            "DANIELA RIZZI": "Daniela Rizzi",
            "FINGEST CREDIT": "Fingest Group",
            "GIUSEPPE NIGRA": "Giuseppe Nigra",
            "LAMYAA HAKIM": "Lamyaa Hakim",
            "MATTEO CATARZI": "Matteo Catarzi",
            "Magnifico Gelsomina ": "Gelsomina Magnifico",
            "Mauro Gualtiero ": "Mauro Gualtiero",
            "Michele  Oranger": "Michele Oranger",
            "RITA NOTO": "Rita Maria Noto",
            "Rita Maria Noto ": "Rita Maria Noto",
            "Rita Noto": "Rita Maria Noto",
            "Ritamaria Noto": "Rita Maria Noto",
            "Mariagiulia Berardi": "Maria Giulia Berardi",
            "Rita maria Noto": "Rita Maria Noto",
            "Ruscelli lisa": "Ruscelli Lisa",
            "Tiziana Alibrandi ": "Tiziana Alibrandi",
            "VALENTINA BARTOLO": "Valentina Bartolo",
            "VALERIA NAPOLEONE": "Valeria Napoleone",
            "carmela lanciano": "Carmela Lanciano",
            "silvia stefanelli": "Silvia Stefanelli",
            " AGECREDIT": "AGECREDIT"
        }
        
    if "GESTORE" in df.columns:
            df["GESTORE"] = df["GESTORE"].replace(mappa_gestori)
        
    # Filtra per gestore corrente (VISUALIZZA STORICO COMPLETO per i grafici)
    username_norm = user["username"].replace(" ", "").lower()
    df_gestore = df[df["GESTORE"].astype(str).str.replace(" ", "").str.lower() == username_norm]
    
    grafici = Grafici(df_gestore)
    col1, col2 = st.columns(2)
    with col1:
        grafici.pivot_spesa_mensile_aggrid()
    with col2:
        grafici.torta_servizio_costo()
    aggrid_spesa_per_portafoglio(df)

if __name__ == "__main__":
    main()