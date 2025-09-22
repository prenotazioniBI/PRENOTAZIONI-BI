import streamlit as st
from home_utente import home_utente
from home_leader import home_Teamleader
import pandas as pd
from sharepoint_utils import SharePointNavigator
import io
from home_admin import home_admin



st.set_page_config(page_title="Prenotazioni BI", layout="wide")




TENANT_ID = st.secrets["TENANT_ID"]
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]




@st.cache_data(show_spinner="Scarico dati da Sharepoint...")  
def get_files_from_sharepoint():
    nav = SharePointNavigator(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    nav.login()
    site_id = nav.get_site_id()
    drive_id, _ = nav.get_drive_id(site_id)
    
    prenotazioni_data = nav.download_file(site_id, drive_id, "General/PRENOTAZIONI_BI/prenotazioni.xlsx")
    soggetti_data = nav.download_file(site_id, drive_id, "General/PRENOTAZIONI_BI/soggetti.parquet")
    utenza = nav.download_file(site_id, drive_id, "General/PRENOTAZIONI_BI/utenza.xlsx")
    

    df_utenza = pd.read_excel(io.BytesIO(utenza["content"]))
    df = pd.read_excel(io.BytesIO(prenotazioni_data['content']))
        
    if 'id' not in df.columns:
        df.insert(0, 'id', range(len(df)))
    
    df_soggetti = pd.read_parquet(io.BytesIO(soggetti_data['content']))
    
    return df, df_soggetti, df_utenza

def prepare_data(df):
    colonne = [
        "PORTAFOGLIO", "CENTRO DI COSTO", "GESTORE", "NDG DEBITORE", "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO", "C.F.", "SERVIZIO RICHIESTO", "NOME SERVIZIO", "PROVIDER",
        "INVIATE AL PROVIDER", "COSTO", "MESE", "ANNO", "RIFATTURAZIONE", "NOMINATIVO RICERCA",
        "DATA RICHIESTA", "RIFIUTATA"
    ]
    if "id" not in df.columns:
        df["id"] = range(1, len(df) + 1)
    colonne_esistenti = [col for col in colonne if col in df.columns]
    if 'id' in df.columns and 'id' not in colonne_esistenti:
        colonne_esistenti.append('id')
    df = df[colonne_esistenti]
    
    return df

def get_navigator():
    nav = SharePointNavigator(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    nav.login()
    return nav



def authentication():
    col1, col2, col3 = st.columns(3)
    with col2:
        st.title("Prenotazioni BI")
        with st.form(key="login_form_unique"):
            username = st.text_input("COGNOME NOME").strip()
            password = st.text_input("PASSWORD", type="password").strip()
            submit = st.form_submit_button("Login")

        if not submit:
            return None, None
        _, _A, df_utenza = get_files_from_sharepoint()
        df = df_utenza.copy()
        df.columns = df.columns.str.strip()

        utente = df[
            (df["username"] == username) &
            (df["password"].astype(str) == password) &
            (df["attivo"] == 1)
        ]

        if utente.empty:
            st.error("Credenziali errate o utente non attivo.")
            return None, None

        ruolo = utente.iloc[0]["ruolo"]
        username = utente.iloc[0]["username"]

        st.success(f"Accesso come {ruolo}. Benvenuto, {username}!")
        return ruolo, username




def main():
    df, df_soggetti, df_utenza = get_files_from_sharepoint()
    df = prepare_data(df)
    
    if 'df_full' not in st.session_state:
        st.session_state['df_full'] = df.copy()
    
    if "user" not in st.session_state:
        ruolo, username = authentication()
        if ruolo and username:
            st.session_state.user = {
                "ruolo": ruolo,
                "username": username
            }

            st.rerun()
        else:
            st.stop()

    user = st.session_state.user
    

    nav = get_navigator()
    
    if user["ruolo"] == "admin":
        home_admin(st.session_state['df_full'], nav, st.session_state['df_full'])
    elif user["ruolo"] == "team leader":
        home_Teamleader(st.session_state['df_full'], df_soggetti, nav)
    else:
        home_utente(st.session_state['df_full'], df_soggetti, nav)

    if hasattr(nav, 'file_buffer') and nav.file_buffer:
        with st.spinner("Caricamento Dati..."):
            nav.upload_file()

if __name__ == "__main__":
    main()