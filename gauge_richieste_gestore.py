# import pandas as pd
# import plotly.graph_objects as go
# import streamlit as st


# mappa_gestori = {
#     "ANTONELLA COCCO": "Antonella cocco",
#     "BEATRICE LAORENZA": "Beatrice Laorenza",
#     "Bacchetta ": "Carlo Bacchetta",
#     "DANIELA RIZZI": "Daniela Rizzi",
#     # "FINGEST CREDIT": "Fingest Group",a
#     "GIUSEPPE NIGRA": "Giuseppe Nigra",
#     "LAMYAA HAKIM": "Lamyaa Hakim",
#     "MATTEO CATARZI": "Matteo Catarzi",
#     "Magnifico Gelsomina ": "Gelsomina Magnifico",
#     "Mauro Gualtiero ": "Mauro Gualtiero",
#     "Michele  Oranger": "Michele Oranger",
#     "RITA NOTO": "Rita Maria Noto",
#     "Rita Maria Noto ": "Rita Maria Noto",
#     "Rita Noto": "Rita Maria Noto",
#     "Ritamaria Noto": "Rita Maria Noto",
#     "Mariagiulia Berardi": "Mariagulia Berardi",
#     "Rita maria Noto": "Rita Maria Noto",
#     "Ruscelli lisa": "Ruscelli Lisa",
#     "Tiziana Alibrandi ": "Tiziana Alibrandi",
#     "VALENTINA BARTOLO": "Valentina Bartolo",
#     "VALERIA NAPOLEONE": "Valeria Napoleone",
#     "carmela lanciano": "Carmela Lanciano",
#     "silvia stefanelli": "Silvia Stefanelli",
#     " AGECREDIT": "AGECREDIT"
# }

# def grafico_ndg_senza_processo(
#     df_richieste_bi: pd.DataFrame,
#     df_performance: pd.DataFrame,
#     df_bridge: pd.DataFrame,  # es: df_dt
# ):
#     bi = df_richieste_bi.copy()
#     perf = df_performance.copy()
#     br = df_bridge.copy()

#     # BI
#     if "NDG DEBITORE" not in bi.columns or "GESTORE" not in bi.columns:
#         st.error("In df_full servono 'NDG DEBITORE' e 'GESTORE'.")
#         return
#     bi["ndg_key"] = bi["NDG DEBITORE"].astype(str).str.strip()
#     bi = bi[bi["ndg_key"] != ""]

#     # performance
#     if "posizione_key" not in perf.columns:
#         st.error("In dt_performance manca 'posizione_key'.")
#         return
#     perf["posizione_key"] = perf["posizione_key"].astype(str).str.strip()
#     pos_in_perf = set(perf.loc[perf["posizione_key"] != "", "posizione_key"].unique())

#     # bridge: deve avere posizione_key + ndg
#     pos_col = next((c for c in ["posizione_key", "POSIZIONE_KEY"] if c in br.columns), None)
#     ndg_col = next((c for c in ["NDG DEBITORE", "ndgSoggetto", "ndg", "NDG"] if c in br.columns), None)

#     if pos_col is None or ndg_col is None:
#         st.error("Il bridge non contiene entrambe le colonne: posizione_key e NDG.")
#         st.write("Colonne bridge:", br.columns.tolist())
#         return

#     br["pos_key"] = br[pos_col].astype(str).str.strip()
#     br["ndg_key"] = br[ndg_col].astype(str).str.strip()
#     br = br[(br["pos_key"] != "") & (br["ndg_key"] != "")]

#     # NDG con processo (da performance via bridge)
#     ndg_con_processo = set(br[br["pos_key"].isin(pos_in_perf)]["ndg_key"].unique())

#     # NDG BI senza processo
#     bi_senza_processo = bi[~bi["ndg_key"].isin(ndg_con_processo)].copy()

#     chart_df = (
#         bi_senza_processo
#         .groupby("GESTORE", dropna=False)["ndg_key"]
#         .nunique()
#         .reset_index(name="NDG_senza_processo")
#         .sort_values("NDG_senza_processo", ascending=False)
#     )

#     st.subheader("NDG senza processo per gestore")
#     st.dataframe(chart_df, use_container_width=True)
#     st.bar_chart(chart_df.set_index("GESTORE")["NDG_senza_processo"])

