import pandas as pd
import streamlit as st
import unicodedata
import re

def _normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.strip().lower()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def filtro_cf(df, key_suffix=""):
    if df is None or df.empty or "C.F." not in df.columns:
        return df
    cf_input = st.text_input("Filtra per CF", key=f"cf_{key_suffix}")
    if cf_input:
        df = df[df["C.F."].astype(str).str.contains(cf_input, case=False, na=False)]
    return df

def filtro_data(df, key_suffix="test"):
    date_col = pd.to_datetime(df["INVIATE AL PROVIDER"], dayfirst=True, errors="coerce")
    valid_dates = date_col.dropna()
    
    if len(valid_dates) == 0:
        return df
    
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    selected_date = st.date_input(
        "Inviate al provider",
        value=None,
        min_value=min_date,
        max_value=max_date,
        key=f"data_picker_{key_suffix}"
    )
    if selected_date:
        mask = date_col.dt.date == selected_date
        df = df[mask]
    return df

def filtro_data_evasione(df, key_suffix=""):
    if df is None or df.empty or "INVIATE AL PROVIDER" not in df.columns:
        return df
    date_col = pd.to_datetime(df["INVIATE AL PROVIDER"], dayfirst=True, errors="coerce")
    valid_dates = date_col.dropna()
    
    if len(valid_dates) == 0:
        return df
    
    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()
    selected_date = st.date_input(
        "Data evasione",
        value=None,
        min_value=min_date,
        max_value=max_date,
        key=f"data_evasione_{key_suffix}"
    )
    if selected_date:
        mask = date_col.dt.date == selected_date
        df = df[mask]
    return df

# CORREZIONE: Nuovo filtro per stato provider
def filtro_stato_provider(df, key_suffix=""):
    if df is None or df.empty or "INVIATE AL PROVIDER" not in df.columns:
        return df
    
    options = ["Tutte", "SOSPESO", "INVIATO"]
    stato_input = st.selectbox("Stato Provider", options=options, key=f"stato_provider_{key_suffix}")
    
    if stato_input == "SOSPESO":
        df = df[df["INVIATE AL PROVIDER"].isnull()]
    elif stato_input == "INVIATO":
        df = df[df["INVIATE AL PROVIDER"].notnull()]
    # Se "Tutte" non filtra nulla
    
    return df

def filtro_evaso(df, key_suffix=""):
    if df is None or df.empty or "INVIATE AL PROVIDER" not in df.columns:
        return df
    option_map = {0: "EVASE", 1: "SOSPESO"}
    selezione = st.pills("", options=option_map.keys(), format_func=lambda x: option_map[x], selection_mode="single", key=f"evaso_{key_suffix}")
    if selezione == 0:
        return df[df["INVIATE AL PROVIDER"].notnull()]
    elif selezione == 1:
        return df[df["INVIATE AL PROVIDER"].isnull()]
    return df

def filtro_massivo_singolo(df, key_suffix=""):
    if df is None or df.empty or "SERVIZIO RICHIESTO" not in df.columns:
        return df
    option_map = {0: "SINGOLE GESTORE", 1: "MASSIVE"}
    selezione = st.pills("", options=option_map.keys(), format_func=lambda x: option_map[x], selection_mode="single", key=f"massivo_{key_suffix}")
    if selezione == 0:
        return df[df["SERVIZIO RICHIESTO"] == "Richiesta singola gestore"]
    elif selezione == 1:
        return df[df["SERVIZIO RICHIESTO"] != "Richiesta singola gestore"]
    return df

def filtro_gestore(df, key_suffix=""):
    if df is None or df.empty or "GESTORE" not in df.columns:
        return df
    gestore_input = st.text_input("Filtra per Gestore", key=f"gestore_{key_suffix}")
    if gestore_input:
        df = df[df["GESTORE"].astype(str).str.contains(gestore_input, case=False, na=False)]
    return df

