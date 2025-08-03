#!/usr/bin/env pwsh
# Script simplificado para iniciar o ambiente Docker
# Smart Core Assistant Painel

# Configuracoes
$ErrorActionPreference = "Stop"
$ProjectName = "smart-core-assistant-painel"

# Funcao para escrever mensagens coloridas
function Write-Message {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    
    if ($Color -and $Color -ne "") {
        Write-Host $Message -ForegroundColor $Color
    } else {
        Write-Host $Message
    }
}

# Funcao para verificar se um comando existe
function Test-Command {
    param([string]$Command)
    
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Banner
Write-Message "Smart Core Assistant Painel - Docker Setup" "Cyan"
Write-Message "================================================" "Cyan"
Write-Message ""

# Verificar pre-requisitos
Write-Message "Verificando pre-requisitos..." "Yellow"

if (-not (Test-Command "docker")) {
    Write-Message "Docker nao encontrado. Instale o Docker Desktop." "Red"
    exit 1
}

Write-Message "Docker encontrado" "Green"

# Verificar se o arquivo .env existe
if (-not (Test-Path ".env")) {
    Write-Message "Arquivo .env nao encontrado." "Yellow"
    Write-Message "Criando arquivo .env basico..." "Yellow"
    
    # Gerar chaves secretas
    $DjangoSecret = -join ((1..50) | ForEach {[char]((65..90) + (97..122) + (48..57) | Get-Random)})
    $EvolutionSecret = -join ((1..32) | ForEach {[char]((65..90) + (97..122) + (48..57) | Get-Random)})
    $MongoPassword = -join ((1..16) | ForEach {[char]((65..90) + (97..122) + (48..57) | Get-Random)})
    $RedisPassword = -join ((1..16) | ForEach {[char]((65..90) + (97..122) + (48..57) | Get-Random)})
    
    # Solicitar OpenAI API Key
    $OpenAIKey = Read-Host "Digite sua OpenAI API Key"
    
    # Criar arquivo .env
    $EnvContent = @"
# Django Configuration
DJANGO_SECRET_KEY=$DjangoSecret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# OpenAI Configuration
OPENAI_API_KEY=$OpenAIKey

# Evolution API Configuration
EVOLUTION_API_URL=http://evolution-api:8080
EVOLUTION_API_KEY=$EvolutionSecret

# MongoDB Configuration
MONGO_HOST=mongodb
MONGO_PORT=27017
MONGO_DB=smart_core_db
MONGO_USER=admin
MONGO_PASSWORD=$MongoPassword

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=$RedisPassword

# Webhook Configuration
WEBHOOK_URL=http://django-app:8000/webhook/
WEBHOOK_SECRET=webhook_secret_key

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
WORKERS=4

# Security
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Logging
LOG_LEVEL=INFO
"@
    
    $EnvContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Message "Arquivo .env criado com sucesso!" "Green"
}

# Selecionar ambiente
Write-Message "Selecione o ambiente:" "Cyan"
Write-Message "1. Desenvolvimento (recomendado)" "White"
Write-Message "2. Desenvolvimento com ferramentas (MongoDB Express, Redis Commander)" "White"
Write-Message "3. Producao" "White"
Write-Message ""

$choice = Read-Host "Digite sua escolha (1-3)"

$composeFile = ""
$profileArgs = @()

switch ($choice) {
    "1" {
        $composeFile = "docker-compose.dev.yml"
        Write-Message "Iniciando ambiente de desenvolvimento..." "Cyan"
    }
    "2" {
        $composeFile = "docker-compose.dev.yml"
        $profileArgs = @("--profile", "tools")
        Write-Message "Iniciando ambiente de desenvolvimento com ferramentas..." "Cyan"
    }
    "3" {
        $composeFile = "docker-compose.yml"
        Write-Message "Iniciando ambiente de producao..." "Cyan"
    }
    default {
        Write-Message "Opcao invalida. Usando desenvolvimento por padrao." "Yellow"
        $composeFile = "docker-compose.dev.yml"
    }
}

# Construir e iniciar servicos
try {
    Write-Message "Construindo imagens..." "Yellow"
    $buildArgs = @("docker", "compose", "-f", $composeFile) + $profileArgs + @("build")
    & $buildArgs[0] $buildArgs[1..($buildArgs.Length-1)]
    
    Write-Message "Iniciando servicos..." "Yellow"
    $upArgs = @("docker", "compose", "-f", $composeFile) + $profileArgs + @("up", "-d")
    & $upArgs[0] $upArgs[1..($upArgs.Length-1)]
    
    Write-Message "Servicos iniciados com sucesso!" "Green"
    
    # Aguardar um pouco para os servicos iniciarem
    Write-Message "Aguardando servicos iniciarem..." "Yellow"
    Start-Sleep -Seconds 10
    
    # Executar migracoes
    Write-Message "Executando migracoes do Django..." "Yellow"
    & docker compose -f $composeFile exec django-app python src/smart_core_assistant_painel/app/ui/manage.py migrate
    
    # Coletar arquivos estaticos
    Write-Message "Coletando arquivos estaticos..." "Yellow"
    & docker compose -f $composeFile exec django-app python src/smart_core_assistant_painel/app/ui/manage.py collectstatic --noinput
    
    Write-Message "" 
    Write-Message "Configuracao concluida com sucesso!" "Green"
    Write-Message "" 
    Write-Message "URLs disponiveis:" "Cyan"
    Write-Message "   - Django: http://localhost:8000" "White"
    Write-Message "   - Evolution API: http://localhost:8080" "White"
    
    if ($choice -eq "2") {
        Write-Message "   - MongoDB Express: http://localhost:8081" "White"
        Write-Message "   - Redis Commander: http://localhost:8082" "White"
    }
    
    Write-Message "" 
    Write-Message "Comandos uteis:" "Cyan"
    Write-Message "   - Ver logs: docker compose -f $composeFile logs -f" "White"
    Write-Message "   - Parar servicos: docker compose -f $composeFile stop" "White"
    Write-Message "   - Remover containers: docker compose -f $composeFile down" "White"
    Write-Message "   - Acessar shell Django: docker compose -f $composeFile exec django-app bash" "White"
    
} catch {
    Write-Message "Erro ao iniciar servicos: $($_.Exception.Message)" "Red"
    exit 1
}

Write-Message "" 
Write-Message "Ambiente Docker configurado e em execucao!" "Green"