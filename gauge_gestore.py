import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


MAPPA_GESTORI = {
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
    "Michele Oranger": "Michele Oranger",
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
    "Mariagiulia Berardi": "Maria Giulia Berardi",
}

MAPPA_SERVIZI = {
    "Ricerca Telefonica": "Ricerca Telefonica",
    "ricerca telefonica": "Ricerca Telefonica",
    "Ricerca Telefonica ": "Ricerca Telefonica",
    "Ricerca telefonica ": "Ricerca Telefonica",
    "Ricerca Telefonica (verificato)": "Ricerca Telefonica",
    "Anagrafica+Telefono": "Ricerca Anagrafica + Telefono",
    "ricerca anagrafica + telefono": "Ricerca Anagrafica + Telefono",
    "Rintraccio Eredi Chiamati con verifica accettazione": "Ricerca eredi",
    "Ricerca eredi accettanti": "Ricerca eredi",
    "Info Lavorativa Full (Residenza + Telefono + Impiego)": "Full(Residenza + Telefono + Impiego)",
    "Rintraccio Conto Corrente": "Info c/c",
    "RINTRACCIO CONTO CORRENTE ": "Info c/c",
}


def _prepara_df(df: pd.DataFrame, anno: int = 2025) -> pd.DataFrame:
    dfc = df.copy()

    if "NOME SERVIZIO" in dfc.columns:
        dfc["NOME SERVIZIO"] = dfc["NOME SERVIZIO"].replace(MAPPA_SERVIZI)

    if "GESTORE" in dfc.columns:
        dfc["GESTORE"] = dfc["GESTORE"].replace(MAPPA_GESTORI).astype(str).str.strip()
    else:
        dfc["GESTORE"] = "Unknown"

    if "DATA RICHIESTA" in dfc.columns:
        dfc["DATA RICHIESTA"] = pd.to_datetime(dfc["DATA RICHIESTA"], errors="coerce", dayfirst=True)
        dfc = dfc[dfc["DATA RICHIESTA"].dt.year == anno]

    dfc["COSTO"] = pd.to_numeric(dfc.get("COSTO", 0), errors="coerce").fillna(0.0)
    return dfc

