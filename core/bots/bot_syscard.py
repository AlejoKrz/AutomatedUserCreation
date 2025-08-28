import logging
import os
import time
from datetime import datetime
from pywinauto import Application, mouse
from pywinauto.findwindows import ElementNotFoundError
import random
import string
from core.credential_manager import CredentialManager
from core.utils import guardar_credencial  # Importar la función para guardar credenciales

def generar_contraseña(longitud=10):
    if longitud != 10:
        raise ValueError("La contraseña debe tener exactamente 10 caracteres.")
    
    # Caracteres obligatorios
    mayuscula = random.choice(string.ascii_uppercase)
    minuscula = random.choice(string.ascii_lowercase)
    numero = random.choice(string.digits)
    simbolo = random.choice("!@#$%^&*()-_=+[]{};:,.<>/?")

    # Rellenar el resto hasta llegar a 10 caracteres
    resto = [
        random.choice(
            string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{};:,.<>/?"
        )
        for _ in range(longitud - 4)
    ]

    # Combinar todos los caracteres
    contraseña = [mayuscula, minuscula, numero, simbolo] + resto
    
    # Mezclar para que no queden siempre al inicio
    random.shuffle(contraseña)

    return "".join(contraseña)


class WidgetLogHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        log_entry = self.format(record)
        if self.widget:
            self.widget.log(log_entry)


