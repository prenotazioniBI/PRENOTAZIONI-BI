import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
from filtro_df import mostra_df_filtrato_home_admin
from io import BytesIO


TENANT_ID = st.secrets["TENANT_ID"] 
CLIENT_ID = st.secrets["CLIENT_ID"] 
CLIENT_SECRET = st.secrets["CLIENT_SECRET"] 


def visualizza_richieste_per_gestore(df, username):
    df_gestore = df.copy()
    richieste_utente = df_gestore[df_gestore["GESTORE"] == username]
    colonne_da_mostrare = [
        "DATA RICHIESTA",
        "C.F.",
        "NOME SERVIZIO",
        "INVIATE AL PROVIDER",
        "PORTAFOGLIO",
        "NDG DEBITORE",
        "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO",
        "NOMINATIVO RICERCA"
    ]
    
    colonne_presenti = [col for col in colonne_da_mostrare if col in richieste_utente.columns]
    richieste_utente = richieste_utente.sort_values("DATA RICHIESTA", ascending=False)
    richieste_utente[colonne_da_mostrare] = richieste_utente[colonne_da_mostrare].fillna("   -    ")
    return richieste_utente[colonne_presenti]


 
def salva_richiesta(
    df,
    portafoglio,
    centro_costo,
    gestore,
    ndg_debitore,
    nominativo_posizione,
    ndg_nominativo_ricercato,
    nominativo_ricerca,
    cf,
    nome_servizio,
    provider,
    data_invio,
    costo,
    mese,
    anno,
    n_richieste,
    rifatturazione,
    tot_posizioni,
    data_richiesta, 
    rifiutata,
    nav
):
    oggi = datetime.now()
    tre_mesi_fa = oggi - timedelta(days=365)
    mask = (df["C.F."].astype(str).str.strip() == str(cf).strip()) & \
        (df["NOME SERVIZIO"].astype(str).str.strip() == str(nome_servizio).strip())
    
    for data_str in df.loc[mask, "DATA RICHIESTA"]:
        data_richiesta = pd.to_datetime(data_str, dayfirst=True, errors="coerce")
        if pd.notnull(data_richiesta) and data_richiesta >= tre_mesi_fa:
            gestore_str = df.loc[mask, "GESTORE"].iloc[0] if not df.loc[mask, "GESTORE"].empty else ""
            return df, False, f"Richiesta già fatta il {data_richiesta.date()} - {nome_servizio} - dal gestore {gestore_str}."

    riga = {
        "PORTAFOGLIO": portafoglio,
        "CENTRO DI COSTO": centro_costo,
        "GESTORE": gestore,
        "NDG DEBITORE": ndg_debitore,
        "NOMINATIVO POSIZIONE": nominativo_posizione,
        "NDG NOMINATIVO RICERCATO": ndg_nominativo_ricercato,
        "NOMINATIVO RICERCA": nominativo_ricerca,
        "C.F.": cf,
        "NOME SERVIZIO": nome_servizio,
        "PROVIDER": provider,
       "INVIATE AL PROVIDER": pd.to_datetime(data_invio, errors="coerce", dayfirst=True) if data_invio else pd.NaT,
        "COSTO": costo,
        "MESE": mese,
        "ANNO": anno,
        "N. RICHIESTE": n_richieste,
        "RIFATTURAZIONE": rifatturazione,
        "TOT POSIZIONI": tot_posizioni,
        "DATA RICHIESTA": data_richiesta,
        "SERVIZIO RICHIESTO": "Richiesta singola gestore"
    }

    df_completo = pd.concat([df, pd.DataFrame([riga])], ignore_index=True)
    df_completo["id"] = range(1, len(df_completo) + 1)
    df_completo["COSTO"] = df_completo["COSTO"].replace("", pd.NA)
    df_completo["COSTO"] = pd.to_numeric(df_completo["COSTO"], errors="coerce")
    df_completo["DATA RICHIESTA"] = df_completo["DATA RICHIESTA"].replace("", pd.NaT)
    df_completo["DATA RICHIESTA"] = pd.to_datetime(df_completo["DATA RICHIESTA"], errors="coerce", dayfirst=True)
    buffer = BytesIO() 
    df_completo.to_parquet(buffer, index=False)
    buffer.seek(0)
    file_content = buffer.getvalue()
    file_data = {
        'filename': "General/PRENOTAZIONI_BI/prenotazioni.parquet",
        'content': file_content,
        'size': len(file_content)
    }
    nav.file_buffer.append(file_data)
    
    return df_completo, True, f"Richiesta salvata con successo - {nome_servizio}"



