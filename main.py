import streamlit as st
from home_utente import home_utente
from home_leader import home_Teamleader
from home_analista import home_analista
import pandas as pd
from sharepoint_utils import SharePointNavigator
import io
from home_admin import home_admin
from firebase_admin import credentials
import firebase_admin
from firebase import firebase_register, firebase_login, firebase_forgot_password


if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase_key"]))
    firebase_admin.initialize_app(cred)


st.set_page_config(page_title="Prenotazioni BI",page_icon="👤",layout="wide")


TENANT_ID = st.secrets["TENANT_ID"]
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]


@st.cache_data(show_spinner="Scarico dati da Sharepoint...")  
def get_files_from_sharepoint():
    nav = SharePointNavigator(TENANT_ID, CLIENT_ID, CLIENT_SECRET)
    nav.login()
    site_id = nav.get_site_id()
    drive_id, _ = nav.get_drive_id(site_id)
    
    prenotazioni_data = nav.download_file(site_id, drive_id, "General/PRENOTAZIONI_BI/prenotazioni.parquet")
    soggetti_data = nav.download_file(site_id, drive_id, "General/PRENOTAZIONI_BI/soggetti.parquet")
    utenza = nav.download_file(site_id, drive_id, "General/PRENOTAZIONI_BI/utenza.xlsx")
    

    df_utenza = pd.read_excel(io.BytesIO(utenza["content"]))
    df = pd.read_parquet(io.BytesIO(prenotazioni_data['content']))
     
        
    if 'id' not in df.columns:
        df.insert(0, 'id', range(len(df)))


    df_soggetti = pd.read_parquet(io.BytesIO(soggetti_data['content']))
    
    return df, df_soggetti, df_utenza

def prepare_data(df):
    colonne = [
        "PORTAFOGLIO", "CENTRO DI COSTO", "GESTORE", "NDG DEBITORE", "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO", "C.F.", "SERVIZIO RICHIESTO", "NOME SERVIZIO", "PROVIDER",
        "INVIATE AL PROVIDER", "COSTO", "MESE", "ANNO", "RIFATTURAZIONE", "NOMINATIVO RICERCA",
        "DATA RICHIESTA"
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


SPECIAL_USERS = {
    "filippo.strocchi@fbs.it": ("analista", "Filippo Strocchi"),
    "simona.tampelli@fbs.it":   ("team leader", "Simona Tampelli"),
    "marco.gabelli@fbs.it":     ("team leader", "Marco Gabelli"),
    "roberto.nicoli@fbs.it":    ("team leader", "Roberto Nicoli"),
    "nicoletta.valanzano@fbs.it": ("team leader", "Nicoletta Valanzano"),
    "filippo.facibeni@fbs.it":  ("admin", "Filippo Facibeni"),
    "ict@fbs.it":  ("admin", "ict")
}

def authentication():
    col1, col2, col3 = st.columns(3)
    with col2:
        st.title("Prenotazioni BI")     
        menu = st.selectbox("Scegli azione", options=["Login", "Crea account", "Password dimenticata"])
        with st.form(key="login_form_unique"):
            email = st.text_input("Email Aziendale", placeholder="nome.cognome@fbs.it")
            password = None
            if menu == "Crea account":
                password = st.text_input("Crea Password", type="password")
            elif menu == "Login":
                password = st.text_input("Inserisci Password", type="password")
            # Nessun campo password per "Password dimenticata"
            submit = st.form_submit_button("Invia")
            if not submit:
                return None, None

            email_norm = email.strip().lower()
            if not email_norm.endswith("@fbs.it"):
                st.error("Email non valida")
                return None, None

            if menu == "Crea account":
                username = email_norm.split("@")[0].replace(".", " ").title()
                ok, msg = firebase_register(email_norm, password)
                if ok:
                    st.success(f" Registrato come: {username}")
                else:
                    st.error(msg)
                return None, None

            elif menu == "Login":
                ok, user_info = firebase_login(email_norm, password)
                if ok:
                    if email_norm in SPECIAL_USERS:
                        ruolo, username = SPECIAL_USERS[email_norm]
                    else:
                        ruolo = "utente"
                        username = email_norm.split("@")[0].replace(".", " ").title()
                    return ruolo, username
                else:
                    st.error(user_info)
                return None, None
            elif menu == "Password dimenticata":
                ok, msg = firebase_forgot_password(email_norm)
                if ok:
                    st.success(msg + " Controlla la tua casella email e la sezione spam (potrebbero volerci alcuni minuti).")
                    st.markdown(
                        f"""
                        **Non hai ricevuto la mail?**
                        [Clicca qui per ricevere supporto](mailto:filippo.facibeni@fbs.it?subject=Recupero%20password%20Prenotazioni%20BI&body=Non%20ho%20ricevuto%20la%20mail%20di%20reset%20password%20per%20l'account:%20{email_norm}.)
                        """
                    )
                else:
                    st.error(msg)
                return None, None
def main():
    df, df_soggetti, df_utenza = get_files_from_sharepoint()
    df = prepare_data(df)
    
    # Genera sempre la colonna id come progressivo
    df["id"] = range(1, len(df) + 1)
    
    # Conversione tipi colonne
    df["COSTO"] = pd.to_numeric(df["COSTO"], errors="coerce")
    df["MESE"] = pd.to_numeric(df["MESE"], errors="coerce").astype("Int64")
    df["ANNO"] = pd.to_numeric(df["ANNO"], errors="coerce").astype("Int64")
    if "N. RICHIESTE" in df.columns:
        df["N. RICHIESTE"] = pd.to_numeric(df["N. RICHIESTE"], errors="coerce").astype("Int64")
    if "TOT POSIZIONI" in df.columns:
        df["TOT POSIZIONI"] = pd.to_numeric(df["TOT POSIZIONI"], errors="coerce").astype("Int64")
    if "INVIATE AL PROVIDER" in df.columns:
        df["INVIATE AL PROVIDER"] = pd.to_datetime(df["INVIATE AL PROVIDER"], errors="coerce", dayfirst=True)
    if "DATA RICHIESTA" in df.columns:
        df["DATA RICHIESTA"] = pd.to_datetime(df["DATA RICHIESTA"], errors="coerce", dayfirst=True)

    if 'df_full' not in st.session_state:
        st.session_state['df_full'] = df.copy()
    
    if "user" not in st.session_state:
        ruolo, username = authentication()
        if ruolo and username:
            st.session_state.user = {
                "ruolo": ruolo,
                "username": username
            }
            st.cache_data.clear()
            st.rerun()
        else:
            st.stop()

    user = st.session_state.user
    

    nav = get_navigator()
    
    if user["ruolo"] == "admin":
        home_admin(st.session_state['df_full'], df_soggetti, nav, st.session_state['df_full'])
    elif user["ruolo"] == "team leader":
        home_Teamleader(st.session_state['df_full'], df_soggetti, nav)
    elif user["ruolo"] == "analista":
        home_analista(st.session_state['df_full'], nav, st.session_state['df_full'])
    else:
        home_utente(st.session_state['df_full'], df_soggetti, nav)

    if hasattr(nav, 'file_buffer') and nav.file_buffer:
        with st.spinner("Caricamento Dati..."):
            nav.upload_file()

if __name__ == "__main__":
    main()
