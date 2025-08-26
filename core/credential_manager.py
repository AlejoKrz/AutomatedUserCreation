import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *


class CredentialManager:
    def __init__(self, credentials_file="secure/credentials.enc"):
        self.credentials_file = credentials_file
        self.master_key = None
        self.fernet = None
        self._load_or_create_master_key()
    
    def _load_or_create_master_key(self):
        key_file = "master.key"
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                self.master_key = f.read()
        else:
            self.master_key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(self.master_key)
        
        self.fernet = Fernet(self.master_key)
    
    def encrypt_credentials(self, credentials_dict):
        json_data = json.dumps(credentials_dict)
        encrypted_data = self.fernet.encrypt(json_data.encode())
        return encrypted_data
    
    def decrypt_credentials(self, encrypted_data):
        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            print(f"Error al desencriptar credenciales: {e}")
            return {}
    
    def save_credentials(self, system_name, credentials):
        all_credentials = self.load_all_credentials()
        all_credentials[system_name] = credentials
        
        encrypted_data = self.encrypt_credentials(all_credentials)
        with open(self.credentials_file, "wb") as f:
            f.write(encrypted_data)
    
    def load_credentials(self, system_name):
        all_credentials = self.load_all_credentials()
        return all_credentials.get(system_name, {})
    
    def load_all_credentials(self):
        if not os.path.exists(self.credentials_file):
            return {}
        
        try:
            with open(self.credentials_file, "rb") as f:
                encrypted_data = f.read()
            return self.decrypt_credentials(encrypted_data)
        except Exception as e:
            print(f"Error al cargar credenciales: {e}")
            return {}
    
    def delete_credentials(self, system_name):
        all_credentials = self.load_all_credentials()
        if system_name in all_credentials:
            del all_credentials[system_name]
            encrypted_data = self.encrypt_credentials(all_credentials)
            with open(self.credentials_file, "wb") as f:
                f.write(encrypted_data)
    
    def list_systems(self):
        return list(self.load_all_credentials().keys())