############### funzioni per l'admin


def visualizza_richieste_per_stato_invio_provider(df):
    df = df[df["INVIATE AL PROVIDER"].isnull()]
    colonne_principali = [
        "GESTORE",
        "C.F.",
        "DATA RICHIESTA",
        "NOME SERVIZIO",
        "PORTAFOGLIO",
        "NDG DEBITORE",
        "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO",
        "NOMINATIVO RICERCA",
        "INVIATE AL PROVIDER"
    ]

    df = df[colonne_principali] 
    df["DATA RICHIESTA"] = pd.to_datetime(df["DATA RICHIESTA"], errors="coerce", dayfirst=False)
    ordino_per_stato = df.sort_values("DATA RICHIESTA", ascending=False)
    return ordino_per_stato


def visualizza_richieste_Evase(df):
    df = df.copy()
    df = df[df["INVIATE AL PROVIDER"].notnull()]
    colonne_principali = [
        "GESTORE",
        "C.F.",
        "DATA RICHIESTA",
        "INVIATE AL PROVIDER",
        "COSTO",
        "NOME SERVIZIO",
        "PORTAFOGLIO",
        "NDG DEBITORE",
        "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO",
        "NOMINATIVO RICERCA"
    ]
    df = df[colonne_principali] 
    ordino_per_stato = df.sort_values("DATA RICHIESTA", ascending=False)
    return ordino_per_stato

# def modifica_celle_excel_eredi(df, mostra_editor=True):
#     df = df[
#     ((df["NOME SERVIZIO"] == "Ricerca eredi accettanti") | (df["NOME SERVIZIO"] == "Ricerca eredi")) &
#     (df["CONVALIDA TL"] == "") &  (df["INVIATE AL PROVIDER"].isnull())]
                                        
#     if not df.empty:
#         colonne = ["C.F.", "DATA RICHIESTA", "NOME SERVIZIO","GESTORE", "PORTAFOGLIO", "NDG DEBITORE", "NOMINATIVO POSIZIONE", 
#                 "NDG NOMINATIVO RICERCATO", "NOMINATIVO RICERCA", "CONVALIDA TL"]
#         cols_to_show = [col for col in colonne if col in df.columns]
#         if 'id' in df.columns and 'id' not in cols_to_show:
#                 cols_to_show.append('id')
#         df = df[cols_to_show] 
        
#         if mostra_editor:
#             df_copy = df.copy().reset_index(drop=True)
#             df_copy = df_copy.loc[:, ~df_copy.columns.duplicated()]
#             edited_df = st.data_editor(
#                 df_copy,
#                 num_rows="dynamic",
#                 height=2000,
#                 use_container_width=True,
#                 key="editor_admin",
#                 column_config={"CONVALIDA TL": st.column_config.SelectboxColumn("CONVALIDA TL", options=["", "VALIDA", "NON VALIDA"], required=False)
#                 }
#             )
#             return edited_df
#         return edited_df
#     else:
#         col1, col2, col3 = st.columns(3)
#         with col2:
#             st.warning("NESSUNA RICHIESTA EREDI IN SOSPESO..")


