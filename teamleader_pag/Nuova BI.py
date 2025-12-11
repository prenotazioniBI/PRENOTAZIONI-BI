
from ottimizzazione import gestisci_nuova_richiesta
from user import menu_utente
import streamlit as st
 
def main(**kwargs):
        st.title('Nuova Richiesta BI')
        nav = kwargs.get('navigator')

        richieste = [
            "Info lavorativa Full (residenza + telefono + impiego)",
            "Ricerca Anagrafica",
            "Ricerca Telefonica",
            "Ricerca Anagrafica + Telefono",
            "Rintraccio Conto corrente"
        ]
        gestisci_nuova_richiesta(st.session_state['df_full'], st.session_state.get('df_soggetti'), richieste, menu_utente, nav)
if __name__ == "__main__":
        
    main(
        user=None,
        df_full=None,
        df_soggetti=None,
        df_utenza=None,
        df_dt_full=None,
        navigator=None,
        navigator_dt=None
    )