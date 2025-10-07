import pandas as pd
import streamlit as st
import datetime
import io
def filtro_cf(df, key_suffix=""):
    cf_input = st.text_input("Filtra per Codice Fiscale o p.iva", key=f"cf_{key_suffix}")
    if cf_input:
        df = df[df["C.F."].astype(str).str.contains(cf_input, case=False, na=False)]
    return df

def filtro_data(df, key_suffix=""):
    date_col = pd.to_datetime(df["DATA RICHIESTA"], dayfirst=True, errors="coerce")
    valid_dates = date_col.dropna()
    
    if len(valid_dates) > 0:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
        
        selected_date = st.date_input(
            "DATA RICHIESTA GESTIONE (lascia vuoto per tutte)",
            value=None,
            min_value=min_date,
            max_value=max_date,
            key=f"data_picker_{key_suffix}"
        )
        if selected_date:
            mask = date_col.dt.date == selected_date
            df = df[mask]
    else:
        st.info("Nessuna data valida trovata nelle richieste.")
    return df

def filtro_data_evasione(df, key_suffix=""):
    date_col = pd.to_datetime(df["INVIATE AL PROVIDER"], dayfirst=True, errors="coerce")
    valid_dates = date_col.dropna()
    
    if len(valid_dates) > 0:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()
        
        selected_date = st.date_input(
            "DATA EVASIONE (lascia vuoto per tutte)",
            value=None,
            min_value=min_date,
            max_value=max_date,
            key=f"data_evasione_{key_suffix}"
        )
        if selected_date:
            mask = date_col.dt.date == selected_date
            df = df[mask]
    else:
        st.info("Nessuna data valida trovata nelle richieste.")
    return df

def filtro_evaso(df, key_suffix=""):
    option_map = {
        0: "EVASE",
        1: "SOSPESO"
    }
    selezione = st.pills(
        "",
        options=option_map.keys(),
        format_func=lambda option: option_map[option],
        selection_mode="single",
        key=f"evaso_{key_suffix}"
    )
    
    if selezione == 0:
        return df[df["INVIATE AL PROVIDER"].notnull()]
    elif selezione == 1:
        return df[df["INVIATE AL PROVIDER"].isnull()]
    return df

def filtro_massivo_singolo(df, key_suffix=""):
    option_map = {
        0: "SINGOLE GESTORE",
        1: "MASSIVE"
    }
    selezione = st.pills(
        "",
        options=option_map.keys(),
        format_func=lambda option: option_map[option],
        selection_mode="single",
        key=f"massivo_{key_suffix}"
    )
    
    if selezione == 0:
        return df[df["SERVIZIO RICHIESTO"] == "Richiesta singola gestore"]
    elif selezione == 1:
        return df[df["SERVIZIO RICHIESTO"] != "Richiesta singola gestore"]
    return df

def filtro_gestore(df, key_suffix=""):
    gestore_input = st.text_input("Filtra per Gestore", key=f"gestore_{key_suffix}")
    if gestore_input:
        df = df[df["GESTORE"].astype(str).str.contains(gestore_input, case=False, na=False)]
    return df

def filtro_portafoglio(df, key_suffix=""):
    portafoglio_input = st.text_input("Filtra per Portafoglio", key=f"portafoglio_{key_suffix}")
    if portafoglio_input:
        df = df[df["PORTAFOGLIO"].astype(str).str.contains(portafoglio_input, case=False, na=False)]
    return df

