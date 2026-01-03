# ============================================
# SMART CORE ASSISTANT - INSTALAÇÃO AUTOMÁTICA
# ============================================
# Este script configura toda a infraestrutura
# necessária para o ambiente do cliente.
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
Write-Host "  SMART CORE ASSISTANT - INSTALAÇÃO" -ForegroundColor White
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
        if (Test-Path ".env.example") {
            Write-Warning ".env não encontrado. Copiando de .env.example..."
            Copy-Item ".env.example" ".env"
            Write-Error2 "Por favor, edite o arquivo .env com suas configurações!"
            Write-Info "Execute: notepad .env"
            exit 1
        }
        else {
            Write-Error2 "Arquivo .env.example não encontrado!"
            exit 1
        }
    }

    # Verificar variáveis obrigatórias (incluindo Evolution PostgreSQL)
    $requiredVars = @(
        "TENANT_SLUG",
        "POSTGRES_PASSWORD",
        "EVOLUTION_POSTGRES_PASSWORD",
        "EVOLUTION_API_KEY",
        "WEBHOOK_CORE_URL"
    )
    $missingVars = @()
    
    $envContent = Get-Content ".env"
    
    foreach ($var in $requiredVars) {
        $found = $envContent | Where-Object { $_ -match "^$var=.+" }
        if (-not $found) {
            $missingVars += $var
        }
    }

    if ($missingVars.Count -gt 0) {
        Write-Error2 "Variáveis obrigatórias não configuradas:"
        foreach ($var in $missingVars) {
            Write-Host "  - $var"
        }
        Write-Info "Edite o arquivo .env e execute o script novamente."
        exit 1
    }

    Write-Success "Arquivo .env validado!"
}

# Configurar firewall
function Configure-Firewall {
    Write-Info "Configurando firewall do Windows..."
    
    try {
        # Verificar se as regras já existem (incluindo porta do Evolution PostgreSQL)
        $rules = @(
            @{Name = "SmartCore-PostgreSQL-Cliente"; Port = 5432; Description = "PostgreSQL do Cliente (Django)" },
            @{Name = "SmartCore-PostgreSQL-Evolution"; Port = 5433; Description = "PostgreSQL do Evolution API" },
            @{Name = "SmartCore-Redis-Cliente"; Port = 6379; Description = "Redis do Cliente (Django)" },
            @{Name = "SmartCore-Redis-Evolution"; Port = 6380; Description = "Redis do Evolution API" },
            @{Name = "SmartCore-Evolution"; Port = 8080; Description = "Evolution API para Smart Core Assistant" }
        )
        
        foreach ($rule in $rules) {
            $existingRule = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue
            if (-not $existingRule) {
                New-NetFirewallRule -DisplayName $rule.Name `
                    -Direction Inbound `
                    -Protocol TCP `
                    -LocalPort $rule.Port `
                    -Action Allow `
                    -Description $rule.Description | Out-Null
                Write-Success "Regra de firewall criada: $($rule.Name)"
            }
            else {
                Write-Info "Regra já existe: $($rule.Name)"
            }
        }
    }
    catch {
        Write-Warning "Não foi possível configurar o firewall automaticamente."
        Write-Info "Abra manualmente as portas: 5432, 5433, 6379, 6380, 8080"
    }
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
            $postgresClienteHealth = docker inspect --format='{{.State.Health.Status}}' smartcore_cliente_postgres 2>$null
            $postgresEvolutionHealth = docker inspect --format='{{.State.Health.Status}}' smartcore_evolution_postgres 2>$null
            $redisClienteHealth = docker inspect --format='{{.State.Health.Status}}' smartcore_cliente_redis 2>$null
            $redisEvolutionHealth = docker inspect --format='{{.State.Health.Status}}' smartcore_evolution_redis 2>$null
            
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
    Write-Host "  INSTALAÇÃO CONCLUÍDA!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    
    # Obter IP do servidor
    $serverIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.PrefixOrigin -eq "Dhcp" } | Select-Object -First 1).IPAddress
    if (-not $serverIP) {
        $serverIP = "localhost"
    }
    
    Write-Success "Seus serviços estão rodando:"
    Write-Host ""
    Write-Host "  PostgreSQL (Django):    ${serverIP}:5432  (smartcore_cliente_db)"
    Write-Host "  PostgreSQL (Evolution): ${serverIP}:5433  (smartcore_evolution_db)"
    Write-Host "  Redis (Django):         ${serverIP}:6379"
    Write-Host "  Redis (Evolution):      ${serverIP}:6380"
    Write-Host "  Evolution API:          http://${serverIP}:8080"
    Write-Host ""
    Write-Info "Próximos passos:"
    Write-Host "  1. Acesse o painel: https://smartcoreassistant.com.br/config"
    Write-Host "  2. Configure as credenciais do banco de dados (porta 5432)"
    Write-Host "  3. Configure a Evolution API"
    Write-Host "  4. Clique em 'Testar Conexão' e depois 'Executar Migrations'"
    Write-Host ""
    Write-Info "Para ver logs: docker compose logs -f"
}

# Execução principal
function Main {
    Verify-Docker
    Validate-EnvFile
    Configure-Firewall
    Start-Containers
    Show-Summary
}

Main
