# ============================================
# SMART CORE ASSISTANT - INSTALAÇÃO AUTOMÁTICA
# ============================================
# Este script configura toda a infraestrutura
# necessária para o ambiente de teste local.
# Compatível com Windows 10/11 e Windows Server.
# ============================================

param(
    [switch]$SkipDockerCheck
)

$ErrorActionPreference = "Stop"

# Cores para output
function Write-Info { Write-Host "[INFO] $args" -ForegroundColor Cyan }
function Write-Success { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Warning { Write-Host "[AVISO] $args" -ForegroundColor Yellow }
function Write-Error2 { Write-Host "[ERRO] $args" -ForegroundColor Red }

# Banner
Write-Host "============================================" -ForegroundColor White
Write-Host "  SMART CORE ASSISTANT - TESTE LOCAL" -ForegroundColor White
Write-Host "============================================" -ForegroundColor White
Write-Host ""

# Verificar se Docker está instalado
function Test-DockerInstalled {
    try {
        $dockerVersion = docker --version 2>$null
        if ($dockerVersion) {
            Write-Success "Docker encontrado: $dockerVersion"
            return $true
        }
    }
    catch {
        # Docker não encontrado
    }
    return $false
}

# Verificar se Docker Desktop está rodando
function Test-DockerRunning {
    try {
        docker info 2>$null | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Instalar Docker Desktop
function Install-DockerDesktop {
    Write-Info "Docker não encontrado. Iniciando instalação..."
    
    $installerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $installerPath = "$env:TEMP\DockerDesktopInstaller.exe"
    
    Write-Info "Baixando Docker Desktop..."
    try {
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
    }
    catch {
        Write-Error2 "Falha ao baixar Docker Desktop."
        Write-Info "Por favor, instale manualmente: https://www.docker.com/products/docker-desktop"
        exit 1
    }
    
    Write-Info "Instalando Docker Desktop (isso pode demorar alguns minutos)..."
    Start-Process -FilePath $installerPath -ArgumentList "install", "--quiet" -Wait
    
    Write-Success "Docker Desktop instalado!"
    Write-Warning "IMPORTANTE: Reinicie o computador e execute este script novamente."
    
    Remove-Item $installerPath -Force
    exit 0
}

# Verificar Docker
function Verify-Docker {
    if (-not $SkipDockerCheck) {
        if (-not (Test-DockerInstalled)) {
            $response = Read-Host "Docker não encontrado. Deseja instalar? (S/N)"
            if ($response -eq "S" -or $response -eq "s") {
                Install-DockerDesktop
            }
            else {
                Write-Error2 "Docker é necessário para continuar."
                exit 1
            }
        }
        
        if (-not (Test-DockerRunning)) {
            Write-Warning "Docker Desktop não está em execução."
            Write-Info "Iniciando Docker Desktop..."
            Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
            
            Write-Info "Aguardando Docker iniciar (máximo 60 segundos)..."
            $timeout = 60
            $elapsed = 0
            while (-not (Test-DockerRunning) -and $elapsed -lt $timeout) {
                Start-Sleep -Seconds 3
                $elapsed += 3
                Write-Host "." -NoNewline
            }
            Write-Host ""
            
            if (-not (Test-DockerRunning)) {
                Write-Error2 "Docker não iniciou. Por favor, inicie manualmente e execute o script novamente."
                exit 1
            }
        }
        
        Write-Success "Docker está rodando!"
    }
}

# Validar arquivo .env
function Validate-EnvFile {
    Write-Info "Validando arquivo .env..."
    
    if (-not (Test-Path ".env")) {
        if (Test-Path ".env.local") {
            Write-Warning ".env não encontrado. Copiando de .env.local..."
            Copy-Item ".env.local" ".env"
            Write-Success "Arquivo .env criado a partir de .env.local"
        }
        else {
            Write-Error2 "Arquivo .env.local não encontrado!"
            exit 1
        }
    }

    Write-Success "Arquivo .env validado!"
}

# Subir containers
function Start-Containers {
    Write-Info "Iniciando containers..."
    
    docker compose up -d
    
    Write-Info "Aguardando containers ficarem saudáveis..."
    
    $timeout = 90
    $elapsed = 0
    
    while ($elapsed -lt $timeout) {
        try {
            # Verificar saúde de TODOS os containers
            $postgresClienteHealth = docker inspect --format='{{.State.Health.Status}}' smartcore_cliente_postgres_teste 2>$null
            $postgresEvolutionHealth = docker inspect --format='{{.State.Health.Status}}' smartcore_evolution_postgres_teste 2>$null
            $redisClienteHealth = docker inspect --format='{{.State.Health.Status}}' smartcore_cliente_redis_teste 2>$null
            $redisEvolutionHealth = docker inspect --format='{{.State.Health.Status}}' smartcore_evolution_redis_teste 2>$null
            
            if ($postgresClienteHealth -eq "healthy" -and $postgresEvolutionHealth -eq "healthy" -and $redisClienteHealth -eq "healthy" -and $redisEvolutionHealth -eq "healthy") {
                Write-Success "Todos os containers estão saudáveis!"
                break
            }
        }
        catch {
            # Container ainda não existe
        }
        
        Start-Sleep -Seconds 3
        $elapsed += 3
        Write-Host "." -NoNewline
    }
    Write-Host ""
    
    if ($elapsed -ge $timeout) {
        Write-Warning "Timeout aguardando containers. Verifique os logs."
    }
    
    # Mostrar status
    Write-Host ""
    Write-Info "Status dos containers:"
    docker compose ps
}

# Exibir informações finais
function Show-Summary {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "  AMBIENTE DE TESTE INICIADO!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    
    $serverIP = "192.168.3.127"
    
    Write-Success "Seus serviços estão rodando:"
    Write-Host ""
    Write-Host "  PostgreSQL (Django):    ${serverIP}:5436  (smartcore_cliente_db)"
    Write-Host "  PostgreSQL (Evolution): ${serverIP}:5437  (smartcore_evolution_db)"
    Write-Host "  Redis (Django):         ${serverIP}:6382"
    Write-Host "  Redis (Evolution):      ${serverIP}:6383"
    Write-Host "  Evolution API:          http://${serverIP}:8080"
    Write-Host ""
    Write-Info "Webhook configurado para: http://192.168.3.90:8000/sync/evolution/webhook/"
    Write-Host ""
    Write-Info "Para ver logs: docker compose logs -f"
}

# Execução principal
function Main {
    Verify-Docker
    Validate-EnvFile
    Start-Containers
    Show-Summary
}

Main
