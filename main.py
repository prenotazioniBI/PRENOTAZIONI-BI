import streamlit as st
import pandas as pd
import io
from sharepoint_utils import SharePointNavigator
from app import MultiApp

st.set_page_config(page_title="Prenotazioni", page_icon="👤", layout="wide")

SITE_URL = st.secrets["SITE_URL"]
TENANT_ID = st.secrets["TENANT_ID"]
CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
LIBRARY_NAME = st.secrets["LIBRARY_NAME"]
FOLDER_PATH = st.secrets["FOLDER_PATH"]
DT_FOLDER_PATH = st.secrets["DT_FOLDER_PATH"]

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

@st.cache_data(show_spinner="Scarico dati da Sharepoint...")
def get_files_from_sharepoint():
    nav = SharePointNavigator(
        SITE_URL,
        TENANT_ID,
        CLIENT_ID,
        CLIENT_SECRET,
        LIBRARY_NAME,
        FOLDER_PATH,
    )
    nav.login()
    site_id = nav.get_site_id()
    drive_id, _ = nav.get_drive_id(site_id)
    
    nav_dt = SharePointNavigator(
        SITE_URL,
        TENANT_ID,
        CLIENT_ID,
        CLIENT_SECRET,
        LIBRARY_NAME,
        DT_FOLDER_PATH  
    )
    nav_dt.login()
    site_id_dt = nav_dt.get_site_id()
    drive_id_dt, _ = nav_dt.get_drive_id(site_id_dt)

    prenotazioni_data = nav.download_file(site_id, drive_id, f"{FOLDER_PATH}/prenotazioni.parquet")
    soggetti_data = nav.download_file(site_id, drive_id, f"{FOLDER_PATH}/soggetti.parquet")
    utenza = nav.download_file(site_id, drive_id, f"{FOLDER_PATH}/utenza.xlsx")
    dt_soggetti_data = nav_dt.download_file(site_id_dt, drive_id_dt, f"{DT_FOLDER_PATH}/dt_soggetti.parquet")
    dt_data = nav_dt.download_file(site_id_dt, drive_id_dt, f"{DT_FOLDER_PATH}/dt.parquet")

    df_utenza = pd.read_excel(io.BytesIO(utenza["content"]))
    df = pd.read_parquet(io.BytesIO(prenotazioni_data['content']))
    df_soggetti = pd.read_parquet(io.BytesIO(soggetti_data['content']))
    df_dt = pd.read_parquet(io.BytesIO(dt_data['content']))
    dt_soggetti = pd.read_parquet(io.BytesIO(dt_soggetti_data['content']))
        
    if 'id' not in df.columns:
        df['id'] = range(1, len(df) + 1)
    
    if 'id' not in df_dt.columns:
        df_dt['id'] = range(1, len(df_dt) + 1)
    
    return df, df_soggetti, df_utenza, df_dt, dt_soggetti

def get_navigator():
    nav = SharePointNavigator(
        SITE_URL,
        TENANT_ID,
        CLIENT_ID,
        CLIENT_SECRET,
        LIBRARY_NAME,
        FOLDER_PATH
    )
    nav.login()
    return nav

def get_navigator_dt():
    nav_dt = SharePointNavigator(
        SITE_URL,
        TENANT_ID,
        CLIENT_ID,
        CLIENT_SECRET,
        LIBRARY_NAME,
        DT_FOLDER_PATH
    )
    nav_dt.login()
    return nav_dt

def initialize_data():
    df, df_soggetti, df_utenza, df_dt, dt_soggetti = get_files_from_sharepoint()
    df = prepare_data(df)
    
    df["id"] = range(1, len(df) + 1)
    df_dt["id"] = range(1, len(df_dt) + 1)
    
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
    if "NDG DEBITORE" in df_dt.columns:
        df_dt["NDG DEBITORE"] = df_dt['NDG DEBITORE'].astype(str)
    if "COSTO" in df_dt.columns:
        df_dt["COSTO"] = pd.to_numeric(df_dt["COSTO"], errors="coerce")
    if "MESE" in df_dt.columns:
        df_dt["MESE"] = pd.to_numeric(df_dt["MESE"], errors="coerce").astype("Int64")
    if "ANNO" in df_dt.columns:
        df_dt["ANNO"] = pd.to_numeric(df_dt["ANNO"], errors="coerce").astype("Int64")
    if "DATA RICHIESTA" in df_dt.columns:
        df_dt["DATA RICHIESTA"] = pd.to_datetime(df_dt["DATA RICHIESTA"], errors="coerce", dayfirst=True)
    
    
    if "TIPOLOGIA DOCUMENTO" not in df_dt.columns and "NOME SERVIZIO" in df_dt.columns:
        df_dt = df_dt.rename(columns={"NOME SERVIZIO": "TIPOLOGIA DOCUMENTO"})
    
    df = prepare_data(df)
    
    st.session_state['df_full'] = df
    st.session_state['df_soggetti'] = df_soggetti
    st.session_state['df_utenza'] = df_utenza
    st.session_state['df_dt_full'] = df_dt if not df_dt.empty else pd.DataFrame()
    st.session_state['dt_soggetti'] = dt_soggetti
    st.session_state['navigator'] = get_navigator()
    st.session_state['navigator_dt'] = get_navigator_dt()

def main():
    if 'df_full' not in st.session_state:
        initialize_data()
    
    MultiApp.main()

if __name__ == "__main__":
    main()

