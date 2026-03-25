import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode


C_BG          = "#f4f3ed"
C_BG2         = "#ecebe3"
C_BORDER      = "#d3d2ca"
C_TEXT        = "#3d3a2a"
C_TEXT_MUTED  = "#8a8775"
C_PRIMARY     = "#bb5a38"
C_GREEN       = "#4a7c59"
C_GREEN_LIGHT = "#d6e8dc"
C_AMBER       = "#c9962a"
C_AMBER_LIGHT = "#f2e8cc"
C_RED_LIGHT   = "#f5dbd4"


def matrice_incassi_post_bi(df: pd.DataFrame, username: str) -> None:
    """
    Mostra con st_aggrid una matrice:
        righe    = Intestazione
        colonne  = dataRichiestaBi (una per ogni richiesta BI)
        celle    = somma incassi post richiesta BI

    Colonne attese in df:
        assetManager, Intestazione, dataContabile, dataRichiestaBi, incasso
    """

    df = df.copy()
    df["dataContabile"]   = pd.to_datetime(df["dataContabile"],   errors="coerce")
    df["dataRichiestaBi"] = pd.to_datetime(df["dataRichiestaBi"], errors="coerce")
    df["incasso"]         = pd.to_numeric(df["incasso"],          errors="coerce").fillna(0)

    # normalizza per confronto
    df["assetManager_norm"] = df["assetManager"].str.strip().str.upper()
    username_parts = username.strip().upper().split()
    username_norm = " ".join(reversed(username_parts))

    # prova match diretto e invertito
    df = df[
        (df["assetManager_norm"] == username_norm) |
        (df["assetManager_norm"] == " ".join(username_parts))
    ]

    # filtra post BI
    df = df[df["dataContabile"] > df["dataRichiestaBi"]]

    if df.empty:
        st.info("Nessun incasso registrato dopo una richiesta BI.")
        return

    # de-duplica prima: una riga per incasso (Intestazione + dataContabile + incasso)
    incassi = (
        df[["Intestazione", "dataContabile", "incasso"]]
        .drop_duplicates(subset=["Intestazione", "dataContabile", "incasso"])
        .copy()
    )

    # per ogni richiesta BI disponibile (Intestazione + dataRichiestaBi + NOME SERVIZIO)
    bi_requests = (
        df[["Intestazione", "dataRichiestaBi", "NOME SERVIZIO"]]
        .drop_duplicates()
        .copy()
    )

    # per ogni incasso, trova la richiesta BI immediatamente precedente (più recente con dataRichiestaBi <= dataContabile)
    def assegna_servizio(row):
        candidate = bi_requests[
            (bi_requests["Intestazione"] == row["Intestazione"]) &
            (bi_requests["dataRichiestaBi"] <= row["dataContabile"])
        ]
        if candidate.empty:
            return None
        idx = candidate["dataRichiestaBi"].idxmax()
        return candidate.loc[idx, "NOME SERVIZIO"]

    incassi["bi_col"] = incassi.apply(assegna_servizio, axis=1)
    df = incassi[incassi["bi_col"].notna()]

    # pivot: righe = Intestazione, colonne = servizio BI, valori = somma incasso
    pivot = (
        df.groupby(["Intestazione", "bi_col"])["incasso"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    bi_cols = [c for c in pivot.columns if c != "Intestazione"]
    pivot["TOTALE"] = pivot[bi_cols].sum(axis=1)
    pivot = pivot.sort_values("TOTALE", ascending=False)

    display = pivot.copy()
    for col in bi_cols + ["TOTALE"]:
        display[col] = display[col].apply(lambda v: f"€ {v:,.0f}")

    gb = GridOptionsBuilder.from_dataframe(display)

    gb.configure_default_column(
        resizable=True,
        sortable=True,
        filter=False,
        wrapHeaderText=True,
        autoHeaderHeight=True,
        cellStyle={"color": C_TEXT, "backgroundColor": C_BG, "fontSize": "13px"},
    )

    gb.configure_column("Intestazione", pinned="left", minWidth=180,
        cellStyle={"fontWeight": "600", "color": C_TEXT, "backgroundColor": C_BG2})

    cell_style_js = JsCode(f"""
        function(params) {{
            if (!params.value) return {{}};
            const raw = parseFloat(params.value.replace(/[€\\s.]/g, '').replace(',', '.'));
            if (isNaN(raw)) return {{}};
            if (raw > 0) return {{backgroundColor: '{C_GREEN_LIGHT}', color: '{C_GREEN}',   fontWeight: '600'}};
            if (raw < 0) return {{backgroundColor: '{C_RED_LIGHT}',   color: '{C_PRIMARY}', fontWeight: '600'}};
            return {{backgroundColor: '{C_BG}', color: '{C_TEXT_MUTED}'}};
        }}
    """)
    for col in bi_cols:
        gb.configure_column(col, minWidth=200, cellStyle=cell_style_js)

    totale_style_js = JsCode(f"""
        function(params) {{
            if (!params.value) return {{}};
            const raw = parseFloat(params.value.replace(/[€\\s.]/g, '').replace(',', '.'));
            if (isNaN(raw)) return {{}};
            if (raw > 0) return {{backgroundColor: '{C_GREEN}',   color: 'white', fontWeight: '700'}};
            if (raw < 0) return {{backgroundColor: '{C_PRIMARY}', color: 'white', fontWeight: '700'}};
            return {{backgroundColor: '{C_BORDER}', color: '{C_TEXT}', fontWeight: '700'}};
        }}
    """)
    gb.configure_column("TOTALE", minWidth=130, pinned="right", cellStyle=totale_style_js)

    gb.configure_grid_options(domLayout="autoHeight", suppressMovableColumns=True, headerHeight=48)

    custom_css = {
        ".ag-root-wrapper": {
            "border": f"1px solid {C_BORDER}",
            "border-radius": "8px",
            "overflow": "hidden",
        },
        ".ag-header": {
            "background-color": C_BG2,
            "color": C_TEXT,
            "font-weight": "700",
            "font-size": "12px",
            "border-bottom": f"2px solid {C_PRIMARY}",
        },
        ".ag-row-even": {"background-color": C_BG},
        ".ag-row-odd":  {"background-color": C_BG2},
        ".ag-row:hover": {"background-color": C_AMBER_LIGHT + " !important"},
    }

    st.markdown(
        f"<p style='color:{C_TEXT_MUTED}; font-size:13px; margin-bottom:6px'>"
        f"Incassi registrati <b style='color:{C_PRIMARY}'>dopo</b> la richiesta BI · gestore: "
        f"<b style='color:{C_TEXT}'>{username}</b></p>",
        unsafe_allow_html=True,
    )

    AgGrid(
        display,
        gridOptions=gb.build(),
        custom_css=custom_css,
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=False,
        height=min(600, 48 + 40 * len(display) + 60),
        theme="alpine",
    )