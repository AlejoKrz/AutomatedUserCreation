import subprocess
import logging
import random
import string
import os
from datetime import datetime


def generar_contraseña(longitud=10):
    if longitud < 10:
        raise ValueError("La contraseña debe tener al menos 10 caracteres.")
    mayuscula = random.choice(string.ascii_uppercase)
    simbolo = random.choice("!@#$%^&*()-_=+[]{};:,.<>/?")
    otros = [
        random.choice(
            string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{};:,.<>/?"
        )
        for _ in range(longitud - 2)
    ]
    contraseña_lista = [mayuscula, simbolo] + otros
    random.shuffle(contraseña_lista)
    return ''.join(contraseña_lista)

def construir_proxy_addresses(user):
        correo = user.Correoelectr_x00f3_nico.strip() if user.Correoelectr_x00f3_nico else None
        correobool = user.Cargo_x003a__x0020_Correo.strip().lower() if user.Cargo_x003a__x0020_Correo else "x"

        if not correo:
            return None  # No hay correo válido

        if correobool == "x":
            # Usar como proxyAddresses principal
            return f"SMTP:{correo}"
        else:
            # No usar proxyAddresses si ya se va a usar el correo como Login principal
            return None

class ADBot:
    def __init__(self, widget=None, log_dir='logs/ad', credentials=None):
        self.widget = widget
        self.credentials = credentials or {}
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'ad_bot_{datetime.now():%Y%m%d}.log')
        self.logger = logging.getLogger(f'ADBot_{id(self)}')
        self.logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(log_file)
        self.logger.addHandler(file_handler)

    
    def execute(self, user):
        # Log de credenciales disponibles (AD no las usa para login pero es informativo)
        if self.credentials:
            self.logger.info(f"Credenciales del gestor disponibles para AD: {self.credentials.get('username', 'N/A')}")
        else:
            self.logger.info("Usando configuración por defecto para AD")
            
        # Obtener primer nombre y primer apellido, y capitalizarlos
        oficina = user.Oficina.strip() if user.Oficina else ""
        oficina_lower = oficina.lower()
        if oficina_lower in ["matriz administrativo", "quito tenis administrativo"]:
            oficina = "MATRIZ"
        elif oficina_lower == "quito tenis":
            oficina = "QUITO TENIS"
        else:
            oficina = oficina.upper()

        primer_nombre = user.Nombres.split()[0].capitalize() if user.Nombres else ""
        primer_apellido = user.Apellidos.split()[0].capitalize() if user.Apellidos else ""

        # Construir el string 'nombres'
        Nombre_Apellido = f"{primer_nombre} {primer_apellido}"

        contraseña = generar_contraseña()

        correobool = user.Cargo_x003a__x0020_Correo

        # Si correobool != "x", usar login_dominio como EmailAddress
        email_address = user.Correoelectr_x00f3_nico
        if correobool.lower() != "x":
            email_address = f"{user.Login}@cpn.fin.ec"
        
        departamento = user.Cargo_x003a__x0020_Departamento.strip() if user.Cargo_x003a__x0020_Departamento and isinstance(user.Cargo_x003a__x0020_Departamento, str) else "N/A"
        
        # Construye los argumentos para el script con los nuevos nombres
        script_path = os.path.abspath("core/bots/Script_AD.ps1")
        ou = user.Departamento_x003a__x0020_Unidad if user.Departamento_x003a__x0020_Unidad else user.Oficina_x003a__x0020_OU_x0020_Ac
        args = [
            "powershell",
            "-ExecutionPolicy", "Bypass",
            "-File", script_path,
            "-Nombre_Apellido", Nombre_Apellido,
            "-Nombres", user.Nombres,
            "-Apellidos", user.Apellidos,
            "-Login", user.Login,
            "-Login_dominio", f"{user.Login}@cpn.fin.ec",
            "-Contraseña", contraseña,
            "-OU", ou,
            "-DisplayName", Nombre_Apellido,
            "-Cargo", user.Cargo,
            "-Departamento", departamento,
            "-Ciudad", user.Oficina_x003a__x0020_Ciudad_x0020.upper(),
            "-Provincia", user.Oficina_x003a__x0020_Provincia,
            "-Oficina", oficina,
            "-EmailAddress", email_address
        ]
        
        proxyAddresses = construir_proxy_addresses(user)

        if proxyAddresses:
            args += ["-proxyAddresses", proxyAddresses]

        try:
            self.logger.info(f"Ejecutando script AD para {user.Nombres} {user.Apellidos}")
            result = subprocess.run(
                args,
                capture_output=True,
                text=True
            )
            # Captura ambos streams
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            log_msg = f"PowerShell STDOUT:\n{stdout}\nPowerShell STDERR:\n{stderr}"
            self.logger.info(log_msg)
            if self.widget:
                self.widget.log(log_msg)
            if result.returncode == 0:
                msg = f"Usuario AD creado correctamente, contraseña {contraseña} Verifica detalles:\n{stdout}"
                self.logger.info(msg)
                if self.widget:
                    self.widget.log(msg)
                return {"status": "success", "stdout": stdout, "stderr": stderr, "contraseña": contraseña}
            else:
                msg = f"Error creando usuario AD. Verifica detalles:\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
                self.logger.error(msg)
                if self.widget:
                    self.widget.log(msg)
                return {"status": "error", "error": stderr, "stdout": stdout}
        except Exception as e:
            msg = f"Excepción ejecutando script AD: {str(e)}"
            self.logger.error(msg)
            if self.widget:
                self.widget.log(msg)
            return {"status": "error", "error": str(e)}