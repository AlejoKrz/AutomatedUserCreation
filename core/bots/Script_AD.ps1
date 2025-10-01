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
    if ([string]::IsNullOrEmpty($Login) -or [string]::IsNullOrEmpty($Contraseña)) {
        throw "Login o contraseña no pueden estar vacíos"
    }
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

    Write-Log "Creando usuario en AD..."

    $proxyAddressesArray = @()
    if (![string]::IsNullOrEmpty($proxyAddresses)) {
        $proxyAddressesArray = @($proxyAddresses)
    }

    $userParams = @{
        Name               = $Nombre_Apellido
        GivenName          = $Nombres
        Surname            = $Apellidos
        SamAccountName     = $Login
        UserPrincipalName  = $Login_dominio
        AccountPassword    = (ConvertTo-SecureString $Contraseña -AsPlainText -Force)
        Enabled            = $true
        Path               = $OU
        DisplayName        = $Nombre_Apellido
        Description        = $Cargo
        Company            = "CPN"
        Department         = $Departamento
        Title              = $Cargo
        StreetAddress      = "."
        City               = $Ciudad
        State              = $Provincia
        Country            = "EC"
        Office             = $Oficina
        EmailAddress       = $EmailAddress
        OtherAttributes    = @{
            wWWHomePage    = $Login
        }
        ErrorAction        = 'Stop'
    }

    if ($proxyAddressesArray.Count -gt 0) {
        $userParams.OtherAttributes.Add("ProxyAddresses", $proxyAddressesArray)
    }
    Write-Log "Parámetros para New-ADUser:"
    $userParams.GetEnumerator() | ForEach-Object {
        Write-Log "  $_.Key = $($_.Value)"
    }

    $newUser = New-ADUser @userParams

    Write-Log "Usuario $Nombre_Apellido creado correctamente (SAM: $Login)"

    Write-Log "Configurando cambio de contraseña en primer login..."
    Set-ADUser -Identity $Login -ChangePasswordAtLogon $true -ErrorAction Stop
    Write-Log "Configuración completada para usuario $Login"

    $createdUser = Get-ADUser -Identity $Login -Properties * -ErrorAction Stop
    Write-Log "Usuario verificado:"
    Write-Log "  Nombre: $($createdUser.Name)"
    Write-Log "  UPN: $($createdUser.UserPrincipalName)"
    Write-Log "  Habilitado: $($createdUser.Enabled)"
    Write-Log "  OU: $($createdUser.DistinguishedName)"

    Write-Log "Proceso completado exitosamente"
    exit 0

} catch {
    $exception = $_.Exception
    $exceptionType = $exception.GetType().FullName
    Write-Log "ERROR: Se produjo un error de tipo $exceptionType" -level "ERROR"
    Write-Log "Mensaje: $($exception.Message)" -level "ERROR"
    
    if ($exception.InnerException) {
        Write-Log "Inner Exception: $($exception.InnerException.Message)" -level "ERROR"
    }
    
    Write-Log "Stack Trace:" -level "DEBUG"
    Write-Log $exception.StackTrace -level "DEBUG"

    Write-Log "Detalles del Error Completo:" -level "DEBUG"
    Write-Log ($Error[0] | Format-List * -Force | Out-String) -level "DEBUG"

    switch ($exceptionType) {
        "Microsoft.ActiveDirectory.Management.ADIdentityAlreadyExistsException" {
            exit 1
        }
        "Microsoft.ActiveDirectory.Management.ADIdentityNotFoundException" {
            exit 2
        }
        "System.Security.Cryptography.CryptographicException" {
            exit 3
        }
        default {
            exit 99
        }
    }
}