class SyscardsApp:
    def __init__(self, app_path, widget=None, log_dir='logs/syscard', credentials=None):
        self.app_path = app_path
        self.app = None
        self.main_window = None
        self.widget = widget

        # Cargar credenciales desde el CredentialManager si no se proporcionan
        if credentials is None:
            credential_manager = CredentialManager()
            self.credentials = credential_manager.load_credentials("bot_syscard")
        else:
            self.credentials = credentials

        # Crear carpeta de logs si no existe
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'syscard_app_{datetime.now():%Y%m%d}.log')

        # Configurar logging
        self.logger = logging.getLogger(f'SyscardsApp_{id(self)}')
        self.logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Handler para el widget
        if widget:
            widget_handler = WidgetLogHandler(widget)
            widget_handler.setFormatter(formatter)
            self.logger.addHandler(widget_handler)

        # (Opcional) Handler de consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def click_element(self, element, description=""):
        """Click en elemento con manejo de errores"""
        try:
            element.click_input()
            self.logger.info(f"Click exitoso en: {description}")
        except Exception as e:
            self.logger.error(f"Error al hacer click en {description}: {str(e)}")
            raise

    def fill_user_data(self, user):
        """Llena todos los campos del formulario con datos del modelo de usuario"""
        try:
            user.Password = generar_contraseña(10)
            self.logger.info(f"Contraseña generada automáticamente: {user.Password}")

            # Ventana de mantenimiento de usuarios
            mantenimiento_usuarios = self.main_window.child_window(
                title=" (2.0.0.0) Mantenimiento de Usuarios", 
                control_type="Window"
            )
            
            # Grupo de información principal
            grupo_info = mantenimiento_usuarios.child_window(
                title="Información del Usuario", 
                control_type="Group"
            )

            primer_nombre = user.Nombres.split()[0].capitalize() if user.Nombres else ""
            primer_apellido = user.Apellidos.split()[0].capitalize() if user.Apellidos else ""

            # 1. Establecer login
            grupo_info.child_window(auto_id="txtLogin", control_type="Edit").set_text(user.Login)
            self.logger.debug(f"Login establecido: {user.Login}")

            # 2. Click en campo nombre
            nombre_field = grupo_info.child_window(auto_id="txtNombre", control_type="Edit")
            nombre_field.click_input()
            self.logger.debug("Click en campo nombre realizado")

            # 3. Click en Aceptar (ventana emergente)
            self.click_element(
                self.main_window.child_window(title="Aceptar", auto_id="2", control_type="Button"),
                "Botón Aceptar ventana emergente"
            )

            # 4. Establecer nombre completo
            nombre_completo = f"{primer_nombre} {primer_apellido}"
            nombre_field.set_text(nombre_completo)
            self.logger.debug(f"Nombre establecido: {nombre_completo}")

            # Selección de empresa
            combo_empresa = grupo_info.child_window(auto_id="cboEmpresa", control_type="ComboBox")
            combo_empresa.click_input()
            self.click_element(
                combo_empresa.child_window(title="1 - Cooperativa Policia Nacional  ", control_type="ListItem"),
                "Selección de empresa"
            )

            # Selección de oficina
            combo_oficina = grupo_info.child_window(auto_id="cboOficina", control_type="ComboBox")
            combo_oficina.click_input()

            NumeroOficina = str(int(float(user.Oficina_x003a__x0020_N_x00fa_mer)))

            try:
                office_pattern = f"^{NumeroOficina}\s-\s"
                office_item = combo_oficina.child_window(
                    title_re=office_pattern,
                    control_type="ListItem"
                )
                
                if office_item.exists():
                    self.click_element(office_item, f"Selección oficina {NumeroOficina}")
                else:
                    # Fallback: Buscar manualmente si el patrón falla
                    items = combo_oficina.child_window(control_type="List").children(control_type="ListItem")
                    for item in items:
                        if item.window_text().startswith(f"{NumeroOficina} -"):
                            item.click_input()
                            break
                    else:
                        raise Exception(f"Oficina {NumeroOficina} no encontrada")

            except Exception as e:
                self.logger.error(f"Error seleccionando oficina: {str(e)}")
                raise

            # Información adicional
            grupo_info_ad = self.main_window.child_window(
                title="Información Adicional del Usuario", 
                auto_id="grpInformacionAdi",
                control_type="Group"
            )
            
            # Nivel de acceso
            combo_nivel = grupo_info_ad.child_window(auto_id="cboNivel", control_type="ComboBox")
            combo_nivel.click_input()
            list_box = combo_nivel.child_window(control_type="List")
            self.click_element(
                list_box.child_window(title="3 - Sucursal", control_type="ListItem"),
                "Selección de nivel"
            )

            # Estado
            combo_estado = grupo_info_ad.child_window(auto_id="cboEstado", control_type="ComboBox")
            combo_estado.click_input()
            combo_estado.select("A - Activo") 

            # Producto por defecto
            combo_producto = grupo_info_ad.child_window(auto_id="cboProductoDef", control_type="ComboBox")
            self.click_element(
                combo_producto.child_window(title="2 - Tarjeta de Crédito", control_type="ListItem"),
                "Selección de producto"
            )

            # Configuración de contraseña
            grupo_contraseña = self.main_window.child_window(
                title="Contraseña", 
                control_type="Group", 
                auto_id="grpPassword"
            )
            
            grupo_contraseña.child_window(auto_id="txtPassword", control_type="Edit").set_text(user.Password)
            grupo_contraseña.child_window(auto_id="txtConfirmarPass", control_type="Edit").set_text(user.Password)
            grupo_contraseña.child_window(auto_id="chkCaducaPass", control_type="CheckBox").click_input()

            

            self.logger.info("Datos de usuario llenados correctamente")
            return True

        except Exception as e:
            self.logger.error(f"Error al llenar datos de usuario: {str(e)}")
            raise

    def execute(self, user):
        """Flujo completo de Syscards con modelo de usuario"""
        try:
            # 1. Iniciar aplicación
            self.logger.info("Iniciando aplicación Syscards")
            self.app = Application(backend="uia").start(self.app_path)
            self.main_window = self.app.window(title="Syscards")
            
            # 2. Login con credenciales del gestor o por defecto
            login_username = self.credentials.get('username', 'squiroz')
            login_password = self.credentials.get('password', 'Alejo1713!')
            self.logger.info(f"Usando credenciales: {login_username}")
            
            username = self.main_window.child_window(title="Usuario:", auto_id="txtUsuario", control_type="Edit")
            username.set_text(login_username)
            
            password = self.main_window.child_window(auto_id="txtPwd", control_type="Edit")
            password.set_text(login_password)
            
            self.click_element(
                self.main_window.child_window(title="OK", auto_id="btnAceptar", control_type="Button"),
                "Botón Aceptar login"
            )
            time.sleep(2)

            # 3. Navegación a Administración
            self.logger.info("Navegando a módulo de Administración")
            mouse.click(coords=(97, 610))
            
            self.main_window.child_window(title="naviGroup394", auto_id="naviGroup394", control_type="Pane").click_input()

            # 4. Acceso a Usuarios
            self.click_element(
                self.main_window.child_window(title="Usuarios", control_type="ListItem"),
                "Opción Usuarios"
            )

            # 5. Creación de nuevo usuario
            self.logger.info(f"Iniciando creación de usuario: {user.Login}")
            self.click_element(
                self.main_window.child_window(title="Nuevo", control_type="Button"),
                "Botón Nuevo"
            )

            # 6. Llenado de información con modelo de usuario
            self.fill_user_data(user)

            self.click_element(
                self.main_window.child_window(title="Grabar", control_type="Button"),
                "Botón Grabar"
            )

            # Guardar credenciales generadas
            guardar_credencial("Syscard", user.Login, user.Password)

            # Espera final con verificación
            self.logger.info("Esperando confirmación...")
            start_time = time.time()
            while time.time() - start_time < 5:  # 5 segundos de espera
                try:
                    # Verificar si aparece algún mensaje de confirmación
                    msg_window = self.app.window(title="Mensaje del sistema")
                    if msg_window.exists():
                        mensaje = msg_window.child_window(control_type="Text").window_text()
                        self.logger.info(f"Mensaje del sistema: {mensaje}")
                        break
                except:
                    pass
                time.sleep(0.5)
            self.logger.info("Proceso completado exitosamente")
            return {"status": "success", "message": f"Usuario {user.Login}, Contraseña {user.Password} creado correctamente"}

        except Exception as e:
            self.logger.error(f"Error en el proceso: {str(e)}", exc_info=True)
            if hasattr(self, 'app') and self.app:
                try:
                    self.app.top_window().capture_as_image().save(f"error_syscards_{user.Login}.png")
                except:
                    pass
            return {"status": "error", "message": str(e)}
        
        finally:
            if hasattr(self, 'app') and self.app:
                try:
                    self.app.kill()
                except:
                    pass