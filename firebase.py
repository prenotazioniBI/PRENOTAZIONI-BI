from firebase_admin import auth
import streamlit as st
import requests


def firebase_register(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        return True, "Registrazione avvenuta con successo"
    except Exception as e:
        return False, str(e)

def firebase_login(email, password):
    import requests
    api_key = st.secrets["FIREBASE_API_KEY"]  # Inserisci la tua API KEY di Firebase in .streamlit/secrets.toml
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
    


def firebase_forgot_password(email):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={st.secrets['FIREBASE_API_KEY']}"
    payload = {"requestType": "PASSWORD_RESET", "email": email}
    resp = requests.post(url, json=payload)
    if resp.status_code == 200:
        return True, "Email di reset inviata!"
    else:
        return False, resp.json().get("error", {}).get("message", "Errore invio reset")