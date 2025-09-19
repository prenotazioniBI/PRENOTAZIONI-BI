from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
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

def aggrid_pivot_delta(
                        df,
                        group_col="CENTRO DI COSTO",
                        sub_col="NOME SERVIZIO",
                        value_col="COSTO",
                        mese_col="MESE",
                        height=500
                    ):

    df_clean = df.copy()
    mesi_unici = df_clean[mese_col].dropna().unique()
    try:
        mesi_numerici = pd.to_numeric(mesi_unici, errors='coerce')
        mesi_ordinati = sorted(mesi_numerici[~pd.isna(mesi_numerici)])
    except Exception:
        mesi_ordinati = sorted(mesi_unici)

    if len(mesi_ordinati) < 2:
        st.error("Servono almeno due mesi per il confronto.")
        return

    mese_attuale = mesi_ordinati[-1]
    mese_prec = mesi_ordinati[-2]

    df_filtrato = df_clean[df_clean[mese_col].isin([mese_prec, mese_attuale])].copy()

    # Pivot: centro di costo, servizio, mese
    df_pivot = (
        df_filtrato
        .groupby([group_col, sub_col, mese_col])[value_col]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Assicura che le colonne dei mesi ci siano sempre
    for mese in [mese_prec, mese_attuale]:
        if mese not in df_pivot.columns:
            df_pivot[mese] = 0.0
        df_pivot[mese] = pd.to_numeric(df_pivot[mese], errors='coerce').fillna(0).round(2)

    # Calcola delta
    # Calcola delta
    df_pivot["DELTA"] = (df_pivot[mese_attuale] - df_pivot[mese_prec]).round(2)

    # Totali per ogni centro di costo
    totali_cc = (
        df_pivot.groupby(group_col)[[mese_prec, mese_attuale, "DELTA"]]
        .sum()
        .reset_index()
    )
    totali_cc[sub_col] = "TOTALE " + totali_cc[group_col]
    totali_cc[group_col] = totali_cc[group_col].astype(str)
    totali_cc = totali_cc[[group_col, sub_col, mese_prec, mese_attuale, "DELTA"]]

    # Totali generali
    totale_prec = df_pivot[mese_prec].sum()
    totale_attuale = df_pivot[mese_attuale].sum()
    totale_delta = df_pivot["DELTA"].sum()
    totale_row = {
        group_col: "TOTALE",
        sub_col: "",
        mese_prec: totale_prec,
        mese_attuale: totale_attuale,
        "DELTA": totale_delta
    }

    # Unisci tutto
    df_pivot = pd.concat([df_pivot, totali_cc, pd.DataFrame([totale_row])], ignore_index=True)
    # Conversione tipi per AgGrid
    for col in [mese_prec, mese_attuale, "DELTA"]:
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
    
    gb.configure_column(
        group_col, 
        headerName=group_col, 
        rowGroup=True, 
        width=150,
        pinned='left', hide = True
    )
    
    gb.configure_column(
        sub_col, 
        headerName=sub_col, 
        width=180
    )
    
    gb.configure_column(
        str(mese_prec), 
        headerName=f"Costo {mese_prec}", 
        width=120, 
        valueFormatter="x.toFixed(2)",
        type="numericColumn"
    )
    
    gb.configure_column(
        str(mese_attuale), 
        headerName=f"Costo {mese_attuale}", 
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
    
    
    # Configurazioni aggiuntive
    gb.configure_auto_height(autoHeight=False)
    gb.configure_side_bar(filters_panel=True, columns_panel=True)
    gb.configure_selection('multiple', use_checkbox=True)
    
    gridOptions = gb.build()
    
    # Render AgGrid
    grid_response = AgGrid(
        df_pivot,
        gridOptions=gridOptions,
        enable_enterprise_modules=True,
        fit_columns_on_grid_load=True,
        height=height,
        theme="streamlit"
    )
        
    return grid_response
