from st_aggrid import AgGrid, GridOptionsBuilder
import streamlit as st
import pandas as pd
import numpy as np

def aggrid_pivot(
    df,
    group_col,
    sub_col,
    value_col,
    value_name="Totale",
    group_width=80,
    sub_width=120,
    value_width=100,
    height=500
):
    # Mappatura per normalizzare i nomi dei servizi
    mappa_servizi = {
        "Ricerca Telefonica": "Ricerca Telefonica",
        "ricerca telefonica": "Ricerca Telefonica",
        "Ricerca Telefonica ": "Ricerca Telefonica",
        "Ricerca telefonica ": "Ricerca Telefonica",
        "Ricerca Telefonica (verificato)": "Ricerca Telefonica",
        "Anagrafica+Telefono" : "Ricerca Anagrafica + Telefono",
        "ricerca anagrafica + telefono" : "Ricerca Anagrafica + Telefono",
        "Rintraccio Eredi Chiamati con verifica accettazione" : "Ricerca eredi",
        "Ricerca eredi accettanti" : "Ricerca eredi",
        "Info Lavorativa Full (Residenza + Telefono + Impiego)" : "Full(Residenza + Telefono + Impiego)",
        "Rintraccio Conto Corrente" : "Info c/c",
        "RINTRACCIO CONTO CORRENTE " : " INFO C/C"
    }
    # Mappatura per normalizzare i nomi dei gestori
    mappa_gestori = {
        "ANTONELLA COCCO": "Antonella Cocco",
        "Antonella cocco": "Antonella Cocco",
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
        "Ritamaria Noto ": "Rita Maria Noto",
        "Rita Noto": "Rita Maria Noto",
        "Rita maria Noto": "Rita Maria Noto",
        "Ruscelli lisa": "Ruscelli Lisa",
        "Tiziana Alibrandi ": "Tiziana Alibrandi",
        "VALENTINA BARTOLO": "Valentina Bartolo",
        "VALERIA NAPOLEONE": "Valeria Napoleone",
        "carmela lanciano": "Carmela Lanciano",
        "silvia stefanelli": "Silvia Stefanelli",
        " AGECREDIT": "AGECREDIT",
        "Lucia Ragone": "Lucia Ragone",
        "Lucia Ragone ": "Lucia Ragone",
        "Mariagiulia Berardi" : "Maria Giulia Berardi"
        # aggiungi qui altre normalizzazioni se servono
    }

    df = df.copy()
    # Normalizza i nomi dei servizi
    if sub_col == "NOME SERVIZIO":
        df[sub_col] = df[sub_col].replace(mappa_servizi)
    # Normalizza i nomi dei gestori se la colonna esiste
    df["GESTORE"] = df["GESTORE"].replace(mappa_gestori)

    df[value_col] = pd.to_numeric(df[value_col], errors="coerce").fillna(0)

    df_grouped = df.groupby([group_col, sub_col], as_index=False)[value_col].sum()
    df_grouped[value_col] = df_grouped[value_col].round(2)
    df_counts = df.groupby([group_col, sub_col])["NOME SERVIZIO"].count().reset_index(name="NUM_RICHIESTE")
    df_grouped = df_grouped.merge(df_counts, on=[group_col, sub_col])
    df_grouped = df_grouped.rename(columns={value_col: value_name})

    totale = df_grouped[value_name].sum()
    num_richieste = df_grouped["NUM_RICHIESTE"].sum()

    totale_row = {
        group_col: "TOTALE",
        sub_col: "",
        value_name: totale,
        "NUM_RICHIESTE": num_richieste
    }
    df_grouped = pd.concat([df_grouped, pd.DataFrame([totale_row])], ignore_index=True)
    df_grouped = df_grouped.applymap(lambda x: float(x) if isinstance(x, (int, float, np.integer, np.floating)) else x)
    
    gb = GridOptionsBuilder.from_dataframe(df_grouped)
    gb.configure_default_column(editable=False, groupable=True, sortable=True, resizable=True)
    gb.configure_column(group_col, headerName=group_col, hide=True, rowGroup=True, width=group_width, rowGroupPanelShow="always")
    gb.configure_column(sub_col, headerName=sub_col, cellStyle={"fontWeight": "bold"}, width=sub_width)
    gb.configure_column(value_name, headerName=value_name, aggFunc="sum", cellStyle={"backgroundColor": "#b9836f", "fontWeight": "bold"}, width=value_width, valueFormatter="x.toFixed(2)", suppressAggFuncInHeader=True)
    gb.configure_column("NUM_RICHIESTE", headerName="N. richieste", width=80, cellStyle={"fontWeight": "bold"})
    gridOptions = gb.build()

    st.markdown(f"SPESA PER {group_col} E {sub_col}")
    AgGrid(
        df_grouped,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True,
        height=height,
        theme="streamlit"
    )

########################################## tabella pivot ########################################################
mesi_italiani = [
    "", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
]
def nome_mese(mese):
    try:
        mese_int = int(mese)
        if 1 <= mese_int <= 12:
            return mesi_italiani[mese_int]
        else:
            return str(mese)
    except:
        return str(mese)
def aggrid_pivot_delta(
    df,
    group_col="CENTRO DI COSTO",
    sub_col="NOME SERVIZIO",
    value_col="COSTO",
    mese_col="MESE",
    anno_col = "ANNO",
    height=500
):


    # Mappatura per normalizzare i nomi dei servizi
    mappa_servizi = {
         "Ricerca Telefonica": "Ricerca Telefonica",
        "Ricerca Telefonica ": "Ricerca Telefonica",
        "Ricerca telefonica ": "Ricerca Telefonica",
        "Ricerca Telefonica (verificato)": "Ricerca Telefonica",
        "Anagrafica+Telefono" : "Ricerca Anagrafica + Telefono",
        "Rintraccio Eredi Chiamati con verifica accettazione" : "Ricerca eredi",
        "Ricerca eredi accettanti" : "Ricerca eredi",
        "Info Lavorativa Full (Residenza + Telefono + Impiego)" : "Full(Residenza + Telefono + Impiego)",
        "Rintraccio Conto Corrente" : "Info c/c"
    }

    df_clean = df.copy()

    df_clean[sub_col] = df_clean[sub_col].replace(mappa_servizi)


    df_clean = df_clean[df_clean["INVIATE AL PROVIDER"].notnull()]
    df_clean = df_clean[df_clean[anno_col] == 2025]
    mesi_unici = df_clean[mese_col].dropna().unique()
    try:
        mesi_numerici = pd.to_numeric(mesi_unici, errors='coerce')
        mesi_ordinati = sorted(mesi_numerici[~pd.isna(mesi_numerici)])
    except Exception:
        mesi_ordinati = sorted(mesi_unici)

    if len(mesi_ordinati) < 2:
        st.error("Non ci sono almeno due mesi disponibili per il confronto.")
        return
    
    mesi_num = mesi_ordinati[-2:]
    mesi_label = [nome_mese(m) for m in mesi_num]
    st.info(f"Confronto tra: {mesi_label[0]} e {mesi_label[1]} 2025")

    df_filtrato = df_clean[df_clean[mese_col].isin(mesi_num)].copy()

    # Pivot: centro di costo, servizio, mese
    df_pivot = (
        df_filtrato
        .groupby([group_col, sub_col, mese_col])[value_col]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )

    for mese in mesi_num:
        if mese not in df_pivot.columns:
            df_pivot[mese] = 0.0
        df_pivot[mese] = pd.to_numeric(df_pivot[mese], errors='coerce').fillna(0).round(2)

    # Calcola delta tra ultimi due mesi selezionati
    mese_attuale = mesi_num[-1]
    mese_prec = mesi_num[-2]
    df_pivot["DELTA"] = (df_pivot[mese_attuale] - df_pivot[mese_prec]).round(2)

    # Totali per ogni centro di costo
    totali_cc = (
        df_pivot.groupby(group_col)[mesi_num + ["DELTA"]]
        .sum()
        .reset_index()
    )
    totali_cc[sub_col] = "TOTALE " + totali_cc[group_col].astype(str)
    totali_cc[group_col] = totali_cc[group_col].astype(str)
    totali_cc = totali_cc[[group_col, sub_col] + mesi_num + ["DELTA"]]

    # Totali generali
    totale_row = {group_col: "TOTALE", sub_col: ""}
    for mese in mesi_num:
        totale_row[mese] = df_pivot[mese].sum()
    totale_row["DELTA"] = df_pivot["DELTA"].sum()

    # Unisci tutto
    df_pivot = pd.concat([df_pivot, totali_cc, pd.DataFrame([totale_row])], ignore_index=True)
    # Conversione tipi per AgGrid
    for col in mesi_num + ["DELTA"]:
        df_pivot[col] = df_pivot[col].astype(float)
    df_pivot[group_col] = df_pivot[group_col].astype(str)
    df_pivot[sub_col] = df_pivot[sub_col].astype(str)

    gb = GridOptionsBuilder.from_dataframe(df_pivot)
    gb.configure_default_column(
        editable=False, 
        groupable=True, 
        sortable=True, 
        resizable=True,
        filter=True
    )
    gb.configure_column(group_col, headerName=group_col, rowGroup=True, width=150, pinned='left', hide=True)
    gb.configure_column(sub_col, headerName=sub_col, width=180)

    for mese in mesi_num:
        gb.configure_column(
            str(mese),
            headerName=f"Costo {nome_mese(mese)}",
            width=120,
            valueFormatter="x.toFixed(2)",
            type="numericColumn"
        )
    gb.configure_column(
        "DELTA",
        headerName="Delta €",
        width=100,
        cellStyle={"fontWeight": "bold"},
        valueFormatter="x.toFixed(2)",
        type="numericColumn"
    )

    gb.configure_auto_height(autoHeight=False)
    gb.configure_side_bar(filters_panel=True, columns_panel=True)
    gb.configure_selection('multiple', use_checkbox=True)
    gridOptions = gb.build()

    grid_response = AgGrid(
        df_pivot,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True,
        height=height,
        theme="streamlit"
    )
    return grid_response

