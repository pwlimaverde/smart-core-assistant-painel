# Script de configuração inicial para Docker
# Smart Core Assistant Painel + Evolution API
# PowerShell Script para Windows

param(
    [string]$Environment = "prod",
    [switch]$Help
)

# Função para imprimir mensagens coloridas
function Write-ColorMessage {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    if ($Color -eq "") {
        $Color = "White"
    }
    Write-Host $Message -ForegroundColor $Color
}

# Função para verificar se comando existe
function Test-Command {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Função para gerar chave secreta Django
function New-DjangoSecret {
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)"
    $secret = ""
    for ($i = 0; $i -lt 50; $i++) {
        $secret += $chars[(Get-Random -Maximum $chars.Length)]
    }
    return $secret
}

# Função para gerar senha aleatória
function New-RandomPassword {
    param([int]$Length = 25)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    $password = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $password += $chars[(Get-Random -Maximum $chars.Length)]
    }
    return $password
}

# Mostrar ajuda
if ($Help) {
    Write-ColorMessage "🚀 Script de Configuração Docker - Smart Core Assistant Painel" "Cyan"
    Write-ColorMessage "" 
    Write-ColorMessage "Uso: .\setup-docker.ps1 [-Environment <env>] [-Help]" "Yellow"
    Write-ColorMessage "" 
    Write-ColorMessage "Parâmetros:" "Yellow"
    Write-ColorMessage "  -Environment: prod, dev, dev-tools (padrão: prod)" "White"
    Write-ColorMessage "  -Help: Mostra esta ajuda" "White"
    Write-ColorMessage "" 
    Write-ColorMessage "Exemplos:" "Yellow"
    Write-ColorMessage "  .\setup-docker.ps1" "White"
    Write-ColorMessage "  .\setup-docker.ps1 -Environment dev" "White"
    Write-ColorMessage "  .\setup-docker.ps1 -Environment dev-tools" "White"
    exit 0
}

Write-ColorMessage "🚀 Configuração Docker - Smart Core Assistant Painel" "Cyan"
Write-ColorMessage "================================================" "Cyan"

# Verificar pré-requisitos
Write-ColorMessage "`n📋 Verificando pré-requisitos..." "Yellow"

if (-not (Test-Command "docker")) {
    Write-ColorMessage "❌ Docker não encontrado. Instale o Docker Desktop primeiro." "Red"
    Write-ColorMessage "   Download: https://www.docker.com/products/docker-desktop" "Blue"
    exit 1
}

if (-not (Test-Command "docker-compose")) {
    Write-ColorMessage "❌ Docker Compose não encontrado. Instale o Docker Compose primeiro." "Red"
    exit 1
}

if (-not (Test-Command "python")) {
    Write-ColorMessage "❌ Python não encontrado. Instale o Python primeiro." "Red"
    Write-ColorMessage "   Download: https://www.python.org/downloads/" "Blue"
    exit 1
}

Write-ColorMessage "✅ Todos os pré-requisitos atendidos!" "Green"

# Verificar se arquivo .env já existe
$envExists = $false
if (Test-Path ".env") {
    Write-ColorMessage "`n⚠️  Arquivo .env já existe." "Yellow"
    $response = Read-Host "Deseja sobrescrever? (y/N)"
    if ($response -notmatch "^[Yy]$") {
        Write-ColorMessage "Mantendo arquivo .env existente." "Blue"
        $envExists = $true
    }
}

# Criar arquivo .env se não existir ou se usuário escolheu sobrescrever
if (-not $envExists) {
    Write-ColorMessage "`n🔧 Configurando variáveis de ambiente..." "Yellow"
    
    # Gerar senhas e chaves
    $djangoSecret = New-DjangoSecret
    $evolutionApiKey = New-RandomPassword
    $mongoPassword = New-RandomPassword
    $redisPassword = New-RandomPassword
    
    # Solicitar OpenAI API Key
    Write-Host ""
    $openaiApiKey = Read-Host "Digite sua OpenAI API Key"
    
    # Criar arquivo .env
    $envContent = @"
# Django Configuration
SECRET_KEY_DJANGO=$djangoSecret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# OpenAI Configuration
OPENAI_API_KEY=$openaiApiKey

# Evolution API Configuration
EVOLUTION_API_KEY=$evolutionApiKey
EVOLUTION_API_URL=http://localhost:8080

# Database Configuration (MongoDB for Evolution API)
MONGO_USERNAME=admin
MONGO_PASSWORD=$mongoPassword

# Redis Configuration
REDIS_PASSWORD=$redisPassword

# Webhook Configuration
WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/

# Server Configuration
SERVER_PORT=8000
EVOLUTION_PORT=8080

# Security
CORS_ORIGIN=*

# Logging
LOG_LEVEL=INFO
"@

    $envContent | Out-File -FilePath ".env" -Encoding UTF8

    Write-ColorMessage "✅ Arquivo .env criado com sucesso!" "Green"
    Write-ColorMessage "📝 Credenciais geradas:" "Blue"
    Write-ColorMessage "   - Evolution API Key: $evolutionApiKey" "Blue"
    Write-ColorMessage "   - MongoDB Password: $mongoPassword" "Blue"
    Write-ColorMessage "   - Redis Password: $redisPassword" "Blue"
}