def gauge_spesa_gestore(
    df: pd.DataFrame,
    gestore_loggato: str,
    anno: int = 2026,
    value_col: str = "COSTO",
    height: int = 420,
):


    gestore_norm = MAPPA_GESTORI.get(gestore_loggato, gestore_loggato).strip()

    dfc = _prepara_df(df, anno=anno)

    if dfc.empty:
        st.warning(f"Nessun dato disponibile per l'anno {anno}.")
        return

    spesa_per_gestore = (
        dfc.groupby("GESTORE")[value_col]
        .sum()
        .reset_index()
        .rename(columns={value_col: "SPESA_TOTALE"})
    )
    spesa_per_gestore["SPESA_TOTALE"] = spesa_per_gestore["SPESA_TOTALE"].round(2)

    media_gestori = spesa_per_gestore["SPESA_TOTALE"].mean()
    max_spesa = spesa_per_gestore["SPESA_TOTALE"].max()

    riga_gestore = spesa_per_gestore[spesa_per_gestore["GESTORE"] == gestore_norm]
    if riga_gestore.empty:
        st.warning(
            f"Gestore **{gestore_norm}** non trovato nei dati {anno}. "
                        "Fai la tua prima richiesta per vedere il tuo punteggio!"
        )
        return

    spesa_gestore = float(riga_gestore["SPESA_TOTALE"].iloc[0])
    n_gestori = len(spesa_per_gestore)

    percentile = float(
        (spesa_per_gestore["SPESA_TOTALE"] <= spesa_gestore).mean() * 100
    )


    delta = spesa_gestore - media_gestori
    delta_pct = (delta / media_gestori * 100) if media_gestori > 0 else 0

    gauge_max = max(max_spesa * 1.15, spesa_gestore * 1.2, 1.0)

    zona_verde = media_gestori * 0.85
    zona_gialla = media_gestori * 1.15

   

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


    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="gauge+number",      
        value=spesa_gestore,
        number={
            "suffix": " €",
            "font": {"size": 36, "color": C_TEXT, "family": "Styrene B, Georgia, serif"},
            "valueformat": ",.2f",
        },
        gauge={
            "axis": {
                "range": [0, gauge_max],
                "tickwidth": 1,
                "tickcolor": C_BORDER,
                "tickformat": ",.0f",
                "tickfont": {"color": C_TEXT_MUTED, "size": 11},
                "nticks": 6,
            },
            "bar": {"color": C_PRIMARY, "thickness": 0.28},
            "bgcolor": C_BG,
            "borderwidth": 2,
            "bordercolor": C_BORDER,
            "steps": [
                {"range": [0, zona_verde],           "color": C_GREEN_LIGHT},
                {"range": [zona_verde, zona_gialla],  "color": C_AMBER_LIGHT},
                {"range": [zona_gialla, gauge_max],   "color": C_RED_LIGHT},
            ],
            "threshold": {
                "line": {"color": C_AMBER, "width": 3},
                "thickness": 0.82,
                "value": media_gestori,
            },
        },
        title={"text": ""},
        domain={"x": [0.05, 0.95], "y": [0, 1]},
    ))


    delta_color  = C_PRIMARY if delta > 0 else C_GREEN
    delta_icon   = "▲" if delta > 0 else "▼"
    delta_str    = f"{delta_icon} {abs(delta):,.2f} € ({delta_pct:+.1f}%)"


    fig.add_annotation(
        x=0.5, y=1.25, xref="paper", yref="paper",
        text=f"<b>{gestore_norm}</b>",
        showarrow=False,
        font={"size": 20, "color": C_TEXT, "family": "Styrene B, Georgia, serif"},
        align="center", yanchor="top",
    )

    fig.add_annotation(
        x=0.5, y=1.15, xref="paper", yref="paper",
        text=f"Spesa {anno}  ·  {n_gestori} gestori  ·  Percentile {percentile:.0f}°",
        showarrow=False,
        font={"size": 12, "color": C_TEXT_MUTED, "family": "Styrene B, Georgia, serif"},
        align="center", yanchor="top",
    )

    fig.add_annotation(
        x=0.5, y=-0.08, xref="paper", yref="paper",
        text=f"<b style='color:{delta_color}'>{delta_str}</b> vs media",
        showarrow=False,
        font={"size": 13, "color": C_TEXT_MUTED, "family": "Styrene B, Georgia, serif"},
        align="center", yanchor="top",
    )

    fig.add_annotation(
        x=0.5, y=-0.20, xref="paper", yref="paper",
        text=(
            f"<span style='color:{C_AMBER}'>▬</span>  "
            f"Media: <b style='color:{C_AMBER}'>{media_gestori:,.2f} €</b>"
        ),
        showarrow=False,
        font={"size": 12, "color": C_TEXT_MUTED, "family": "Styrene B, Georgia, serif"},
        align="center", yanchor="top",
    )

    fig.update_layout(
        paper_bgcolor=C_BG,
        plot_bgcolor=C_BG,
        margin={"t": 80, "b": 90, "l": 20, "r": 20},
        height=height,
        font={"family": "Styrene B, Georgia, serif", "color": C_TEXT},
    )


    st.markdown(
        f"""
        <style>
        .gauge-header {{
            font-family: 'Styrene B', Georgia, serif;
            font-size: 15px;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: {C_TEXT_MUTED};
            margin-bottom: 2px;
        }}
        .gauge-wrap {{
            background: {C_BG};
            border: 1px solid {C_BORDER};
            border-radius: 0.6rem;
            padding: 16px 20px 8px;
        }}
        /* colora i delta delle metric card in linea col tema */
        [data-testid="stMetricDelta"] svg {{ display: none; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown(
            f'<div class="gauge-header">Performance di spesa · Investigazioni {anno}</div>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        delta_icon = "▲" if delta > 0 else "▼"
        _, c1, c2, c3, _ = st.columns([3, 2, 2, 2, 2])

        c1.metric(
            label="💼 Spesa personale",
            value=f"€ {spesa_gestore:,.2f}",
        )
        c2.metric(
            label="⌀ Media gestori",
            value=f"€ {media_gestori:,.2f}",
        )
        c3.metric(
            label="Δ Scostamento",
            value=f"{delta_icon} € {abs(delta):,.2f}",
            delta=f"{delta_pct:+.1f}% vs media",
            delta_color="inverse",
        )

    return fig


