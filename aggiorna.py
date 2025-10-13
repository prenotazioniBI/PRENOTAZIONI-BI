import streamlit as st
import pandas as pd
import glob
from io import BytesIO

def aggiorna_prenotazioni_centralizzato(nav):
    # Scarica lo storico centralizzato da SharePoint
    nav.download_file("prenotazioni.parquet", "prenotazioni.parquet")
    df_centralizzato = pd.read_parquet("prenotazioni.parquet")
    # Trova tutti i file utente locali (scaricali prima da SharePoint se necessario)
    files_utenti = glob.glob("*_prenotazioni.parquet")
    nuove_righe = []
    chiavi = ["C.F.", "NOME SERVIZIO", "DATA RICHIESTA"]  # personalizza le colonne chiave!
    # Unisci solo le righe nuove
    for file in files_utenti:
        df_utente = pd.read_parquet(file)
        for _, riga in df_utente.iterrows():
            tupla_riga = tuple(riga[k] for k in chiavi)
            # Controlla se la riga esiste già
            if not ((df_centralizzato[chiavi].apply(tuple, axis=1) == tupla_riga).any()):
                nuove_righe.append(riga)
    if nuove_righe:
        df_nuovo = pd.DataFrame(nuove_righe)
        max_id = df_centralizzato["id"].max() if not df_centralizzato.empty else 0
        df_nuovo["id"] = range(max_id + 1, max_id + 1 + len(df_nuovo))
        df_centralizzato = pd.concat([df_centralizzato, df_nuovo], ignore_index=True)
        # Salva e carica su SharePoint
        buffer = BytesIO()
        df_centralizzato.to_parquet(buffer, index=False)
        buffer.seek(0)
        nav.upload_file(buffer, "General/PRENOTAZIONI_BI/prenotazioni.parquet")
        st.success(f"Aggiornato! {len(df_nuovo)} nuove richieste aggiunte.")
    else:
        st.info("Nessuna nuova richiesta da aggiungere.")

