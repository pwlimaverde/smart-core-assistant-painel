# Docker Manager - Smart Core Assistant Painel
# Script único para configuração e gerenciamento do ambiente Docker
# PowerShell Script para Windows

param(
    [string]$Action = "help",
    [string]$Environment = "prod",
    [switch]$Tools,
    [switch]$Force,
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

# Função para verificar pré-requisitos
function Test-Prerequisites {
    Write-ColorMessage "`n[INFO] Verificando pre-requisitos..." "Yellow"
    
    $allOk = $true
    
    if (-not (Test-Command "docker")) {
        Write-ColorMessage "[ERRO] Docker nao encontrado. Instale o Docker Desktop primeiro." "Red"
        Write-ColorMessage "   Download: https://www.docker.com/products/docker-desktop" "Blue"
        $allOk = $false
    }
    
    if (-not (Test-Command "docker-compose")) {
        Write-ColorMessage "[ERRO] Docker Compose nao encontrado. Instale o Docker Compose primeiro." "Red"
        $allOk = $false
    }
    
    if (-not (Test-Command "python")) {
        Write-ColorMessage "[ERRO] Python nao encontrado. Instale o Python primeiro." "Red"
        Write-ColorMessage "   Download: https://www.python.org/downloads/" "Blue"
        $allOk = $false
    }
    
    # Verificar se Docker está rodando
    try {
        docker info | Out-Null
    }
    catch {
        Write-ColorMessage "[ERRO] Docker nao esta rodando. Por favor, inicie o Docker primeiro." "Red"
        $allOk = $false
    }
    
    if ($allOk) {
        Write-ColorMessage "[OK] Todos os pre-requisitos atendidos!" "Green"
    }
    
    return $allOk
}

# Função para configurar arquivo .env
function Set-EnvironmentFile {
    # Verificar se arquivo .env já existe
    $envExists = $false
    if (Test-Path ".env") {
        if (-not $Force) {
            Write-ColorMessage "`n[AVISO] Arquivo .env ja existe." "Yellow"
            $response = Read-Host "Deseja sobrescrever? (y/N)"
            if ($response -notmatch "^[Yy]$") {
                Write-ColorMessage "Mantendo arquivo .env existente." "Blue"
                return $true
            }
        }
    }
    
    Write-ColorMessage "`n[INFO] Configurando variaveis de ambiente..." "Yellow"
    
    # Gerar senhas e chaves
    $djangoSecret = New-DjangoSecret
    $evolutionApiKey = New-RandomPassword
    $webhookSecret = New-RandomPassword
    
    Write-ColorMessage "[OK] Chaves geradas automaticamente!" "Green"
    Write-ColorMessage "[INFO] SECRET_KEY_DJANGO: Gerada automaticamente" "Blue"
    Write-ColorMessage "[INFO] EVOLUTION_API_KEY: Gerada automaticamente" "Blue"
    Write-ColorMessage "[INFO] WEBHOOK_SECRET: Gerada automaticamente" "Blue"
    
    # Criar arquivo .env
    $envContent = @"
# Firebase Configuration
GOOGLE_APPLICATION_CREDENTIALS=src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/firebase_key.json

# Django Configuration
SECRET_KEY_DJANGO=$djangoSecret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Evolution API Configuration
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=$evolutionApiKey
EVOLUTION_API_GLOBAL_WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/

# PostgreSQL Configuration
POSTGRES_DB=smart_core_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Webhook Configuration
WEBHOOK_URL=http://localhost:8000/oraculo/webhook_whatsapp/
WEBHOOK_SECRET=$webhookSecret

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

# Ollama Configuration (for local development)
OLLAMA_HOST=localhost
OLLAMA_PORT=11434

# As seguintes variáveis são carregadas dinamicamente do Firebase Remote Config:
# - OPENAI_API_KEY
# - GROQ_API_KEY
# - WHATSAPP_API_BASE_URL
# - WHATSAPP_API_SEND_TEXT_URL
# - WHATSAPP_API_START_TYPING_URL
# - WHATSAPP_API_STOP_TYPING_URL
# - LLM_CLASS
# - MODEL
# - TEMPERATURE
# - PROMPT_SYSTEM_ANALISE_CONTEUDO
# - PROMPT_HUMAN_ANALISE_CONTEUDO
# - PROMPT_SYSTEM_MELHORIA_CONTEUDO
# - CHUNK_OVERLAP
# - CHUNK_SIZE
# - FAISS_MODEL
# - PROMPT_HUMAN_ANALISE_PREVIA_MENSAGEM
# - PROMPT_SYSTEM_ANALISE_PREVIA_MENSAGEM
# - VALID_ENTITY_TYPES
# - VALID_INTENT_TYPES
"@

    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-ColorMessage "[OK] Arquivo .env criado com sucesso!" "Green"
    Write-ColorMessage "[INFO] Credenciais geradas:" "Blue"
    Write-ColorMessage "   - SECRET_KEY_DJANGO: Gerada automaticamente" "Blue"
    Write-ColorMessage "   - EVOLUTION_API_KEY: $evolutionApiKey" "Blue"
    Write-ColorMessage "   - WEBHOOK_SECRET: Gerada automaticamente" "Blue"
    Write-ColorMessage "" 
    Write-ColorMessage "[IMPORTANTE] Configure o Firebase Remote Config" "Yellow"
    Write-ColorMessage "   1. Coloque o arquivo firebase_key.json em:" "Blue"
    Write-ColorMessage "      src/smart_core_assistant_painel/modules/initial_loading/utils/keys/firebase_config/" "Blue"
    Write-ColorMessage "   2. Configure as variáveis no Firebase Remote Config:" "Blue"
    Write-ColorMessage "      - OPENAI_API_KEY, GROQ_API_KEY, etc." "Blue"
    
    return $true
}

# Função para verificar Firebase
function Test-Firebase {
    $firebaseKeyPath = "..\src\smart_core_assistant_painel\modules\initial_loading\utils\keys\firebase_config\firebase_key.json"
    if (-not (Test-Path $firebaseKeyPath)) {
        Write-ColorMessage "[ERRO] Arquivo de credenciais do Firebase nao encontrado!" "Red"
        Write-ColorMessage "[INFO] Certifique-se de que o arquivo firebase_key.json esta presente em:" "Yellow"
        Write-ColorMessage "   $firebaseKeyPath" "Yellow"
        Write-ColorMessage "" 
        Write-ColorMessage "[DICA] Para obter as credenciais:" "Cyan"
        Write-ColorMessage "   1. Acesse o Console do Firebase" "White"
        Write-ColorMessage "   2. Vá em Configurações do Projeto > Contas de Serviço" "White"
        Write-ColorMessage "   3. Clique em 'Gerar nova chave privada'" "White"
        Write-ColorMessage "   4. Salve o arquivo como firebase_key.json no caminho indicado" "White"
        return $false
    }
    
    Write-ColorMessage "[OK] Credenciais do Firebase encontradas!" "Green"
    return $true
}

# Função para verificar Ollama (opcional)
function Test-Ollama {
    Write-ColorMessage "[INFO] Verificando se o Ollama esta rodando..." "Cyan"
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET -TimeoutSec 5 -ErrorAction Stop
        Write-ColorMessage "[OK] Ollama esta rodando!" "Green"
        return $true
    } catch {
        Write-ColorMessage "[AVISO] Ollama nao esta acessivel em localhost:11434" "Yellow"
        Write-ColorMessage "[INFO] Certifique-se de que o Ollama esta rodando localmente" "Yellow"
        Write-ColorMessage "[DICA] Para instalar/iniciar o Ollama: https://ollama.ai/" "Cyan"
        return $false
    }
}

