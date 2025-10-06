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
    df_clean = df.copy()
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
    st.info(f"Confronto tra: {mesi_label[0]} e {mesi_label[1]}")

    df_filtrato = df_clean[df_clean[mese_col].isin(mesi_num)].copy()

    # Pivot: centro di costo, servizio, mese
    df_pivot = (
        df_filtrato
        .groupby([group_col, sub_col, mese_col])[value_col]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Assicura che le colonne dei mesi selezionati ci siano sempre
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