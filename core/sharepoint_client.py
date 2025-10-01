import requests
from .models import SharePointUser
from .config.settings import SHAREPOINT

class SharePointClient:
    def __init__(self):
        self.base_url = f"https://graph.microsoft.com/v1.0/sites/{SHAREPOINT['site_id']}/lists/{SHAREPOINT['list_id']}/items"
        self.headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            'Prefer': 'HonorNonIndexedQueriesWarningMayFailRandomly'
        }

    def _get_access_token(self):
        """Obtiene token de acceso para la API."""
        auth_url = f"https://login.microsoftonline.com/{SHAREPOINT['tenant_id']}/oauth2/v2.0/token"
        response = requests.post(auth_url, data={
            "client_id": SHAREPOINT['client_id'],
            "client_secret": SHAREPOINT['client_secret'],
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials"
        })
        return response.json()["access_token"]

    def get_pending_users(self):
        """
        Obtiene usuarios aprobados desde la lista de SharePoint y los convierte a objetos SharePointUser.
        """
        select_fields = [
            "id",
            "Title",
            "Oficina",
            "Nombres",
            "Apellidos",
            "G_x00e9_nero",
            "Oficina_x003a__x0020_N_x00fa_mer",
            "Oficina_x003a__x0020_Extreme_x00",
            "Oficina_x003a__x0020_Ciudad_x002",
            "Oficina_x003a__x0020_OU_x0020_Ac",
            "Cargo",
            "Cargo_x003a__x0020_Correo",
            "Cargo_x003a__x0020_Cargo_x0020_e",
            "Cargo_x003a__x0020_Rol_x0020_en_",
            "Cargo_x003a__x0020_Departamento",
            "Cargo_x003a__x0020_Cargo_x0020_e0",
            "Cargo_x003a__x0020_Departamento_0",
            "Cargo_x003a__x0020_Tipo_x0020_Em",
            "Cargo_x003a__x0020_Rol_x0020_Sys",
            "Cargo_x003a__x0020_Rol_x0020_Ext",
            "Cargo_x003a__x0020_Departamento_",
            "JefeInmediato",
            "Login",
            "Correoelectr_x00f3_nico",
            "Departamento",
            "Departamento_x003a__x0020_Unidad",
            "Oficina_x003a_Login_x0020_Nodos_",
            "Oficina_x003a__x0020_Region",
            "Oficina_x003a__x0020_Ciudad_x0020",
            "Oficina_x003a__x0020_Regi_x00f3_",
            "Oficina_x003a__x0020_Provincia",

            "Fechadeingreso",
            "Estado"
        ]
        select_query = ','.join(select_fields)

        url = (
            f"{self.base_url}"
            f"?$expand=fields($select={select_query})&filter=fields/Estado eq 'Aprobado'"
        )

        response = requests.get(url, headers=self.headers)
        if not response.ok:
            print("Error:", response.status_code)
            print(response.text)
            response.raise_for_status()
        data = response.json().get("value", [])
        # Solo procesa los que tengan 'fields'
        usuarios = []
        for item in data:
            if "fields" in item:
                # Elimina '@odata.etag' si existe en fields
                fields = {k: v for k, v in item["fields"].items() if k != "@odata.etag"}
                try:
                    usuario = SharePointUser(**fields)
                    usuarios.append(usuario)
                except Exception as e:
                    print(f"Error creando SharePointUser: {e}")
                    print(fields)
        return usuarios

    def update_user_status(self, item_id: str, new_status: str):
        """Actualiza el estado del usuario en SharePoint."""
        url = f"{self.base_url}/{item_id}/fields"
        data = {"Estado": new_status}
        response = requests.patch(url, headers=self.headers, json=data)
        if not response.ok:
            print(f"Error actualizando estado a {new_status}: {response.status_code}")
            print(response.text)
            response.raise_for_status()
