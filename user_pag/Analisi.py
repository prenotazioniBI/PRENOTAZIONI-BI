import streamlit as st
from grafici_utente import Grafici
from grafici import aggrid_spesa_per_portafoglio
from gauge_gestore import gauge_spesa_gestore
from gauge_richieste_gestore import chart_richieste_incasso


def main(**kwargs):
    st.title("Analisi delle tue Richieste")

    df = kwargs.get("df_full")
    user = kwargs.get("user") or {}
    navigator = kwargs.get("navigator")
    dt_performance = kwargs.get("dt_performance") or st.session_state.get("dt_performance")

    username = user.get("username")


    if df is None or dt_performance is None or not username:
        st.warning("Dati mancanti.")
        st.stop()


    if dt_performance is None:
        st.warning("dt_performance non disponibile.")
        st.stop()

    if not username:
        st.warning("Utente non disponibile.")
        st.stop()

    # Copie locali sicure
    df = df.copy()
    dt_performance = dt_performance.copy()

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
        " AGECREDIT": "AGECREDIT",
    }

    if "GESTORE" in df.columns:
        df["GESTORE"] = df["GESTORE"].replace(mappa_gestori)

    gauge_spesa_gestore(df, gestore_loggato=username)
    # chart_richieste_incasso(
    #     dt_performance,
    #     gestore_loggato=username,
    #     anno=2025,
    #     mappa_gestori=mappa_gestori,
    # )



if __name__ == "__main__":
    st.info("Questa pagina va aperta dal flusso principale dell'app.")