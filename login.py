import pandas as pd
import streamlit as st
from sharepoint_utils import SharePointNavigator
from main import get_files_from_sharepoint
def authentication():
    col1, col2, col3 = st.columns(3)
    with col2:
        _,_,df_utenza = get_files_from_sharepoint()
        st.title("Prenotazioni BI")
        with st.form(key="login_form_unique"):
            username = st.text_input("COGNOME NOME").strip()
            password = st.text_input("PASSWORD", type="password").strip()
            submit = st.form_submit_button("Login")

        if not submit:
            return None, None

        df = pd.read_excel(df_utenza)
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



