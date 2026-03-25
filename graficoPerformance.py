import pandas as pd
import streamlit as st
import plotly.graph_objects as go

C_BG          = "#f4f3ed"
C_BG2         = "#ecebe3"
C_BORDER      = "#d3d2ca"
C_TEXT        = "#3d3a2a"
C_TEXT_MUTED  = "#8a8775"
C_PRIMARY     = "#bb5a38"
C_GREEN       = "#4a7c59"
C_GREEN_LIGHT = "#d6e8dc"
C_RED_LIGHT   = "#f5dbd4"


def grafico_conversione_bi(df_full: pd.DataFrame, dt_performance: pd.DataFrame, username: str) -> None:
    """
    - df_full:        colonna gestore = 'GESTORE'
    - dt_performance: colonna gestore = 'assetManager'
    """

    username_parts = username.strip().upper().split()
    username_norm  = " ".join(reversed(username_parts))

    # ── 1. TOTALE da df_full (colonna: GESTORE) ──
    df = df_full.copy()
    df["_gest_norm"] = df["GESTORE"].str.strip().str.upper()
    df_gestore = df[
        (df["_gest_norm"] == username_norm) |
        (df["_gest_norm"] == " ".join(username_parts))
    ]
    tutte_posizioni = set(df_gestore["NOMINATIVO POSIZIONE"].dropna().unique())
    totale = len(tutte_posizioni)

    if totale == 0:
        st.info("Nessuna posizione trovata per questo gestore in df_full.")
        return

    # ── 2. INCASSATE da dt_performance (colonna: assetManager) ──
    dt = dt_performance.copy()
    dt["_am_norm"] = dt["assetManager"].str.strip().str.upper()
    dt_gestore = dt[
        (dt["_am_norm"] == username_norm) |
        (dt["_am_norm"] == " ".join(username_parts))
    ]
    posizioni_incassate = set(dt_gestore["Intestazione"].dropna().unique())

    # ── 3. NON INCASSATE = totale - incassate ──
    posizioni_non_incassate = tutte_posizioni - posizioni_incassate

    n_incassate     = len(posizioni_incassate)
    n_non_incassate = len(posizioni_non_incassate)

    # ── 4. UI ──
    st.markdown(
        f"<p style='color:{C_TEXT_MUTED}; font-size:13px; margin-bottom:12px'>"
        f"Conversione richieste BI · gestore: <b style='color:{C_TEXT}'>{username}</b> · "
        f"totale posizioni: <b style='color:{C_TEXT}'>{totale}</b></p>",
        unsafe_allow_html=True,
    )

    col_chart, col_metrics = st.columns([1.4, 1])

    with col_chart:
        fig = go.Figure(data=[go.Pie(
            labels=["Hanno incassato", "Non hanno incassato"],
            values=[n_incassate, n_non_incassate],
            hole=0.62,
            marker=dict(
                colors=[C_GREEN, C_PRIMARY],
                line=dict(color=C_BG, width=3),
            ),
            textinfo="percent",
            textfont=dict(size=13, family="Georgia, serif"),
            hovertemplate="<b>%{label}</b><br>Posizioni: %{value}<br>%{percent}<extra></extra>",
            direction="clockwise",
            sort=False,
        )])

        fig.update_layout(
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            annotations=[dict(
                text=f"<b>{totale}</b><br><span style='font-size:10px'>posizioni<br>totali</span>",
                x=0.5, y=0.5,
                font=dict(size=13, color=C_TEXT, family="Georgia, serif"),
                showarrow=False,
            )],
            height=280,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_metrics:
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

        def card(label, count, color_bg, color_accent):
            pct = round(count / totale * 100, 1) if totale else 0
            st.markdown(f"""
                <div style="background:{color_bg}; border-left:4px solid {color_accent};
                            border-radius:8px; padding:12px 16px; margin-bottom:10px">
                    <div style="color:{C_TEXT_MUTED}; font-size:10px; text-transform:uppercase;
                                letter-spacing:.06em; margin-bottom:3px">{label}</div>
                    <div style="color:{color_accent}; font-size:26px; font-weight:700;
                                font-family:'Georgia',serif">{pct}%</div>
                    <div style="color:{C_TEXT_MUTED}; font-size:11px">{count} su {totale} posizioni</div>
                </div>
            """, unsafe_allow_html=True)

        card("✅ Hanno incassato",     n_incassate,     C_GREEN_LIGHT, C_GREEN)
        card("⏳ Non hanno incassato", n_non_incassate, C_RED_LIGHT,   C_PRIMARY)

    if posizioni_non_incassate:
        with st.expander(f"Hai richiesto BI per 📋 {n_non_incassate} posizioni che non hanno ancora incassato", expanded=False):
            st.dataframe(
                pd.DataFrame({"Intestazione": sorted(posizioni_non_incassate)}),
                use_container_width=True,
                hide_index=True,
            )