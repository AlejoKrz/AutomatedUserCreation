import threading
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter.scrolledtext import ScrolledText
from .credential_manager import CredentialManagerGUI


class ProgressWidget(tb.Window):
    def __init__(self, workflow_manager):
        super().__init__(themename="superhero")
        self.workflow_manager = workflow_manager

        self.overrideredirect(True)
        self.attributes("-topmost", True)

        self.width = 380
        self.height = 220
        self._update_position()
        self.after(1000, self._keep_bottom_right)

        # Barra de título personalizada
        self.title_bar = tb.Frame(self, bootstyle="secondary", padding=6)
        self.title_bar.pack(fill="x")

        self.title_label = tb.Label(
            self.title_bar,
            text="Control de Ejecución",
            font=("Segoe UI Semibold", 11),
            bootstyle="inverse-secondary"
        )
        self.title_label.pack(side="left", padx=10)

        close_button = tb.Button(
            self.title_bar,
            text="✖",
            bootstyle="danger",
            width=3,
            command=self.destroy,
            cursor="hand2"
        )
        close_button.pack(side="right", padx=8, pady=2)

        # Contenido principal
        content_frame = tb.Frame(self, padding=12)
        content_frame.pack(fill="both", expand=True)

        button_frame = tb.Frame(content_frame)
        button_frame.pack(pady=(0, 10))

        self.start_button = tb.Button(
            button_frame, text="▶", bootstyle=SUCCESS, width=6,
            command=self.start_workflow, cursor="hand2"
        )
        self.start_button.pack(side=LEFT, padx=8)

        self.stop_button = tb.Button(
            button_frame, text="⏹", bootstyle=DANGER, width=6,
            command=self.stop_workflow, state=DISABLED, cursor="hand2"
        )
        self.stop_button.pack(side=LEFT, padx=8)

        self.credentials_button = tb.Button(
            button_frame, text="🔑", bootstyle=WARNING, width=6,
            command=self.open_credential_manager, cursor="hand2"
        )
        self.credentials_button.pack(side=LEFT, padx=8)

        self.progress = tb.Progressbar(content_frame, length=360, mode='indeterminate', bootstyle=INFO)
        self.progress.pack(padx=5, pady=(0, 12))

        self.log_text = ScrolledText(
            content_frame,
            height=7,
            width=52,
            state='disabled',
            wrap='word',
            bg="#212529",
            fg="#e9ecef",
            bd=0,
            relief="flat",
            font=("Segoe UI", 10)
        )
        self.log_text.pack(padx=5, pady=5)

        self.workflow_thread = None

    def _update_position(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = screen_width - self.width - 15
        y = screen_height - self.height - 40
        self.geometry(f"{self.width}x{self.height}+{x}+{y}")

    def _keep_bottom_right(self):
        self._update_position()
        self.after(1000, self._keep_bottom_right)

    # Workflow control
    def start_workflow(self):
        self.start_button.config(state=DISABLED)
        self.stop_button.config(state=NORMAL)
        self.clear_logs()
        self.progress['value'] = 0
        self.progress.start(12)
        self.workflow_thread = threading.Thread(target=self.workflow_manager.run, daemon=True)
        self.workflow_thread.start()

    def stop_workflow(self):
        self.workflow_manager.stop()
        self.progress.stop()
        self.start_button.config(state=NORMAL)
        self.stop_button.config(state=DISABLED)

    def open_credential_manager(self):
        """Abre el gestor de credenciales"""
        credential_window = CredentialManagerGUI(self)
        credential_window.grab_set()  # Hace la ventana modal

    def pause_workflow(self):
        if self.workflow_manager:
            self.workflow_manager.pause()
            self.log("⏸️ Ejecución pausada.")

    def resume_workflow(self):
        if self.workflow_manager:
            self.workflow_manager.resume()
            self.log("▶️ Ejecución reanudada.")

    def update_progress(self, value, maximum):
        self.progress.config(mode='determinate')
        self.progress['maximum'] = maximum
        self.progress['value'] = value
        self.update_idletasks()

    def log(self, text):
        self.log_text.config(state='normal')
        self.log_text.insert('end', text + "\n")
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.update_idletasks()

    def clear_logs(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, 'end')
        self.log_text.config(state='disabled')

    def set_progress_indeterminate(self):
        self.progress.config(mode='indeterminate')
        self.progress.start(12)

    def set_progress_determinate_full(self):
        self.progress.stop()
        self.progress.config(mode='determinate')
        self.progress['value'] = self.progress['maximum']

    def reset_progress(self):
        self.progress.stop()
        self.progress.config(mode='determinate')
        self.progress['value'] = 0

    def mainloop(self):
        super().mainloop()
