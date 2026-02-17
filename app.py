import streamlit as st
from PIL import Image
from streamlit_option_menu import option_menu
import importlib
import os
from auth import authentication
import inspect

def get_pages_by_role(role):
    
    role_config = {
        'admin': {
            'folder': 'admin_pag',
            'pages':  ['Nuova Bi', 'Convalida Dati Bi', 'Richieste In Sospeso Bi', 'Richieste Evase Bi', 'Diffide E Welcome Letter', 'Telegrammi'],
            'page_labels': ['Nuova Bi', 'Convalida Dati Bi', 'Richieste In Sospeso Bi', 'Richieste Evase Bi', 'Diffide E Welcome Letter', 'Telegrammi'],
            'icons':['bi-plus-circle', 'bi-list-check', 'bi-cloud-plus', 'bi-box-arrow-right','bi-list-check','bi-list-check']
        },
        'team leader': {
            'folder': 'teamleader_pag',
            'pages': ['Business Information', 'Nuova BI',  'Nuova Diffida, Telegramma, Welcome Letter','Diffide, Telegrammi, Welcome Letter', 'Richiesta Massiva'],
            'page_labels':['Business Information', 'Nuova BI',  'Nuova Diffida, Telegramma, Welcome Letter','Diffide, Telegrammi, Welcome Letter', 'Richiesta Massiva'],
            'icons': ['bi-person', 'bi-plus-circle', 'bi-plus-circle',  'bi-list-check', 'bi-person-lines-fill']
        },
        'analista': {
            'folder': 'analista_pag',
            'pages': ["Pivot", "Grafici"],
            'page_labels': ["Pivot", "Grafici"],
            'icons': ['bi-table' , 'bi-graph-up']
        },
        'utente': {
            'folder': 'user_pag',
            'pages': ['Le mie Bi', 'Nuova Bi',  'Nuova Diffida - Telegramma - Welcome Letter','Le mie Diffide - Telegrammi - Welcome letter', 'Analisi'],
            'page_labels': ['Le mie Bi', 'Nuova Bi', 'Nuova Diffida - Telegramma - Welcome Letter','Le mie Diffide - Telegrammi - Welcome letter','Analisi'],
            'icons': [ 'bi-person-lines-fill', 'bi-plus-circle', 'bi-plus-circle', 'bi-list-check', 'bi-graph-up']
        }
    }
    
    if role not in role_config:
        st.error(f"Ruolo '{role}' non riconosciuto")
        return [], [], []
    
    config = role_config[role]
    PAGES_FOLDER = config['folder']
    page_order = config['pages']
    page_labels = config['page_labels']
    icons = config['icons']
    
    pages = []
    modules = []
    BLACKLIST_FILES = ['__init__', 'test', 'auth', 'utils']
    
    # Verifica se la cartella esiste
    if not os.path.exists(PAGES_FOLDER):
        st.error(f"Directory '{PAGES_FOLDER}' non trovata per il ruolo {role}!")
        return [], [], []
    
    # Ottieni i file nella cartella
    files = [f[:-3] for f in os.listdir(PAGES_FOLDER) 
             if f.endswith('.py') and f[:-3] not in BLACKLIST_FILES]
    
    # Ordina secondo l'ordine specificato e importa moduli
    for i, page_file in enumerate(page_order):
        if page_file in files:
            try:
                pages.append(page_labels[i])
                module = importlib.import_module(f'{PAGES_FOLDER}.{page_file}')
                modules.append(module)
            except ImportError as e:
                st.warning(f"Impossibile importare il modulo '{page_file}': {e}")
                continue
    
    return pages, icons[:len(pages)], modules

class MultiApp:
    def __init__(self):
        self.apps = []

    def add_app(self, title, function):
        self.apps.append({
            "title": title,
            "function": function
        })

    @staticmethod
    def main():
        if "user" not in st.session_state:

            ruolo, username, email = authentication()
            
            if ruolo and username and email:
                st.session_state["user"] = {
                    "username": username,
                    "ruolo": ruolo,
                    "email": email,  
                    "nome": username 
                }
                st.rerun()
            else:
                st.stop()
        
        user = st.session_state.user
        role = user["ruolo"]
        username = user["username"]

        pages, icons, modules = get_pages_by_role(role)
        
        if not pages:
            st.error("Nessuna pagina disponibile per il tuo ruolo!")
            return


        with st.sidebar:
       
            app = option_menu(
                menu_title="Menu",
                options=pages,
                icons=icons,
                menu_icon="bi-list",
                default_index=0,
                styles={
                "container": {
                    "padding": "0!important",
                    "background-color": "#e8e7dd"
                },
                "icon": {
                    "color": "#3d3a2a",
                    "font-size": "18px"
                },
                "nav-link": {
                    "font-size": "16px",
                    "text-align": "left",
                    "margin": "10px 0",
                    "color": "#3d3a2a",
                    "background-color": "transparent",
                    "font-family": "Styrene B"
                },
                "nav-link-selected": {
                    "background-color": "#bb5a38",
                    "color": "#f4f3ed",
                    "font-family": "Styrene B"
                },
            }
        )

        try:
            selected_index = pages.index(app)
            main_func = modules[selected_index].main
            sig = inspect.signature(main_func)
  
            data_dict = {
                'user': user,
                'df_full': st.session_state.get('df_full'),
                'df_soggetti': st.session_state.get('df_soggetti'),
                'df_utenza': st.session_state.get('df_utenza'),
                'df_dt_full': st.session_state.get('df_dt_full'),
                'dt_soggetti': st.session_state.get('dt_soggetti'),
                'navigator': st.session_state.get('navigator'),
                'navigator_dt': st.session_state.get('navigator_dt')
            }
            
            if len(sig.parameters) > 0:
                modules[selected_index].main(**data_dict)
            else:
                modules[selected_index].main()
        except Exception as e:
            st.error(f"Errore nell'esecuzione della pagina: {e}")

if __name__ == "__main__":
    MultiApp.main()