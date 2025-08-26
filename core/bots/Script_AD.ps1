param(
    [string]$Nombre_Apellido,
    [string]$Nombres,
    [string]$Apellidos,
    [string]$Login,
    [string]$Login_dominio,
    [string]$Contraseña,
    [string]$OU, 
    [string]$DisplayName,
    [string]$Cargo,
    [string]$Departamento,
    [string]$Ciudad,
    [string]$Provincia,
    [string]$Oficina,
    [string]$EmailAddress,
    [string]$proxyAddresses
)

# Configurar logging detallado
$LogPath = "C:\Logs\ADUserCreation"
if (-not (Test-Path -Path $LogPath)) {
    New-Item -ItemType Directory -Path $LogPath -Force
}
$LogFile = "$LogPath\ADUserCreation_$(Get-Date -Format 'yyyyMMdd').log"

function Write-Log {
    param([string]$message, [string]$level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$level] $message"
    Add-Content -Path $LogFile -Value $logEntry
    Write-Host $logEntry
}

try {
    Write-Log "Iniciando creación de usuario $Nombre_Apellido ($Login)"
    
    # Validación básica de parámetros
    if ([string]::IsNullOrEmpty($Login) -or [string]::IsNullOrEmpty($Contraseña)) {
        throw "Login o contraseña no pueden estar vacíos"
    }

    # Mostrar parámetros recibidos (sin contraseña)
    Write-Log "Parámetros recibidos:"
    Write-Log "  Nombre_Apellido: $Nombre_Apellido"
    Write-Log "  Nombres: $Nombres"
    Write-Log "  Apellidos: $Apellidos"
    Write-Log "  Login: $Login"
    Write-Log "  OU: $OU"
    Write-Log "  Cargo: $Cargo"
    Write-Log "  Departamento: $Departamento"
    Write-Log "  Oficina: $Oficina"
    Write-Log "  Email: $EmailAddress"

    # Crear usuario
    Write-Log "Creando usuario en AD..."

$proxyAddressesArray = @()
if (![string]::IsNullOrEmpty($proxyAddresses)) {
    $proxyAddressesArray = @($proxyAddresses)
}

$userParams = @{
    Name              = $Nombre_Apellido
    GivenName         = $Nombres
    Surname           = $Apellidos
    SamAccountName    = $Login
    UserPrincipalName = $Login_dominio
    AccountPassword   = (ConvertTo-SecureString $Contraseña -AsPlainText -Force)
    Enabled           = $true
    Path              = $OU
    DisplayName       = $Nombre_Apellido
    Description       = $Cargo
    Company           = "CPN"
    Department        = $Departamento
    Title             = $Cargo
    StreetAddress     = "."
    City              = $Ciudad
    State             = $Provincia
    Country           = "EC"
    Office            = $Oficina
    EmailAddress      = $EmailAddress
    OtherAttributes   = @{
        wWWHomePage    = $Login
    }
    ErrorAction       = 'Stop'
}

# Agregar ProxyAddresses a OtherAttributes si hay direcciones
if ($proxyAddressesArray.Count -gt 0) {
    $userParams.OtherAttributes.Add("ProxyAddresses", $proxyAddressesArray)
}
    Write-Log "Parámetros para New-ADUser:"
    $userParams.GetEnumerator() | ForEach-Object {
        Write-Log "  $_.Key = $($_.Value)"
    }

    $newUser = New-ADUser @userParams

    Write-Log "Usuario $Nombre_Apellido creado correctamente (SAM: $Login)"

    # Configurar cambio de contraseña en primer login
    Write-Log "Configurando cambio de contraseña en primer login..."
    Set-ADUser -Identity $Login -ChangePasswordAtLogon $true -ErrorAction Stop
    Write-Log "Configuración completada para usuario $Login"

    # Verificar creación
    $createdUser = Get-ADUser -Identity $Login -Properties * -ErrorAction Stop
    Write-Log "Usuario verificado:"
    Write-Log "  Nombre: $($createdUser.Name)"
    Write-Log "  UPN: $($createdUser.UserPrincipalName)"
    Write-Log "  Habilitado: $($createdUser.Enabled)"
    Write-Log "  OU: $($createdUser.DistinguishedName)"

    Write-Log "Proceso completado exitosamente"
    exit 0

} catch [Microsoft.ActiveDirectory.Management.ADIdentityAlreadyExistsException] {
    Write-Log "ERROR: El usuario $Login ya existe en Active Directory" -level "ERROR"
    Write-Log "Detalles del error: $($_.Exception.Message)" -level "ERROR"
    Write-Log "Stack Trace: $($_.Exception.StackTrace)" -level "DEBUG"
    exit 1
} catch [Microsoft.ActiveDirectory.Management.ADIdentityNotFoundException] {
    Write-Log "ERROR: Problema con la OU o dominio" -level "ERROR"
    Write-Log "Mensaje: $($_.Exception.Message)" -level "ERROR"
    Write-Log "OU especificada: $OU" -level "DEBUG"
    exit 2
} catch [System.Security.Cryptography.CryptographicException] {
    Write-Log "ERROR: Problema con la contraseña" -level "ERROR"
    Write-Log "Mensaje: $($_.Exception.Message)" -level "ERROR"
    exit 3
} catch {
    Write-Log "ERROR: Error inesperado" -level "ERROR"
    Write-Log "Tipo de excepción: $($_.Exception.GetType().FullName)" -level "ERROR"
    Write-Log "Mensaje: $($_.Exception.Message)" -level "ERROR"
    Write-Log "Stack Trace: $($_.Exception.StackTrace)" -level "DEBUG"
    
    # Información adicional del error
    if ($_.Exception.InnerException) {
        Write-Log "Inner Exception: $($_.Exception.InnerException.Message)" -level "DEBUG"
    }
    
    exit 99
}