# Determinar arquivo de compose e configurações
$composeFile = ""
$composeProfiles = ""
$envName = ""

switch ($Environment.ToLower()) {
    "prod" {
        $composeFile = "docker-compose.yml"
        $envName = "Produção"
    }
    "dev" {
        $composeFile = "docker-compose.yml"
        $envName = "Desenvolvimento"
    }
    "dev-tools" {
        $composeFile = "docker-compose.yml"
        $composeProfiles = "--profile tools"
        $envName = "Desenvolvimento + Ferramentas"
    }
    default {
        Write-ColorMessage "Ambiente inválido. Usando produção." "Yellow"
        $composeFile = "docker-compose.yml"
        $envName = "Produção"
    }
}

Write-ColorMessage "`n🏗️  Ambiente selecionado: $envName" "Blue"

Write-ColorMessage "`n🔨 Construindo imagens Docker..." "Yellow"
try {
    & docker compose -f $composeFile build
    if ($LASTEXITCODE -ne 0) { throw "Erro ao construir imagens" }
} catch {
    Write-ColorMessage "❌ Erro ao construir imagens Docker: $_" "Red"
    exit 1
}

Write-ColorMessage "`n🚀 Iniciando serviços ($envName)..." "Yellow"
try {
    if ($composeProfiles) {
        $profileArgs = $composeProfiles.Split(' ')
        & docker compose -f $composeFile $profileArgs up -d
    } else {
        & docker compose -f $composeFile up -d
    }
    if ($LASTEXITCODE -ne 0) { throw "Erro ao iniciar serviços" }
} catch {
    Write-ColorMessage "❌ Erro ao iniciar serviços: $_" "Red"
    exit 1
}

# Aguardar serviços ficarem prontos
Write-ColorMessage "`n⏳ Aguardando serviços ficarem prontos..." "Yellow"
Start-Sleep -Seconds 15

# Executar migrações
Write-ColorMessage "`n📊 Executando migrações do banco de dados..." "Yellow"
try {
    & docker compose -f $composeFile exec -T django-app python src/smart_core_assistant_painel/app/ui/manage.py migrate
    if ($LASTEXITCODE -ne 0) { 
        Write-ColorMessage "⚠️  Aviso: Erro ao executar migrações. Verifique os logs." "Yellow"
    }
} catch {
    Write-ColorMessage "⚠️  Aviso: Erro ao executar migrações: $_" "Yellow"
}

# Coletar arquivos estáticos
Write-ColorMessage "`n📁 Coletando arquivos estáticos..." "Yellow"
try {
    & docker compose -f $composeFile exec -T django-app python src/smart_core_assistant_painel/app/ui/manage.py collectstatic --noinput
    if ($LASTEXITCODE -ne 0) { 
        Write-ColorMessage "⚠️  Aviso: Erro ao coletar arquivos estáticos. Verifique os logs." "Yellow"
    }
} catch {
    Write-ColorMessage "⚠️  Aviso: Erro ao coletar arquivos estáticos: $_" "Yellow"
}

# Verificar status dos serviços
Write-ColorMessage "`n📊 Status dos serviços:" "Yellow"
& docker compose -f $composeFile ps

# Informações finais
Write-ColorMessage "`n🎉 Configuração concluída com sucesso!" "Green"
Write-ColorMessage "`n📱 URLs de acesso:" "Blue"
Write-ColorMessage "   - Django Admin: http://localhost:8000/admin/" "Blue"
Write-ColorMessage "   - Evolution API: http://localhost:8080" "Blue"

if ($Environment -eq "dev-tools") {
    Write-ColorMessage "   - MongoDB Express: http://localhost:8081" "Blue"
    Write-ColorMessage "   - Redis Commander: http://localhost:8082" "Blue"
}

Write-ColorMessage "`n🔧 Próximos passos:" "Yellow"
Write-ColorMessage "   1. Acesse http://localhost:8000/admin/ para criar um superusuário" "Yellow"
Write-ColorMessage "   2. Configure sua instância do WhatsApp na Evolution API" "Yellow"
Write-ColorMessage "   3. Teste o webhook em http://localhost:8000/oraculo/webhook_whatsapp/" "Yellow"

Write-ColorMessage "`n📚 Comandos úteis:" "Blue"
Write-ColorMessage "   - Ver logs: docker compose -f $composeFile logs -f" "Blue"
Write-ColorMessage "   - Parar: docker compose -f $composeFile down" "Blue"
Write-ColorMessage "   - Reiniciar: docker compose -f $composeFile restart" "Blue"
Write-ColorMessage "   - Criar superusuário: docker compose -f $composeFile exec django-app python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser" "Blue"

Write-ColorMessage "`n✨ Setup concluído! Bom desenvolvimento!" "Green"