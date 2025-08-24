param(
    [switch]$CleanBuild
)

$ErrorActionPreference = 'Stop'

# Caminho do docker-compose.yml na raiz do projeto
$composeFile = Join-Path (Split-Path $PSScriptRoot -Parent) 'docker-compose.yml'
if (-not (Test-Path $composeFile)) {
    Write-Error 'Arquivo docker-compose.yml nao encontrado no diretorio raiz do projeto.'
    exit 1
}

Write-Host 'Iniciando setup do ambiente Django...' -ForegroundColor Cyan

# Garanta que Docker esteja disponivel
try {
    docker --version | Out-Null
} catch {
    Write-Error 'Docker nao esta instalado ou nao esta no PATH. Instale o Docker Desktop e tente novamente.'
    exit 1
}

# 1) Derrubar containers antigos
Write-Host 'Removendo containers anteriores...' -ForegroundColor Yellow
try { docker compose -f $composeFile down -v --remove-orphans } catch { }

# 2) Build das imagens
Write-Host 'Construindo imagens...' -ForegroundColor Cyan
if ($CleanBuild) {
    docker compose -f $composeFile build --no-cache
} else {
    docker compose -f $composeFile build
}
if ($LASTEXITCODE -ne 0) {
    Write-Error 'Falha ao construir imagens Docker.'
    exit 1
}

# 3) Subir os servicos
Write-Host 'Subindo servicos...' -ForegroundColor Cyan
docker compose -f $composeFile up -d
if ($LASTEXITCODE -ne 0) {
    Write-Error 'Falha ao subir os servicos com docker compose.'
    exit 1
}

# 4) Aguardar Postgres ficar pronto
Write-Host 'Aguardando PostgreSQL (postgres-django) ficar pronto...' -ForegroundColor Yellow
$maxAttempts = 60
$attempt = 0
$ready = $false
while (-not $ready -and $attempt -lt $maxAttempts) {
    $attempt++
    try {
        docker compose -f $composeFile exec -T postgres-django pg_isready -U postgres -d smart_core_db -h localhost | Out-Null
        if ($LASTEXITCODE -eq 0) { $ready = $true }
    } catch { }
    if (-not $ready) { Start-Sleep -Seconds 2 }
}
if (-not $ready) {
    Write-Error 'PostgreSQL nao ficou pronto a tempo. Verifique os logs com docker compose logs.'
    exit 1
}

# 5) Aguardar aplicação aplicar migrações (executadas no startup do container)
Write-Host 'Aguardando aplicação aplicar migrações e iniciar...' -ForegroundColor Yellow
$maxAttempts = 60
$attempt = 0
$ready = $false
while (-not $ready -and $attempt -lt $maxAttempts) {
    $attempt++
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/' -TimeoutSec 5
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) { $ready = $true }
    } catch { }
    if (-not $ready) { Start-Sleep -Seconds 2 }
}
if (-not $ready) {
    Write-Error 'Aplicação não iniciou a tempo. Verifique os logs com docker compose logs.'
    exit 1
}

# 6) Criar/atualizar superusuario admin (senha 123456) de forma idempotente
Write-Host 'Garantindo superusuario admin (senha: 123456)...' -ForegroundColor Cyan
# Caminho do script Python estatico
$srcPy = Join-Path $PSScriptRoot 'create_superuser.py'
if (-not (Test-Path $srcPy)) {
    Write-Error 'Arquivo create_superuser.py nao encontrado.'
    exit 1
}

# Obtem o container id do servico django-app e copia o arquivo
$containerId = (docker compose -f $composeFile ps -q django-app).Trim()
if (-not $containerId) { Write-Error 'Nao foi possivel obter o ID do container django-app.'; exit 1 }

docker cp $srcPy "${containerId}:/tmp/create_su.py"

# Executa o script dentro do container com o ambiente do projeto (via uv)
docker compose -f $composeFile exec -T django-app uv run python /tmp/create_su.py
if ($LASTEXITCODE -ne 0) {
    Write-Error 'Falha ao criar/atualizar o superusuario.'
    exit 1
}

# 7) Informacoes finais
Write-Host 'Setup concluido!' -ForegroundColor Green
Write-Host 'URLs disponiveis:' -ForegroundColor Cyan
Write-Host '  - Django App:   http://localhost:8000/'
Write-Host '  - Django Admin: http://localhost:8000/admin/'

# 8) Verificacao simples do servico
try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/' -TimeoutSec 10
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
        Write-Host "Servico Django acessivel (HTTP $($resp.StatusCode))." -ForegroundColor Green
    } else {
        Write-Host "Servico respondeu (HTTP $($resp.StatusCode)), verifique se esta tudo OK." -ForegroundColor Yellow
    }
} catch {
    Write-Host 'Nao foi possivel acessar http://localhost:8000/. Verifique os logs com docker compose logs.' -ForegroundColor Red
}