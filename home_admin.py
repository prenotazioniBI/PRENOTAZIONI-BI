import streamlit as st
from filtro_df import  mostra_df_filtrato
from excel_funzioni import modifica_celle_excel
from grafici import aggrid_pivot, aggrid_pivot_delta
import io
import pandas as pd



def refreshino(key_suffix=""):
    refresh = st.button("⟳", key=f"refresh_{key_suffix}")
    if refresh:
        st.cache_data.clear()

def home_admin(df, nav, df_full):
    user = st.session_state.get("user")
    if not user or user.get("ruolo") != "admin":
        st.warning("Sessione scaduta o non autorizzata. Effettua di nuovo il login.")
        st.stop()
    else:
        st.title("Area Admin")
        sezione = st.sidebar.radio("",["AGGIORNA", "DA INVIARE","DASHBOARD"])

        if sezione == "DA INVIARE":
            col1, col2, _ = st.columns([0.04, 1, 0.1])
            with col1:
                refreshino(key_suffix="1")
            with col2:
                st.subheader("DA INVIARE")
                mostra_df_filtrato(df_full)


        if sezione == "AGGIORNA":
            col1, col2, col3 = st.columns([0.04, 1, 0.2])
            with col1:
                refreshino(key_suffix="2")
            with col2:
                st.subheader("AGGIORNA")
            with col3: 
                st.write("") 
                salva = st.button("Salva modifiche", key="salva_modifiche_excel")
            
            edited_df = modifica_celle_excel(st.session_state['df_full'])
            if salva:
                if edited_df is None or edited_df.empty:
                    st.warning("Nessuna modifica da salvare.")
                else:
                    updated = 0
                    unmatched = 0
                    for _, row in edited_df.iterrows():
                        uid = row.get('id', None)
                        if pd.isna(uid):
                            unmatched += 1
                            continue

                        mask = st.session_state['df_full']['id'] == uid
                        if mask.any():
                            cols_to_update = [c for c in edited_df.columns if c != 'id']
                            st.session_state['df_full'].loc[mask, cols_to_update] = row[cols_to_update].values
                            updated += mask.sum()
                        else:
                            unmatched += 1
                    buffer = io.BytesIO()
                    st.session_state['df_full'].to_excel(buffer, index=False)
                    buffer.seek(0)
                    file_content = buffer.getvalue()
                    file_data = {
                        'filename': "General/REPORT INCASSI/SOFTWARE INCASSI/prenotazioni.xlsx",
                        'content': file_content,
                        'size': len(file_content)
                    }
                    nav.file_buffer.append(file_data)
                    nav.upload_file()
                    st.cache_data.clear()
                    st.rerun()
                    st.toast(f"Salvate {updated} modifiche. Non abbinate: {unmatched}")


        if sezione == "DASHBOARD":
            st.subheader("DASHBOARD")
            aggrid_pivot_delta(df,
            group_col="CENTRO DI COSTO",
            sub_col="NOME SERVIZIO",
            value_col="COSTO",
            mese_col="MESE",
            height=500)

            st.subheader("PIVOT")
            df["MESE"] = pd.to_numeric(df["MESE"], errors="coerce").fillna(0).astype(int)
            mesi = df["MESE"].dropna().unique().tolist()
            mesi.sort()
            mesi.insert(0, "Tutti")
            mese_sel = st.pills("Filtra per mese", mesi)

            if mese_sel != "Tutti":
                df_filtrato = df[df["MESE"] == mese_sel]
            else:
                df_filtrato = df
            col1, spacer, col2 = st.columns([1, 0.1, 1])
            with col1:
                aggrid_pivot(df_filtrato, "GESTORE", "PORTAFOGLIO", "COSTO", value_name="Totale Costo", group_width=80,sub_width=130,value_width=130,height=500)
            with col2:
                aggrid_pivot(df_filtrato, "GESTORE", "NOME SERVIZIO", "COSTO", value_name="Totale Costo", group_width=80,sub_width=120,value_width=100,height=500)
               
            col1, spacer, col2 = st.columns([1, 0.1, 1])
            with col1:
                aggrid_pivot(df_filtrato, "CENTRO DI COSTO", "NOME SERVIZIO", "COSTO", value_name="Totale Costo", group_width=80,sub_width=120,value_width=100,height=500)
            with col2:
                aggrid_pivot(df_filtrato, "CENTRO DI COSTO", "PORTAFOGLIO", "COSTO", value_name="Totale Importo",group_width=80,sub_width=120,value_width=100,height=500)
            
            col1, spacer, col2 = st.columns([1, 0.1, 1])
            with col1:
                aggrid_pivot(df_filtrato, "PORTAFOGLIO", "GESTORE", "COSTO", value_name="Totale Importo",group_width=80,sub_width=120,value_width=100,height=500)