from dataclasses import dataclass
from typing import Optional

@dataclass
class SharePointUser:
    """
    Modelo exacto para mapear las columnas de tu lista SharePoint.
    Los nombres de atributos deben coincidir exactamente con los nombres técnicos.
    """

    id: str  # ID único del ítem en SharePoint
    Title: str  # Cédula o identificador principal
    Oficina: str  # Nombre de la oficina
    Nombres: str  # Nombres del usuario
    Apellidos: str  # Apellidos del usuario
    G_x00e9_nero: str  # Género
    Oficina_x003a__x0020_N_x00fa_mer: str  # Número de oficina
    Oficina_x003a__x0020_Extreme_x00: str  # Oficina en Extreme
    Oficina_x003a__x0020_Ciudad_x002: str  # Ciudad Nómina

    Oficina_x003a__x0020_Region : str  # Región Nomenclatur nómina
    Oficina_x003a__x0020_Ciudad_x0020  : str  # Ciudad de la oficina STR
    Oficina_x003a__x0020_Regi_x00f3_ : str  # Región de la oficina en STR
    Oficina_x003a__x0020_Provincia: str  # Provincia de la oficina
    
    Cargo: str  # Cargo del usuario
    Cargo_x003a__x0020_Correo: str  # Correo asociado al cargo
    Cargo_x003a__x0020_Cargo_x0020_e: str  # Cargo en Cobis
    Cargo_x003a__x0020_Rol_x0020_en_: str  # Rol en Cobis
    Cargo_x003a__x0020_Departamento: str  # Departamento String
    Cargo_x003a__x0020_Cargo_x0020_e0: str  # Cargo Nomina
    Cargo_x003a__x0020_Departamento_0: str  # Departamento Nomina
    Cargo_x003a__x0020_Tipo_x0020_Em: str  # Tipo de empleado Nómina
    Cargo_x003a__x0020_Rol_x0020_Sys: str  # Rol de Syscard
    Cargo_x003a__x0020_Rol_x0020_Ext: str  # Rol Extreme web
    Cargo_x003a__x0020_Departamento_: str  # Departamento en Cobis


    JefeInmediato: str  # Correo del jefe inmediato
    Login: str  # Usuario de Windows
    Correoelectr_x00f3_nico: str  # Correo electrónico asignado
    Fechadeingreso: str  # Fecha de ingreso
    Estado: str  # Estado de la solicitud
    Departamento: Optional[str] = None  # Departamento principal
    Departamento_x003a__x0020_Unidad: Optional[str] = None  # Unidad organizacional

    Oficina_x003a__x0020_OU_x0020_Ac: Optional[str] = None  # OU de Active Directory (opcional)
    # Campos de control (no vienen de SharePoint)
    procesado: bool = False  # Indica si fue procesado
    error_procesamiento: Optional[str] = None  # Mensaje de error si hubo problema

    @property
    def name(self):
        """Nombre completo del usuario."""
        return f"{self.Nombres} {self.Apellidos}"

@dataclass
class ProcessResult:
    """
    Resultado de la ejecución de un bot.
    """
    bot_name: str  # "ad_bot", "email_bot", etc.
    success: bool
    message: str
