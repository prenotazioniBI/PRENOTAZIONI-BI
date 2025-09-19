import pandas as pd
from datetime import datetime, timedelta
import streamlit as st
from filtro_df import mostra_df_filtrato_home_admin
from sharepoint_utils import SharePointNavigator
# funzione che riconosce se una richiesta è gia stata fatta in passato per quel cf (oppure id laweb) 
# meno di tre mesi fa
# non controllo se la data sia stringa o date, tanto avendo creata con datetime non c'è rischio che abbia formato diverso   
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
        "RIFIUTATA",
        "PORTAFOGLIO",
        "NDG DEBITORE",
        "NOMINATIVO POSIZIONE",
        "NDG NOMINATIVO RICERCATO",
        "NOMINATIVO RICERCA"
    ]
    
    colonne_presenti = [col for col in colonne_da_mostrare if col in richieste_utente.columns]
    richieste_utente = richieste_utente.sort_values("DATA RICHIESTA", ascending=False)
    richieste_utente["INVIATE AL PROVIDER"] = richieste_utente["INVIATE AL PROVIDER"].fillna("In Attesa..")
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
    tre_mesi_fa = oggi - timedelta(days=90)
    mask = (df["C.F."].astype(str).str.strip() == str(cf).strip()) & \
        (df["NOME SERVIZIO"].astype(str).str.strip() == str(nome_servizio).strip())
    
    for data_str in df.loc[mask, "DATA RICHIESTA"]:
        data_richiesta = pd.to_datetime(data_str, dayfirst=True, errors="coerce")
        if pd.notnull(data_richiesta) and data_richiesta >= tre_mesi_fa:
            return df, False, f"Richiesta già presente negli ultimi 3 mesi ({data_richiesta.date()}) - {nome_servizio}"

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
        "INVIATE AL PROVIDER": data_invio,
        "COSTO": costo,
        "MESE": mese,
        "ANNO": anno,
        "N. RICHIESTE": n_richieste,
        "RIFATTURAZIONE": rifatturazione,
        "TOT POSIZIONI": tot_posizioni,
        "DATA RICHIESTA": data_richiesta,
        "RIFIUTATA": rifiutata,
        "SERVIZIO RICHIESTO": "Richiesta singola gestore"
    }
    
    df_completo = pd.concat([df, pd.DataFrame([riga])], ignore_index=True)
    if "id" not in df_completo.columns:
        df_completo["id"] = range(1, len(df_completo) + 1)
    else:
        df_completo["id"] = range(1, len(df_completo) + 1)
    buffer = BytesIO()
    df_completo.to_excel(buffer, index=False)
    buffer.seek(0)
    file_content = buffer.getvalue()
    file_data = {
        'filename': "General/REPORT INCASSI/SOFTWARE INCASSI/prenotazioni.xlsx",
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
        "NOMINATIVO RICERCA",
        "RIFIUTATA"
    ]
    df = df[colonne_principali] 
    ordino_per_stato = df.sort_values("DATA RICHIESTA", ascending=False)
    return ordino_per_stato

def modifica_celle_excel(df, mostra_editor=True):
    df_filtered = mostra_df_filtrato_home_admin(st.session_state['df_full'])
    
    if df_filtered is None or df_filtered.empty:
        st.warning("Nessun dato disponibile dopo l'applicazione dei filtri.")
        return None

    colonne = ["C.F.", "DATA RICHIESTA", "GESTORE", "INVIATE AL PROVIDER", "PORTAFOGLIO",
               "CENTRO DI COSTO", "NDG DEBITORE", "NOMINATIVO POSIZIONE", 
               "NDG NOMINATIVO RICERCATO", "NOMINATIVO RICERCA", "SERVIZIO RICHIESTO",
               "NOME SERVIZIO", "PROVIDER", "COSTO", "RIFATTURAZIONE", "RIFIUTATA"]

    cols_to_show = [col for col in colonne if col in df_filtered.columns]
    if 'id' in df_filtered.columns and 'id' not in cols_to_show:
        cols_to_show.append('id')

    df_filtered = df_filtered[cols_to_show]

    if mostra_editor:
        df_copy = df_filtered.copy().reset_index(drop=True)
        df_copy = df_copy.loc[:, ~df_copy.columns.duplicated()]
        
        # Prepara la colonna COSTO
        if 'COSTO' in df_copy.columns:
            df_copy['COSTO'] = df_copy['COSTO'].fillna('').astype(str)
        
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
                "RIFATTURAZIONE": st.column_config.SelectboxColumn("RIFATTURAZIONE", options=["SI", "NO"], required=False),
                "INVIATE AL PROVIDER": st.column_config.DateColumn("INVIATE AL PROVIDER", format="DD.MM.YYYY", required=False),
                "CENTRO DI COSTO": st.column_config.SelectboxColumn("CENTRO DI COSTO", options=["ACERO SPV", "CLESSIDRA", "CF PLUS", "FBS"], required=False), 
                "COSTO": st.column_config.SelectboxColumn(label="COSTO (€)", options=["", "11", "2,9", "1,1", "19,5", "0,6", "50", "2,3", "15"], required=False),
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
                    "Lotto UnipolRec 1"], required=False),
                "RIFIUTATA": st.column_config.SelectboxColumn("RIFIUTATA", options=["", "Codice Fiscale non valido", "Altra motivazione"], required=False)
            }
        )
        
        if 'COSTO' in edited_df.columns:
            edited_df['COSTO'] = edited_df['COSTO'].replace('', None)
            edited_df['COSTO'] = edited_df['COSTO'].astype(str).str.replace(',', '.')
            edited_df['COSTO'] = pd.to_numeric(edited_df['COSTO'], errors='coerce')
            
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
        "NOMINATIVO RICERCA",
        "RIFIUTATA"
    ]
    df = df[colonne_principali] 
    ordino_per_stato = df.sort_values("DATA RICHIESTA", ascending=False)
    return ordino_per_stato