def aggrid_spesa_per_portafoglio(df, group_col="PORTAFOGLIO", value_col="COSTO", height=500):

    dfc = df.copy()

    if "DATA RICHIESTA" in dfc.columns:
        dfc["DATA RICHIESTA"] = pd.to_datetime(dfc["DATA RICHIESTA"], errors="coerce", dayfirst=True)
        dfc = dfc[dfc["DATA RICHIESTA"].dt.year == 2025]

    if dfc.empty:
        st.info("Nessun dato per il 2025")
        return None

    if "GESTORE" not in dfc.columns:
        dfc["GESTORE"] = "Unknown"

    if group_col not in dfc.columns:
        st.error(f"Colonna {group_col} mancante nel DataFrame")
        return None

    if value_col not in dfc.columns:
        st.error(f"Colonna {value_col} mancante nel DataFrame")
        return None

    dfc[group_col] = dfc[group_col].astype(str).str.strip()
    dfc["GESTORE"] = dfc["GESTORE"].astype(str).str.strip()
    dfc[value_col] = pd.to_numeric(dfc[value_col], errors="coerce").fillna(0.0)

    agg = dfc.groupby([group_col, "GESTORE"], as_index=False).agg(
        TOTALE_SPESA=(value_col, "sum"),
        NUM_RICHIESTE=(value_col, "count")
    )
    agg["TOTALE_SPESA"] = agg["TOTALE_SPESA"].round(2)
    agg = agg.sort_values([group_col, "TOTALE_SPESA"], ascending=[True, False]).reset_index(drop=True)
    tot_per_port = agg.groupby(group_col, as_index=False).agg(
        TOTALE_PORTAFOGLIO=("TOTALE_SPESA", "sum")
    )
    tot_per_port["TOTALE_PORTAFOGLIO"] = tot_per_port["TOTALE_PORTAFOGLIO"].round(2)
    agg = agg.merge(tot_per_port, on=group_col, how="left")

    totale = agg["TOTALE_SPESA"].sum()
    num_richieste = agg["NUM_RICHIESTE"].sum()
    totale_row = {
        group_col: "TOTALE",
        "GESTORE": "",
        "TOTALE_SPESA": totale,
        "NUM_RICHIESTE": int(num_richieste),
        "TOTALE_PORTAFOGLIO": ""
    }
    agg = pd.concat([agg, pd.DataFrame([totale_row])], ignore_index=True)

    agg["NUM_RICHIESTE"] = agg["NUM_RICHIESTE"].astype(int)

    gb = GridOptionsBuilder.from_dataframe(agg)
    gb.configure_default_column(editable=False, groupable=True, sortable=True, resizable=True, filter=True)
    # mostra la colonna PORTAFOGLIO (non nascosta) e mantienila come group key
    gb.configure_column(group_col, headerName=group_col, rowGroup=True, hide=False, width=260, pinned='left')
    gb.configure_column("GESTORE", headerName="Gestore", width=260)
    gb.configure_column("TOTALE_SPESA", headerName="Totale €", valueFormatter="x.toFixed(2)", width=140, type="numericColumn")
    gb.configure_column("NUM_RICHIESTE", headerName="N. richieste", width=120)
    # colonna fissa visibile che mostra sempre il totale per portafoglio
    gb.configure_column("TOTALE_PORTAFOGLIO", headerName="Totale Portafoglio €", valueFormatter="x.toFixed(2)", width=160, pinned='left')
    gb.configure_auto_height(autoHeight=False)
    gb.configure_side_bar(filters_panel=True, columns_panel=True)
    gridOptions = gb.build()

    st.markdown("### Spesa per portafoglio e dettaglio gestore (2025)")
    AgGrid(
        agg,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True,
        height=height,
        theme="streamlit"
    )
    return agg
