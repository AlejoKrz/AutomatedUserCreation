import time
from datetime import datetime
from .sharepoint_client import SharePointClient
from .user_processor import UserProcessor
from .config import settings
import threading

class WorkflowManager:
    def __init__(self, processor, widget=None):
        self.sp_client = SharePointClient()
        self.processor = processor
        self.widget = widget  # Referencia al widget de progreso
        self.running = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Comienza sin estar en pausa

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

    def run(self, interval_minutes=settings.WORKFLOW_INTERVAL_MINUTES):
        """Ejecuta el flujo cada X minutos."""
        self.running = True
        while self.running:
            msg = f"{datetime.now():%Y-%m-%d %H:%M:%S} - 🔍 Buscando usuarios aprobados..."
            if self.widget:
                self.widget.set_progress_indeterminate()
                self.widget.log(msg)
            else:
                print(msg)
            try:
                users = self.sp_client.get_pending_users()
                if self.widget:
                    self.widget.set_progress_indeterminate()

                for idx, user in enumerate(users, 1):
                    msg = f"{datetime.now():%Y-%m-%d %H:%M:%S} - ⚙️ Procesando usuario: {user.Nombres}"
                    if self.widget:
                        self.widget.log(msg)
                    else:
                        print(msg)
                    # Cambia estado a "En Proceso"
                    self.sp_client.update_user_status(user.id, "En Proceso")
                    results = self.processor.process_user(user, pause_event=self.pause_event)
                    # Si todos los bots fueron exitosos, cambia a "Finalizado"
                    if all(result.success for result in results):
                        if not getattr(settings, "TEST_MODE", False):
                            # Solo actualiza el estado si NO está en modo pruebas
                            self.sp_client.update_user_status(user.id, "Finalizado")
                        else:
                            # En modo pruebas, solo loguea
                            if self.widget:
                                self.widget.log(f"[TEST_MODE] No se actualiza el estado a 'Cerrado' en SharePoint para {user.Nombres}")
                            self.sp_client.update_user_status(user.id, "Aprobado")
                    for result in results:
                        if result.success:
                            log_msg = f"{datetime.now():%Y-%m-%d %H:%M:%S} -   - {result.bot_name}: ✅ Se finalizó la ejecución correctamente. {result.message}"
                        else:
                            log_msg = f"{datetime.now():%Y-%m-%d %H:%M:%S} -   - {result.bot_name}: ❌ Ocurrió un error durante la ejecución. {result.message}"
                        if self.widget:
                            self.widget.log(log_msg)
                        else:
                            print(log_msg)
                wait_msg = f"{datetime.now():%Y-%m-%d %H:%M:%S} - ⏳ Esperando {interval_minutes} minutos..."
                if self.widget:
                    self.widget.log(wait_msg)
                    self.widget.set_progress_indeterminate()
                else:
                    print(wait_msg)
                # Sleep controlado para permitir detener el workflow
                for _ in range(interval_minutes * 60):
                    if not self.running:
                        break
                    time.sleep(1)
            except Exception as e:
                error_msg = f"{datetime.now():%Y-%m-%d %H:%M:%S} - ⚠️ Error crítico: {str(e)}"
                if self.widget:
                    self.widget.log(error_msg)
                else:
                    print(error_msg)
                time.sleep(5)

    def stop(self):
        self.running = False