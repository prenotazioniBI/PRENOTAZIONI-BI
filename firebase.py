import firebase_admin
from firebase_admin import credentials, auth
import streamlit as st
import requests

# Inizializza Firebase Admin SDK una sola volta
def initialize_firebase():
    """Inizializza Firebase Admin SDK se non già inizializzato"""
    if not firebase_admin._apps:
        try:
            # Carica le credenziali da Streamlit secrets
            cred = credentials.Certificate({
                "type": st.secrets["firebase"]["type"],
                "project_id": st.secrets["firebase"]["project_id"],
                "private_key_id": st.secrets["firebase"]["private_key_id"],
                "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),
                "client_email": st.secrets["firebase"]["client_email"],
                "client_id": st.secrets["firebase"]["client_id"],
                "auth_uri": st.secrets["firebase"]["auth_uri"],
                "token_uri": st.secrets["firebase"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
            })
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            st.error(f"Errore inizializzazione Firebase: {e}")
            return False
    return True

def firebase_register(email, password):
    """Registra un nuovo utente su Firebase"""
    # Inizializza Firebase prima di usare auth
    if not initialize_firebase():
        return False, "Errore inizializzazione Firebase"
    
    try:
        user = auth.create_user(email=email, password=password)
        return True, "Registrazione avvenuta con successo"
    except Exception as e:
        return False, str(e)

def firebase_login(email, password):
    """Effettua il login tramite Firebase REST API"""
    try:
        api_key = st.secrets["FIREBASE_API_KEY"]
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            return True, resp.json()
        else:
            return False, resp.json().get("error", {}).get("message", "Errore di autenticazione")
    except Exception as e:
        return False, f"Errore connessione: {str(e)}"

def firebase_forgot_password(email):
    """Invia email di reset password"""
    try:
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={st.secrets['FIREBASE_API_KEY']}"
        payload = {"requestType": "PASSWORD_RESET", "email": email}
        resp = requests.post(url, json=payload)
        if resp.status_code == 200:
            return True, "Email di reset inviata!"
        else:
            return False, resp.json().get("error", {}).get("message", "Errore invio reset")
    except Exception as e:
        return False, f"Errore: {str(e)}"