def filtro_portafoglio(df, key_suffix=""):
    if df is None or df.empty or "PORTAFOGLIO" not in df.columns:
        return df
    portafoglio_input = st.text_input("Filtra per Portafoglio", key=f"portafoglio_{key_suffix}")
    if portafoglio_input:
        df = df[df["PORTAFOGLIO"].astype(str).str.contains(portafoglio_input, case=False, na=False)]
    return df

def filtro_servizio_dt(df, key_suffix=""):
    if df is None or df.empty or "TIPOLOGIA DOCUMENTO" not in df.columns:
        return df

    tipologie_disponibili = df["TIPOLOGIA DOCUMENTO"].dropna().unique()
    
    options = ["Tutte"]
    has_diffida = any("DIFFIDA" in str(tip).upper() or "DIFFDA" in str(tip).upper() 
                     for tip in tipologie_disponibili)
    if has_diffida:
        options.append("Diffida")
    has_welcome = any("WELCOME" in str(tip).upper() or "WL" in str(tip).upper() 
                     for tip in tipologie_disponibili)
    if has_welcome:
        options.append("Welcome Letter")
    has_combo = any("+" in str(tip) or "E" in str(tip).upper() 
                   for tip in tipologie_disponibili)
    if has_combo:
        options.append("Diffida + Welcome Letter")
    
    servizio_input = st.selectbox("Filtra per richieste", options=options, key=f"richieste_{key_suffix}")
    
    if servizio_input and servizio_input.lower() != "tutte":
        if servizio_input == "Diffida":
            mask = (df["TIPOLOGIA DOCUMENTO"].astype(str).str.contains("DIFFIDA|DIFFDA", case=False, na=False)) & \
                   (~df["TIPOLOGIA DOCUMENTO"].astype(str).str.contains("WL|WELCOME", case=False, na=False))
        elif servizio_input == "Welcome Letter":
            mask = (df["TIPOLOGIA DOCUMENTO"].astype(str).str.contains("WL|WELCOME", case=False, na=False)) & \
                   (~df["TIPOLOGIA DOCUMENTO"].astype(str).str.contains("DIFFIDA|DIFFDA", case=False, na=False))
        elif servizio_input == "Diffida + Welcome Letter":
            mask = (df["TIPOLOGIA DOCUMENTO"].astype(str).str.contains("DIFFIDA|DIFFDA", case=False, na=False)) & \
                   (df["TIPOLOGIA DOCUMENTO"].astype(str).str.contains("WL|WELCOME", case=False, na=False))
        else:
            mask = df["TIPOLOGIA DOCUMENTO"].astype(str).str.contains(servizio_input, case=False, na=False)
        
        df = df[mask]
    
    return df

def filtro_servizio(df, key_suffix=""):
    if df is None or df.empty or "NOME SERVIZIO" not in df.columns:
        return df
    options = [
        "Tutte",
        "INFO LAVORATIVA FULL",
        "RICERCA ANAGRAFICA",
        "RICERCA TELEFONICA",
        "RICERCA ANAGRAFICA + TELEFONO",
        "RINTRACCIO CONTO CORRENTE",
        "RINTRACCIO EREDI",
        "DD PERSONE GIURIDICHE",
        "RICERCA EREDI ACCETTANTI",
        "VISURA CAMERALE",
        "DD PERSONE FISICHE"
    ]
    servizio_input = st.selectbox("Filtra per richieste", options=options, key=f"richieste_{key_suffix}")
    if not servizio_input or servizio_input.lower() == "tutte":
        return df
    sel_norm = _normalize_text(servizio_input)
    df["_svc_norm"] = df["NOME SERVIZIO"].astype(str).apply(_normalize_text)
    mask = df["_svc_norm"].str.contains(re.escape(sel_norm), na=False)
    df = df[mask].copy()
    df = df.drop(columns=["_svc_norm"], errors="ignore")
    return df

