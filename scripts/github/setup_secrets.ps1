# ============================================
# Script para Configurar GitHub Secrets
# Deploy Automático via Tags
# ============================================
#
# Pré-requisitos:
#   1. gh CLI instalado (winget install GitHub.cli)
#   2. Autenticado com: gh auth login
#
# Uso:
#   .\scripts\github\setup_secrets.ps1
#
# ============================================

$ErrorActionPreference = "Stop"

Write-Host "=== Configurando GitHub Secrets para Deploy ===" -ForegroundColor Cyan

# Verificar autenticação
Write-Host "`nVerificando autenticação do gh CLI..." -ForegroundColor Yellow
$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: gh CLI não autenticado. Execute: gh auth login" -ForegroundColor Red
    exit 1
}
Write-Host "OK - Autenticado" -ForegroundColor Green

# Definir repositório
$repo = "pwlimaverde/smart-core-assistant-painel"

# Secrets a configurar
$secrets = @{
    "SERVER_HOST" = "76.13.229.210"
    "SERVER_USER" = "root"
    "SERVER_PORT" = "22"
}

# Configurar secrets simples
foreach ($key in $secrets.Keys) {
    Write-Host "`nConfigurando $key..." -ForegroundColor Yellow
    echo $secrets[$key] | gh secret set $key --repo $repo
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK - $key configurado" -ForegroundColor Green
    } else {
        Write-Host "ERRO ao configurar $key" -ForegroundColor Red
    }
}

# Configurar chave SSH (arquivo)
$sshKeyPath = "$env:USERPROFILE\.ssh\id_hostinger_root"
if (Test-Path $sshKeyPath) {
    Write-Host "`nConfigurando SERVER_SSH_KEY (chave privada)..." -ForegroundColor Yellow
    Get-Content $sshKeyPath -Raw | gh secret set SERVER_SSH_KEY --repo $repo
    if ($LASTEXITCODE -eq 0) {
        Write-Host "OK - SERVER_SSH_KEY configurado" -ForegroundColor Green
    } else {
        Write-Host "ERRO ao configurar SERVER_SSH_KEY" -ForegroundColor Red
    }
} else {
    Write-Host "AVISO: Chave SSH não encontrada em $sshKeyPath" -ForegroundColor Yellow
    Write-Host "Configure manualmente: gh secret set SERVER_SSH_KEY < chave_privada.txt" -ForegroundColor Yellow
}

Write-Host "`n=== Configuração Concluída ===" -ForegroundColor Cyan
Write-Host "`nPara verificar: gh secret list --repo $repo" -ForegroundColor Gray
Write-Host "`nPróximo passo: criar tag v1.0.0 para disparar deploy" -ForegroundColor Gray
Write-Host "  git tag -a v1.0.0 -m 'Release 1.0.0'" -ForegroundColor White
Write-Host "  git push origin v1.0.0" -ForegroundColor White
