import streamlit as st
from firebase import firebase_register, firebase_login, firebase_forgot_password
import pandas as pd
import io

SPECIAL_USERS = {
    "filippo.strocchi@fbs.it": ("analista", "Filippo Strocchi"),
    "simona.tampelli@fbs.it": ("team leader", "Simona Tampelli"),
    "marco.gabelli@fbs.it": ("team leader", "Marco Gabelli"),
    "roberto.nicoli@fbs.it": ("team leader", "Roberto Nicoli"),
    "nicoletta.valanzano@fbs.it": ("team leader", "Nicoletta Valanzano"),
    "filippo.facibeni@fbs.it": ("admin", "Filippo Facibeni"),
    "ict@fbs.it": ("team leader", "ict")
}

def create_user_profile_on_sharepoint(email, username):
    """Crea il profilo utente su SharePoint creando i file Parquet"""
    try:
        from sharepoint_utils import SharePointNavigator
        
        # Configura SharePoint
        SITE_URL = st.secrets["SITE_URL"]
        TENANT_ID = st.secrets["TENANT_ID"]
        CLIENT_ID = st.secrets["CLIENT_ID"]
        CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
        LIBRARY_NAME = st.secrets["LIBRARY_NAME"]
        FOLDER_PATH = st.secrets["FOLDER_PATH"]
        DT_FOLDER_PATH = st.secrets["DT_FOLDER_PATH"]
        
        # Nome file basato su email
        safe_email = email.replace('@', '_').replace('.', '_')
        
        # Crea DataFrame vuoto per BI
        df_bi = pd.DataFrame({
            'PORTAFOGLIO': pd.Series(dtype='str'),
            'CENTRO DI COSTO': pd.Series(dtype='str'),
            'GESTORE': pd.Series(dtype='str'),
            'NDG DEBITORE': pd.Series(dtype='str'),
            'NOMINATIVO POSIZIONE': pd.Series(dtype='str'),
            'NDG NOMINATIVO RICERCATO': pd.Series(dtype='str'),
            'C.F.': pd.Series(dtype='str'),
            'SERVIZIO RICHIESTO': pd.Series(dtype='str'),
            'NOME SERVIZIO': pd.Series(dtype='str'),
            'PROVIDER': pd.Series(dtype='str'),
            'INVIATE AL PROVIDER': pd.Series(dtype='str'),
            'COSTO': pd.Series(dtype='float'),
            'MESE': pd.Series(dtype='Int64'),
            'ANNO': pd.Series(dtype='Int64'),
            'RIFATTURAZIONE': pd.Series(dtype='str'),
            'NOMINATIVO RICERCA': pd.Series(dtype='str'),
            'DATA RICHIESTA': pd.Series(dtype='str'),
            'id': pd.Series(dtype='int')
        })
        
        # Crea DataFrame vuoto per DT
        df_dt = pd.DataFrame({
            'PORTAFOGLIO': pd.Series(dtype='str'),
            'CENTRO DI COSTO': pd.Series(dtype='str'),
            'GESTORE': pd.Series(dtype='str'),
            'NDG DEBITORE': pd.Series(dtype='str'),
            'NOMINATIVO POSIZIONE': pd.Series(dtype='str'),
            'TIPOLOGIA DOCUMENTO': pd.Series(dtype='str'),
            'PROVIDER': pd.Series(dtype='str'),
            'COSTO': pd.Series(dtype='float'),
            'MESE': pd.Series(dtype='Int64'),
            'ANNO': pd.Series(dtype='Int64'),
            'DATA RICHIESTA': pd.Series(dtype='str'),
            'id': pd.Series(dtype='int')
        })
        
        # === UPLOAD FILE BI ===
        nav_bi = SharePointNavigator(
            SITE_URL, TENANT_ID, CLIENT_ID, CLIENT_SECRET, 
            LIBRARY_NAME, FOLDER_PATH
        )
        nav_bi.login()
        site_id_bi = nav_bi.get_site_id()
        drive_id_bi, _ = nav_bi.get_drive_id(site_id_bi)
        
        # Converti in bytes
        buffer_bi = io.BytesIO()
        df_bi.to_parquet(buffer_bi, index=False)
        buffer_bi.seek(0)
        
        # Upload file BI
        file_path_bi = f"{FOLDER_PATH}/{safe_email}_prenotazioni.parquet"
        success_bi = nav_bi.upload_file_direct(
            site_id_bi, drive_id_bi, file_path_bi, buffer_bi.getvalue()
        )
        
        if not success_bi:
            return False, "Errore upload file BI"
        
        # === UPLOAD FILE DT ===
        nav_dt = SharePointNavigator(
            SITE_URL, TENANT_ID, CLIENT_ID, CLIENT_SECRET,
            LIBRARY_NAME, DT_FOLDER_PATH
        )
        nav_dt.login()
        site_id_dt = nav_dt.get_site_id()
        drive_id_dt, _ = nav_dt.get_drive_id(site_id_dt)
        
        # Converti in bytes
        buffer_dt = io.BytesIO()
        df_dt.to_parquet(buffer_dt, index=False)
        buffer_dt.seek(0)
        
        # Upload file DT
        file_path_dt = f"{DT_FOLDER_PATH}/{safe_email}_dt.parquet"
        success_dt = nav_dt.upload_file_direct(
            site_id_dt, drive_id_dt, file_path_dt, buffer_dt.getvalue()
        )
        
        if not success_dt:
            return False, "Errore upload file DT"
        
        return True, f"Profilo creato: {safe_email}_prenotazioni.parquet e {safe_email}_dt.parquet"
        
    except Exception as e:
        return False, f"Errore creazione profilo: {str(e)}"

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
            
            # Validazione email
            if not (email_norm.endswith("@fbs.it") or email_norm.endswith("@fbsnext.it")):
                st.error("❌ Email non valida. Usa un'email aziendale @fbs.it o @fbsnext.it")
                st.stop()
                
            if menu == "Crea account":
                # Validazione password
                if not password or len(password) < 6:
                    st.error("❌ La password deve essere di almeno 6 caratteri")
                    st.stop()
                
                username_raw = email_norm.split("@")[0]
                if username_raw.endswith(".ext"):
                    username_raw = username_raw[:-4]
                username = username_raw.replace(".", " ").title()
                
                # Mostra progress
                with st.status("Creazione account in corso...", expanded=True) as status:
                    st.write("🔐 Registrazione su Firebase...")
                    
                    # Registra su Firebase
                    ok, msg = firebase_register(email_norm, password)
                    
                    if not ok:
                        st.error(f"❌ Errore registrazione Firebase: {msg}")
                        status.update(label="❌ Registrazione fallita", state="error")
                        st.stop()
                    
                    st.write("✅ Firebase OK")
                    st.write("📁 Creazione profilo su SharePoint...")
                    
                    # Crea profilo su SharePoint
                    profile_ok, profile_msg = create_user_profile_on_sharepoint(email_norm, username)
                    
                    if profile_ok:
                        st.write(f"✅ SharePoint OK")
                        status.update(label="✅ Account creato con successo!", state="complete")
                        st.success(f"🎉 Benvenuto {username}! Ora puoi effettuare il login.")
                        st.balloons()
                    else:
                        st.warning(f"⚠️ Account Firebase creato ma errore SharePoint: {profile_msg}")
                        status.update(label="⚠️ Registrazione parziale", state="error")
                
                st.stop()

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
                    st.error(f"❌ {user_info}")
                    st.stop()
                
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
                st.stop()