# Função para construir imagens
function Build-Images {
    param([bool]$NoCache = $false)
    
    Write-ColorMessage "`n[INFO] Construindo imagens Docker..." "Yellow"
    
    try {
        if ($NoCache) {
            & docker compose build --no-cache
        } else {
            & docker compose build
        }
        
        if ($LASTEXITCODE -ne 0) { throw "Erro ao construir imagens" }
        Write-ColorMessage "[OK] Imagens construidas com sucesso!" "Green"
        return $true
    } catch {
        Write-ColorMessage "[ERRO] Erro ao construir imagens Docker: $_" "Red"
        return $false
    }
}

# Função para iniciar serviços
function Start-Services {
    param([string]$Env, [bool]$WithTools = $false)
    
    # Determinar configurações
    $composeFile = "..\docker-compose.yml"
    $composeProfiles = ""
    $envName = ""
    
    switch ($Env.ToLower()) {
        "prod" {
            $envName = "Produção"
        }
        "dev" {
            $envName = "Desenvolvimento"
        }
        default {
            Write-ColorMessage "Ambiente inválido. Usando produção." "Yellow"
            $envName = "Produção"
        }
    }
    
    if ($WithTools) {
        $composeProfiles = "--profile tools"
        $envName += " + Ferramentas"
    }
    
    Write-ColorMessage "`n[INFO] Ambiente selecionado: $envName" "Blue"
    
    # Parar containers existentes
    Write-ColorMessage "`n[INFO] Parando containers existentes..." "Yellow"
    & docker compose down
    
    # Iniciar serviços
    Write-ColorMessage "`n[INFO] Iniciando servicos ($envName)..." "Yellow"
    try {
        if ($composeProfiles) {
            $profileArgs = $composeProfiles.Split(' ')
            & docker compose -f $composeFile $profileArgs up -d
        } else {
            & docker compose -f $composeFile up -d
        }
        if ($LASTEXITCODE -ne 0) { throw "Erro ao iniciar serviços" }
    } catch {
        Write-ColorMessage "[ERRO] Erro ao iniciar servicos: $_" "Red"
        return $false
    }
    
    # Aguardar serviços ficarem prontos
    Write-ColorMessage "`n⏳ Aguardando serviços ficarem prontos..." "Yellow"
    Start-Sleep -Seconds 15
    
    return $true
}

