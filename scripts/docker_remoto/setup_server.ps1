<#
.SYNOPSIS
    Configura o servidor Windows para aceitar conexões SSH sem senha.

.DESCRIPTION
    Este script realiza a configuração completa do OpenSSH Server no Windows:
    1. Instala o OpenSSH Server (se necessário)
    2. Configura e inicia o serviço sshd
    3. Abre a porta 22 no firewall
    4. Configura a chave pública autorizada para administradores
    5. Ajusta permissões de acordo com os requisitos do Windows

.PARAMETER PublicKey
    A chave pública SSH a ser autorizada (formato: ssh-ed25519 AAAA... comment)
    Se não fornecida, solicita interativamente.

.EXAMPLE
    .\setup_server.ps1 -PublicKey "ssh-ed25519 AAAAC3NzaC... user@host"

.NOTES
    Requer execução como Administrador.
    Autor: Smart Core Assistant
#>

param(
    [string]$PublicKey
)

# Garantir que está rodando como Admin
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "[ERRO] Execute este script como Administrador!" -ForegroundColor Red
    exit 1
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  SETUP SSH SERVER - SMART CORE ASSISTANT  " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# 1. Solicitar chave se não fornecida
if (-not $PublicKey) {
    Write-Host "`n[INPUT] Cole a chave pública SSH (ssh-ed25519 AAAA...):" -ForegroundColor Yellow
    $PublicKey = Read-Host
}

if (-not $PublicKey -or $PublicKey.Length -lt 50) {
    Write-Host "[ERRO] Chave pública inválida ou muito curta!" -ForegroundColor Red
    exit 1
}

# 2. Instalar OpenSSH Server
Write-Host "`n[1/5] Verificando OpenSSH Server..." -ForegroundColor Yellow
$sshCapability = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'
if ($sshCapability.State -ne 'Installed') {
    Write-Host "      -> Instalando (pode demorar)..." -ForegroundColor Magenta
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
    Write-Host "      [OK] Instalado!" -ForegroundColor Green
} else {
    Write-Host "      [OK] Já instalado." -ForegroundColor Green
}

# 3. Configurar e iniciar serviço
Write-Host "`n[2/5] Configurando serviço sshd..." -ForegroundColor Yellow
Stop-Service sshd -ErrorAction SilentlyContinue
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
$status = (Get-Service sshd).Status
if ($status -eq 'Running') {
    Write-Host "      [OK] Serviço rodando." -ForegroundColor Green
} else {
    Write-Host "      [ERRO] Serviço não iniciou ($status)" -ForegroundColor Red
    exit 1
}

# 4. Configurar Firewall
Write-Host "`n[3/5] Configurando Firewall (porta 22)..." -ForegroundColor Yellow
Remove-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -DisplayName "OpenSSH Server (sshd)" `
    -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22 | Out-Null
Write-Host "      [OK] Porta 22 liberada." -ForegroundColor Green

# 5. Configurar chave para administradores
Write-Host "`n[4/5] Configurando chave autorizada..." -ForegroundColor Yellow
$adminKeyFile = "$env:ProgramData\ssh\administrators_authorized_keys"

# Salvar chave
Set-Content $adminKeyFile $PublicKey -Force

# Configurar permissões estritas (CRÍTICO para funcionar)
$acl = Get-Acl $adminKeyFile
$acl.SetAccessRuleProtection($true, $false)

$adminSid  = New-Object System.Security.Principal.SecurityIdentifier("S-1-5-32-544")
$systemSid = New-Object System.Security.Principal.SecurityIdentifier("S-1-5-18")

$ruleAdmin  = New-Object System.Security.AccessControl.FileSystemAccessRule($adminSid, "FullControl", "Allow")
$ruleSystem = New-Object System.Security.AccessControl.FileSystemAccessRule($systemSid, "FullControl", "Allow")

$acl.AddAccessRule($ruleAdmin)
$acl.AddAccessRule($ruleSystem)
Set-Acl $adminKeyFile $acl

Write-Host "      [OK] Chave salva em: $adminKeyFile" -ForegroundColor Green

# 6. Garantir sshd_config correto para admins
Write-Host "`n[5/5] Validando sshd_config..." -ForegroundColor Yellow
$configPath = "$env:ProgramData\ssh\sshd_config"
$content = Get-Content $configPath
$needsRestart = $false

# Verificar se as linhas de admin estão ativas
$hasMatchAdmin = $content | Where-Object { $_ -match "^Match Group administrators" }
$hasAdminKeys  = $content | Where-Object { $_ -match "AuthorizedKeysFile __PROGRAMDATA__" }

if (-not $hasMatchAdmin -or -not $hasAdminKeys) {
    # Adicionar linhas no final se não existirem
    $adminConfig = @"

Match Group administrators
       AuthorizedKeysFile __PROGRAMDATA__/ssh/administrators_authorized_keys
"@
    Add-Content $configPath $adminConfig
    $needsRestart = $true
    Write-Host "      -> Adicionadas linhas de admin no sshd_config" -ForegroundColor Cyan
}

if ($needsRestart) {
    Restart-Service sshd
    Write-Host "      [OK] Serviço reiniciado." -ForegroundColor Green
} else {
    Write-Host "      [OK] Configuração já presente." -ForegroundColor Green
}

# Resultado final
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "  CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!       " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Cyan

$ip = (Get-NetIPAddress | Where-Object { $_.AddressFamily -eq 'IPv4' -and $_.PrefixOrigin -eq 'Dhcp' } | Select-Object -First 1).IPAddress
if (-not $ip) {
    $ip = (Get-NetIPAddress | Where-Object { $_.AddressFamily -eq 'IPv4' -and $_.InterfaceAlias -notlike '*Loopback*' } | Select-Object -First 1).IPAddress
}

$user = $env:USERNAME
Write-Host "`nConecte-se com:" -ForegroundColor Yellow
Write-Host "  ssh $user@$ip" -ForegroundColor White
Write-Host "`n(Não deve pedir senha se a chave estiver correta)" -ForegroundColor Gray