def mostra_df_filtrato_utente(df):
    if df is None or df.empty:
        st.warning("Nessun dato disponibile")
        return pd.DataFrame()
    
    df = df.copy()
    user = st.session_state.get("user", {})
    
    if "GESTORE" in df.columns and user.get("username"):
        username_norm = user["username"].replace(" ", "").lower()
        df = df[df["GESTORE"].astype(str).str.replace(" ", "").str.lower() == username_norm]
    
    columns = ["C.F.", "PORTAFOGLIO", "NOMINATIVO POSIZIONE", "NDG DEBITORE", "NOMINATIVO RICERCA", "NOME SERVIZIO", "DATA RICHIESTA", "INVIATE AL PROVIDER", "COSTO"]
    existing_columns = [col for col in columns if col in df.columns]
    df = df[existing_columns].copy()
    
    col1, col2 = st.columns(2)
    with col1:
        df = filtro_data(df, key_suffix="utente_data")
    with col2:
        df = filtro_cf(df, key_suffix="utente_cf")
    
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True, height=500)
    return df

def mostra_df_filtrato(df):
    if df is None or df.empty:
        st.warning("Nessun dato disponibile")
        return pd.DataFrame()
    
    df = df.copy()
    if "INVIATE AL PROVIDER" in df.columns:
        df = df[df["INVIATE AL PROVIDER"].isnull()]
    
    columns = ["C.F.", "GESTORE", "PORTAFOGLIO", "NOMINATIVO POSIZIONE", "NDG DEBITORE", "NOMINATIVO RICERCA", "NOME SERVIZIO", "DATA RICHIESTA"]
    existing_columns = [col for col in columns if col in df.columns]
    df = df[existing_columns].copy()
    
    if "DATA RICHIESTA" in df.columns:
        df = df[df["DATA RICHIESTA"].notnull()]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        df = filtro_cf(df, key_suffix="admin_cf")
    with col2:
        df = filtro_gestore(df, key_suffix="admin_gestore")
    with col3:
        df = filtro_portafoglio(df, key_suffix="admin_portafoglio")
    
    df = filtro_data(df, key_suffix="admin_data")
    
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True, height=500)
    return df

def mostra_df_filtrato_home_admin(df):
    if df is None or df.empty:
        st.warning("Nessun dato disponibile")
        return pd.DataFrame()
    
    df = df.copy()
    if "COSTO" in df.columns:
        df["COSTO"] = df["COSTO"].fillna("").astype(str)
    
    df = filtro_evaso(df, key_suffix="home_admin_evaso")
    if df is None:
        return pd.DataFrame()
    
    df = filtro_massivo_singolo(df, key_suffix="home_admin_gnuo")
    if df is None:
        return pd.DataFrame()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        df = filtro_cf(df, key_suffix="home_admin_cf")
        if df is None:
            return pd.DataFrame()
    with col2:
        df = filtro_gestore(df, key_suffix="home_admin_gestore")
        if df is None:
            return pd.DataFrame()
    with col3:
        df = filtro_portafoglio(df, key_suffix="home_admin_portafoglio")
        if df is None:
            return pd.DataFrame()
    with col4:
        df = filtro_servizio(df, key_suffix="home_admin_servizio")
        if df is None:
            return pd.DataFrame()
    
    col1, col2 = st.columns(2)
    with col1:
        df = filtro_data(df, key_suffix="home_admin_data")
        if df is None:
            return pd.DataFrame()
    with col2:
        df = filtro_data_evasione(df, key_suffix="home_admin_data_evasione")
        if df is None:
            return pd.DataFrame()
    
    if df is None:
        return pd.DataFrame()
    return df
