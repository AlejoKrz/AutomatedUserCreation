# Gestor de Credenciales

## Descripción

El Gestor de Credenciales es una herramienta integrada en el widget de control que permite almacenar y gestionar credenciales de acceso para los diferentes sistemas de forma segura y cifrada.

## Características

- **Cifrado seguro**: Las credenciales se almacenan en un archivo cifrado usando la biblioteca `cryptography`
- **Interfaz gráfica intuitiva**: Ventana modal fácil de usar
- **Gestión por sistema**: Cada sistema puede tener sus propias credenciales
- **Campos flexibles**: Usuario y contraseña para cada sistema

## Cómo usar

### 1. Abrir el Gestor de Credenciales

1. Ejecuta la aplicación principal
2. En el widget de control, haz clic en el botón **🔑** (Gestor de Credenciales)
3. Se abrirá una ventana modal con el gestor

### 2. Agregar un nuevo sistema

1. En la sección "Sistemas", haz clic en **"Agregar Sistema"**
2. Ingresa el nombre del sistema (ej: "Cobis", "Extreme", "AD", etc.)
3. Haz clic en **"Agregar"**

### 3. Configurar credenciales

1. Selecciona el sistema de la lista
2. Completa los campos de credenciales:
   - **Usuario**: Nombre de usuario para el sistema
   - **Contraseña**: Contraseña del usuario
3. Haz clic en **"Guardar Credenciales"**

### 4. Eliminar un sistema

1. Selecciona el sistema de la lista
2. Haz clic en **"Eliminar Sistema"**
3. Confirma la eliminación

## Sistemas compatibles

El gestor está diseñado para trabajar con los siguientes sistemas:

- **Cobis**: Sistema de gestión bancaria
- **Extreme**: Sistema de gestión de red
- **Active Directory**: Gestión de usuarios de dominio
- **Nómina**: Sistema de nómina
- **Syscard**: Sistema de tarjetas

## Estructura de archivos

- `credentials.enc`: Archivo cifrado con todas las credenciales
- `master.key`: Clave maestra para cifrar/descifrar credenciales
- `core/credential_manager.py`: Módulo principal del gestor

## Seguridad

- Las credenciales se almacenan usando cifrado AES-256
- La clave maestra se genera automáticamente en la primera ejecución
- Los archivos de credenciales no deben compartirse ni respaldarse sin protección adicional

## Integración con bots

Los bots han sido modificados para usar automáticamente las credenciales del gestor:

### Bot de Cobis
```python
# Usa credenciales del gestor si están disponibles
username = self.credentials.get('username', 'usuario_por_defecto')
password = self.credentials.get('password', 'password_por_defecto')
```

### Bot de Extreme
```python
# Usa credenciales del gestor si están disponibles
if credentials:
    admin_user = credentials.get('username', admin_user)
    admin_pass = credentials.get('password', admin_pass)
    oficina = credentials.get('server', oficina)
```

## Dependencias

Asegúrate de tener instalada la dependencia:
```bash
pip install cryptography>=41.0.0
```

## Solución de problemas

### Error al cargar credenciales
- Verifica que el archivo `master.key` existe
- Si se corrompió, elimina `master.key` y `credentials.enc` para regenerar

### Credenciales no se aplican
- Verifica que el nombre del sistema coincida exactamente
- Revisa los logs para ver si hay errores de autenticación

### Ventana no se abre
- Verifica que ttkbootstrap esté instalado correctamente
- Asegúrate de que no haya errores en la consola