# Função para executar migrações e setup
function Invoke-DatabaseSetup {
    Write-ColorMessage "`n[INFO] Executando migracoes do banco de dados..." "Yellow"
    try {
        & docker compose exec -T django-app python src/smart_core_assistant_painel/app/ui/manage.py migrate
        if ($LASTEXITCODE -ne 0) { 
            Write-ColorMessage "[AVISO] Erro ao executar migracoes. Verifique os logs." "Yellow"
        } else {
            Write-ColorMessage "[OK] Migracoes executadas com sucesso!" "Green"
        }
    } catch {
        Write-ColorMessage "[AVISO] Erro ao executar migracoes: $_" "Yellow"
    }
    
    Write-ColorMessage "`n[INFO] Coletando arquivos estaticos..." "Yellow"
    try {
        & docker compose exec -T django-app python src/smart_core_assistant_painel/app/ui/manage.py collectstatic --noinput
        if ($LASTEXITCODE -ne 0) { 
            Write-ColorMessage "[AVISO] Erro ao coletar arquivos estaticos. Verifique os logs." "Yellow"
        } else {
            Write-ColorMessage "[OK] Arquivos estaticos coletados com sucesso!" "Green"
        }
    } catch {
        Write-ColorMessage "[AVISO] Erro ao coletar arquivos estaticos: $_" "Yellow"
    }
}

# Função para mostrar status
function Show-Status {
    Write-ColorMessage "`n[INFO] Status dos servicos:" "Yellow"
    & docker compose ps
    
    Write-ColorMessage "`n[INFO] Logs do Django (ultimas 10 linhas):" "Cyan"
    & docker compose logs --tail=10 django-app
}

# Função para mostrar informações finais
function Show-FinalInfo {
    param([bool]$WithTools = $false)
    
    Write-ColorMessage "`n[OK] Configuracao concluida com sucesso!" "Green"
    Write-ColorMessage "`n[INFO] URLs de acesso:" "Blue"
    Write-ColorMessage "   - Django Admin: http://localhost:8000/admin/" "Blue"
    Write-ColorMessage "   - Evolution API: http://localhost:8080" "Blue"
    
    if ($WithTools) {
        Write-ColorMessage "   - MongoDB Express: http://localhost:8081" "Blue"
        Write-ColorMessage "   - Redis Commander: http://localhost:8082" "Blue"
    }
    
    Write-ColorMessage "`n[INFO] Proximos passos:" "Yellow"
    Write-ColorMessage "   1. Acesse http://localhost:8000/admin/ para criar um superusuário" "Yellow"
    Write-ColorMessage "   2. Configure sua instância do WhatsApp na Evolution API" "Yellow"
    Write-ColorMessage "   3. Teste o webhook em http://localhost:8000/oraculo/webhook_whatsapp/" "Yellow"
    
    Write-ColorMessage "`n[INFO] Comandos uteis:" "Blue"
    Write-ColorMessage "   - Ver logs: .\docker-manager.ps1 logs" "Blue"
    Write-ColorMessage "   - Parar: .\docker-manager.ps1 stop" "Blue"
    Write-ColorMessage "   - Reiniciar: .\docker-manager.ps1 restart" "Blue"
    Write-ColorMessage "   - Status: .\docker-manager.ps1 status" "Blue"
    Write-ColorMessage "   - Criar superusuário: .\docker-manager.ps1 createsuperuser" "Blue"
    
    Write-ColorMessage "`n[OK] Setup concluido! Bom desenvolvimento!" "Green"
}

