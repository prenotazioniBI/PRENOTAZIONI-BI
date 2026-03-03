import pandas as pd
import plotly.graph_objects as go
import streamlit as st


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
    "Ritamaria Noto": "Rita Maria Noto",
    "Mariagiulia Berardi": "Maria Giulia Berardi",
    "Rita maria Noto": "Rita Maria Noto",
    "Ruscelli lisa": "Ruscelli Lisa",
    "Tiziana Alibrandi ": "Tiziana Alibrandi",
    "VALENTINA BARTOLO": "Valentina Bartolo",
    "VALERIA NAPOLEONE": "Valeria Napoleone",
    "carmela lanciano": "Carmela Lanciano",
    "silvia stefanelli": "Silvia Stefanelli",
    " AGECREDIT": "AGECREDIT"
}


def _prepara_df(df: pd.DataFrame, anno: int) -> pd.DataFrame:
    """Filtra per anno e normalizza colonne."""
    dfc = df.copy()
    dfc["dataRichiesta"] = pd.to_datetime(dfc["dataRichiesta"], errors="coerce")
    dfc = dfc[dfc["dataRichiesta"].dt.year == anno]
    dfc["GESTORE"] = dfc["GESTORE"].astype(str).str.strip()
    return dfc


def chart_richieste_incasso(dt_performance, gestore_loggato, anno, mappa_gestori, height=500):
    """
    Grafico Donut + Barre: conversion rate per gestore.
    
    Colonne attese in dt_performance:
    - GESTORE (stringa)
    - dataRichiesta (data)
    - nomeProcesso (string)
    - portafoglio (string)
    - importo (float, nullable)
    """
    
    # Validazione input
    if dt_performance is None or dt_performance.empty:
        st.warning("Nessun dato disponibile per il gestore.")
        return None
    
    # Copia locale
    dfc = dt_performance.copy()
    
    # Normalizza colonne critiche
    dfc["dataRichiesta"] = pd.to_datetime(dfc["dataRichiesta"], errors="coerce")
    dfc["GESTORE"] = dfc["GESTORE"].astype(str).str.strip()
    
    # Filtra per anno
    dfc = dfc[dfc["dataRichiesta"].dt.year == anno]
    
    if dfc.empty:
        st.warning(f"Nessun dato per l'anno {anno}.")
        return None
    
    # Applica mappa gestori al dataframe
    dfc["GESTORE"] = dfc["GESTORE"].replace(mappa_gestori)
    
    # Normalizza gestore loggato
    gestore_norm = str(gestore_loggato).strip()
    gestore_norm = mappa_gestori.get(gestore_norm, gestore_norm)
    
    # Filtra per gestore loggato
    dfc_g = dfc[dfc["GESTORE"] == gestore_norm].copy()
    
    if dfc_g.empty:
        st.warning(
            f"Gestore **{gestore_norm}** non trovato nei dati {anno}. "
            "Benvenuto in Fbs!"

        )
        return None
    
    # --- Aggrega a livello di richiesta (portafoglio + dataRichiesta) ---
    # Una richiesta ha prodotto incasso se almeno una riga ha importo valorizzato
    richieste = (
        dfc_g.groupby(["portafoglio", "dataRichiesta"])["importo"]
        .apply(lambda x: x.notna().any())
        .reset_index()
        .rename(columns={"importo": "ha_incasso"})
    )
    
    n_con = int(richieste["ha_incasso"].sum())
    n_senza = int((~richieste["ha_incasso"]).sum())
    n_totale = n_con + n_senza
    pct_con = (n_con / n_totale * 100) if n_totale > 0 else 0
    
    # Media gestori (per confronto)
    tutte = (
        dfc.groupby(["GESTORE", "portafoglio", "dataRichiesta"])["importo"]
        .apply(lambda x: x.notna().any())
        .reset_index()
        .rename(columns={"importo": "ha_incasso"})
    )
    media_conv = (
        tutte.groupby("GESTORE")["ha_incasso"]
        .mean()
        .mean() * 100
    )
    
    # ------------------------------------------------------------------ #
    #  LAYOUT: Donut + Barre orizzontali
    # ------------------------------------------------------------------ #
    fig = go.Figure()
    
    # --- Donut ---
    fig.add_trace(go.Pie(
        labels=["Con incasso", "Senza incasso"],
        values=[n_con, n_senza],
        hole=0.62,
        marker=dict(
            colors=["#4caf87", "#e05c4b"],
            line=dict(color="#13100d", width=3),
        ),
        textinfo="percent",
        textfont=dict(size=13, color="#f0ece4", family="Georgia, serif"),
        hovertemplate="<b>%{label}</b><br>%{value} richieste (%{percent})<extra></extra>",
        domain={"x": [0, 0.45], "y": [0.1, 0.9]},
        sort=False,
    ))
    
    # Annotazione centrale nel donut
    fig.add_annotation(
        x=0.225, y=0.5,
        xref="paper", yref="paper",
        text=(
            f"<b style='font-size:28px;color:#f0ece4'>{pct_con:.0f}%</b><br>"
            f"<span style='font-size:11px;color:#9e9080'>conversion rate</span>"
        ),
        showarrow=False,
        font=dict(family="Georgia, serif"),
        align="center",
    )
    
    # --- Barre orizzontali (confronto gestore vs media) ---
    fig.add_trace(go.Bar(
        x=[pct_con],
        y=[gestore_norm],
        orientation="h",
        name=gestore_norm,
        marker=dict(
            color="#b9836f",
            line=dict(color="#13100d", width=1),
        ),
        text=[f"{pct_con:.1f}%"],
        textposition="outside",
        textfont=dict(color="#f0ece4", size=12, family="Georgia, serif"),
        hovertemplate=f"<b>{gestore_norm}</b>: %{{x:.1f}}%<extra></extra>",
        xaxis="x2",
        yaxis="y2",
        width=0.4,
    ))
    
    fig.add_trace(go.Bar(
        x=[media_conv],
        y=["Media gestori"],
        orientation="h",
        name="Media gestori",
        marker=dict(
            color="#3a6b8a",
            line=dict(color="#13100d", width=1),
        ),
        text=[f"{media_conv:.1f}%"],
        textposition="outside",
        textfont=dict(color="#f0ece4", size=12, family="Georgia, serif"),
        hovertemplate="<b>Media gestori</b>: %{x:.1f}%<extra></extra>",
        xaxis="x2",
        yaxis="y2",
        width=0.4,
    ))
    
    # ------------------------------------------------------------------ #
    #  UPDATE LAYOUT
    # ------------------------------------------------------------------ #
    fig.update_layout(
        paper_bgcolor="#13100d",
        plot_bgcolor="#13100d",
        height=height,
        margin=dict(t=90, b=60, l=30, r=60),
        font=dict(family="Georgia, serif"),
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.5, y=-0.08,
            xanchor="center",
            font=dict(color="#9e9080", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        title=dict(
            text=(
                f"<b>Richieste BI · {gestore_norm}</b>  "
                f"<span style='font-size:13px;color:#9e9080'>"
                f"Anno {anno}  ·  {n_totale} richieste totali</span>"
            ),
            font=dict(size=17, color="#f0ece4", family="Georgia, serif"),
            x=0.5,
            xanchor="center",
            y=0.97,
        ),
        xaxis2=dict(
            domain=[0.55, 1.0],
            range=[0, max(pct_con, media_conv) * 1.35],
            ticksuffix="%",
            tickfont=dict(color="#9e9080", size=10),
            gridcolor="#1e1a16",
            zerolinecolor="#2e2620",
            showgrid=True,
            anchor="y2",
        ),
        yaxis2=dict(
            domain=[0.25, 0.75],
            tickfont=dict(color="#c0b09a", size=11),
            gridcolor="#1e1a16",
            anchor="x2",
        ),
    )
    
    # Linea media su barre
    fig.add_shape(
        type="line",
        x0=media_conv, x1=media_conv,
        y0=-0.5, y1=1.5,
        xref="x2", yref="y2",
        line=dict(color="#f5c842", width=2, dash="dot"),
    )
    fig.add_annotation(
        x=media_conv, y=1.55,
        xref="x2", yref="y2",
        text=f"<span style='color:#f5c842'>media {media_conv:.1f}%</span>",
        showarrow=False,
        font=dict(size=10, family="Georgia, serif"),
    )
    
    # ------------------------------------------------------------------ #
    #  STREAMLIT RENDER
    # ------------------------------------------------------------------ #
    st.markdown(
        """
        <style>
        .rb-header {
            font-family: 'Georgia', serif;
            font-size: 11px;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: #8c7a68;
            margin-bottom: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown(
        '<div class="rb-header">Efficacia Richieste BI · Conversion Rate</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    
    # KPI pills sotto il grafico
    col1, col2, col3, col4 = st.columns(4)
    delta_vs_media = pct_con - media_conv
    
    col1.metric("Richieste totali", f"{n_totale:,}")
    col2.metric("Con incasso", f"{n_con:,}", delta=f"{pct_con:.1f}%")
    col3.metric("Senza incasso", f"{n_senza:,}")
    col4.metric(
        "vs media gestori",
        f"{delta_vs_media:+.1f} pp",
        delta=f"{delta_vs_media:+.1f}",
        delta_color="normal",
    )
    
    return fig