def mostra_df_completo_dt(df_dt, key_suffix=""):
    """Visualizza tutto il DataFrame delle richieste con filtri opzionali"""
    if df_dt is None or df_dt.empty:
        st.warning("Nessun dato disponibile")
        return pd.DataFrame()
    
    df_dt = df_dt.copy()
    
    # Pulizia colonne numeriche
    if 'NDG DEBITORE' in df_dt.columns:
        df_dt['NDG DEBITORE'] = df_dt['NDG DEBITORE'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    
    if 'NDG NOMINATIVO RICERCATO' in df_dt.columns:
        df_dt['NDG NOMINATIVO RICERCATO'] = df_dt['NDG NOMINATIVO RICERCATO'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    
    if 'NUMERO CIVICO' in df_dt.columns:
        df_dt['NUMERO CIVICO'] = df_dt['NUMERO CIVICO'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    
    if 'CAP' in df_dt.columns:
        df_dt['CAP'] = df_dt['CAP'].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', '')
    
    # Aggiungi i 4 filtri
    col1, col2, col3, col4 = st.columns([0.25, 0.25, 0.25, 0.25])
    
    with col1:
        df_dt = filtro_gestore(df_dt, key_suffix=f"completo_gestore_dt_{key_suffix}")
        if df_dt is None or df_dt.empty:
            return pd.DataFrame()
    with col2:
        df_dt = filtro_portafoglio(df_dt, key_suffix=f"completo_portafoglio_dt_{key_suffix}")
        if df_dt is None or df_dt.empty:
            return pd.DataFrame()
    with col3:
        df_dt = filtro_servizio_dt(df_dt, key_suffix=f"completo_servizio_dt_{key_suffix}")
        if df_dt is None or df_dt.empty:
            return pd.DataFrame()
    with col4:
        df_dt = filtro_stato_provider(df_dt, key_suffix=f"completo_stato_dt_{key_suffix}")
        if df_dt is None or df_dt.empty:
            return pd.DataFrame()
    
    # Filtro DATA RICHIESTA (da gennaio 2026 in poi)
    if "DATA RICHIESTA" in df_dt.columns:
        date_col = pd.to_datetime(df_dt["DATA RICHIESTA"], dayfirst=True, errors="coerce")
        valid_dates = date_col.dropna()
        
        if len(valid_dates) > 0:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            
            from datetime import date
            default_date = date(2026, 1, 1)
            
            selected_date = st.date_input(
                "Data Richiesta (da)",
                value=default_date,
                min_value=min_date,
                max_value=max_date,
                key=f"data_richiesta_completo_{key_suffix}"
            )
            
            if selected_date:
                mask = date_col.dt.date >= selected_date
                df_dt = df_dt[mask]
    
    # Rimuovi le colonne non desiderate
    colonne_da_escludere = ["UTP/NPL", "PROVIDER", "id", "MESE", "NUMERO CIVICO", "PEC", "COSTO", "ANNO", "CENTRO DI COSTO"]
    df_dt = df_dt.drop(columns=[col for col in colonne_da_escludere if col in df_dt.columns])
    
    # Visualizza il DataFrame con i filtri applicati
    if df_dt is not None and not df_dt.empty:
        st.dataframe(df_dt, use_container_width=True, height=2000)
    else:
        st.warning("Nessun dato corrisponde ai filtri selezionati")
    
    return df_dt



def mostra_df_filtrato_home_admin_dt(df_dt, key_suffix=""):
    if df_dt is None or df_dt.empty:
        colonne_attese = [
            "PORTAFOGLIO",
            "NDG DEBITORE", 
            "NOMINATIVO POSIZIONE",
            "RAPPORTO",
            "NDG NOMINATIVO RICERCATO",
            "GBV ATTUALE",
            "DESTINATARIO",
            "GESTORE",
            "TELEFONO GESTORE",
            "EMAIL GESTORE",
            "DATA RICHIESTA",
            "INVIATE AL PROVIDER",
            "TIPO LUOGO",
            "SIGLA",
            "REGIONE",
            "PEC DESTINATARIO",
            "INDIRIZZO",
            "NUMERO CIVICO",
            "CITTA",
            "CAP",
            "PROVINCIA",
            "TIPOLOGIA DOCUMENTO",
            "MODALITA INVIO",
            "ORIGINATOR",
            "id"
        ]
        df_dt = pd.DataFrame(columns=colonne_attese)
    
    if 'NDG DEBITORE' in df_dt.columns:
        df_dt['NDG DEBITORE'] = df_dt['NDG DEBITORE'].astype(str)
        df_dt['NDG DEBITORE'] = df_dt['NDG DEBITORE'].str.replace(r'\.0$', '', regex=True)
        df_dt['NDG DEBITORE'] = df_dt['NDG DEBITORE'].replace('nan', '')
    
    if 'NDG NOMINATIVO RICERCATO' in df_dt.columns:
        df_dt['NDG NOMINATIVO RICERCATO'] = df_dt['NDG NOMINATIVO RICERCATO'].astype(str)
        df_dt['NDG NOMINATIVO RICERCATO'] = df_dt['NDG NOMINATIVO RICERCATO'].str.replace(r'\.0$', '', regex=True)
        df_dt['NDG NOMINATIVO RICERCATO'] = df_dt['NDG NOMINATIVO RICERCATO'].replace('nan', '')
    
    if 'NUMERO CIVICO' in df_dt.columns:
        df_dt['NUMERO CIVICO'] = df_dt['NUMERO CIVICO'].astype(str)
        df_dt['NUMERO CIVICO'] = df_dt['NUMERO CIVICO'].str.replace(r'\.0$', '', regex=True)
        df_dt['NUMERO CIVICO'] = df_dt['NUMERO CIVICO'].replace('nan', '')
    
    if 'CAP' in df_dt.columns:
        df_dt['CAP'] = df_dt['CAP'].astype(str)
        df_dt['CAP'] = df_dt['CAP'].str.replace(r'\.0$', '', regex=True)
        df_dt['CAP'] = df_dt['CAP'].replace('nan', '')
    col1, col2, col3, col4 = st.columns([0.25, 0.25, 0.25, 0.25])
    
    with col1:
        df_dt = filtro_gestore(df_dt, key_suffix=f"home_admin_gestore_dt_{key_suffix}")
        if df_dt is None:
            return pd.DataFrame()
    with col2:
        df_dt = filtro_portafoglio(df_dt, key_suffix=f"home_admin_portafoglio_dt_{key_suffix}")
        if df_dt is None:
            return pd.DataFrame()
    with col3:
        df_dt = filtro_servizio_dt(df_dt, key_suffix=f"home_admin_servizio_dt_{key_suffix}")
        if df_dt is None:
            return pd.DataFrame()
    with col4:
        df_dt = filtro_stato_provider(df_dt, key_suffix=f"home_admin_stato_dt_{key_suffix}")
        if df_dt is None:
            return pd.DataFrame()
    
    col1, col2 = st.columns(2)
    with col1:
        if "DATA RICHIESTA" in df_dt.columns:
            date_col = pd.to_datetime(df_dt["DATA RICHIESTA"], dayfirst=True, errors="coerce")
            valid_dates = date_col.dropna()
            
            if len(valid_dates) > 0:
                min_date = valid_dates.min().date()
                max_date = valid_dates.max().date()
                selected_date = st.date_input(
                    "Data Richiesta",
                    value=None,
                    min_value=min_date,
                    max_value=max_date,
                    key=f"data_richiesta_{key_suffix}"
                )
                if selected_date:
                    mask = date_col.dt.date == selected_date
                    df_dt = df_dt[mask]
        
    with col2:
        df_dt = filtro_data_evasione(df_dt, key_suffix=f"home_admin_data_evasione_dt_{key_suffix}")
        if df_dt is None:
            return pd.DataFrame()
    
    if df_dt is None:
        return pd.DataFrame()
    return df_dt