# Função para mostrar ajuda
function Show-Help {
    Write-ColorMessage "[INFO] Docker Manager - Smart Core Assistant Painel" "Cyan"
    Write-ColorMessage "================================================" "Cyan"
    Write-ColorMessage "" 
    Write-ColorMessage "Uso: .\docker-manager.ps1 [AÇÃO] [OPÇÕES]" "Yellow"
    Write-ColorMessage "" 
    Write-ColorMessage "AÇÕES:" "Yellow"
    Write-ColorMessage "  setup       - Configuração inicial completa (padrão)" "White"
    Write-ColorMessage "  start       - Iniciar serviços" "White"
    Write-ColorMessage "  stop        - Parar serviços" "White"
    Write-ColorMessage "  restart     - Reiniciar serviços" "White"
    Write-ColorMessage "  status      - Mostrar status dos serviços" "White"
    Write-ColorMessage "  logs        - Mostrar logs" "White"
    Write-ColorMessage "  build       - Construir imagens" "White"
    Write-ColorMessage "  clean       - Limpeza completa" "White"
    Write-ColorMessage "  shell       - Acessar shell do Django" "White"
    Write-ColorMessage "  migrate     - Executar migrações" "White"
    Write-ColorMessage "  createsuperuser - Criar superusuário Django" "White"
    Write-ColorMessage "  help        - Mostrar esta ajuda" "White"
    Write-ColorMessage "" 
    Write-ColorMessage "OPÇÕES:" "Yellow"
    Write-ColorMessage "  -Environment [env]  - Ambiente: prod, dev (padrao: prod)" "White"
    Write-ColorMessage "  -Tools              - Incluir ferramentas (MongoDB Express, Redis Commander)" "White"
    Write-ColorMessage "  -Force              - Forçar sobrescrita de arquivos" "White"
    Write-ColorMessage "  -Help               - Mostrar esta ajuda" "White"
    Write-ColorMessage "" 
    Write-ColorMessage "EXEMPLOS:" "Yellow"
    Write-ColorMessage "  .\docker-manager.ps1 setup" "White"
    Write-ColorMessage "  .\docker-manager.ps1 setup -Environment dev -Tools" "White"
    Write-ColorMessage "  .\docker-manager.ps1 start -Tools" "White"
    Write-ColorMessage "  .\docker-manager.ps1 logs" "White"
    Write-ColorMessage "  .\docker-manager.ps1 clean -Force" "White"
}

# Função principal
function Main {
    # Mostrar ajuda se solicitado
    if ($Help -or $Action -eq "help") {
        Show-Help
        return
    }
    
    Write-ColorMessage "🚀 Docker Manager - Smart Core Assistant Painel" "Cyan"
    Write-ColorMessage "================================================" "Cyan"
    
    # Executar ação solicitada
    switch ($Action.ToLower()) {
        "setup" {
            # Configuração inicial completa
            if (-not (Test-Prerequisites)) { return }
            if (-not (Set-EnvironmentFile)) { return }
            if (-not (Test-Firebase)) { return }
            Test-Ollama | Out-Null
            if (-not (Build-Images)) { return }
            if (-not (Start-Services -Env $Environment -WithTools $Tools)) { return }
            Invoke-DatabaseSetup
            Show-Status
            Show-FinalInfo -WithTools $Tools
        }
        
        "start" {
            if (-not (Test-Prerequisites)) { return }
            if (-not (Start-Services -Env $Environment -WithTools $Tools)) { return }
            Show-Status
            Show-FinalInfo -WithTools $Tools
        }
        
        "stop" {
            Write-ColorMessage "`n[INFO] Parando servicos..." "Yellow"
            & docker compose down
            Write-ColorMessage "[OK] Servicos parados!" "Green"
        }
        
        "restart" {
            Write-ColorMessage "`n[INFO] Reiniciando servicos..." "Yellow"
            & docker compose restart
            Show-Status
        }
        
        "status" {
            Show-Status
        }
        
        "logs" {
            Write-ColorMessage "`n[INFO] Logs dos servicos:" "Cyan"
            & docker compose logs -f
        }
        
        "build" {
            if (-not (Test-Prerequisites)) { return }
            Build-Images -NoCache $Force
        }
        
        "clean" {
            if ($Force -or (Read-Host "Tem certeza que deseja fazer limpeza completa? (y/N)") -match "^[Yy]$") {
                Write-ColorMessage "`n[INFO] Fazendo limpeza completa..." "Yellow"
                & docker compose down -v --remove-orphans
                & docker compose down --rmi all
                Write-ColorMessage "[OK] Limpeza concluida!" "Green"
            }
        }
        
        "shell" {
            Write-ColorMessage "`n[INFO] Acessando shell do Django..." "Cyan"
            & docker compose exec django-app bash
        }
        
        "migrate" {
            Invoke-DatabaseSetup
        }
        
        "createsuperuser" {
            Write-ColorMessage "`n[INFO] Criando superusuario Django..." "Cyan"
            & docker compose exec django-app python src/smart_core_assistant_painel/app/ui/manage.py createsuperuser
        }
        
        default {
            Write-ColorMessage "[ERRO] Acao invalida: $Action" "Red"
            Write-ColorMessage "Use '.\docker-manager.ps1 help' para ver as opcoes disponiveis." "Yellow"
        }
    }
}

# Executar função principal
Main