import logging
import os
import time
from datetime import datetime
from pywinauto import Application
from pywinauto.keyboard import send_keys

from pywinauto.findwindows import ElementNotFoundError
from core.credential_manager import CredentialManager

class WidgetLogHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        log_entry = self.format(record)
        if self.widget:
            self.widget.log(log_entry)

class CobisApp:
    def __init__(self, app_path, widget=None, log_dir='logs/cobis', credentials=None):
        self.app_path = app_path
        self.app = None
        self.main_window = None
        self.widget = widget

        # Cargar credenciales desde el CredentialManager si no se proporcionan
        if credentials is None:
            credential_manager = CredentialManager()
            self.credentials = credential_manager.load_credentials("bot_cobis")
        else:
            self.credentials = credentials

        # Crear carpeta de logs si no existe
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'cobis_app_{datetime.now():%Y%m%d}.log')

        # Configurar logging
        self.logger = logging.getLogger(f'CobisApp_{id(self)}')
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
        """Ejecuta un click en el elemento especificado con logging"""
        try:
            element.click_input()
            self.logger.info(f"Click realizado: {description}")
        except Exception as e:
            self.logger.error(f"Error al hacer click en {description}: {str(e)}")
            raise

    def handle_server_dialog(self):
        """Maneja la búsqueda del diálogo de conexión al servidor"""
        try:
            dialog = self.main_window.window(title="Conexión con el Servidor")
            self.logger.debug("Diálogo encontrado: 'Conexión con el Servidor'")
            return dialog
        except ElementNotFoundError:
            try:
                dialog = self.main_window.window(title="Conexión al Servidor")
                self.logger.debug("Diálogo encontrado: 'Conexión al Servidor'")
                return dialog
            except ElementNotFoundError:
                dialog = self.main_window.window(title_re="Conexión.*Servidor")
                self.logger.debug(f"Diálogo encontrado por patrón: {dialog.window_text()}")
                return dialog

    def handle_login(self, server_dialog):
        """Maneja el proceso de ingreso de credenciales"""
        try:
            username_field = server_dialog.child_window(auto_id="_txtCampo_1", control_type="Edit")
            password_field = server_dialog.child_window(auto_id="_txtCampo_2", control_type="Edit")
            
            # Usar credenciales del gestor si están disponibles
            username = self.credentials.get('username', 'squiroz')
            password = self.credentials.get('password', 'Alejo1713#')
            
            username_field.set_text(username)
            password_field.set_text(password)
            self.logger.info("Credenciales ingresadas en el formulario de login")
        except Exception as e:
            self.logger.error(f"Error al ingresar credenciales: {str(e)}")
            raise

    def click_accept_button(self, server_dialog):
        """Intenta hacer clic en Aceptar o OK"""
        try:
            self.click_element(server_dialog.child_window(title="Aceptar", control_type="Button"), "Botón Aceptar")
        except ElementNotFoundError:
            self.click_element(server_dialog.child_window(title="OK", control_type="Button"), "Botón OK")

    def check_distributivo_error(self, parent_window, timeout=3):
        """
        Verifica si aparece el mensaje de error de distributivo.
        Retorna True si aparece el error, False si no aparece.
        """
        try:
            error_dialog = parent_window.window(title="Mensaje del servidor", control_type="Window")
            if error_dialog.exists(timeout=timeout):
                message_text = error_dialog.child_window(control_type="Text").window_text()
                
                if "No Existe el distributivo" in message_text:
                    self.logger.warning("Se encontró mensaje de error: No Existe el distributivo")
                    self.click_element(
                        error_dialog.child_window(title="Aceptar", control_type="Button"),
                        "Aceptar en mensaje de error"
                    )
                    return True
        except ElementNotFoundError:
            return False
        except Exception as e:
            self.logger.warning(f"Error al verificar diálogo de distributivo: {str(e)}")
            return False
        return False

    def handle_post_login_dialogs(self):
        """Maneja los diálogos posteriores al login"""
        dialogs = ["Copyright", "Datos Generales", "Segurid"]
        
        for dialog_title in dialogs:
            try:
                dialog = self.main_window.window(title=dialog_title, control_type="Window")
                try:
                    self.click_element(dialog.child_window(title="Aceptar", control_type="Button"), f"Aceptar en {dialog_title}")
                except ElementNotFoundError:
                    self.click_element(dialog.child_window(title="OK", control_type="Button"), f"OK en {dialog_title}")
                self.logger.info(f"Diálogo {dialog_title} manejado correctamente")
            except Exception as e:
                self.logger.warning(f"No se pudo manejar el diálogo {dialog_title}: {str(e)}")

    def fill_funcionario_fields(self, ventana_funcionarios, user):
        """Llena todos los campos del formulario de registro de funcionarios"""
        try:
            campos = {
                "_txtCampo_0": f" {user.Apellidos} {user.Nombres}",
                "_txtCampo_1": user.Login,
                "txtCedula": user.Title,
                "_txtCampo_6": str(int(float(user.Oficina_x003a__x0020_N_x00fa_mer))),
                "_txtCampo_2": str(int(float(user.Cargo_x003a__x0020_Departamento_))),
                "_txtCampo_3": str(int(float(user.Cargo_x003a__x0020_Cargo_x0020_e))),
                "_txtCampo_4": "1668",          #Func. Inmediato Superior
                "_txtCampo_7": "V",
                "_txtCampo_10": "steven.quiroz@cpn.fin.ec",
            }
            
            Sexo = "F"

            for auto_id, valor in campos.items():
                campo = ventana_funcionarios.child_window(auto_id=auto_id, control_type="Edit")
                campo.set_text(str(valor))
                time.sleep(0.1)
                self.logger.debug(f"Campo {auto_id} llenado con: {valor}")
            
            try:
                ventana_funcionarios.child_window(title=Sexo, control_type="RadioButton").click()
                self.logger.debug(f"Sexo seleccionado: {Sexo}")
            except Exception:
                self.logger.warning("No se encontró opción de sexo")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error al llenar formulario de funcionario: {str(e)}")
            raise


    def asignRol(self, ventana_funcionarios, user):
        try:
            rol_button= ventana_funcionarios.child_window(title="Roles", control_type="Button")
            rol_button.click_input()
            time.sleep(1)
            self.logger.info("Botón Roles presionado")
            rol_window= self.main_window.window(title="Roles por Usuario")
            rol_field = rol_window.child_window(auto_id="_txtCampo_1", control_type="Edit")
            rol_field.set_text(str(int(float(user.Cargo_x003a__x0020_Rol_x0020_en_))))
            rol_horario = rol_window.child_window(auto_id="_txtCampo_2", control_type="Edit")
            rol_horario.set_text("1")
            rol_transmitir = rol_window.child_window(title="Transmitir", control_type="Button")
            rol_transmitir.click_input()
        except Exception as e:
            self.logger.error(f"Error al asignar rol: {str(e)}")
            raise
    
    def asignLogin(self, ventana_funcionarios, user):
        try:
            login_button= ventana_funcionarios.child_window(title="Login", control_type="Button")
            login_button.click_input()
            self.logger.info("Botón Login presionado")
            login_window= self.main_window.window(title="Login en Nodos")
            filial_field = login_window.child_window(auto_id="_txtCampo_1", control_type="Edit")
            filial_field.set_text("1")
            oficina_field = login_window.child_window(auto_id="_txtCampo_2", control_type="Edit")
            oficina_field.set_text(str(int(float(user.Oficina_x003a__x0020_N_x00fa_mer))))
            nodo_field = login_window.child_window(auto_id="_txtCampo_3", control_type="Edit")
            nodo_field.set_text(str(int(float(user.Oficina_x003a_Login_x0020_Nodos_))))
            login_transmitir = login_window.child_window(title="Transmitir", control_type="Button")
            login_transmitir.click_input()
        except Exception as e:
            self.logger.error(f"Error al asignar login: {str(e)}")
            raise


    def execute(self, user):
        """Método principal que ejecuta todo el flujo"""
        try:
            self.logger.info("Iniciando aplicación COBIS")
            self.app = Application(backend="uia").start(self.app_path)
            self.main_window = self.app.window(title="C.O.B.I.S. Subsistema de Seguridad")
            
            # Navegación del menú
            menu_bar = self.main_window.child_window(auto_id="MainMenu1", control_type="MenuBar")
            self.click_element(menu_bar.child_window(title="Conexión", control_type="MenuItem"), "Menú Conexión")
            self.click_element(self.main_window.child_window(title="Log on", control_type="MenuItem"), "Opción Log on")
            
            # Proceso de login
            server_dialog = self.handle_server_dialog()
            self.handle_login(server_dialog)
            self.click_accept_button(server_dialog)
            
            # Manejo de diálogos posteriores
            self.handle_post_login_dialogs()

            # Verificar error de distributivo
            if self.check_distributivo_error(self.main_window):
                self.logger.warning("Error de distributivo detectado y manejado")

            # Navegación a Funcionarios
            menu_bar = self.main_window.child_window(auto_id="MainMenu1", control_type="MenuBar")
            self.click_element(menu_bar.child_window(title="Funcionarios", control_type="MenuItem"), "Menú Funcionarios")
            self.click_element(self.main_window.child_window(title="Ingresar", control_type="MenuItem"), "Opción Ingresar")

            # Llenado de formulario
            ventana_func = self.main_window.window(title="Registro de Funcionarios")
            self.fill_funcionario_fields(ventana_func, user)

            # Hacer clic directo en el botón Transmitir
            try:
                transmitir_btn = ventana_func.child_window(title="Transmitir", auto_id="_cmdBoton_0", control_type="Button")
                transmitir_btn.click_input()
                time.sleep(2)  # Espera breve después del clic
                self.logger.info("Botón Transmitir presionado exitosamente")
            except Exception as e:
                error_msg = f"Error al presionar Transmitir: {str(e)}"
                self.logger.error(error_msg)
                return {"status": "error", "message": error_msg}
            
            time.sleep(2)  # Espera para que se procese la transmisión
            self.logger.info("Usuario creado exitosamente")
            self.logger.info(f"Se procede a asignar rol: {user.Cargo_x003a__x0020_Rol_x0020_en_}")
            self.asignRol(ventana_func, user)      
            self.asignLogin(ventana_func, user)
            self.logger.info(f"Se asignó login en nodo: {user.Oficina_x003a_Login_x0020_Nodos_}")      
            self.logger.info("Formulario de funcionario cerrado")
            return {"status": "success", "message": "Proceso completado correctamente"}
            
        except Exception as e:
            self.logger.critical(f"Error en la ejecución: {str(e)}", exc_info=True)
            if hasattr(self, 'main_window') and self.main_window:
                try:
                    error_img = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    self.main_window.capture_as_image().save(error_img)
                    self.logger.info(f"Captura de pantalla guardada como {error_img}")
                except Exception as img_error:
                    self.logger.error(f"No se pudo capturar pantalla: {str(img_error)}")
            
            return {"status": "error", "message": str(e)}
        
        finally:
            if hasattr(self, 'app') and self.app:
                try:
                    self.app.kill()
                    self.logger.info("Aplicación COBIS cerrada")
                except Exception:
                    self.logger.warning("No se pudo cerrar la aplicación COBIS")