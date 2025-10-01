import os
import re
import json
import requests
from msal import ConfidentialClientApplication
from core.config import settings
from email.utils import formatdate

CRED_FILE = os.path.join(os.getcwd(), "credenciales_generadas.txt")

def guardar_credencial(sistema, usuario, contraseña, archivo=CRED_FILE):
    os.makedirs(os.path.dirname(archivo) or ".", exist_ok=True)
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(f"Sistema: {sistema}\nUsuario: {usuario}\nContraseña: {contraseña}\n\n")

def leer_credenciales(archivo=CRED_FILE):
    """
    Devuelve un dict {sistema: {'username':..., 'password':...}, ...}
    Lee el formato escrito por guardar_credencial.
    """
    if not os.path.exists(archivo):
        return {}
    data = {}
    with open(archivo, "r", encoding="utf-8") as f:
        content = f.read()
    # separa bloques por doble nueva línea
    bloques = [b.strip() for b in content.split("\n\n") if b.strip()]
    for b in bloques:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        sistema = usuario = contraseña = None
        for line in lines:
            if line.lower().startswith("sistema:"):
                sistema = line.split(":", 1)[1].strip()
            elif line.lower().startswith("usuario:"):
                usuario = line.split(":", 1)[1].strip()
            elif line.lower().startswith("contraseña:") or line.lower().startswith("contrasena:"):
                contraseña = line.split(":", 1)[1].strip()
        if sistema:
            data.setdefault(sistema, []).append({"username": usuario, "password": contraseña})
    return data

def generar_cuerpo_html(credenciales_dict):
    """
    Genera HTML (tabla) con las credenciales. credenciales_dict puede tener listas por sistema.
    """
    filas = ""
    for sistema, items in credenciales_dict.items():
        for item in items:
            user = item.get("username", "")
            pwd = item.get("password", "")
            filas += f"""
            <tr>
                <td style="padding:6px;border:1px solid #ccc;">{sistema}</td>
                <td style="padding:6px;border:1px solid #ccc;">{user}</td>
                <td style="padding:6px;border:1px solid #ccc;">{pwd}</td>
            </tr>
            """
    if not filas:
        filas = "<tr><td colspan='3'>No se generaron credenciales.</td></tr>"
    cuerpo_html = f"""<html><body>
    <p>Estimado/a,</p>
    <p>Adjunto las credenciales generadas:</p>
    <table style="border-collapse:collapse;width:100%;">
      <thead>
        <tr>
          <th style="padding:6px;border:1px solid #ccc;background:#f2f2f2;">Sistema</th>
          <th style="padding:6px;border:1px solid #ccc;background:#f2f2f2;">Usuario</th>
          <th style="padding:6px;border:1px solid #ccc;background:#f2f2f2;">Contraseña</th>
        </tr>
      </thead>
      <tbody>
        {filas}
      </tbody>
    </table>
    <p>Por seguridad, las contraseñas son temporales y deben ser cambiadas en el primer ingreso.</p>
    <p>Atentamente,<br/>Automatización</p>
    </body></html>"""
    return cuerpo_html

def _obtener_token_graph():
    tenant = settings.SHAREPOINT.get("tenant_id")
    client_id = settings.SHAREPOINT.get("client_id")
    client_secret = settings.SHAREPOINT.get("client_secret")
    if not all([tenant, client_id, client_secret]):
        raise RuntimeError("Faltan credenciales de Graph API en settings.SHAREPOINT")
    app = ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant}",
        client_credential=client_secret,
    )
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" not in token:
        raise RuntimeError(f"Error al obtener token Graph: {token}")
    return token["access_token"]

def enviar_correo_graph(destinatario, asunto, cuerpo_html, archivo_a_eliminar=None):
    """
    Envía un correo HTML usando Microsoft Graph (application permission).
    Si 'archivo_a_eliminar' se suministra y el envío tiene éxito, elimina ese archivo.
    """
    token = _obtener_token_graph()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    message = {
        "subject": asunto,
        "body": {"contentType": "HTML", "content": cuerpo_html},
        "toRecipients": [{"emailAddress": {"address": destinatario}}],
    }
    payload = {"message": message, "saveToSentItems": "true"}
    endpoint = "https://graph.microsoft.com/v1.0/users/a4022c89-ca57-4cca-9ada-0d475e63b9d5/sendMail"
    resp = requests.post(endpoint, headers=headers, json=payload)
    if resp.status_code not in (200, 202):
        raise RuntimeError(f"Error al enviar correo Graph {resp.status_code}: {resp.text}")

    # Si todo salió bien, intentar eliminar el archivo de credenciales (si se indicó)
    if archivo_a_eliminar:
        try:
            # sólo eliminar si el archivo existe y está dentro del cwd o ruta permitida
            archivo_a_eliminar = os.path.abspath(archivo_a_eliminar)
            cwd = os.path.abspath(os.getcwd())
            if os.path.exists(archivo_a_eliminar) and (archivo_a_eliminar.startswith(cwd) or os.path.dirname(archivo_a_eliminar)):
                os.remove(archivo_a_eliminar)
        except Exception as e:
            # No interrumpe el flujo principal; registrar el error si hace falta
            # (poner un print simple para no importar logging en utils)
            print(f"Advertencia: no se pudo eliminar el archivo de credenciales: {e}")