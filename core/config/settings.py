import os
from dotenv import load_dotenv

# Carga variables de entorno desde .env (opcional pero recomendado)
load_dotenv()

# ===== SharePoint =====
SHAREPOINT = {
    "tenant_id": os.getenv("TENANT_ID", "tu_tenant_id"),
    "client_id": os.getenv("CLIENT_ID", "tu_client_id"),
    "client_secret": os.getenv("CLIENT_SECRET", "tu_client_secret"),
    "site_id": os.getenv("SITE_ID", "tu_site_id"),
    "list_id": os.getenv("LIST_ID", "tu_list_id"),
    "polling_interval": 5,
}

# ===== Bots =====
BOTS = {
    "NominaApp": {
        "app_path": r"C:\Users\squiroz\OneDrive - Cooperativa Policía Nacional\Documentos\Reportes\ModuloNomina.exe"
    },
    "Cobis": {
        "app_path": r"C:\Cobis\Admin\Seguridad\Segurid.exe"
    },
    "Syscard": {
        "app_path": r"C:\Syscards_PRODUCCION\Win\clientasm\winLaunch.exe"
    },
    "ExtremeWeb": {
        "url": "http://172.20.0.50/ExtremeWebTs/#/Login"  # Reemplaza con la URL real
    }
}

# ===== Logging =====
LOGGING = {
    "level": "INFO",
    "file": "user_automation.log",
    "max_size": 10,
    "backup_count": 3,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# ===== Validaciones =====
VALIDATIONS = {
    "required_fields": ["name", "email", "department"],
    "email_domains": ["@tudominio.com", "@partner.com"],
}

WORKFLOW_INTERVAL_MINUTES = 1

# Parámetros de prueba
TEST_MODE = False
BOTS_A_PROBAR = ["bot_cobis"]
