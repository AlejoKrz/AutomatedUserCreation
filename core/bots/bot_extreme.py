import logging
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from core.credential_manager import CredentialManager
from core.utils import guardar_credencial  

class WidgetLogHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        log_entry = self.format(record)
        if self.widget:
            self.widget.log(log_entry)

class ExtremeWebApp:
    def __init__(self, widget=None, log_dir='logs/extreme_web', credentials=None, url=None):
        self.app = None
        self.main_window = None
        self.widget = widget
        self.url = url
        # Cargar credenciales desde el CredentialManager si no se proporcionan
        if credentials is None:
            credential_manager = CredentialManager()
            self.credentials = credential_manager.load_credentials("bot_extreme")
        else:
            self.credentials = credentials

        # Crear carpeta de logs si no existe
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'extreme_web_app_{datetime.now():%Y%m%d}.log')

        # Configurar logging
        self.logger = logging.getLogger(f'ExtremeWebApp_{id(self)}')
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

    def iniciar_driver(self):
        """Inicializa el WebDriver de Edge"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(self.url)
            self.logger.info("Navegador Edge iniciado correctamente")
            return True
        except Exception as e:
            self.logger.error(f"Error al iniciar el navegador: {str(e)}")
            raise

    def esperar_y_enviar(self, by, value, texto, descripcion, timeout=15):
        """Espera y envía texto a un elemento"""
        try:
            elemento = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value)))
            elemento.clear()
            elemento.send_keys(texto)
            self.logger.info(f"{descripcion} ingresado correctamente")
            return elemento
        except Exception as e:
            self.logger.error(f"Error en {descripcion}: {str(e)}")
            raise

    def esperar_y_click(self, by, value, descripcion, timeout=15):
        """Espera y hace clic en un elemento"""
        try:
            elemento = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value)))
            elemento.click()
            self.logger.info(f"Clic en {descripcion} realizado correctamente")
            return elemento
        except Exception as e:
            self.logger.error(f"Error al hacer clic en {descripcion}: {str(e)}")
            raise



    def seleccionar_grupo_extreme(self, texto_grupo):
        """
        Selecciona un grupo que coincida parcialmente con el texto buscado
        Hace scroll más pronunciado hasta encontrarlo
        
        Args:
            texto_grupo: Texto parcial para buscar coincidencias en los grupos
        """
        try:
            if not texto_grupo or not str(texto_grupo).strip():
                self.logger.warning("Texto de grupo vacío recibido, omitiendo...")
                return False

            texto_grupo = str(texto_grupo).strip().upper()
            self.logger.info(f"Buscando grupo que contenga: {texto_grupo}")

            # 1. Localizar elementos necesarios
            select_grupos = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "ctl00_maincontent_TxtGrupos"))
            )
            
            # 2. Hacer scroll inicial más pronunciado
            self.driver.execute_script("""
                arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});
                arguments[0].scrollTop -= 150;  // Desplazamiento adicional hacia arriba
            """, select_grupos)
            time.sleep(0.5)

            # 3. Búsqueda con scroll progresivo
            opcion = None
            scroll_attempts = 0
            last_scroll_position = -1
            scroll_increment = 250  # Scroll más pronunciado (px)
            max_attempts = 10
            
            while scroll_attempts < max_attempts and opcion is None:
                try:
                    # Buscar por coincidencia parcial en valor o texto
                    xpath = f"""
                        //select[@id='ctl00_maincontent_TxtGrupos']/option[
                            contains(translate(@value, 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{texto_grupo}') or 
                            contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{texto_grupo}')
                        ]
                    """
                    opciones = self.driver.find_elements(By.XPATH, xpath)
                    
                    if opciones:
                        opcion = opciones[0]  # Tomar la primera coincidencia
                        self.logger.info(f"Grupo encontrado: {opcion.text.strip()}") 
                        break
                
                except Exception as e:
                    self.logger.debug(f"Intento {scroll_attempts}: No encontrado aún")
                
                # Hacer scroll más pronunciado
                current_position = self.driver.execute_script("""
                    var prevPos = arguments[0].scrollTop;
                    arguments[0].scrollTop += arguments[1];
                    return prevPos;
                """, select_grupos, scroll_increment)
                
                if current_position == last_scroll_position:
                    break  # No hay más scroll posible
                    
                last_scroll_position = current_position
                scroll_attempts += 1
                time.sleep(0.3)

            if not opcion:
                raise Exception(f"No se encontró ningún grupo que contenga '{texto_grupo}'")

            # 4. Seleccionar el grupo encontrado
            if not opcion.is_selected():
                try:
                    self.driver.execute_script("arguments[0].selected = true;", opcion)
                    self.driver.execute_script("""
                        var event = new Event('change', {bubbles: true});
                        arguments[0].dispatchEvent(event);
                    """, select_grupos)
                    
                    self.logger.info(f"Grupo seleccionado: {opcion.text.strip()}")
                    return True
                except Exception as e:
                    raise Exception(f"Error al seleccionar: {str(e)}")
            else:
                self.logger.info(f"El grupo ya estaba seleccionado")
                return True

        except Exception as e:
            self.logger.error(f"Error al buscar grupo: {str(e)}")
            self.driver.save_screenshot(f"error_grupo_{texto_grupo}.png")
            return False
            
    def adicionar_grupos(self):
        """
        Confirma la adición de los grupos seleccionados
        """
        try:
            # Localizar el botón Adicionar dentro del panel
            btn_adicionar = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.ID, "ctl00_maincontent_BtnAdicionar"))
            )
            
            # Hacer clic usando JavaScript para evitar problemas de visibilidad
            self.driver.execute_script("arguments[0].click();", btn_adicionar)
            self.logger.info("Botón Adicionar clickeado correctamente")
            
            # Esperar a que los grupos aparezcan en el select de la derecha
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#ctl00_maincontent_TxtGruposUser option"))
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al adicionar grupos: {str(e)}")
            self.driver.save_screenshot("error_adicion_grupos.png")
            return False
    
    def click_guardar_y_esperar(self):
        """Hace clic en el botón Guardar y espera 2 segundos"""
        try:
            # Localizar el botón por su ID (la forma más segura)
            btn_guardar = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.ID, "ctl00_maincontent_ImageButton1"))
            )
            
            # Hacer scroll al botón para asegurar visibilidad
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn_guardar)
            time.sleep(0.3)  # Pequeña pausa para el scroll
            
            # Hacer clic usando JavaScript para evitar problemas de interceptación
            self.driver.execute_script("arguments[0].click();", btn_guardar)
            self.logger.info("Clic en botón Guardar realizado correctamente")
            
            # Esperar 2 segundos explícitamente
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error al hacer clic en Guardar: {str(e)}")
            self.driver.save_screenshot("error_boton_guardar.png")
            return False

    def rellenar_alias_con_click(self, user):
        """
        Versión que:
        1. Hace clic en el campo primero
        2. Limpia exhaustivamente
        3. Intenta múltiples métodos de escritura
        4. Verifica el resultado
        """
        alias = (user.Nombres[:2] + user.Apellidos[:2]).upper()
        intentos_maximos = 3

        for intento in range(intentos_maximos):
            try:
                # 1. Localizar el campo y hacer scroll
                campo = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "ctl00_maincontent_TxtAlias"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", campo)
                
                # 2. Hacer clic y esperar
                ActionChains(self.driver).move_to_element(campo).click().perform()
                time.sleep(0.5)  # Esperar posible focus/animación
                
                # 3. Limpiar el campo exhaustivamente
                campo.send_keys(Keys.CONTROL + 'a')  # Seleccionar todo
                campo.send_keys(Keys.DELETE)         # Eliminar
                campo.clear()                        # Limpieza adicional
                time.sleep(0.3)
                
                # 4. Escribir usando método directo
                campo.send_keys(alias)
                
                # 5. Disparar eventos manualmente
                self.driver.execute_script("""
                    var evt = new Event('input', {bubbles: true});
                    arguments[0].dispatchEvent(evt);
                """, campo)
                
                # 6. Verificación inmediata
                valor = self.driver.execute_script("return arguments[0].value;", campo)
                if valor == alias:
                    self.logger.info(f"Alias '{alias}' escrito correctamente")
                    return True
                    
                # 7. Fallback: método JavaScript si falló
                self.driver.execute_script(f"arguments[0].value = '{alias}';", campo)
                time.sleep(0.5)
                
                if campo.get_attribute("value") == alias:
                    return True
                    
                raise Exception(f"Fallo verificación (Valor: {campo.get_attribute('value')})")
                
            except Exception as e:
                self.logger.warning(f"Intento {intento+1} fallido: {str(e)}")
                if intento == intentos_maximos - 1:
                    self.driver.save_screenshot("error_alias_final.png")
                time.sleep(1)
        
        self.logger.error("No se pudo establecer el alias después de múltiples intentos")
        return False

    def execute(self, user, credentials=None, admin_user="squiroz", admin_pass="Alejo1713%", oficina="0000"):
        try:
            # 1. Iniciar navegador
            self.logger.info(f"Iniciando proceso para habilitar usuario {user.Login} en Extreme Web")
            self.iniciar_driver()
            
            # 2. Login (con credenciales del gestor o por defecto)
            if credentials:
                admin_user = credentials.get('username', admin_user)
                admin_pass = credentials.get('password', admin_pass)
                self.logger.info(f"Usando credenciales del gestor: {admin_user}")
            else:
                self.logger.info("Usando credenciales por defecto")
                
            self.logger.info("Realizando login como administrador")
            self.esperar_y_enviar(By.XPATH, "//input[@placeholder='Usuario']", admin_user, "Usuario admin")
            self.esperar_y_enviar(By.XPATH, "//input[@placeholder='Clave']", admin_pass, "Clave admin")
            self.esperar_y_enviar(By.XPATH, "//input[@placeholder='Oficina']", oficina, "Oficina")
            self.esperar_y_click(By.XPATH, "//button[@type='submit']", "Login")
            time.sleep(2)

            # 3. Navegación al módulo
            self.logger.info("Navegando al módulo de usuarios Extreme Web")
            self.esperar_y_click(By.XPATH, '//*[@title="Abrir menú"]', "Menú hamburguesa")
            self.esperar_y_click(By.XPATH, "//button[@aria-label='toggle SEGURIDAD - Administracion de Seguridad']", "SEGURIDAD")
            self.esperar_y_click(By.XPATH, "//button[@aria-label='toggle MANTENIMIENTOS']", "MANTENIMIENTOS")
            self.esperar_y_click(By.XPATH, "//button[contains(text(), 'SE05 Usuarios del Active Directory')]", "SE05")

            # 4. Cambiar a iframe
            try:
                iframe = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "iframe_SE05")))
                self.driver.switch_to.frame(iframe)
                self.logger.info("Cambiado al iframe iframe_SE05 correctamente")
            except Exception as e:
                self.logger.error(f"Error al cambiar al iframe: {str(e)}")
                raise

            # 5. Buscar y habilitar usuario del modelo
            self.logger.info(f"Buscando usuario {user.Login} para habilitar")
            self.esperar_y_enviar(By.NAME, "ctl00$maincontent$txtCriteria", user.Login, "Campo de búsqueda")
            self.esperar_y_click(By.ID, "ctl00_maincontent_BtnActiveUser", "Usuarios...")

            # 6. Doble clic en fila del usuario
            try:
                fila_usuario = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, f"//tr[td[text()='{user.Login}']]")))
                ActionChains(self.driver).double_click(fila_usuario).perform()
                self.logger.info(f"Doble clic en usuario {user.Login} realizado")
            except Exception as e:
                self.logger.error(f"Error al hacer doble clic en el usuario: {str(e)}")
                raise
            
            # 7. Generar y rellenar alias
            self.rellenar_alias_con_click(user)
            
            # 9. Habilitar usuario
            self.esperar_y_click(By.ID, "ctl00_maincontent_BtnAgregar", "Ver Grupos...")
            
            self.seleccionar_grupo_extreme(user.Cargo_x003a__x0020_Rol_x0020_Ext)

            # 10. Adicionar grupos seleccionados
            self.adicionar_grupos()

            # 11. Guardar cambios
            self.click_guardar_y_esperar()

            guardar_credencial("Extreme", user.Login, "WINDOWS")

            return {"status": "success", "message": f"Usuario {user.Login} habilitado en Extreme Web"}

        except Exception as e:
            self.logger.error(f"Error en el proceso: {str(e)}", exc_info=True)
            # Capturar pantalla del error
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.driver.save_screenshot(f"error_ad_{timestamp}.png")
            except Exception as capture_error:
                self.logger.error(f"No se pudo capturar pantalla: {str(capture_error)}")
            

            return {"status": "error", "message": str(e)}
        
        finally:
            if hasattr(self, 'driver') and self.driver:
                try:
                    self.driver.quit()
                    self.logger.info("Navegador cerrado correctamente")
                except Exception as e:
                    self.logger.error(f"Error al cerrar navegador: {str(e)}")

    def __del__(self):
        """Destructor para asegurar que el driver se cierre"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass