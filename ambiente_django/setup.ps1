param(
    [switch]$CleanBuild
)

$ErrorActionPreference = 'Stop'

Write-Host "🚀 Iniciando setup do ambiente Django..." -ForegroundColor Cyan

# Garanta que Docker esteja disponível
try {
    docker --version | Out-Null
} catch {
    Write-Error "Docker não está instalado ou não está no PATH. Instale o Docker Desktop e tente novamente."
    exit 1
}

# 1) Derrubar containers antigos
Write-Host "⏹️  Removendo containers anteriores..." -ForegroundColor Yellow
try { docker compose down -v --remove-orphans } catch { }

# 2) Build das imagens (executa uv sync dentro do Dockerfile)
Write-Host "🔨 Construindo imagens..." -ForegroundColor Cyan
if ($CleanBuild) {
    docker compose build --no-cache
} else {
    docker compose build
}

# 3) Subir os serviços
Write-Host "📦 Subindo serviços..." -ForegroundColor Cyan
docker compose up -d

# 4) Aguardar Postgres ficar pronto
Write-Host "⏳ Aguardando PostgreSQL (postgres-django) ficar pronto..." -ForegroundColor Yellow
$maxAttempts = 60
$attempt = 0
$ready = $false
while (-not $ready -and $attempt -lt $maxAttempts) {
    $attempt++
    try {
        docker compose exec -T postgres-django pg_isready -U postgres -d smart_core_db -h localhost | Out-Null
        if ($LASTEXITCODE -eq 0) { $ready = $true }
    } catch { }
    if (-not $ready) { Start-Sleep -Seconds 2 }
}
if (-not $ready) {
    Write-Error "PostgreSQL não ficou pronto a tempo. Verifique os logs com 'docker compose logs'."
    exit 1
}

# 5) Sincronizar dependências com uv (garante consistência quando pyproject.toml está montado via volume)
Write-Host "📦 Sincronizando dependências (uv sync)..." -ForegroundColor Cyan
docker compose exec -T django-app uv sync --frozen

# 6) Aplicar migrações
Write-Host "📊 Aplicando migrações do Django..." -ForegroundColor Cyan
docker compose exec -T django-app uv run python src/smart_core_assistant_painel/app/ui/manage.py migrate

# 7) Criar/atualizar superusuário admin (senha 123456) de forma idempotente
Write-Host "👤 Garantindo superusuário admin (senha: 123456)..." -ForegroundColor Cyan
# Gera script Python localmente e copia para dentro do container para evitar problemas de quoting
$pyContent = @'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "smart_core_assistant_painel.app.ui.core.settings")
django.setup()
from django.contrib.auth import get_user_model
U = get_user_model()
u, created = U.objects.get_or_create(username="admin", defaults={"email": "admin@example.com"})
u.is_superuser = True
u.is_staff = True
u.set_password("123456")
u.save()
print("created" if created else "updated")
'@

# Cria arquivo temporário local
$tmpPy = Join-Path $env:TEMP "create_su.py"
$pyContent | Out-File -FilePath $tmpPy -Encoding UTF8 -Force

# Obtém o container id do serviço django-app e copia o arquivo
$containerId = (docker compose ps -q django-app).Trim()
if (-not $containerId) { Write-Error "Não foi possível obter o ID do container django-app."; exit 1 }

# Usar ${containerId} para delimitar corretamente a variável no PowerShell
docker cp $tmpPy "${containerId}:/tmp/create_su.py"

# Executa o script dentro do container com o ambiente do projeto
docker compose exec -T django-app uv run python /tmp/create_su.py

# Limpa arquivo temporário local
Remove-Item -Path $tmpPy -Force -ErrorAction SilentlyContinue

# 8) Informações finais
Write-Host "✅ Setup concluído!" -ForegroundColor Green
Write-Host "URLs disponíveis:" -ForegroundColor Cyan
Write-Host "  - Django App:   http://localhost:8000/"
Write-Host "  - Django Admin: http://localhost:8000/admin/"

# 9) Verificação simples do serviço
try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8000/' -TimeoutSec 10
    if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
        Write-Host "🟢 Serviço Django acessível (HTTP $($resp.StatusCode))." -ForegroundColor Green
    } else {
        Write-Host "🟡 Serviço respondeu (HTTP $($resp.StatusCode)), verifique se está tudo OK." -ForegroundColor Yellow
    }
} catch {
    Write-Host '🔴 Não foi possível acessar http://localhost:8000/. Verifique os logs com "docker compose logs".' -ForegroundColor Red
}