def modifica_celle_excel(df, mostra_editor=True):
    df_filtered = mostra_df_filtrato_home_admin(st.session_state['df_full'])
    if df_filtered is None or df_filtered.empty:
        st.warning("Nessun dato disponibile dopo l'applicazione dei filtri.")
        return None

    colonne = ["C.F.", "DATA RICHIESTA", "GESTORE", "COSTO", "INVIATE AL PROVIDER", "PORTAFOGLIO",
               "CENTRO DI COSTO", "NDG DEBITORE", "NOMINATIVO POSIZIONE", 
               "NDG NOMINATIVO RICERCATO", "NOMINATIVO RICERCA", "SERVIZIO RICHIESTO",
               "NOME SERVIZIO", "PROVIDER", "RIFATTURAZIONE"]

    cols_to_show = [col for col in colonne if col in df_filtered.columns]
    if 'id' in df_filtered.columns and 'id' not in cols_to_show:
        cols_to_show.append('id')

    df_filtered = df_filtered[cols_to_show]

    if mostra_editor:
        df_copy = df_filtered.copy().reset_index(drop=True)
        df_copy = df_copy.loc[:, ~df_copy.columns.duplicated()]
        if 'NDG DEBITORE' in df_copy.columns:
            df_copy['NDG DEBITORE'] = df_copy['NDG DEBITORE'].astype(str)
        if 'C.F.' in df_copy.columns:
            df_copy['C.F.'] = df_copy['C.F.'].astype(str)
        if 'NDG NOMINATIVO RICERCATO' in df_copy.columns:
            df_copy['NDG NOMINATIVO RICERCATO'] = df_copy['NDG NOMINATIVO RICERCATO'].fillna('').astype(str)
        if 'COSTO' in df_copy.columns:
            df_copy['COSTO'] = df_copy['COSTO'].astype(str)
        df_copy["INVIATE AL PROVIDER"] = pd.to_datetime(df_copy["INVIATE AL PROVIDER"], format="mixed", dayfirst=True, errors="coerce")        
        edited_df = st.data_editor(
            df_copy,
            num_rows="dynamic",
            height=2000,
            use_container_width=True,
            key="editor_admin",
            column_config={
                "PROVIDER": st.column_config.SelectboxColumn(
                    "PROVIDER", options=["AZ", "Abbrevia", "CreditVision", "BD", "Europa"], required=False),
                "NOMINATIVO RICERCA": st.column_config.TextColumn("NOMINATIVO RICERCA", required=False), 
                "NDG NOMINATIVO RICERCATO": st.column_config.TextColumn("NDG NOMINATIVO RICERCATO", required=False),
                "NOMINATIVO POSIZIONE": st.column_config.TextColumn("NOMINATIVO POSIZIONE", required=False), 
                "NDG DEBITORE": st.column_config.TextColumn("NDG DEBITORE", required=False),
                "RIFATTURAZIONE": st.column_config.SelectboxColumn("RIFATTURAZIONE", options=["", "SI", "NO"], required=False),
                "INVIATE AL PROVIDER": st.column_config.DateColumn("INVIATE AL PROVIDER", format="DD.MM.YYYY", required=False),
                "CENTRO DI COSTO": st.column_config.SelectboxColumn("CENTRO DI COSTO", options=["ACERO SPV", "CLESSIDRA", "CF PLUS", "FBS"], required=False), 
                "COSTO": st.column_config.TextColumn("COSTO", required=False),
                "PORTAFOGLIO": st.column_config.SelectboxColumn("PORTAFOGLIO", options=[
                    "", "Lotto Acero 1", "Lotto Banca di Imola 2", "Lotto Banca Imola", 
                    "Lotto Banca Pop Valconca", "Lotto Banca Pop Valconca - Acquisto", 
                    "Lotto Banco di Lucca", "Lotto BAPS 1", "Lotto BAPS 2", "Lotto BAPS 3",
                    "Lotto BAPS 4", "Lotto Benetton 1", "Lotto Blu Banca", "Lotto BP Lazio", 
                    "Lotto BPER 1", "Lotto BPER 2", "Lotto BPER 3", "Lotto BPER 4", 
                    "Lotto CF Plus", "Lotto Clessidra", "Lotto Climb 3", "Lotto ex Bramito", 
                    "Lotto Giamarca", "Lotto Giasone", "Lotto Girasole", "Lotto IRFIS",
                    "Lotto La Cassa di Ravenna", "Lotto Libra", "Lotto Platinum", 
                    "Lotto Pop Npl 2018", "Lotto Pop Npl 2018 2", "Lotto Pop Npl 2018 3",
                    "Lotto Ragusa", "Lotto Ragusa 2", "Lotto Ragusa 3", "Lotto Ragusa 4", 
                    "Lotto UnipolRec 1"], required=False)
            }
        )
        
            
        return edited_df
    
    return df_filtered




################## team leader #################################



def visualizza_richieste_TeamLeader(df):
    df = df.copy()
    colonne_principali = [
        "GESTORE",
        "C.F.",
        "SERVIZIO RICHIESTO",
        "DATA RICHIESTA",
        "INVIATE AL PROVIDER",
        "COSTO",
        "NOME SERVIZIO",
        "PORTAFOGLIO",
        "NDG DEBITORE",
        "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO",
        "NOMINATIVO RICERCA"
    ]
    df = df[colonne_principali] 
    ordino_per_stato = df.sort_values("DATA RICHIESTA", ascending=False)
    return ordino_per_stato




##############################################################################

