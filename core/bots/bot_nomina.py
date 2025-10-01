import logging
import os
import time
import pyautogui
import time
from datetime import datetime
from pywinauto import Application, mouse
from pywinauto.timings import Timings
from pywinauto.findwindows import ElementNotFoundError
from core.credential_manager import CredentialManager
from core.utils import guardar_credencial  
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # .../core/bots
IMG_DIR = os.path.join(BASE_DIR, "..", "config", "bot_utils")  # .../core/config/bot_utils
imgs = [
    os.path.join(IMG_DIR, "datos_secundarios_nomina.png")
]

class WidgetLogHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        log_entry = self.format(record)
        if self.widget:
            self.widget.log(log_entry)

class NominaApp:
    def __init__(self, app_path, widget=None, log_dir='logs/nomina', credentials=None):
        self.app_path = app_path
        self.app = None
        self.main_window = None
        self.widget = widget

        # Cargar credenciales desde el CredentialManager si no se proporcionan
        if credentials is None:
            credential_manager = CredentialManager()
            self.credentials = credential_manager.load_credentials("bot_nomina")
        else:
            self.credentials = credentials

        # Crear carpeta de logs si no existe
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'nomina_app_{datetime.now():%Y%m%d}.log')

        # Configurar logging
        self.logger = logging.getLogger(f'NominaApp_{id(self)}')
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

        Timings.window_find_timeout = 5
        Timings.after_clickinput_wait = 0.1

    @staticmethod
    def click_por_imagen_etiqueta(nombres_png, timeout=5, confidences=(0.9, 0.85, 0.8, 0.75, 0.7), region=None, grayscale=True):
        fin = time.time() + timeout
        while time.time() < fin:
            for png in nombres_png:
                for conf in confidences:
                    try:
                        loc = pyautogui.locateCenterOnScreen(png, confidence=conf, region=region, grayscale=grayscale)
                        if loc:
                            pyautogui.click(loc.x, loc.y)
                            return True
                    except Exception:
                        pass
            time.sleep(0.2)
        return False



    def wait_for_element(self, element, timeout=2, retry_interval=0.5, description=""):
        start_time = time.time()
        last_exception = None
        while time.time() - start_time < timeout:
            try:
                if element.exists() and element.is_visible():
                    self.logger.debug(f"Elemento encontrado: {description}")
                    return element
                time.sleep(retry_interval)
            except Exception as e:
                last_exception = e
                time.sleep(retry_interval)
        error_msg = f"Timeout al esperar elemento: {description}"
        if last_exception:
            error_msg += f" (Último error: {str(last_exception)})"
        self.logger.error(error_msg)
        raise ElementNotFoundError(error_msg)

    def click_element(self, element, description="", timeout=1):
        try:
            target = self.wait_for_element(element, timeout=timeout, description=description)
            target.click_input()
            self.logger.info(f"Clic exitoso en: {description}")
            return True
        except Exception as e:
            self.logger.error(f"Error al hacer clic en {description}: {str(e)}")
            if hasattr(self, "app") and self.app:
                try:
                    self.app.top_window().capture_as_image().save(
                        f"error_click_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    )
                except Exception:
                    pass
            raise

    def login(self, username, password):
        try:
            self.logger.info(f"Iniciando login para usuario: {username}")
            login_pane = self.wait_for_element(
                self.main_window.child_window(
                    title="....Login para el Módulo de Usuarios", 
                    control_type="Pane"
                ),
                description="Panel de Login"
            )
            user_field = self.wait_for_element(
                login_pane.child_window(auto_id="1", control_type="Edit"),
                description="Campo de usuario"
            )
            user_field.set_text(username)
            pass_field = self.wait_for_element(
                login_pane.child_window(auto_id="2", control_type="Edit"),
                description="Campo de contraseña"
            )
            pass_field.set_text(password)
            self.click_element(
                login_pane.child_window(title="OK", auto_id="3", control_type="Button"),
                "Botón OK de login"
            )
            self.logger.info("Login completado exitosamente")
        except Exception as e:
            self.logger.error(f"Error en login: {str(e)}")
            raise

    def handle_popups(self, count=7, timeout=2):
        self.logger.info(f"Manejando hasta {count} popups...")
        for i in range(1, count + 1):
            try:
                dialog = self.wait_for_element(
                    self.main_window.child_window(title="ModuloNomina", control_type="Window"),
                    timeout=timeout,
                    description=f"Popup {i}"
                )
                self.click_element(
                    dialog.child_window(title="Aceptar", auto_id="2", control_type="Button"),
                    f"Aceptar en popup {i}"
                )
                self.logger.debug(f"Popup {i} manejado correctamente")
            except ElementNotFoundError:
                self.logger.debug(f"No se encontró popup {i}, continuando...")
                break
            except Exception as e:
                self.logger.warning(f"Error en popup {i}: {str(e)}")
                if hasattr(self, "app") and self.app:
                    try:
                        self.app.top_window().capture_as_image().save(
                            f"error_popup_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                        )
                    except Exception:
                        pass
                continue

    def navigate_to_personal_data(self):
        try:
            self.logger.info("Navegando a Datos Personales...")
            # 1) Construir y esperar el spec de "Nómina"
            nomina_menu_spec = self.main_window.child_window(
                title="Aplicación", control_type="MenuBar"
            ).child_window(title="Nómina", control_type="MenuItem")
            nomina_menu_spec = self.wait_for_element(
                nomina_menu_spec, description="Menú Nómina"
            )  # espera sobre WindowSpecification [web:47]

            # 2) Solo para "Nómina": convertir a wrapper y clic con delta; NO llamar click_element con wrapper
            nomina_menu = nomina_menu_spec.wrapper_object()  # convertir después del wait [web:55]
            ptn = nomina_menu.rectangle().mid_point()
            from pywinauto import mouse
            mouse.click(coords=(ptn.x + 20, ptn.y))  # compensación a la derecha [web:6]

            # 3) Mantener la lógica original para "Datos Personales" (sin cambios)
            datos_personales = self.wait_for_element(
                nomina_menu_spec.child_window(title="Datos Personales", auto_id="58", control_type="MenuItem"),
                description="Opción Datos Personales"
            )  # aquí sí se pasa un spec, no wrapper [web:47]
            self.click_element(datos_personales, "Datos Personales")  # tu helper opera sobre el spec [web:47]

            self.logger.info("Navegacion a Datos Personales completada")
        except Exception as e:
            self.logger.error(f"Error al navegar a Datos Personales: {str(e)}")
            raise


    def execute(self, user=None):
        self.logger.info("Entrando a execute de NominaApp")
        try:
            # Paso seguro: antes de abrir la app
            
            self.logger.info(f"Iniciando aplicación: {self.app_path}")
            self.app = Application(backend="uia").start(self.app_path)

            # Paso seguro: esperando ventana principal
            
            self.logger.info("Esperando ventana principal")
            self.main_window = self.wait_for_element(
                self.app.window(title_re=".*Rol de Pagos.*"),
                timeout=30,
                description="Ventana principal 'Rol de Pagos'"
            )

            # Paso seguro: enfocar ventana
            
            self.main_window.set_focus()
            self.logger.info("Ventana principal enfocada")

            # --- NO PAUSAR ENTRE ABRIR MENÚ Y CLICK EN OPCIÓN ---
            # Abrir menú Archivo y hacer click en Conectar (sin pausa entre estos pasos)
            archivo_menu = self.wait_for_element(
                self.main_window.child_window(
                    title="Aplicación",
                    control_type="MenuBar"
                ).child_window(title="Archivo", control_type="MenuItem"),
                description="Menú Archivo"
            )
            self.click_element(archivo_menu, "Menú Archivo")
            self.click_element(
                archivo_menu.child_window(title="Conectar....", auto_id="2", control_type="MenuItem"),
                "Conectar"
            )
            #Ahora sí, pausa segura después de cerrar el menú
            

            # Login con credenciales del gestor o por defecto
            username = self.credentials.get('username')
            password = self.credentials.get('password')
            self.logger.info(f"Usando credenciales: {username}")
            self.login(username, password)
            

            # Manejar popups
            self.handle_popups(7)
            

            # Navegar a Datos Personales
            self.navigate_to_personal_data()
            

            # Llenar formulario de Datos Personales
            campos = self.wait_for_element(
                self.main_window.child_window(
                    title="Información sobre Datos Personales del Empleado",
                    auto_id="32768",
                    control_type="Window"
                ),
                description="Formulario de Datos Personales"
            )
            

            self.click_element(
                campos.child_window(title="Nuevo", auto_id="6", control_type="Button"),
                "Botón Nuevo"
            )
            

            # Separar apellidos
            apellidos = user.Apellidos.split(" ")
            primer_apellido = apellidos[0]
            segundo_apellido = apellidos[1] if len(apellidos) > 1 else ""

            # Rellenar campos con esperas
            fields = [
                ("43", user.Title, "Cédula"),
                ("42", primer_apellido, "Apellido"),
                ("41", user.Nombres, "Nombre"),
                ("40", segundo_apellido, "Segundo Apellido"),
                ("35", user.Oficina_x003a__x0020_Ciudad_x0020.upper(), "Ciudad"),
                ("31", "CS", "Estado Civil"),
                ("30", "1", "Profesión"),
            ]
            for field_id, value, description in fields:
                
                try:
                    element = campos.child_window(auto_id=field_id, control_type="Edit")
                    element.set_text(value)
                    self.logger.debug(f"Campo {description} llenado con: {value}")
                except Exception as e:
                    self.logger.warning(f"Error al llenar campo {description}: {str(e)}")

            # Manejar dropdown de Sexo
            
            try:
                dropdown = campos.child_window(auto_id="DropDown", control_type="Button")
                Sexo = "M"
                if Sexo == "F":
                    dropdown.type_keys("{DOWN}{ENTER}")
                elif Sexo == "M":
                    dropdown.type_keys("{DOWN}{DOWN}{ENTER}")
                self.logger.info(f"Sexo seleccionado: {Sexo}")
            except Exception as e:
                self.logger.error(f"Error al seleccionar sexo: {str(e)}")

            # Click en coordenadas
            rect = self.main_window.rectangle()
            region = (rect.left, rect.top, rect.width(), rect.height())

            ok = self.click_por_imagen_etiqueta(
                imgs,        # usa la lista definida arriba con rutas completas
                timeout=6,
                region=region
            )
            if not ok:
                self.logger.warning("No se encontró la etiqueta por imagen, reintentando con OCR...")

            
            fields = [
                ("25", str(int(float(user.Oficina_x003a__x0020_Ciudad_x002))), "Ciudad"),
                ("26", "1", "Moneda"),
                ("22", str(int(float(user.Oficina_x003a__x0020_Region))), "Sección"),
                ("9", str(int(float(user.Cargo_x003a__x0020_Tipo_x0020_Em))), "Tipo Empleado"),
                ("24", str(int(float(user.Oficina_x003a__x0020_N_x00fa_mer))), "Oficina"),
                ("23", str(int(float(user.Cargo_x003a__x0020_Departamento_0))), "Departamento"),
                ("21", str(int(float(user.Cargo_x003a__x0020_Cargo_x0020_e0))), "Cargo"),
                ("19", "2", "Cuenta Banco"),
                ("18", "MT", "Turno de Trabajo"),
                ("17", "0", "Años de Servicio"),
                ("14", "5", "Categoría Salarial"),
                ("20", "3", "Banco"),
                ("13", "V", "Estado")
            ]
            for field_id, value, description in fields:
                
                try:
                    element = campos.child_window(auto_id=field_id, control_type="Edit")
                    element.set_text(value)
                    self.logger.debug(f"Campo {description} llenado con: {value}")
                except Exception as e:
                    self.logger.warning(f"Error al llenar campo {description}: {str(e)}")

            
            self.click_element(
                campos.child_window(auto_id="14", control_type="Edit"),
                "Click Fuera de campo"
            )

            self.click_element(
                campos.child_window(title="Grabar", auto_id="4", control_type="Button"),
                "Guardado"
            )

            #Esperar a que se complete el proceso
            time.sleep(5)

            self.logger.info("Proceso de nómina completado correctamente")
            if self.app:
                self.app.kill()

            guardar_credencial("Nomina", user.Login, "INGRESADO")
            
            return {"status": "success"}
        except Exception as e:
            self.logger.critical(f"Error crítico en ejecución: {str(e)}", exc_info=True)
            if hasattr(self, "app") and self.app:
                try:
                    self.app.top_window().capture_as_image().save(
                        f"error_critico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    )
                    self.app.kill()
                except Exception:
                    pass
            raise

