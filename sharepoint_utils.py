import json
import requests
from msal import ConfidentialClientApplication
import os
from urllib.parse import quote



SAVE_TOKEN = False
TOKEN_FILE = "sharepoint_token.json"


class SharePointNavigator:
    def __init__(self, site_url, tenant_id, client_id, client_secret, library_name, folder_path):
        self.site_url = site_url
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.library_name = library_name
        self.folder_path = folder_path
        self.graph_url = "https://graph.microsoft.com/v1.0"
        self.access_token = None
        
        self.app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}"
        )
        self.file_buffer = []  
    
    def login(self):
        try:
            if SAVE_TOKEN and os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'r') as f:
                    token_data = json.load(f)
                    if 'access_token' in token_data:
                        self.access_token = token_data['access_token']
                        if self._test_token():
                            return True
            
            result = self.app.acquire_token_for_client(
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                
                if SAVE_TOKEN:
                    with open(TOKEN_FILE, 'w') as f:
                        json.dump({"access_token": self.access_token}, f)
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Errore: {str(e)}")
            return False
    
    def _test_token(self):
        """Test token validity"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(f"{self.graph_url}/sites", headers=headers)
            return response.status_code == 200
        except:
            return False
    
    def get_site_id(self):
        site_path = self.site_url.replace("https://", "").replace("http://", "")
        parts = site_path.split('/')
        hostname = parts[0]
        if len(parts) > 2 and parts[1] == "sites":
            site_name = parts[2]
            api_url = f"{self.graph_url}/sites/{hostname}:/sites/{site_name}"
        else:
            api_url = f"{self.graph_url}/sites/{hostname}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                site_data = response.json()
                return site_data['id']
            else:
                return None
        except Exception as e:
            return None
    
    def get_drive_id(self, site_id):
        url = f"{self.graph_url}/sites/{site_id}/drives"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                drives = response.json()["value"]
                
                print(f"  Trovate {len(drives)} libraries:")
                for drive in drives:
                    print(f"   - {drive['name']} (ID: {drive['id'][:20]}...)")
                print()
                
                search_names = [
                    self.library_name,
                    "Shared Documents",
                    "Documents", 
                    "Documenti",
                    "Documenti condivisi"
                ]
                
                for search_name in search_names:
                    for drive in drives:
                        if search_name.lower() in drive['name'].lower():
                            print(f"Uso library: {drive['name']}")
                            return drive['id'], drive['name']
                
                if drives:
                    print(f"Uso library default: {drives[0]['name']}")
                    return drives[0]['id'], drives[0]['name']
                
                print("Nessuna library trovata")
                return None, None
            else:
                print(f"Errore: {response.status_code}")
                return None, None
                
        except Exception as e:
            print(f"Errore: {str(e)}")
            return None, None
    
    def navigate_to_folder(self, site_id, drive_id, folder_path):
        encoded_path = quote(folder_path)
        url = f"{self.graph_url}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                items = response.json()["value"]
                print(f"Path trovato! ({len(items)} elementi)\n")
                return items, folder_path
            
            elif response.status_code == 404:
                print("Path completo non trovato, navigazione step-by-step...\n")
                return self._navigate_progressively(site_id, drive_id, folder_path)
            
            else:
                print(f"Errore {response.status_code}")
                return [], None
                
        except Exception as e:
            print(f"Errore: {str(e)}")
            return [], None
    
    def _navigate_progressively(self, site_id, drive_id, folder_path):
        """Navigate folder by folder"""
        folders = folder_path.split('/')
        current_items = []
        successful_path = ""
        
        print("🔄 Navigazione progressiva:")
        
        url = f"{self.graph_url}/sites/{site_id}/drives/{drive_id}/root/children"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                root_items = response.json()["value"]
                print(f"  📂 Root library ({len(root_items)} elementi)")
                
                root_folders = [item['name'] for item in root_items if 'folder' in item]
                if root_folders:
                    print(f"     Cartelle: {', '.join(root_folders[:5])}")
                    if len(root_folders) > 5:
                        print(f"     ... e altre {len(root_folders)-5}")
                print()
        except:
            pass
        
        current_path = ""
        for i, folder_name in enumerate(folders):
            if i == 0:
                current_path = folder_name
            else:
                current_path = f"{current_path}/{folder_name}"
            
            print(f"  → Accedo a: {current_path}")
            
            encoded_path = quote(current_path)
            url = f"{self.graph_url}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"
            
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    current_items = response.json()["value"]
                    successful_path = current_path
                    print(f"     ✓ OK ({len(current_items)} elementi)")
                    
                    if i == len(folders) - 1:
                        print(f"\nRaggiunto: {successful_path}\n")
                        return current_items, successful_path
                    
                    subfolders = [item['name'] for item in current_items if 'folder' in item]
                    if subfolders and i < len(folders) - 1:
                        next_folder = folders[i + 1]
                        if next_folder not in subfolders:
                            print(f"     '{next_folder}' non trovata")
                            print(f"     Cartelle disponibili: {', '.join(subfolders[:5])}")
                            break
                else:
                    print(f"     ✗ Errore {response.status_code}")
                    
                    if successful_path:
                        print(f"\nFermato a: {successful_path}")
                        return current_items, successful_path
                    break
                    
            except Exception as e:
                print(f"     ✗ Errore: {str(e)}")
                break
        
        return current_items, successful_path

    def download_file(self, site_id, drive_id, file_path):
        """Scarica un file da SharePoint"""
        encoded_path = quote(file_path)
        url = f"{self.graph_url}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        file_data = {
            'filename': file_path,
            'content': response.content,
            'size': len(response.content)
        }
        
        self.file_buffer.append(file_data)
        return file_data

    def upload_file_direct(self, site_id, drive_id, file_path, content):
        """Upload diretto senza buffer - per creazione file utente"""
        encoded_path = quote(file_path)
        url = f"{self.graph_url}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/octet-stream"
        }
        
        response = requests.put(url, headers=headers, data=content)
        
        if response.status_code in [200, 201]:
            print(f"File '{file_path}' caricato con successo")
            return True
        else:
            print(f"Errore upload: {response.status_code}")
            return False

    def file_exists(self, site_id, drive_id, file_path):
        """Verifica se un file esiste su SharePoint"""
        encoded_path = quote(file_path)
        url = f"{self.graph_url}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            return response.status_code == 200
        except:
            return False

    def list_user_files(self, site_id, drive_id):
        """Lista tutti i file *_prenotazioni.parquet nella cartella"""
        url = f"{self.graph_url}/sites/{site_id}/drives/{drive_id}/root:/{quote(self.folder_path)}:/children"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                items = response.json()["value"]
                # Filtra solo i file che terminano con _prenotazioni.parquet
                user_files = [
                    item['name'] for item in items 
                    if item['name'].endswith('_prenotazioni.parquet') 
                    and item['name'] != 'prenotazioni.parquet'
                ]
                return user_files
            return []
        except Exception as e:
            print(f"Errore lista file utente: {e}")
            return []

    def upload_file(self):
        """Upload dei file nel buffer"""
        for file_data in self.file_buffer:
            print(f"📤 Upload finale: {file_data['filename']}")
            encoded_path = quote(file_data['filename'])
            url = f"{self.graph_url}/sites/{self.get_site_id()}/drives/{self.get_drive_id(self.get_site_id())[0]}/root:/{encoded_path}:/content"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.put(url, headers=headers, data=file_data['content'])
            if response.status_code in [200, 201]:
                print(f"File '{file_data['filename']}' caricato su SharePoint!")
            else:
                print(f"Errore upload: {response.status_code} - {response.text}")