import streamlit as st
from firebase import firebase_register, firebase_login, firebase_forgot_password



SPECIAL_USERS = {
    "filippo.strocchi@fbs.it": ("analista", "Filippo Strocchi"),
    "simona.tampelli@fbs.it": ("team leader", "Simona Tampelli"),
    "marco.gabelli@fbs.it": ("team leader", "Marco Gabelli"),
    "roberto.nicoli@fbs.it": ("team leader", "Roberto Nicoli"),
    "nicoletta.valanzano@fbs.it": ("team leader", "Nicoletta Valanzano"),
    "filippo.facibeni@fbs.it": ("admin", "Filippo Facibeni"),
    "ict@fbs.it": ("team leader", "ict")
}

def authentication():
    col1, col2, col3 = st.columns(3)
    with col2:
        st.title("Prenotazioni \n ### BI ~   Welcome letter ~ Diffide ~ Telegrammi")     
        menu = st.selectbox("Scegli azione", options=["Login", "Crea account", "Password dimenticata"])
        with st.form(key="login_form_unique"):
            email = st.text_input("Email Aziendale", placeholder="nome.cognome@fbs.it")
            password = None
            if menu == "Crea account":
                password = st.text_input("Crea Password", type="password")
            elif menu == "Login":
                password = st.text_input("Inserisci Password", type="password")
            submit = st.form_submit_button("Invia")
            if not submit:
                return None, None, None  

            email_norm = email.strip().lower()
            if not (email_norm.endswith("@fbs.it") or email_norm.endswith("@fbsnext.it")):
                st.error("Email non valida")
                return None, None, None  
                
            if menu == "Crea account":
                username_raw = email_norm.split("@")[0]
                if username_raw.endswith(".ext"):
                    username_raw = username_raw[:-4]
                username = username_raw.replace(".", " ").title()
                ok, msg = firebase_register(email_norm, password)
                if ok:
                    st.success(f"Registrato come: {username}")
                return None, None, None  

            elif menu == "Login":
                ok, user_info = firebase_login(email_norm, password)
                if ok:
                    if email_norm in SPECIAL_USERS:
                        ruolo, username = SPECIAL_USERS[email_norm]
                    else:
                        ruolo = "utente"
                        username_raw = email_norm.split("@")[0]
                        if username_raw.endswith(".ext"):
                            username_raw = username_raw[:-4]
                        username = username_raw.replace(".", " ").title()
                    
   
                    return ruolo, username, email_norm
                else:
                    st.error(user_info)
                return None, None, None  
                
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
                return None, None, None 