class CredentialManagerGUI(tb.Toplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.credential_manager = CredentialManager()
        
        self.title("Gestor de Credenciales")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Hacer la ventana verdaderamente modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        self.center_window()
        self.setup_ui()
        self.load_systems_list()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (600 // 2)
        self.geometry(f"500x600+{x}+{y}")
    
    def setup_ui(self):
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        title_label = tb.Label(
            main_frame,
            text="Gestor de Credenciales",
            font=("Segoe UI Semibold", 16),
            bootstyle="primary"
        )
        title_label.pack(pady=(0, 20))
        
        systems_frame = tb.LabelFrame(main_frame, text="Sistemas", padding=10)
        systems_frame.pack(fill="x", pady=(0, 15))
        
        self.systems_listbox = tk.Listbox(
            systems_frame,
            height=8,
            selectmode="single",
            font=("Segoe UI", 10)
        )
        self.systems_listbox.pack(fill="x", pady=(0, 10))
        self.systems_listbox.bind('<<ListboxSelect>>', self.on_system_select)
        
        systems_buttons_frame = tb.Frame(systems_frame)
        systems_buttons_frame.pack(fill="x")
        
        tb.Button(
            systems_buttons_frame,
            text="Agregar Sistema",
            bootstyle="success",
            command=self.add_system
        ).pack(side="left", padx=(0, 5))
        
        tb.Button(
            systems_buttons_frame,
            text="Eliminar Sistema",
            bootstyle="danger",
            command=self.delete_system
        ).pack(side="left", padx=(0, 5))
        
        credentials_frame = tb.LabelFrame(main_frame, text="Credenciales", padding=10)
        credentials_frame.pack(fill="both", expand=True)
        
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        
        tb.Label(credentials_frame, text="Usuario:").pack(anchor="w")
        self.username_entry = tb.Entry(credentials_frame, textvariable=self.username_var, width=40)
        self.username_entry.pack(fill="x", pady=(0, 10))
        
        tb.Label(credentials_frame, text="Contraseña:").pack(anchor="w")
        self.password_entry = tb.Entry(credentials_frame, textvariable=self.password_var, show="*", width=40)
        self.password_entry.pack(fill="x", pady=(0, 15))
        
        credentials_buttons_frame = tb.Frame(credentials_frame)
        credentials_buttons_frame.pack(fill="x")
        
        tb.Button(
            credentials_buttons_frame,
            text="Guardar Credenciales",
            bootstyle="primary",
            command=self.save_credentials
        ).pack(side="left", padx=(0, 5))
        
        tb.Button(
            credentials_buttons_frame,
            text="Limpiar Campos",
            bootstyle="secondary",
            command=self.clear_fields
        ).pack(side="left", padx=(0, 5))
        
        tb.Button(
            main_frame,
            text="Cerrar",
            bootstyle="outline-secondary",
            command=self.destroy
        ).pack(pady=(20, 0))
        
        self.selected_system = None
    
    def load_systems_list(self):
        self.systems_listbox.delete(0, tk.END)
        systems = self.credential_manager.list_systems()
        for system in systems:
            self.systems_listbox.insert(tk.END, system)
    
    def on_system_select(self, event):
        selection = self.systems_listbox.curselection()
        if selection:
            self.selected_system = self.systems_listbox.get(selection[0])
            self.load_system_credentials()
        else:
            # Si no hay selección, limpiar campos
            self.selected_system = None
            self.clear_fields()
    
    def load_system_credentials(self):
        if self.selected_system:
            try:
                credentials = self.credential_manager.load_credentials(self.selected_system)
                self.username_var.set(credentials.get('username', ''))
                self.password_var.set(credentials.get('password', ''))
            except Exception as e:
                print(f"Error al cargar credenciales para {self.selected_system}: {e}")
                self.username_var.set('')
                self.password_var.set('')
    
    def add_system(self):
        dialog = AddSystemDialog(self)
        self.wait_window(dialog)
        if dialog.system_name:
            # Guardar credenciales vacías para el nuevo sistema
            self.credential_manager.save_credentials(dialog.system_name, {'username': '', 'password': ''})
            self.load_systems_list()
            # Seleccionar el nuevo sistema
            for i in range(self.systems_listbox.size()):
                if self.systems_listbox.get(i) == dialog.system_name:
                    self.systems_listbox.selection_set(i)
                    self.selected_system = dialog.system_name
                    self.load_system_credentials()
                    break
    
    def delete_system(self):
        if not self.selected_system:
            messagebox.showwarning("Advertencia", "Por favor seleccione un sistema para eliminar.")
            return
            
        try:
            system_name = self.selected_system
            if messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar el sistema '{system_name}'?"):
                self.credential_manager.delete_credentials(system_name)
                self.load_systems_list()
                self.clear_fields()
                self.selected_system = None
                messagebox.showinfo("Éxito", f"Sistema '{system_name}' eliminado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar sistema: {str(e)}")
    
    def save_credentials(self):
        if not self.selected_system:
            messagebox.showwarning("Advertencia", "Por favor seleccione un sistema primero.")
            return
        
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Advertencia", "Por favor complete tanto el usuario como la contraseña.")
            return
        
        credentials = {
            'username': username,
            'password': password
        }
        
        try:
            self.credential_manager.save_credentials(self.selected_system, credentials)
            messagebox.showinfo("Éxito", f"Credenciales guardadas para '{self.selected_system}'")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar credenciales: {str(e)}")
    
    def clear_fields(self):
        self.username_var.set('')
        self.password_var.set('')
        self.selected_system = None


class AddSystemDialog(tb.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.system_name = None
        
        self.title("Agregar Sistema")
        self.geometry("300x150")
        self.resizable(False, False)
        
        # Hacer la ventana verdaderamente modal
        self.transient(parent)
        self.grab_set()
        self.focus_set()
        
        self.center_window()
        self.setup_ui()
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.winfo_screenheight() // 2) - (150 // 2)
        self.geometry(f"300x150+{x}+{y}")
    
    def setup_ui(self):
        main_frame = tb.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        tb.Label(main_frame, text="Nombre del Sistema:", font=("Segoe UI", 10)).pack(anchor="w")
        
        self.system_entry = tb.Entry(main_frame, width=30)
        self.system_entry.pack(fill="x", pady=(5, 15))
        self.system_entry.focus()
        
        buttons_frame = tb.Frame(main_frame)
        buttons_frame.pack(fill="x")
        
        tb.Button(
            buttons_frame,
            text="Agregar",
            bootstyle="success",
            command=self.add_system
        ).pack(side="left", padx=(0, 5))
        
        tb.Button(
            buttons_frame,
            text="Cancelar",
            bootstyle="outline-secondary",
            command=self.destroy
        ).pack(side="left")
        
        self.system_entry.bind('<Return>', lambda e: self.add_system())
    
    def add_system(self):
        system_name = self.system_entry.get().strip()
        if system_name:
            self.system_name = system_name
            self.destroy()
        else:
            messagebox.showwarning("Advertencia", "Por favor ingrese un nombre para el sistema.")