def mostra_df_filtrato_utente(df):
    col1, col2 = st.columns(2)
    user = st.session_state.get("user")
    df = df.copy()
    
    # Mappatura per normalizzare i nomi dei gestori
    mappa_gestori = {
        "ANTONELLA COCCO": "Antonella cocco",
        "BEATRICE LAORENZA": "Beatrice Laorenza",
        "Bacchetta ": "Carlo Bacchetta",
        "DANIELA RIZZI": "Daniela Rizzi",
        "FINGEST CREDIT": "Fingest Group",
        "GIUSEPPE NIGRA": "Giuseppe Nigra",
        "LAMYAA HAKIM": "Lamyaa Hakim",
        "MATTEO CATARZI": "Matteo Catarzi",
        "Magnifico Gelsomina ": "Gelsomina Magnifico",
        "Mauro Gualtiero ": "Mauro Gualtiero",
        "Michele  Oranger": "Michele Oranger",
        "RITA NOTO": "Rita Maria Noto",
        "Rita Maria Noto ": "Rita Maria Noto",
        "Rita Noto": "Rita Maria Noto",
        "Rita maria Noto": "Rita Maria Noto",
        "Ruscelli lisa": "Ruscelli Lisa",
        "Tiziana Alibrandi ": "Tiziana Alibrandi",
        "VALENTINA BARTOLO": "Valentina Bartolo",
        "VALERIA NAPOLEONE": "Valeria Napoleone",
        "carmela lanciano": "Carmela Lanciano",
        "silvia stefanelli": "Silvia Stefanelli",
        " AGECREDIT": "AGECREDIT"
        # aggiungi qui altre normalizzazioni se servono
    }
    if "GESTORE" in df.columns:
        df["GESTORE"] = df["GESTORE"].replace(mappa_gestori)
    
    if user and "username" in user:

        username_norm = user["username"].replace(" ", "").lower()
        df = df[df["GESTORE"].astype(str).str.replace(" ", "").str.lower() == username_norm]
        columns = [
            "C.F.",
            "PORTAFOGLIO",
            "NOMINATIVO POSIZIONE",
            "NDG DEBITORE",
            "NOMINATIVO RICERCA",
            "NOME SERVIZIO",
            "DATA RICHIESTA",
            "INVIATE AL PROVIDER",
            "COSTO"
        ]
        existing_columns = [col for col in columns if col in df.columns]
        df = df[existing_columns].copy()
    with col1:
        df = filtro_data(df, key_suffix="utente_data")
    with col2:
        df = filtro_cf(df, key_suffix="utente_cf")
    
    st.dataframe(df, use_container_width=True, height=500)
    return df

def mostra_df_filtrato(df):
    df = df[df["INVIATE AL PROVIDER"].isnull()]
    col1, col2, col3 = st.columns(3)
    columns = [
        "C.F.",
        "GESTORE", 
        "PORTAFOGLIO",
        "NOMINATIVO POSIZIONE",
        "NDG DEBITORE",
        "NOMINATIVO RICERCA",
        "NOME SERVIZIO",
        "DATA RICHIESTA"
    ]
    
    existing_columns = [col for col in columns if col in df.columns]
    df = df[existing_columns].copy()
    df = df[df["DATA RICHIESTA"].notnull()]

    
    with col1:
        df = filtro_cf(df, key_suffix="admin_cf")
    with col2:
        df = filtro_gestore(df, key_suffix="admin_gestore")
    with col3:
        df = filtro_portafoglio(df, key_suffix="admin_portafoglio")
    
    df = filtro_data(df, key_suffix="admin_data")
    st.dataframe(df, use_container_width=True, height=500)

    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        label="Scarica Excel",
        data=buffer,
        file_name="Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )




def mostra_df_filtrato_home_admin(df):
    df = df.copy()
    if "COSTO" in df.columns:
        df["COSTO"] = df["COSTO"].fillna("").astype(str)
    df = filtro_evaso(df, key_suffix="home_admin_evaso")

    df = filtro_massivo_singolo(df, key_suffix="home_admin_gnuo")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        df = filtro_cf(df, key_suffix="home_admin_cf")
    with col2:
        df = filtro_gestore(df, key_suffix="home_admin_gestore")
    with col3:
        df = filtro_portafoglio(df, key_suffix="home_admin_portafoglio")
    col1, col2 = st.columns(2)    
    with col1:
        df = filtro_data(df, key_suffix="home_admin_data")
    with col2:
        df = filtro_data_evasione(df, key_suffix="home_admin_data3")
    
    return df